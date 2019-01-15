"""Class that handles the parameters of a MaBoSS simulation.
"""

import collections
from sys import stderr, stdout
from contextlib import ExitStack

from colomoto import ModelState

from .result import Result
import os
import uuid

_default_parameter_list = collections.OrderedDict({'time_tick': 0.1,
                  'max_time': 4,
                  'sample_count': 10000,
                  'discrete_time': 0,
                  'use_physrandgen': 1,
                  'seed_pseudorandom': 0,
                  'display_traj': 0,
                  'statdist_traj_count': 0,
                  'statdist_cluster_threshold': 1,
                  'thread_count': 1,
                  'statdist_similarity_cache_max_size': 20000
                  })


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


    def __init__(self, nt, parameters=collections.OrderedDict({}), **kwargs):
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
        self.refstate = {}

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

    def print_bnd(self, out=stdout):
        """Produce the content of the bnd file associated to the simulation."""
        print(self.network, file=out)

    def print_cfg(self, out=stdout):
        """Produce the content of the cfg file associated to the simulation."""
        print("$nb_mutable = " + str(len(self.mutations)) + ";", file=out)
        for p in self.param:
            if p[0] == '$':
                print(p + ' = ' + str(self.param[p]) + ';', file=out)
        self.network.print_istate(out=out)
        print('', file=out)

        for p in self.param:
            if p[0] != '$':
                print(p + ' = ' + str(self.param[p]) + ';', file=out)

        for name in self.network.names:
            string = name+'.is_internal = ' + str(int(self.network[name].is_internal)) + ';'
            print(string, file=out)

        for nd in self.refstate:
            string = nd +'.refstate = ' + self.refstate[nd] + ';'
            print(string, file=out)

    def run(self, command=None):
        """Run the simulation with MaBoSS and return a Result object.

        :param command: specify a MaBoSS command, default to None for automatic selection
        :rtype: :py:class:`Result`
        """
        return Result(self, command)


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

