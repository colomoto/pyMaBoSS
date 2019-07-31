"""
Class that contains the stationnary distribution results of a MaBoSS simulation.
"""

from __future__ import print_function
from sys import version_info
import pandas as pd
import numpy as np
from multiprocessing import Pool
if version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO

class StatDistResult(object):
    
    def __init__(self, path, traj_count=None, thread_count=1):
        
        self._path = path
        self._traj_count = traj_count
        self._thread_count = thread_count
    
        self.state_statdist = None
        self.statdist_clusters = None
        self.statdist_clusters_summary = None
        self.statdist_clusters_summary_error = None

        self.raw_statdist = None
        self.raw_statdist_clusters = None
        self.raw_statdist_clusters_summary = None

    def get_states_statdist(self):
        if self.state_statdist is None:
            table = self._get_raw_statdist()
            cols = range(0, len(table.columns), 2)

            states = _get_states(table, cols)
            self.state_statdist = _make_statdist_table(table, states)
        return self.state_statdist

    def _get_raw_statdist(self):
        if self.raw_statdist is None:
            statdist_traj_count = self._get_trajcount()
            self.raw_statdist = pd.read_csv(
                self.get_statdist_file(), "\t", 
                nrows=statdist_traj_count, 
                index_col=0,
                dtype=self._get_statdist_dtypes()
            )
        return self.raw_statdist

    def _get_trajcount(self):
        if self._traj_count is None:
            with open(self.get_statdist_file(), 'r') as t_file:
                for i, line in enumerate(t_file):
                    if len(line.strip("\n")) == 0:
                        self._traj_count = i - 1
                        break
        return self._traj_count

    def _get_raw_statdist_clusters(self):
        if self.raw_statdist_clusters is None:
            self.raw_statdist_clusters = []

            indexes = []
            nb_lines = 0
            nb_cols = []
            nbs_cols = []
            with open(self.get_statdist_file(), 'r') as t_file:
                for i, line in enumerate(t_file):
                    # We look for the line breaks between each cluster
                    if line == '\n':
                        if len(indexes) > 0:
                            nbs_cols.append(max(nb_cols))
                            nb_cols = []

                        indexes.append(i)

                    if len(indexes) > 0:
                        nb_cols.append(len(line.split("\t")))
                nb_lines = i+1

            for i, index in enumerate(indexes):
                if i < len(indexes)-1:
                    start = index+2
                    end = indexes[i+1]-1
                
                    new_columns = ["Trajectory", "State", "Proba"]
                    for i in range(1, nbs_cols[i]//2):
                        new_columns += ["State.%d" % i, "Proba.%d" % i]
                    
                    df = pd.read_csv(
                        self.get_statdist_file(), 
                        skiprows=start, nrows=(end-start+1), 
                        header=None, sep="\t", index_col=0, names=new_columns
                    )

                    self.raw_statdist_clusters.append(df)
        return self.raw_statdist_clusters

    def get_statdist_clusters(self):
        if self.statdist_clusters is None:
            self.statdist_clusters = []

            # Getting all states
            all_states = set()
            for cluster in self._get_raw_statdist_clusters():
                for i_row, (index_row, row) in enumerate(cluster.iterrows()): 
                    t_states = [val for _, val in row[0::2].iteritems() if type(val) is str]
                    all_states.update(t_states)

                t_statdist_cluster = pd.DataFrame(
                    np.zeros((len(cluster.index), len(all_states))), 
                    index=cluster.index, columns=all_states
                )

                for index_row, row in cluster.iterrows():
                    for i_col, (_, state) in enumerate(row[0::2].iteritems()):
                        if type(state) is str:
                            val = row.iloc[(i_col*2)+1]
                            t_statdist_cluster.loc[index_row, state] = val

                self.statdist_clusters.append(t_statdist_cluster)

        return self.statdist_clusters

    def _get_raw_statdist_clusters_summary(self):
        if self.raw_statdist_clusters_summary is None:
            start = 0
            with open(self.get_statdist_file(), 'r') as t_file:
                for i, line in enumerate(t_file):
                    if line == '\n':
                        start = i
            max_cols = 0
            lines = []
            with open(self.get_statdist_file(), 'r') as t_file:
                for i, line in enumerate(t_file):
                    if i > start+1: 
                        lines.append(line)
                        if len(line.split("\t")) > max_cols:
                            max_cols = len(line.split("\t"))

            cols = ["Cluster"] + ["State", "Proba", "ErrProba"]*((max_cols-1)//3)
            cols_tabs = "\t".join(cols) + "\n"
            lines.insert(0, cols_tabs)
            self.raw_statdist_clusters_summary = pd.read_csv(StringIO("".join(lines)), sep="\t", index_col=0)

        return self.raw_statdist_clusters_summary

    def get_statdist_clusters_summary(self):
        if self.statdist_clusters_summary is None:
            raw = self._get_raw_statdist_clusters_summary()

            # Getting all states
            all_states = set()
            for i_row, (index_row, row) in enumerate(raw.iterrows()): 
                t_states = [val for _, val in row[0::3].iteritems() if type(val) is str]
                all_states.update(t_states)

            self.statdist_clusters_summary = pd.DataFrame(
                np.zeros((len(raw.index), len(all_states))), 
                index=raw.index, columns=all_states
            )

            for index_row, row in raw.iterrows():
                for i_col, (_, state) in enumerate(row[0::3].iteritems()):
                    if type(state) is str:
                        val = row.iloc[(i_col*3)+1]
                        self.statdist_clusters_summary.loc[index_row, state] = val

        return self.statdist_clusters_summary


    def get_statdist_clusters_summary_error(self):
        if self.statdist_clusters_summary_error is None:
            raw = self._get_raw_statdist_clusters_summary()

            all_states = set()
            for i_row, (index_row, row) in enumerate(raw.iterrows()): 
                t_states = [val for _, val in row[0::3].iteritems() if type(val) is str]
                all_states.update(t_states)

            self.statdist_clusters_summary_error = pd.DataFrame(
                np.zeros((len(raw.index), len(all_states))), 
                index=raw.index, columns=all_states
            )

            for index_row, row in raw.iterrows():
                for i_col, (_, state) in enumerate(row[0::3].iteritems()):
                    if type(state) is str:
                        val = row.iloc[(i_col*3)+2]
                        self.statdist_clusters_summary_error.loc[index_row, state] = val

        return self.statdist_clusters_summary_error

    def _get_statdist_dtypes(self):
        with open(self.get_statdist_file(), 'r') as statdist:
            cols = statdist.readline().split("\t")
            dtype = {}
            dtype.update({"State": np.str, "Proba": np.float64})

            for i in range(1, len(cols)//2):
                dtype.update({"State.%d" % i: np.str, "Proba.%d" % i: np.float64})
            
            return dtype

    def write_statdist_table(self, filename, prob_cutoff=None):
        clusters = self._get_raw_statdist_clusters()
        clusters_summary = self._get_raw_statdist_clusters_summary()
        with open(filename, 'w') as statdist_table:

            for i_cluster, cluster in enumerate(clusters_summary.iterrows()):

                line_0 = "Probability threshold=%s\n" % (str(prob_cutoff) if prob_cutoff is not None else "") 
                line_1 = ["Prob[Cluster %s]" % cluster[0]] 
                line_2 = ["%g" % (len(clusters[i_cluster])/self._get_trajcount())]
                line_3 = ["ErrorProb"]

                t_cluster = cluster[1].dropna()

                for i in range(0, len(t_cluster), 3):
                    if prob_cutoff is None or t_cluster[i+1] > prob_cutoff:
                        line_1.append("Prob[%s | Cluster %s]" % (t_cluster[i], cluster[0]))
                        line_2.append("%g" % t_cluster[i+1])
                        line_3.append("%g" % t_cluster[i+2])

                statdist_table.write(line_0)
                statdist_table.write("\t".join(line_1) + "\n")
                statdist_table.write("\t".join(line_2) + "\n")
                statdist_table.write("\t".join(line_3) + "\n")
                statdist_table.write("\n")

def _make_statdist_table(df, states):    
    time_table = pd.DataFrame(
        np.zeros((len(df.index), len(states))),
        columns=states
    )

    for index, (_, row) in enumerate(time_table.iterrows()):
        _make_statdist_line(row, df, range(0, len(df.columns), 2), index)

    return time_table

def _make_statdist_line(row, df, cols, index):
    for c in cols:
        if type(df.iloc[index, c]) is str:  # Otherwise it is nan
            state = df.iloc[index, c]
            row[state] = df.iloc[index, c+1]


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
