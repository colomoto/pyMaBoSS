"""Class that handles the parameters of a MaBoSS simulation.
"""

from __future__ import print_function
import collections
from sys import stderr, stdout, version_info
if version_info[0] < 3:
    from contextlib2 import ExitStack
else:
    from contextlib import ExitStack

from colomoto import ModelState

from .result import Result
from .cmabossresult import CMaBoSSResult
import os
import uuid
import subprocess
import tempfile
import shutil
from colomoto_jupyter import import_colomoto_tool
from colomoto_jupyter.sessionfiles import new_output_file

_default_parameter_list = collections.OrderedDict([
    ('time_tick', 0.1),
    ('max_time', 4),
    ('sample_count', 10000),
    ('discrete_time', 0),
    ('use_physrandgen', 1),
    ('seed_pseudorandom', 0),
    ('display_traj', 0),
    ('statdist_traj_count', 0),
    ('statdist_cluster_threshold', 1),
    ('thread_count', 1),
    ('statdist_similarity_cache_max_size', 20000)
])

class Simulation(object):
    """
    Class that handles MaBoSS simulations.


    .. py:attribute:: network

      A Network object, that will be translated in a bnd file

    .. py:attribute:: mutations

      A list of nodes for which mutation can be triggered by
      modifying the cfg file

    .. py:attribute:: palette

      A mapping of nodes to color for plotting the results of
      the simulation.

    .. py:attribute:: param

      A dictionary that contains global variables (keys starting with a '$'),
      and simulation parameters (keys not starting with a '$').
    """


    def __init__(self, nt, parameters=collections.OrderedDict({}), command=None, **kwargs):
        """
        Initialize the Simulation object.

        :param nt: the network associated with the simulation.
        :type nt: :py:class:`Network`
        :param dict kwargs: parameters of the simulation
        """
        self.param = _default_parameter_list.copy()
        self.palette = {}
        for cfg in (parameters, kwargs):
            for p in cfg:
                if p in _default_parameter_list or p[0] == '$':
                    self.param[p] = cfg[p]
                elif p == "palette":
                    self.palette = kwargs[p]
                else:
                    print("Warning: unused parameter %s" % p, file=stderr)

        self.network = nt
        self.mutations = []
        self.mutationTypes = {}
        self.refstate = {}

        self.workdir = None
        self.overwrite = False

        errors = self.check(command=command)
        if len(errors) > 0:
            print(errors)

    def update_parameters(self, **kwargs):
        """Add elements to ``self.param``."""
        for p in kwargs:
            if p in _default_parameter_list or p[0] == '$':
                self.param[p] = kwargs[p]
            else:
                print("Warning: unused parameter %s" % p, file=stderr)

    def copy(self):
        new_network = self.network.copy()
        result = Simulation(new_network, self.param, palette=self.palette)
        if self.mutations:
            result.mutations = self.mutations.copy()
        return result

    def check(self, command=None):

        try:
            path = tempfile.mkdtemp()
            cfg_fd, cfg_path = tempfile.mkstemp(dir=path, suffix='.cfg')
            os.close(cfg_fd)
            bnd_fg, bnd_path = tempfile.mkstemp(dir=path, suffix='.bnd')
            os.close(bnd_fg)

            with ExitStack() as stack:
                bnd_file = stack.enter_context(open(bnd_path, 'w'))
                cfg_file = stack.enter_context(open(cfg_path, 'w'))
                self.print_bnd(out=bnd_file)
                self.print_cfg(out=cfg_file)

            maboss_cmd = self.get_maboss_cmd()
            if command is not None:
                maboss_cmd = command

            proc = subprocess.Popen(
                [maboss_cmd, "--check", "-c", cfg_path, bnd_path],
                cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            (t_stdout, t_stderr) = proc.communicate()

            shutil.rmtree(path)

            messages = []
            if len(t_stderr) != 0:
                messages = [mess.replace("MaBoSS: ", "") for mess in list(set(t_stderr.decode().split("\n"))) if mess != '']

            return messages

        except ValueError as e:
            return [str(e)]

    def get_maboss_cmd(self):

        maboss_cmd = "MaBoSS"

        l = len(self.network)
        assert l <= 1024, "Models with more than 1024 nodes are not compatible with this version of MaBoSS"

        if l <= 64:
            pass
        elif l <= 128:
            maboss_cmd = "MaBoSS_128n"
        elif l <= 256:
            maboss_cmd = "MaBoSS_256n"
        elif l <= 512:
            maboss_cmd = "MaBoSS_512n"
        else:
            maboss_cmd = "MaBoSS_1024n"

        return maboss_cmd

    def get_cmaboss(self):
        l = len(self.network)
        assert l <= 1024, "Models with more than 1024 nodes are not compatible with this version of MaBoSS"

        if l <= 64:
            return __import__("cmaboss")
        elif l <= 128:
            return __import__("cmaboss_128n")
        elif l <= 256:
            return __import__("cmaboss_256n")
        elif l <= 512:
            return __import__("cmaboss_512n")
        else:
            return __import__("cmaboss_1024n")

    def print_bnd(self, out=stdout):
        """Produce the content of the bnd file associated to the simulation."""
        print(self.network, file=out)

    def print_cfg(self, out=stdout):
        """Produce the content of the cfg file associated to the simulation."""
        print(self.str_cfg(), file=out)

    def str_cfg(self):

        res = "$nb_mutable = %d;\n" % len(self.mutations)
        for p in self.param:
            if p[0] == '$':
                res += "%s = %s;\n" % (p, self.param[p])

        res += self.network.str_istate() + "\n"
        res += "\n"

        for p in self.param:
            if p[0] != '$':
                res += "%s = %s;\n" % (p, self.param[p])

        for name in self.network.names:
            res += "%s.is_internal = %s;\n" % (name, self.network[name].is_internal)

        for nd in self.refstate:
            res += "%s.refstate = %s;\n" % (nd, self.refstate[nd])

        return res

    def get_logical_rules(self):

        path = tempfile.mkdtemp()
        cfg_fd, cfg_path = tempfile.mkstemp(dir=path, suffix='.cfg')
        os.close(cfg_fd)
        bnd_fd, bnd_path = tempfile.mkstemp(dir=path, suffix='.bnd')
        os.close(bnd_fd)
        
        with ExitStack() as stack:
            bnd_file = stack.enter_context(open(bnd_path, 'w'))
            cfg_file = stack.enter_context(open(cfg_path, 'w'))
            self.print_bnd(out=bnd_file)
            self.print_cfg(out=cfg_file)

        proc = subprocess.Popen(
            [self.get_maboss_cmd(), "-c", cfg_path, "-l", bnd_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = proc.communicate()

        if proc.returncode != 0:
            raise Exception(err.decode())
            
        rules = {}
        for line in out.decode().split("\n"):
            if ":" in line:
                node, rule = line.split(" : ", 1)
                rules.update({node.strip(): rule.strip()})

        return rules



    def run(self, command=None, workdir=None, overwrite=False, prefix="res", cmaboss=False, only_final_state=False):
        """Run the simulation with MaBoSS and return a Result object.

        :param command: specify a MaBoSS command, default to None for automatic selection
        :rtype: :py:class:`Result`
        """
        if cmaboss:
            return CMaBoSSResult(self, workdir=workdir, overwrite=overwrite, only_final_state=only_final_state)

        if workdir is not None:
            self.workdir = workdir

        if overwrite:
            self.overwrite = overwrite
            
        return Result(self, command, self.workdir, self.overwrite, prefix)


    def mutate(self, node, state):
        """
        Trigger or untrigger mutation for a node.

        :param node: The :py:class:`Node` to be modified
        :type node: :py:class:`Node`
        :param str State:

            * ``'ON'`` (always up)
            * ``'OFF'`` (always down)
            * ``'WT'`` (mutable but with normal behaviour)


        The node will appear as a mutable node in the bnd file.
        This means that its rate will be of the form:

        ``rate_up = $LowNode ? 0 :($HighNode ? 1: (@logic ? rt_up : 0))``

        If the node is already mutable, this method will simply set $HighNode
        and $LowNode accordingly to the desired mutation.
        """
        if node not in self.network:
            print("Error, unknown node %s" % node, file=stderr)
            return

        nd = self.network[node]
        if not nd.is_mutant:
            self.network[node]=_make_mutant_node(nd)
            self.mutations.append(nd.name)
            self.mutationTypes.update({nd.name: state})


        lowvar = "$Low_"+node
        highvar = "$High_"+node
        if state == "ON":
            self.param[lowvar] = 0
            self.param[highvar] = 1


        elif state == "OFF":
            self.param[lowvar] = 1
            self.param[highvar] = 0

        elif state == "WT":
            self.param[lowvar] = 0
            self.param[highvar] = 0

        else:
            print("Error, state must be ON, OFF or WT", file=stderr)
            return

    def continue_from_result(self, result):
        """Set the initial state from as the last state from result."""
        node_prob = result.get_nodes_probtraj()
        nodes = node_prob.iloc[-1]
        for i in nodes.index:
            if i != "<nil>":
                prob = nodes[i]
                self.network.set_istate(i, [1 - prob, prob])

    def get_initial_state(self):
        """
        TODO
        """
        istate = ModelState()
        for nd in self.network.keys():
            states = set()
            for state in [0, 1]:
                if self.network._initState[nd][state]:
                    states.add(state)
            istate[nd] = states.pop() if len(states) == 1 else states
        return istate

    def get_mutations(self):
        return self.mutationTypes

    def set_workdir(self, path, overwrite=False):
        self.workdir = path
        self.overwrite = overwrite

def _make_mutant_node(nd):
    """Create a new logic for mutation that can be activated from .cfg file."""
    curent_rt_up = nd.rt_up
    curent_rt_down = nd.rt_down

    lowvar = "$Low_"+nd.name
    highvar = "$High_"+nd.name
    rt_up = (lowvar+" ? 0 : (" + highvar + " ? 1E308/$nb_mutable : ("
             + curent_rt_up + "))")
    rt_down = (highvar + " ? 0 : (" + lowvar + " ? 1E308/$nb_mutable : ("
             + curent_rt_down + "))")
    # Once this is done, the mutation can be activated by modifying the value
    # of $Low_nodename and $High_nodename in the .cfg file
    newNode = nd.copy()
    newNode.rt_up = rt_up
    newNode.rt_down = rt_down
    newNode.is_mutant = True
    return newNode

def set_nodes_istate(masim, nodes, istate):
    for n in nodes:
        masim.network.set_istate(n, istate)

def set_output(masim, output):
    masim.network.set_output(output)

def copy_and_mutate(masim, nodes, mut):
    masim2 = masim.copy()
    for node in nodes:
        masim2.mutate(node, mut)
    return masim2

def copy_and_update_parameters(sim, parameters):
    new_sim = sim.copy()
    new_sim.update_parameters( **parameters )
    return new_sim

def to_biolqm(maboss_model):
    
    biolqm = import_colomoto_tool("biolqm")
    bnet_filename = new_output_file("bnet")
    with open(bnet_filename, "w") as bnet_file:
        for node, rule in maboss_model.get_logical_rules().items():
            bnet_file.write("%s, %s\n" % (node, rule))

    return biolqm.load(bnet_filename)

def to_minibn(maboss_model):
    from colomoto import minibn
    bnet_filename = new_output_file("bnet")
    with open(bnet_filename, "w") as bnet_file:
        for node, rule in maboss_model.get_logical_rules().items():
            bnet_file.write("%s, %s\n" % (node, rule))

    return minibn.BooleanNetwork.load(bnet_filename)