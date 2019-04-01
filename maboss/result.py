"""
Class that contains the results of a MaBoSS simulation.
"""

from __future__ import print_function
from sys import stderr, stdout, version_info
if version_info[0] < 3:
    from contextlib2 import ExitStack
else:
    from contextlib import ExitStack
from .figures import make_plot_trajectory, plot_piechart, plot_fix_point, plot_node_prob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyparsing as pp
import shutil
import tempfile
import os
import subprocess
from multiprocessing import Pool

class BaseResult(object):
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

    def __init__(self, simul=None, command=None):
        
        self._trajfig = None
        self._piefig = None
        self._fpfig = None
        self._ndtraj = None
        self._err = False
        self.palette = {}
        if simul is not None:
            self.palette = simul.palette
        self.fptable = None
        self.states = None
        self.nodes = None
        self.state_probtraj = None
        self.state_probtraj_errors = None
        self.last_states_probtraj = None
        self.nd_probtraj = None
        self.nd_probtraj_error = None
        self._nd_entropytraj = None

        self.raw_probtraj = None

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
                table_error = table_error[table.columns]

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

    def get_nodes_probtraj(self, prob_cutoff=None):
        if self.nd_probtraj is None:
            table = self.get_raw_probtraj()
            self.nd_probtraj = self.make_node_proba_table(table)
        
        if prob_cutoff is not None:
            maxs = self.nd_probtraj.max(axis=0)
            return self.nd_probtraj[maxs[maxs>prob_cutoff].index]
     
        return self.nd_probtraj

    def get_nodes_probtraj_error(self):
        if self.nd_probtraj_error is None:
            table = self.get_raw_probtraj()
            self.nd_probtraj_error = self.make_node_proba_error_table(table)
        return self.nd_probtraj_error

    def get_states_probtraj(self, prob_cutoff=None, nb_cores=1):
        if self.state_probtraj is None:
            table = self.get_raw_probtraj()
            if nb_cores > 1:
                self.state_probtraj = self.make_trajectory_table_parallel(table, nb_cores)
            else:
                self.state_probtraj = self.make_trajectory_table(table)
        
        if prob_cutoff is not None:
            maxs = self.state_probtraj.max(axis=0)
            return self.state_probtraj[maxs[maxs>prob_cutoff].index]
            
        return self.state_probtraj

    def get_states_probtraj_errors(self):
        if self.state_probtraj_errors is None:
            table = self.get_raw_probtraj()
            self.state_probtraj_errors = self.make_trajectory_error_table(table)
        return self.state_probtraj_errors

    def get_last_states_probtraj(self):
        if self.last_states_probtraj is None:
            table = self.get_raw_probtraj()
            self.last_states_probtraj = self.make_trajectory_table(table.tail(1))
        return self.last_states_probtraj

    def get_entropy_trajectory(self):
        if self._nd_entropytraj is None:
            self._nd_entropytraj = pd.read_csv(
                self.get_probtraj_file(), "\t", usecols=('TH', 'H'), dtype=self.get_probtraj_dtypes()
            )
        return self._nd_entropytraj

    def get_raw_probtraj(self):
        if self.raw_probtraj is None:
            self.raw_probtraj = pd.read_csv(self.get_probtraj_file(), "\t", dtype=self.get_probtraj_dtypes())
        return self.raw_probtraj

    def get_probtraj_dtypes(self):
        with open(self.get_probtraj_file(), 'r') as probtraj:
            cols = probtraj.readline().split("\t")
            nb_states = int((len(cols) - 5) / 3)

            dtype = {"Time": np.float64, "TH": np.float64, "ErrorTH": np.float64, "H": np.float64, "HD=0": np.float64,
                     "State": np.str, "Proba": np.float64, "ErrorProba": np.float64}
            for i in range(1, nb_states):
                dtype.update({"State.%d" % i: np.str, "Proba.%d" % i: np.float64, "ErrorProba.%d" % i: np.float64})
            return dtype

    def get_states_parallel(self, df, nb_cores):
        if self.states is None:
            self.states = set()
            with Pool(processes=nb_cores) as pool:
                self.states = self.states.union(*(pool.map(
                    get_state_from_line, 
                    [df.iloc[i, :] for i in df.index]
                )))
        return self.states

    def get_states(self, df, cols):
        if self.states is None:
            self.states = set()
            for i in range(len(df.index)):
                for c in cols:
                    if type(df.iloc[i, c]) is str:  # Otherwise it is nan
                        self.states.add(df.iloc[i, c])
        return self.states
        
    def get_nodes(self, df, cols):
        if self.nodes is None:
            states = self.get_states(df, cols)
            self.nodes = set()
            for s in states:
                nds = s.split(' -- ')
                for nd in nds:
                    self.nodes.add(nd)
        return self.nodes

    def make_trajectory_table(self, df):
        """Creates a table giving the probablilty of each state a every moment.

            The rows are indexed by time points and the columns are indexed by
            state name.
        """
        cols = range(5, len(df.columns), 3)
        states = self.get_states(df, cols)
        time_points = np.asarray(df['Time'])
        time_table = pd.DataFrame(
            np.zeros((len(time_points), len(states))),
            index=time_points, columns=states
        )

        time_table.apply(make_trajectory_line, args=(df, cols), axis=1)        
        time_table.sort_index(axis=1, inplace=True) 

        return time_table

    def make_trajectory_error_table(self, df):
        """Creates a table giving the probablilty of each state a every moment.

            The rows are indexed by time points and the columns are indexed by
            state name.
        """
        cols = range(5, len(df.columns), 3)
        states = self.get_states(df, cols)
        time_points = np.asarray(df['Time'])
        time_table = pd.DataFrame(
            np.zeros((len(time_points), len(states))),
            index=time_points, columns=states
        )

        time_table.apply(make_trajectory_error_line, args=(df, cols), axis=1)        
        time_table.sort_index(axis=1, inplace=True) 

        return time_table

    def make_trajectory_table_parallel(self, df, nb_cores):
        # TODO : Here we should parallelize all these functions
        """Creates a table giving the probablilty of each state a every moment.

            The rows are indexed by time points and the columns are indexed by
            state name.
        """
        cols = range(5, len(df.columns), 3)
        states = self.get_states_parallel(df, nb_cores)
    
        with Pool(processes=nb_cores) as pool:
            time_table = pd.concat(pool.starmap(
                make_trajectory_line_parallel, 
                [(df.iloc[i, :], states, cols) for i in df.index]
            ))
        
        time_table.sort_index(axis=1, inplace=True) 
        return time_table

    def make_node_proba_table(self, df):
        """Same as make_trajectory_table but with nodes instead of states."""
        cols = range(5, len(df.columns), 3)
        nodes = self.get_nodes(df, cols)
        time_points = np.asarray(df['Time'])
        time_table = pd.DataFrame(
            np.zeros((len(time_points), len(nodes))),
            index=time_points, columns=nodes
        )
        time_table.apply(make_node_proba_line, args=(df, cols), axis=1)
        time_table.sort_index(axis=1, inplace=True)
        return time_table

    def make_node_proba_error_table(self, df):
        """Same as make_trajectory_table but with nodes instead of states."""
        cols = range(5, len(df.columns), 3)
        nodes = self.get_nodes(df, cols)
        time_points = np.asarray(df['Time'])
        time_table = pd.DataFrame(
            np.zeros((len(time_points), len(nodes))),
            index=time_points, columns=nodes
        )
        time_table.apply(make_node_proba_error_line, args=(df, cols), axis=1)
        time_table.sort_index(axis=1, inplace=True)
        return time_table


class Result(BaseResult):

    def __init__(self, simul, command=None):
        BaseResult.__init__(self, simul, command)
        self._path = tempfile.mkdtemp()
        cfg_fd, self._cfg = tempfile.mkstemp(dir=self._path, suffix='.cfg')
        os.close(cfg_fd)
        
        bnd_fd, self._bnd = tempfile.mkstemp(dir=self._path, suffix='.bnd')
        os.close(bnd_fd)
        
        with ExitStack() as stack:
            bnd_file = stack.enter_context(open(self._bnd, 'w'))
            cfg_file = stack.enter_context(open(self._cfg, 'w'))
            simul.print_bnd(out=bnd_file)
            simul.print_cfg(out=cfg_file)

        maboss_cmd = simul.get_maboss_cmd()
        if command:
            maboss_cmd = command

        self._err = subprocess.call([maboss_cmd, "-c", self._cfg, "-o",
                                     self._path+'/res', self._bnd])
        if self._err:
            print("Error, MaBoSS returned non 0 value", file=stderr)

    def get_fp_file(self):
        return "{}/res_fp.csv".format(self._path)

    def get_probtraj_file(self):
        return "{}/res_probtraj.csv".format(self._path)
    
    def get_statdist_file(self):
        return "{}/res_statdist.csv".format(self._path)
    
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
            os.makedirs(prefix)
        except OSError:
            if not replace:
                print('Error directory already exists: %s' % prefix,
                      file=stderr)
                return
            elif prefix.startswith('rpl_'):
                shutil.rmtree(prefix)
                os.makedirs(prefix)
            else:
                print('Error only directries begining with "rpl_" can be'
                      'replaced', file=stderr)
                return

        # Moves all the files into it
        shutil.copy(self._bnd, prefix+'/%s.bnd' % os.path.basename(prefix))
        shutil.copy(self._cfg, prefix+'/%s.cfg' % os.path.basename(prefix))

        maboss_files = filter(lambda x: x.startswith('res'),
                              os.listdir(self._path))
        for f in maboss_files:
            shutil.copy(self._path + '/' + f, prefix)

    def __del__(self):
        shutil.rmtree(self._path)



class StoredResult(BaseResult):

    def __init__(self, path):
        
        self._path = path
        BaseResult.__init__(self)
     
    def get_fp_file(self):
        return os.path.join(self._path, "res_fp.csv")

    def get_probtraj_file(self):
        return os.path.join(self._path, "res_probtraj.csv")

    def get_statdist_file(self):
        return os.path.join(self._path, "res_statdist.csv")

def _check_prefix(prefix):
    if type(prefix) is not str:
        print('Error save method expected string')
        return False
    return True

def make_trajectory_line(row, df, cols):
    for c in cols:
        index = df.index.get_loc(row.name)
        if type(df.iloc[index, c]) is str:  # Otherwise it is nan
            state = df.iloc[index, c]
            row[state] = df.iloc[index, c+1]

def make_trajectory_error_line(row, df, cols):
    for c in cols:
        index = df.index.get_loc(row.name)
        if type(df.iloc[index, c]) is str:  # Otherwise it is nan
            state = df.iloc[index, c]
            row[state] = df.iloc[index, c+2]

def make_trajectory_line_parallel(row, states, cols):
    df = pd.DataFrame(np.zeros((1, len(states))), index=[row["Time"]], columns=states)
    for c in cols:
        if type(row[c]) is str:  # Otherwise it is nan
            state = row[c]
            df[state][row["Time"]] = row[c+1]
    return df

def get_state_from_line(line):
    t_states = set()
    for c in range(5, len(line), 3):
        if type(line[c]) is str:  # Otherwise it is nan
            t_states.add(line[c])
    return t_states

def make_node_proba_line(row, df, cols):
    for c in cols:
        index = df.index.get_loc(row.name)
        if type(df.iloc[index, c]) is str:
            state = df.iloc[index, c]
            nodes = state.split(' -- ')
            for nd in nodes:
                row[nd] += df.iloc[index, c+1]

def make_node_proba_error_line(row, df, cols):
    for c in cols:
        index = df.index.get_loc(row.name)
        if type(df.iloc[index, c]) is str:
            state = df.iloc[index, c]
            nodes = state.split(' -- ')
            for nd in nodes:
                row[nd] += df.iloc[index, c+2]

__all__ = ["Result", "StoredResult"]
