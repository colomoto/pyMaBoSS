"""
Class that contains the results of a MaBoSS simulation.
"""

import pandas as pd
import numpy as np

class ProbTrajResult(object):
    
    def __init__(self, output_nodes=None):

        self.output_nodes = output_nodes    
        
        self.state_probtraj = None
        self.state_probtraj_errors = None
        self.state_probtraj_full = None
        
        self.nd_probtraj = None
        self.nd_probtraj_error = None
        
        self.entropy_probtraj = None
        self.entropy_probtraj_error = None
        
        self.last_states_probtraj = None
        self.last_nodes_probtraj = None
        
        self._raw_data = None
        self._first_state_index = None

        self._raw_states = None
        self._raw_probas = None
        self._raw_errors = None
        self._raw_entropy = None
        self._raw_last_data = None

        self.indexes = None
        self.states = None
        self.nodes = None
        self.states_indexes = None
        self.nodes_indexes = None

    def get_states_probtraj(self, prob_cutoff=None):
        """
            Returns the state probability vs time, as a pandas dataframe.

            :param float prob_cutoff: returns only the states with proba > cutoff
        """
        if self.state_probtraj is None:

            raw_states = self._get_raw_states()
            raw_probas = self._get_raw_probas()
            indexes, states = self._get_indexes()
            states_indexes = self._get_states_indexes()
            
            new_data = np.zeros((len(raw_probas), len(states)))
            for i, t_probas in enumerate(raw_probas):
                for j, proba in enumerate(t_probas):
                    new_data[i, states_indexes[raw_states[i][j]]] = proba    
            
            self.state_probtraj = pd.DataFrame(
                data=new_data,
                columns=states,
                index=indexes

            )
            self.state_probtraj.sort_index(axis=1, inplace=True)

        if prob_cutoff is not None:
            maxs = self.state_probtraj.max(axis=0)
            return self.state_probtraj[maxs[maxs>prob_cutoff].index]

        return self.state_probtraj

    def get_states_probtraj_errors(self):
        """
            Returns the state probability error vs time, as a pandas dataframe.
        """
        if self.state_probtraj_errors is None:
            
            raw_states = self._get_raw_states()
            raw_errors = self._get_raw_errors()
            indexes, states = self._get_indexes()
            states_indexes = self._get_states_indexes()

            new_data = np.zeros((len(raw_errors), len(states)))
            for i, t_errors in enumerate(raw_errors):
                for j, error in enumerate(t_errors):
                    new_data[i, states_indexes[raw_states[i][j]]] = error    
            
            self.state_probtraj_errors = pd.DataFrame(
                data=new_data,
                columns=states,
                index=indexes

            )
            self.state_probtraj_errors.sort_index(axis=1, inplace=True)

        return self.state_probtraj_errors

    def get_nodes_probtraj(self, prob_cutoff=None):
        """
            Returns the node probability vs time, as a pandas dataframe.

            :param float prob_cutoff: returns only the nodes with proba > cutoff
        """
        if self.nd_probtraj is None:

            raw_states = self._get_raw_states()
            raw_probas = self._get_raw_probas()
            indexes, states = self._get_indexes()
            nodes = self.output_nodes if self.output_nodes is not None else self._get_nodes()
            nodes_indexes = self._get_nodes_indexes()

            new_probs = np.zeros((len(indexes), len(nodes)))
            for i, t_probas in enumerate(raw_probas):
                for j, proba in enumerate(t_probas):
                    if raw_states[i][j] != "<nil>":
                        for node in raw_states[i][j].split(" -- "):
                            new_probs[i, nodes_indexes[node]] += proba

            self.nd_probtraj = pd.DataFrame(new_probs, columns=nodes, index=indexes)
            self.nd_probtraj.sort_index(axis=1, inplace=True)

        if prob_cutoff is not None:
            maxs = self.nd_probtraj.max(axis=0)
            return self.nd_probtraj[maxs[maxs>prob_cutoff].index]

        return self.nd_probtraj

    def get_nodes_probtraj_error(self):
        """
            Returns the node probability error vs time, as a pandas dataframe.
        """
        if self.nd_probtraj_error is None:

            raw_states = self._get_raw_states()
            raw_errors = self._get_raw_errors()
            indexes, states = self._get_indexes()
            nodes = self.output_nodes if self.output_nodes is not None else self._get_nodes()
            nodes_indexes = self._get_nodes_indexes()
            
            new_errors = np.zeros((len(indexes), len(nodes)))
            for i, t_raw_errors in enumerate(raw_errors):
                for j, error in enumerate(t_raw_errors):
                    if raw_states[i][j] != "<nil>":
                        for node in raw_states[i][j].split(" -- "):
                            new_errors[i, nodes_indexes[node]] += error

            self.nd_probtraj_error = pd.DataFrame(new_errors, columns=nodes, index=indexes)
            self.nd_probtraj_error.sort_index(axis=1, inplace=True)

        return self.nd_probtraj_error

    def get_states_probtraj_full(self, prob_cutoff=None):
        if self.state_probtraj_full is None:

            raw_states = self._get_raw_states()
            raw_probas = self._get_raw_probas()
            raw_errors = self._get_raw_errors()
            raw_entropy = self._get_raw_entropy()
            indexes, states = self._get_indexes()
            states_indexes = self._get_states_indexes()

            full_cols = ["TH", "ErrorTH", "H"]
            for col in states:
                full_cols.append("Prob[%s]" % col)
                full_cols.append("ErrProb[%s]" % col)

            new_data = np.zeros((len(indexes), len(full_cols)))

            for i, t_entropy in enumerate(raw_entropy):
                new_data[i, 0:3] = t_entropy

            for i, t_probas in enumerate(raw_probas):
                for j, proba in enumerate(t_probas):
                    new_data[i, 3+(states_indexes[raw_states[i][j]]*2)] = proba

            for i, t_errors in enumerate(raw_errors):
                for j, error in enumerate(t_errors):
                    new_data[i, 4+(states_indexes[raw_states[i][j]]*2)] = error

            self.state_probtraj_full = pd.DataFrame(new_data, columns=full_cols, index=indexes)

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
        """
            Returns the asymptotic state probability, as a pandas dataframe.
        """
        if self.last_states_probtraj is None:
            
            data, first_col = self._get_raw_last_data()

            states = [s for s in data[first_col::3]]
            probs = np.array([float(v) for v in data[first_col+1::3]])
            
            self.last_states_probtraj = pd.DataFrame([probs], columns=states, index=[data[0]])
            self.last_states_probtraj.sort_index(axis=1, inplace=True)
             
        return self.last_states_probtraj

    def get_last_nodes_probtraj(self):
        """
            Returns the asymptotic node probability, as a pandas dataframe.
        """
        if self.last_nodes_probtraj is None:
            data, first_col = self._get_raw_last_data()
              
            raw_states = [s for s in data[first_col::3]]
            raw_probs = np.array([float(v) for v in data[first_col+1::3]])

            nodes = set()
            for state in raw_states:
                if state != "<nil>":
                    nodes.update([node for node in state.split(" -- ")])
            nodes = list(nodes) 
            nodes_indexes = {node:index for index, node in enumerate(nodes)}

            new_probas = np.zeros((1, len(nodes)))
            for i, proba in enumerate(raw_probs):
                if raw_states[i] != "<nil>":
                    for node in raw_states[i].split(" -- "):
                        new_probas[0, nodes_indexes[node]] += proba

            self.last_nodes_probtraj = pd.DataFrame(new_probas, columns=nodes, index=[data[0]])
            self.last_nodes_probtraj.sort_index(axis=1, inplace=True)

        return self.last_nodes_probtraj

    def get_entropy_trajectory(self):
        """
            Returns the entropy vs time, as a pandas dataframe.
        """
        if self.entropy_probtraj is None:

            raw_entropy = self._get_raw_entropy()
            indexes, _ = self._get_indexes()
            
            new_data = np.zeros((len(raw_entropy), 2))
            for i, entropy in enumerate(raw_entropy):
                new_data[i, 0] = entropy[0]
                new_data[i, 1] = entropy[2]
            
            self.entropy_probtraj = pd.DataFrame(
                data=new_data,
                columns=["TH", "H"],
                index=indexes
            )

        return self.entropy_probtraj

    def get_entropy_trajectory_error(self):
        """
            Returns the entropy error vs time, as a pandas dataframe.
        """
        if self.entropy_probtraj_error is None:

            raw_entropy = self._get_raw_entropy()
            indexes, _ = self._get_indexes()
            
            new_data = np.zeros((len(raw_entropy), 2))
            for i, entropy in enumerate(raw_entropy):
                new_data[i, 0] = entropy[1]
                new_data[i, 1] = entropy[2]
            
            self.entropy_probtraj_error = pd.DataFrame(
                data=new_data,
                columns=["ErrorTH", "H"],
                index=indexes
            )

        return self.entropy_probtraj_error

    def _get_probtraj_fd(self):
        return open(self.get_probtraj_file(), 'r')

    def _get_raw_data(self):
    
        if self._raw_data is None:
            with self._get_probtraj_fd() as probtraj:

                raw_lines = probtraj.readlines()

                if self._first_state_index is None:                    
                    self._first_state_index = next(i for i, col in enumerate(raw_lines[0].strip("\n").split("\t")) if col == "State")

                self._raw_data = [line.strip("\n").split("\t") for line in raw_lines[1:]]
        
        return self._raw_data, self._first_state_index
        
    def _get_raw_last_data(self):
    
        if self._raw_last_data is None:
            with self._get_probtraj_fd() as probtraj:

                if self._first_state_index is None:
                    first_line = probtraj.readline()
                    self._first_state_index = next(i for i, col in enumerate(first_line.strip("\n").split("\t")) if col == "State")

                last_line = probtraj.readlines()[-1]
                self._raw_last_data = last_line.strip("\n").split("\t")
        
        return self._raw_last_data, self._first_state_index

    def _get_raw_states(self):
        if self._raw_states is None:
            data, first_state_index = self._get_raw_data()
            self._raw_states = [[s for s in t_data[first_state_index::3]] for t_data in data]
        return self._raw_states

    def _get_raw_probas(self):
        if self._raw_probas is None:
            data, first_state_index = self._get_raw_data()
            self._raw_probas = [[np.float64(p) for p in t_data[first_state_index+1::3]] for t_data in data]
        return self._raw_probas

    def _get_raw_errors(self):
        if self._raw_errors is None:
            data, first_state_index = self._get_raw_data()
            self._raw_errors = [[np.float64(p) for p in t_data[first_state_index+2::3]] for t_data in data]
        return self._raw_errors
        
    def _get_raw_entropy(self):
        if self._raw_entropy is None:
            data, _ = self._get_raw_data()
            self._raw_entropy = [[np.float64(p) for p in t_data[1:4]] for t_data in data]
        return self._raw_entropy

    def _get_indexes(self):

        if self.indexes is None:
            data, _ = self._get_raw_data()
            self.indexes = [float(t_data[0]) for t_data in data] 
            
        if self.states is None:
            self.states = set()
            for t_states in self._get_raw_states():
                self.states.update(t_states)
            self.states = list(self.states)

        return self.indexes, self.states
    
    def _get_nodes(self):
        
        if self.nodes is None:
            self.nodes = set()
            for t_states in self._get_raw_states():
                for state in t_states:
                    if state != "<nil>":
                        self.nodes.update([node for node in state.split(" -- ")])
            self.nodes = list(self.nodes)
        
        return self.nodes

    def _get_states_indexes(self):
        if self.states_indexes is None:
            _, states = self._get_indexes()
            self.states_indexes = {state:index for index, state in enumerate(states)}
        return self.states_indexes

    def _get_nodes_indexes(self):
        if self.nodes_indexes is None:
            nodes = self.output_nodes if self.output_nodes is not None else self._get_nodes()
            self.nodes_indexes = {node:index for index, node in enumerate(nodes)}
        return self.nodes_indexes

        