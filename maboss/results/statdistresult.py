"""
Class that contains the stationnary distribution results of a MaBoSS simulation.
"""

import pandas as pd
import numpy as np


class StatDistResult(object):
    
    def __init__(self):
            
        self.state_statdist = None
        self.statdist_clusters = None
        self.statdist_clusters_summary = None
        self.statdist_clusters_summary_error = None

        self._traj_count = None
        self._raw_statdist = None
        self._raw_statdist_clusters = None
        self._raw_statdist_clusters_summary = None
       
    def get_states_statdist(self):
        if self.state_statdist is None:
            raw_statdist, _ = self._get_raw_statdist()
            raw_values = [[val for val in t_data.strip("\n").split("\t")] for t_data in raw_statdist[1:]]
            raw_states = [vals[1::2] for vals in raw_values]
            raw_probas = [vals[2::2] for vals in raw_values]
           
            states = set()
            for t_states in raw_states:
                states.update(t_states)
            states = list(states)

            indexes = [vals[0] for vals in raw_values]
            new_data = np.zeros((len(raw_states), len(states)))
            
            for i, t_probas in enumerate(raw_probas):
                for j, proba in enumerate(t_probas):
                    new_data[i, states.index(raw_states[i][j])] = np.float64(proba)
            
            self.state_statdist = pd.DataFrame(
                data=new_data,
                columns=states,
                index=indexes

            )
            self.state_statdist.sort_index(axis=1, inplace=True)

        return self.state_statdist


    def get_statdist_clusters(self):
        if self.statdist_clusters is None:
            clusters, _ = self._get_raw_statdist_clusters()
            self.statdist_clusters = []
            for cluster in clusters:
                raw_values = [raw_value.strip("\n").split("\t") for raw_value in cluster]
                raw_states = [values[1::2] for values in raw_values]
                raw_probas = [values[2::2] for values in raw_values]

                states = set()
                for t_states in raw_states:
                    states.update(t_states)
                states = list(states)

                indexes = [vals[0] for vals in raw_values]
                new_data = np.zeros((len(raw_states), len(states)))
                
                for i, t_probas in enumerate(raw_probas):
                    for j, proba in enumerate(t_probas):
                        new_data[i, states.index(raw_states[i][j])] = np.float64(proba)
                
                df_cluster = pd.DataFrame(
                    data=new_data,
                    columns=states,
                    index=indexes

                )
                df_cluster.sort_index(axis=1, inplace=True)
                self.statdist_clusters.append(df_cluster)

        
        return self.statdist_clusters

    def get_statdist_clusters_summary(self):

        if self.statdist_clusters_summary is None:
            _, summary = self._get_raw_statdist_clusters()
            raw_values = [cluster.strip("\n").split("\t") for cluster in summary]
            raw_states = [values[1::3] for values in raw_values]
            raw_probas = [values[2::3] for values in raw_values]

            states = set()
            for t_states in raw_states:
                states.update(t_states)
            states = list(states)

            indexes = [vals[0] for vals in raw_values]
            new_data = np.zeros((len(raw_states), len(states)))

            for i, t_probas in enumerate(raw_probas):
                for j, proba in enumerate(t_probas):
                    new_data[i, states.index(raw_states[i][j])] = np.float64(proba)

            self.statdist_clusters_summary = pd.DataFrame(
                data=new_data,
                columns=states,
                index=indexes

            )
            self.statdist_clusters_summary.sort_index(axis=1, inplace=True) 

        return self.statdist_clusters_summary

    def get_statdist_clusters_summary_error(self):

        if self.statdist_clusters_summary_error is None:
            _, summary = self._get_raw_statdist_clusters()
            raw_values = [cluster.strip("\n").split("\t") for cluster in summary]
            raw_states = [values[1::3] for values in raw_values]
            raw_errors = [values[3::3] for values in raw_values]

            states = set()
            for t_states in raw_states:
                states.update(t_states)
            states = list(states)

            indexes = [vals[0] for vals in raw_values]
            new_data = np.zeros((len(raw_states), len(states)))

            for i, t_errors in enumerate(raw_errors):
                for j, error in enumerate(t_errors):
                    new_data[i, states.index(raw_states[i][j])] = np.float64(error)

            self.statdist_clusters_summary_error = pd.DataFrame(
                data=new_data,
                columns=states,
                index=indexes
            )
            self.statdist_clusters_summary_error.sort_index(axis=1, inplace=True) 

        return self.statdist_clusters_summary_error

    def write_statdist_table(self, filename, prob_cutoff=None):
        clusters, summary = self._get_raw_statdist_clusters()
        with open(filename, 'w') as statdist_table:
            for i_cluster, cluster in enumerate(summary):

                raw_values = cluster.strip("\n").split("\t")
                
                line_0 = "Probability threshold=%s\n" % (str(prob_cutoff) if prob_cutoff is not None else "") 
                line_1 = ["Prob[Cluster %s]" % raw_values[0]] 
                line_2 = ["%g" % (len(clusters[i_cluster])/self._traj_count)]
                line_3 = ["ErrorProb"]

                for i in range(0, len(raw_values[1:]), 3):
                    if prob_cutoff is None or raw_values[1:i+1] > prob_cutoff:
                        line_1.append("Prob[%s | Cluster %s]" % (raw_values[1+i], raw_values[0]))
                        line_2.append("%s" % raw_values[1+i+1])
                        line_3.append("%s" % raw_values[1+i+2])

                statdist_table.write(line_0)
                statdist_table.write("\t".join(line_1) + "\n")
                statdist_table.write("\t".join(line_2) + "\n")
                statdist_table.write("\t".join(line_3) + "\n")
                statdist_table.write("\n")

    def _get_raw_statdist(self):
        if self._raw_statdist is None or self._traj_count is None:
            with open(self.get_statdist_file(), "r") as f:
                self._raw_statdist = []
                self._traj_count = None
                for i, line in enumerate(f.readlines()):
                    if self._traj_count is None:
                        if len(line.strip("\n")) == 0:
                            self._traj_count = i
                            break
                        
                        self._raw_statdist.append(line)

        return self._raw_statdist, self._traj_count

    def _get_raw_statdist_clusters(self):
        if self._raw_statdist_clusters is None or self._raw_statdist_clusters_summary is None:
                
            _, traj_count = self._get_raw_statdist()
            self._raw_statdist_clusters = []
            self._raw_statdist_clusters_summary = []

            with open(self.get_statdist_file(), "r") as f:
                started_cluster = False
                t_cluster = []
                started_summary = False
                for i, line in enumerate(f.readlines()[self._traj_count+1:]):
                    if not started_summary:
                        if len(line.strip("\n")) == 0:
                            self._raw_statdist_clusters.append(t_cluster)
                            t_cluster = []
                            started_cluster = False

                        elif line.startswith("Cluster\tState"):
                            started_summary = True
                        elif not started_cluster:
                            started_cluster = True
                        else:
                            t_cluster.append(line)

                    else:
                        self._raw_statdist_clusters_summary.append(line)

        return self._raw_statdist_clusters, self._raw_statdist_clusters_summary

