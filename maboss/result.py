"""
Class that contains the results of a MaBoSS simulation.

When this module is imported, a global dictionary ``results``, maping
results names (strings) to Result object, is created.
"""

from sys import stderr, stdout
from .figures import make_plot_trajectory, plot_piechart, plot_fix_point, plot_node_prob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyparsing as pp
import shutil
import tempfile
from contextlib import ExitStack
import os
import subprocess

results = {}  # global maping of results name to results objects
class Result(object):
    """
    Class that handles the results of MaBoSS simulation.
    
    :param simul: The simulation object that produce the results.
    :type simul: :py:class:`Simulation`
    :param str name: The key under which the object will be stored in the ``results`` dictionary.
    
    When a Result object is created, two temporary files are written in ``/tmp/``
    these files are the ``.bnd`` and ``.cfg`` file represented by the associated
    Simulation object. MaBoSS is then executed on these to temporary files and
    its output are stored in a temporary folder. 
    The Result object has several attributes to access the contents of the
    folder as pandas dataframe. It also has methods to produce somme plots.

    By default, the cfg, bnd and MaBoSS output are removed from the disk when the
    Result object is destructed. Result object has a method to save cfg, bnd and results
    in the working directory.
    """

    def __init__(self, simul, name):
        self._path = tempfile.mkdtemp()
        self._cfg = tempfile.mkstemp(dir=self._path, suffix='.cfg')[1]
        self._bnd = tempfile.mkstemp(dir=self._path, suffix='.bnd')[1]
        self._trajfig = None
        self._piefig = None
        self._fpfig = None
        self._ndtraj = None
        self.palette = simul.palette
        self.fptable = None
        self.state_probtraj = None
        self.nd_probtraj = None
        if name in results:
            print("Error result % already exists" % name, file=stderr)
        else:
            results[name] = self

        with ExitStack() as stack:
            bnd_file = stack.enter_context(open(self._bnd, 'w'))
            cfg_file = stack.enter_context(open(self._cfg, 'w'))
            simul.print_bnd(out=bnd_file)
            simul.print_cfg(out=cfg_file)

        self._err = subprocess.call(["MaBoSS", "-c", self._cfg, "-o",
                                     self._path+'/res', self._bnd])
        if self._err:
            print("Error, MaBoSS returned non 0 value", file=stderr)
        else:
            print("MaBoSS ended successfuly")

    def plot_trajectory(self):
        """Plot the graph state probability vs time."""
        if self._trajfig is None:
            if self._err:
                print("Error, plot_trajectory cannot be called because MaBoSS"
                      "returned non 0 value", file=stderr)
                return
            self._trajfig = self.make_trajectory()
            return self._trajfig
        else:
            return self._trajfig.show()

    def make_trajectory(self):
        prefix = self._path+'/res'
        self._trajfig, self._trajax = plt.subplots(1, 1)
        table = self.get_states_probtraj()
        make_plot_trajectory(table, self._trajax, self.palette)
        return self._trajfig

    def plot_piechart(self):
        """Plot the states probability distribution of last time point."""
        if self._piefig is None:
            if self._err:
                print("Error, plot_piechart cannot be called because MaBoSS"
                      "returned non 0 value", file=stderr)
                return
            self._piefig, self._pieax = plt.subplots(1, 1)
            table = self.get_states_probtraj()
            plot_piechart(table, self._pieax, self.palette)
        return self._piefig

    def plot_fixpoint(self):
        """Plot the probability distribution of fixed point."""
        if self._fpfig is None:
            if self._err:
                print("Error maboss previously returned non 0 value",
                      file=stderr)
                return
            self._fpfig, self._fpax = plt.subplots(1, 1)
            plot_fix_point(self.get_fptable(), self._fpax, self.palette)
        return self._fpfig

    def plot_node_trajectory(self):
        """Plot the probability of each node being up over time."""
        if self._ndtraj is None:
            if self._err:
                print("Error maboss previously returned non 0 value",
                      file=stderr)
                return
            self._ndtraj, self._ndtrajax = plt.subplots(1, 1)
            table = self.get_nodes_probtraj()
            plot_node_prob(table, self._ndtrajax, self.palette)
        return self._ndtraj

    def get_fptable(self): 
        """Return the content of fp.csv as a pandas dataframe."""
        if self.fptable is None:
            table_file = "{}/res_fp.csv".format(self._path)
            self.fptable = pd.read_csv(table_file, "\t", skiprows=[0])
        return self.fptable

    def get_nodes_probtraj(self):
        if self.nd_probtraj is None:
            table_file = "{}/res_probtraj.csv".format(self._path)
            table = pd.read_csv(table_file, "\t")
            self.nd_probtraj = make_node_proba_table(table)
        return self.nd_probtraj

    def get_states_probtraj(self):
        if self.state_probtraj is None:
            table_file = "{}/res_probtraj.csv".format(self._path)
            table = pd.read_csv(table_file, "\t")
            self.state_probtraj = make_trajectory_table(table)
        return self.state_probtraj

    def save(self, prefix, replace=False):
        """
        Write the cfg, bnd and all results in working dir.

        prefix is a string that will determine the name of the created files.
        If there is a conflict with existing files, the existing files will be
        replaced or not, depending on the value of the replace argument.
        """
        if not _check_prefix(prefix):
            return

        # Create the results directory
        try:
            os.mkdir(prefix)
        except FileExistsError:
            if not replace:
                print('Error directory already exists: %s' % prefix,
                      file=stderr)
                return
            elif prefix.startswith('rpl_'):
                shutil.rmtree(prefix)
                os.mkdir(prefix)
            else:
                print('Error only directries begining with "rpl_" can be'
                      'replaced', file=stderr)
                return

        # Moves all the files into it
        shutil.copy(self._bnd, prefix+'/%s.bnd' % prefix)
        shutil.copy(self._cfg, prefix+'/%s.cfg' % prefix)

        maboss_files = filter(lambda x: x.startswith('res'),
                              os.listdir(self._path))
        for f in maboss_files:
            shutil.copy(self._path + '/' + f, prefix)

    def __del__(self):
        shutil.rmtree(self._path)


def _check_prefix(prefix):
    if type(prefix) is not str:
        print('Error save method expected string')
        return False
    else:
        prefix_grammar = pp.Word(pp.alphanums + '_-')
        return prefix_grammar.matches(prefix)


def make_trajectory_table(df):
    """Creates a table giving the probablilty of each state a every moment.

        The rows are indexed by time points and the columns are indexed by
        state name.
    """
    states = get_states(df)
    nb_sates = len(states)
    time_points = np.asarray(df['Time'])
    time_table = pd.DataFrame(np.zeros((len(time_points), nb_sates)),
                              index=time_points, columns=states)

    cols = list(filter(lambda s: s.startswith("State"), df.columns))
    for i in df.index:
        tp = df["Time"][i]
        for c in cols:
            prob_col = c.replace("State", "Proba")
            if type(df[c][i]) is str:  # Otherwise it is nan
                state = df[c][i]
                time_table[state][tp] = df[prob_col][i]

    return time_table


def make_node_proba_table(df):
    """Same as make_trajectory_table but with nodes instead of states."""
    nodes = get_nodes(df)
    nb_nodes = len(nodes)
    time_points = np.asarray(df['Time'])
    time_table = pd.DataFrame(np.zeros((len(time_points), nb_nodes)),
                              index=time_points, columns=nodes)
    cols = list(filter(lambda s: s.startswith("State"), df.columns))
    for i in df.index:
        tp = df["Time"][i]
        for c in cols:
            prob_col = c.replace("State", "Proba")
            if type(df[c][i]) is str:
                state = df[c][i]
                if ' -- ' in state:
                    nodes = state.split(' -- ')
                else:
                    nodes = [state]
                for nd in nodes:
                    time_table[nd][tp] += df[prob_col][i]
    return time_table
    
def get_nodes(df):
    states = get_states(df)
    nodes = set()
    for s in states:
        nds = s.split(' -- ')
        for nd in nds:
            nodes.add(nd)
    return nodes
        
def get_states(df):
    cols = list(filter(lambda s: s.startswith("State"), df.columns))
    states = set()
    for i in df.index:
        for c in cols:
            if type(df[c][i]) is str:  # Otherwise it is nan
                states.add(df[c][i])
    return states