"""
Class that contains the results of a MaBoSS simulation.
"""

import pandas
import tempfile
import os
from .results.baseresult import BaseResult
from contextlib import ExitStack

class CMaBoSSResult(BaseResult):

    def __init__(self, simul, workdir=None, overwrite=False, prefix="res", only_final_state=False):

        self.simul = simul
        self.output_nodes = simul.network.get_output()
        self.only_final_state = only_final_state
        BaseResult.__init__(self, simul, output_nodes=self.output_nodes)
        
        cmaboss_module = simul.get_cmaboss()
        cmaboss_sim = cmaboss_module.MaBoSSSim(
            network_str=str(simul.network), 
            config_str=simul.str_cfg()
        )

        self.cmaboss_result = cmaboss_sim.run(self.only_final_state)

        if workdir is not None:
            if not os.path.exists(workdir):
                os.makedirs(workdir)

            self.cmaboss_result.display_run(os.path.join(workdir, "%s_run.txt" % prefix))

            if self.only_final_state:
                self.cmaboss_result.display_final_states(os.path.join(workdir, "%s_finalprob.csv" % prefix))
            else:
                self.cmaboss_result.display_probtraj(os.path.join(workdir, "%s_probtraj.csv" % prefix))
                self.cmaboss_result.display_fp(os.path.join(workdir, "%s_fp.csv" % prefix))
                self.cmaboss_result.display_statdist(os.path.join(workdir, "%s_statdist.csv" % prefix))


    def get_last_states_probtraj(self):
        raw_res = self.cmaboss_result.get_last_states_probtraj()
        final_time = self.cmaboss_result.get_final_time()
        
        states = []
        vals = []
        for state, val in raw_res.items():
            states.append(state)
            vals.append(val)

        df = pandas.DataFrame([vals], columns=states, index=[final_time])
        return df

    def get_states_probtraj(self, prob_cutoff=None):
        if not self.only_final_state:
            raw_res = self.cmaboss_result.get_raw_probtrajs()
            (timepoints, states) = self.cmaboss_result.get_states()
            df = pandas.DataFrame(raw_res, columns=states, index=timepoints)
            df.sort_index(axis=1, inplace=True)

            if prob_cutoff is not None:
                maxs = df.max(axis=0)
                return df[maxs[maxs>prob_cutoff].index]

            return df

    def get_nodes_probtraj(self, prob_cutoff=None):
        if not self.only_final_state:
            raw_res = self.cmaboss_result.get_raw_nodes_probtrajs()
            (timepoints, nodes) = self.cmaboss_result.get_nodes()
            df = pandas.DataFrame(raw_res, columns=nodes, index=timepoints)
            df.sort_index(axis=1, inplace=True)

            if prob_cutoff is not None:
                maxs = df.max(axis=0)
                return df[maxs[maxs>prob_cutoff].index]

            return df

    def get_fptable(self):
        if not self.only_final_state:
            raw_res = self.cmaboss_result.get_fp_table()

            df = pandas.DataFrame(["#%d" % fp for fp in sorted(raw_res.keys())], columns=["FP"])

            df["Proba"] = [raw_res[fp][0] for fp in sorted(raw_res.keys())]
            df["State"] = [raw_res[fp][1] for fp in sorted(raw_res.keys())]

            for node in self.simul.network.keys():
                df[node] = [1 if node in raw_res[fp][1].split(" -- ") else 0 for fp in sorted(raw_res.keys())]

            return df


__all__ = ["CMaBoSSResult"]
