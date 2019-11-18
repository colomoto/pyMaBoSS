"""
Class that contains the results of a MaBoSS simulation.
"""

from __future__ import print_function
from sys import stderr, stdout, version_info
from .statdistresult import StatDistResult
from .probtrajresult import ProbTrajResult
from ..figures import make_plot_trajectory, plot_piechart, plot_fix_point, plot_node_prob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
if version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO

class BaseResult(ProbTrajResult, StatDistResult):
    """
    Class that handles the results of MaBoSS simulation.
    
    :param simul: The simulation object that produce the results.
    :type simul: :py:class:`Simulation`
    :param command: specify a MaBoSS command, default to None for automatic selection
    
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

    def __init__(self, path, simul=None, command=None, workdir=None, output_nodes=None):
        
        ProbTrajResult.__init__(self, output_nodes)
        StatDistResult.__init__(self)
        self._path = path
        self._trajfig = None
        self._piefig = None
        self._fpfig = None
        self._ndtraj = None
        self._err = False
        self.palette = {}
        self.statdist_traj_count = None
        self.thread_count = 1
    
        if simul is not None:
            self.palette = simul.palette
            self.thread_count = simul.param['thread_count']
    
        self.fptable = None
   
    def plot_trajectory(self, legend=True, until=None, error=False, prob_cutoff=0.01):
        """Plot the graph state probability vs time.

        :param float until: plot only up to time=`until`
        :param bool legend: display legend
        """
        if self._err:
            print("Error, plot_trajectory cannot be called because MaBoSS"
                  "returned non 0 value", file=stderr)
            return
        table = self.get_states_probtraj(prob_cutoff=prob_cutoff)
        table_error = None
        if error:
            table_error = self.get_states_probtraj_errors()
            if prob_cutoff is not None:
                table_error = table_error.loc[:, table.columns]

        if until:
            table = table[table.index <= until]
            if error:
                table_error = table_error[table_error.index <= until]

        _, ax = plt.subplots(1,1)
      
        make_plot_trajectory(table, ax, self.palette, legend=legend, error_table=table_error)

    def plot_piechart(self, embed_labels=False, autopct=4, prob_cutoff=0.01):
        """Plot the states probability distribution of last time point.

        :param float prob_cutoff: states with a probability below this cut-off
            are grouped as "Others"
        :param bool embed_labels: if True, the labels are displayed within the
            pie
        :param autopct: display pourcentages greater than `autopct` within the
            pie (defaults to 4 if it is a Boolean)
        :type autopct: float or bool
        """
        if self._err:
            print("Error, plot_piechart cannot be called because MaBoSS"
                  "returned non 0 value", file=stderr)
            return
        self._piefig, self._pieax = plt.subplots(1, 1)
        table = self.get_last_states_probtraj()
        plot_piechart(table, self._pieax, self.palette,
                embed_labels=embed_labels, autopct=autopct,
                prob_cutoff=prob_cutoff)

    def plot_fixpoint(self):
        """Plot the probability distribution of fixed point."""
        if self._err:
            print("Error maboss previously returned non 0 value",
                  file=stderr)
            return
        self._fpfig, self._fpax = plt.subplots(1, 1)
        plot_fix_point(self.get_fptable(), self._fpax, self.palette)

    def plot_node_trajectory(self, until=None, legend=True, error=False, prob_cutoff=0.01):
        """Plot the probability of each node being up over time.

        :param float until: plot only up to time=`until`.
        """
        if self._err:
            print("Error maboss previously returned non 0 value",
                  file=stderr)
            return
        self._ndtraj, self._ndtrajax = plt.subplots(1, 1)
        table = self.get_nodes_probtraj(prob_cutoff=prob_cutoff)
        table_error = None
        if error:
            table_error = self.get_nodes_probtraj_error()
        if until:
            table = table[table.index <= until]
            if error:
                table_error = table_error[table_error.index <= until]

        plot_node_prob(table, self._ndtrajax, self.palette, legend=legend, error_table=table_error)

    def plot_entropy_trajectory(self, until=None):
        """Plot the evolution of the (transition) entropy over time.

        :param float until: plot only up to time=`until`.
        """
        if self._err:
            print("Error maboss previously returned non 0 value",
                  file=stderr)
            return
        table = self.get_entropy_trajectory()
        if until:
            table = table[table.index <= until]
        table.plot()

    def get_fptable(self): 
        """Return the content of fp.csv as a pandas dataframe."""
        if self.fptable is None:
            try:
                self.fptable = pd.read_csv(self.get_fp_file(), "\t", skiprows=[0])

            except pd.errors.EmptyDataError:
                pass

        return self.fptable

__all__ = ["Result"]
