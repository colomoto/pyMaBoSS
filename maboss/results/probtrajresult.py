"""
Class that contains the results of a MaBoSS simulation.
"""

from __future__ import print_function
from sys import stderr, stdout, version_info
import pandas as pd
import numpy as np
from multiprocessing import Pool
if version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO

class ProbTrajResult(object):
    
    def __init__(self, path, thread_count=1):
        
        self._path = path
        self.thread_count = thread_count
        self.first_state_index = None
        self.state_probtraj = None
        self.state_probtraj_errors = None
        self.state_probtraj_full = None
        self.last_states_probtraj = None
   
        self.nd_probtraj = None
        self.nd_probtraj_error = None
        self._nd_entropytraj = None

        self.raw_probtraj = None
   

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
            cols = get_states_cols(table)
            if nb_cores == 1:
                states = _get_states(table, cols)
            else:
                states = _get_states_parallel(table, cols, nb_cores)
            if nb_cores > 1:
                self.state_probtraj = self.make_trajectory_table_parallel(table, states, cols, nb_cores)
            else:
                self.state_probtraj = self.make_trajectory_table(table, states, cols)
        
        if prob_cutoff is not None:
            maxs = self.state_probtraj.max(axis=0)
            return self.state_probtraj[maxs[maxs>prob_cutoff].index]
            
        return self.state_probtraj

    def get_states_probtraj_errors(self):
        if self.state_probtraj_errors is None:
            table = self.get_raw_probtraj()
            cols = get_states_cols(table)
            states = _get_states(table, cols)
            self.state_probtraj_errors = self.make_trajectory_error_table(table, states, cols)
        return self.state_probtraj_errors

    def get_states_probtraj_full(self, prob_cutoff=None):
        if self.state_probtraj_full is None:
            table = self.get_raw_probtraj()
            cols = get_states_cols(table)
            full_cols = ["TH", "ErrorTH", "H"]

            for col in _get_states(table, cols):
                full_cols.append("Prob[%s]" % col)
                full_cols.append("ErrProb[%s]" % col)

            self.state_probtraj_full = self.make_trajectory_full_table(table, full_cols, cols)

        if prob_cutoff is not None:
            maxs = self.state_probtraj_full.max(axis=0)
            cols = ["TH", "ErrorTH", "H"]

            for state in maxs[maxs > prob_cutoff].index:
                if state.startswith("Prob["):
                    cols.append(state)
                    cols.append("Err%s" % state)

            return self.state_probtraj_full[cols]            
      
        return self.state_probtraj_full

    def get_last_states_probtraj(self):
        if self.last_states_probtraj is None:
            last_table = self.get_raw_probtraj().tail(1).copy().dropna(axis='columns')
            cols = get_states_cols(last_table)
            last_states = _get_states(last_table, cols, nona=True)
            self.last_states_probtraj = self.make_trajectory_table(last_table, last_states, cols, nona=True)

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

            first_state_index = 5
            for i in range(first_state_index, len(cols)):
                if cols[i].startswith("State"):
                    first_state_index = i
                    break

            nb_states = int((len(cols) - first_state_index) / 3)

            dtype = {"Time": np.float64, "TH": np.float64, "ErrorTH": np.float64, "H": np.float64, "HD=0": np.float64}
            
            for i in range(first_state_index-5):
                dtype.update({("HD=%d" % (i+1)): np.float64})
            
            dtype.update({"State": np.str, "Proba": np.float64, "ErrorProba": np.float64})
            for i in range(1, nb_states):
                dtype.update({"State.%d" % i: np.str, "Proba.%d" % i: np.float64, "ErrorProba.%d" % i: np.float64})
            return dtype

  
    def make_trajectory_table(self, df, states, cols, nona=False):
        """Creates a table giving the probablilty of each state a every moment.

            The rows are indexed by time points and the columns are indexed by
            state name.
        """

        time_points = np.asarray(df['Time'])
        
        time_table = pd.DataFrame(
            np.zeros((len(time_points), len(states))),
            index=time_points, columns=states
        )

        if len(time_points) > 1:
            for index, (_, row) in enumerate(time_table.iterrows()):
                make_trajectory_line(row, df, cols, index, nona)
        
            time_table.sort_index(axis=1, inplace=True) 
        else:
            make_trajectory_line(time_table.iloc[0, :], df, cols, 0, nona)
            time_table.sort_index(axis=1, inplace=True) 

        return time_table


    def make_trajectory_error_table(self, df, states, cols):
        """Creates a table giving the probablilty of each state a every moment.

            The rows are indexed by time points and the columns are indexed by
            state name.
        """
        
        time_points = np.asarray(df['Time'])
        time_table = pd.DataFrame(
            np.zeros((len(time_points), len(states))),
            index=time_points, columns=states
        )
        for index, (_, row) in enumerate(time_table.iterrows()):
            make_trajectory_error_line(row, df, cols, index)

        time_table.sort_index(axis=1, inplace=True) 

        return time_table

    def make_trajectory_full_table(self, df, states, cols): 
        """
        Creates a table with the format used in the original script MBSS_FormatTable.pl

        """
        time_points = df["Time"]
        time_table = pd.DataFrame(
            np.zeros((len(time_points), len(states))),
            index=time_points, columns=states
        )

        time_table['TH'] = df['TH'].values
        time_table['ErrorTH'] = df['ErrorTH'].values
        time_table['H'] = df['H'].values

        for index, (_, row) in enumerate(time_table.iterrows()):
            make_trajectory_full_line(row, df, cols, index)

        return time_table

    def make_trajectory_table_parallel(self, df, states, cols, nb_cores):
        # TODO : Here we should parallelize all these functions
        """Creates a table giving the probablilty of each state a every moment.

            The rows are indexed by time points and the columns are indexed by
            state name.
        """

        with Pool(processes=nb_cores) as pool:
            time_table = pd.concat(pool.starmap(
                make_trajectory_line_parallel, 
                [(df.iloc[i, :], states, cols) for i in df.index]
            ))
        
        time_table.sort_index(axis=1, inplace=True) 
        return time_table

    def make_node_proba_table(self, df):
        """Same as make_trajectory_table but with nodes instead of states."""
        cols = get_states_cols(df)
        nodes = _get_nodes(df, cols)
        time_points = np.asarray(df['Time'])
        time_table = pd.DataFrame(
            np.zeros((len(time_points), len(nodes))),
            index=time_points, columns=nodes
        )

        for index, (_, row) in enumerate(time_table.iterrows()):
            make_node_proba_line(row, df, cols, index)

        time_table.sort_index(axis=1, inplace=True)
        return time_table

    def make_node_proba_error_table(self, df):
        """Same as make_trajectory_table but with nodes instead of states."""
        cols = get_states_cols(df)
        nodes = _get_nodes(df, cols)
        time_points = np.asarray(df['Time'])
        time_table = pd.DataFrame(
            np.zeros((len(time_points), len(nodes))),
            index=time_points, columns=nodes
        )
        for index, (_, row) in enumerate(time_table.iterrows()):
            make_node_proba_error_line(row, df, cols, index)

        time_table.sort_index(axis=1, inplace=True)
        return time_table


def make_trajectory_line(row, df, cols, index, nona=False):
    if nona:
        for c in cols:
            state = df.iloc[index, c]
            row[state] = df.iloc[index, c+1]
    else:
        for c in cols:
            if type(df.iloc[index, c]) is str:  # Otherwise it is nan
                state = df.iloc[index, c]
                row[state] = df.iloc[index, c+1]
   
def make_trajectory_error_line(row, df, cols, index):
    for c in cols:
        if type(df.iloc[index, c]) is str:  # Otherwise it is nan
            state = df.iloc[index, c]
            row[state] = df.iloc[index, c+2]

def make_trajectory_full_line(row, df, cols, index):
    for c in cols:
        if type(df.iloc[index, c]) is str:# Otherwise it's NaN
            state = df.iloc[index, c]
            row["Prob[%s]" % state] = df.iloc[index, c+1]
            row["ErrProb[%s]" % state] = df.iloc[index, c+2]

def make_trajectory_line_parallel(row, states, cols):
    df = pd.DataFrame(np.zeros((1, len(states))), index=[row["Time"]], columns=states)
    for c in cols:
        if type(row[c]) is str:  # Otherwise it is nan
            state = row[c]
            df[state][row["Time"]] = row[c+1]
    return df


def make_node_proba_line(row, df, cols, index):
    for c in cols:
        if type(df.iloc[index, c]) is str:
            state = df.iloc[index, c]
            if state != '<nil>':
                nodes = state.split(' -- ')
                for nd in nodes:
                    value = df.iloc[index, c+1]
                    row[nd] += value

def make_node_proba_error_line(row, df, cols, index):
    for c in cols:
        if type(df.iloc[index, c]) is str:
            state = df.iloc[index, c]
            if state != '<nil>':
                nodes = state.split(' -- ')
                for nd in nodes:
                    row[nd] += df.iloc[index, c+2]


def _get_state_from_line(line, cols):
    t_states = set()
    for c in cols:
        if type(line[c]) is str:  # Otherwise it is nan
            t_states.add(line[c])
    return t_states

def _get_states_parallel(df, cols, nb_cores):
    states = set()
    with Pool(processes=nb_cores) as pool:
        states = states.union(*(pool.starmap(
            _get_state_from_line, 
            [(df.iloc[i, :], cols) for i in df.index]
        )))
    return states

def _get_states(df, cols, nona=False):
    states = set()
    if nona:
        for i in range(len(df.index)):
            for c in cols:
                states.add(df.iloc[i, c])
    else:
        for i in range(len(df.index)):
            for c in cols:
                if type(df.iloc[i, c]) is str:  # Otherwise it is nan
                    states.add(df.iloc[i, c])

    return states
      
def _get_nodes(df, cols):
    states = _get_states(df, cols)
    nodes = set()
    for s in states:
        if s != '<nil>':
            nds = s.split(' -- ')
            for nd in nds:
                nodes.add(nd)
    return nodes

def get_first_state_index(df):
    """Return the indice of the first column being a state
        By default it's five, but if we specify some refstate,
        it'll be more.
    """
    first_state_index = None
    for i in range(5, len(df.columns)):
        if df.columns[i].startswith("State"):
            first_state_index = i
            break

    return first_state_index

def get_states_cols(df):
    if isinstance(df, pd.DataFrame):
        return range(get_first_state_index(df), len(df.columns), 3)
    else:
        return range(get_first_state_index(df), len(df), 3)

__all__ = ["Result", "StoredResult"]
