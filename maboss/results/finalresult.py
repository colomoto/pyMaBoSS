"""
Class that contains the results of a MaBoSS simulation.
"""

class FinalResult(object):
    
    def __init__(self, simul, output_nodes=None):
        self.output_nodes = output_nodes
        
    def get_last_states_probtraj(self):
        """
            Returns the asymptotic state probability, as a pandas dataframe.
        """
        if self.last_states_probtraj is None:
            
            data = self._get_raw_last_data()

            states = [t_data[1] for t_data in data]
            probs = np.array([float(t_data[0]) for t_data in data])
            
            self.last_states_probtraj = pd.DataFrame([probs], columns=states)
            self.last_states_probtraj.sort_index(axis=1, inplace=True)
            
        return self.last_states_probtraj

    def get_last_nodes_probtraj(self):
        """
            Returns the asymptotic node probability, as a pandas dataframe.
        """
        if self.last_nodes_probtraj is None:
            data = self._get_raw_last_data()
              
            raw_states = [t_data[1] for t_data in data]
            raw_probs = np.array([float(t_data[0]) for t_data in data])

            nodes = self.output_nodes
            if nodes is None:
                nodes = set()
                for state in raw_states:
                    if state != "<nil>":
                        nodes.update([node for node in state.split(" -- ")])
                nodes = list(nodes) 

            nodes_indexes = {node:index for index, node in enumerate(self.output_nodes)}

            new_probas = np.zeros((1, len(self.output_nodes)))
            for i, proba in enumerate(raw_probs):
                if raw_states[i] != "<nil>":
                    for node in raw_states[i].split(" -- "):
                        new_probas[0, nodes_indexes[node]] += proba

            self.last_nodes_probtraj = pd.DataFrame(new_probas, columns=nodes)
            self.last_nodes_probtraj.sort_index(axis=1, inplace=True)

        return self.last_nodes_probtraj

 
    def _get_raw_last_data(self):
    
        if self._raw_last_data is None:
            with self._get_probtraj_fd() as probtraj:
                self._raw_last_data = [line.split("\t") for line in probtraj.readlines()]
    
        return self._raw_last_data

__all__ = ["FinalResult"]
