from __future__ import print_function
import os
import sys
import re
import random
import pandas as pd
if sys.version_info[0] < 3:
    from contextlib2 import ExitStack
else:
    from contextlib import ExitStack
import glob
from ..result import StoredResult
import shutil

class UpdatePopulationResults:
    def __init__(self, uppModel, verbose=False, workdir=None, overwrite=False, previous_run=None):
        self.uppModel = uppModel
        self.pop_ratios = pd.Series()
        self.stepwise_probability_distribution = None
        self.results = []
        self.verbose = verbose
        self.workdir = workdir
        self.overwrite = overwrite
        self.pop_ratio = uppModel.pop_ratio

        if os.path.exists(workdir) and not self.overwrite:
            # Restoring
            self.results = [None] * (self.uppModel.step_number + 1)

            for folder in sorted(glob.glob("%s/Step_*/" % self.workdir)):
                step = os.path.basename(folder[0:-1]).split("_")[-1]
                self.results[int(step)] = StoredResult(folder)

            self.pop_ratios = pd.read_csv(
                os.path.join(self.workdir, "PopRatios.csv"),
                index_col=0, squeeze=True
            ) / self.uppModel.base_ratio

            if previous_run:
                # Load the previous run final state
                _get_next_condition_from_trajectory(previous_run, self.uppModel.model)

        else:
            if self.overwrite and os.path.exists(workdir):
                shutil.rmtree(workdir)
            os.makedirs(workdir)
            if previous_run:
                # Load the previous run final state
                _get_next_condition_from_trajectory(previous_run, self.uppModel.model)

            self._run()

    def _run(self):
        
        if self.verbose:
            print("Run MaBoSS step 0")

        result = self.uppModel.model.run()
        if self.workdir is not None:
            result.save(os.path.join(self.workdir, "Step_0"))

        self.results.append(result)
        self.pop_ratios[self.uppModel.time_shift] = self.pop_ratio
    
        modelStep = self.uppModel.model.copy()

        for stepIndex in range(1, self.uppModel.step_number+1):

            LastLinePrevTraj = ""                
            with open(result.get_probtraj_file(), 'r') as PrStepTrajF:
                LastLinePrevTraj = PrStepTrajF.readlines()[-1]
            
            self.pop_ratio *= self._updatePopRatio(LastLinePrevTraj)
            self.pop_ratios[self.uppModel.time_shift + self.uppModel.time_step*stepIndex] = self.pop_ratio
            
            modelStep = self._buildUpdateCfg(modelStep, LastLinePrevTraj)
            
            if modelStep is None:
                if self.verbose:
                    print("No cells left")

                break

            else:
                if self.verbose:
                    print("Running MaBoSS for step %d" % stepIndex)

                result = modelStep.run()
                if self.workdir is not None:
                    result.save(os.path.join(self.workdir, "Step_%d" % stepIndex))

                self.results.append(result)

        if self.workdir is not None:
            self.save_population_ratios(os.path.join(self.workdir, "PopRatios.csv"))

    def get_population_ratios(self, name=None):
        if name:
            self.pop_ratios.name = name
        return self.pop_ratios*self.uppModel.base_ratio

    def get_stepwise_probability_distribution(self):
        if self.stepwise_probability_distribution is None:
            tables = [result.get_last_states_probtraj() for result in self.results]
            self.stepwise_probability_distribution = pd.concat(tables, axis=0, sort=False)
            self.stepwise_probability_distribution.fillna(0, inplace=True)
            self.stepwise_probability_distribution.set_index([list(range(0, len(tables)))], inplace=True)
            self.stepwise_probability_distribution.insert(0, column='PopRatio', value=(self.pop_ratios*self.uppModel.base_ratio).values)
            
        return self.stepwise_probability_distribution

    def save(self, path):
        if not os.path.exists(path):
            os.mkdir(path)

        self.save_model(path)
        self.save_population_ratios(os.path.join(path, "PopRatios.csv"))
        self.save_stepwise_probability_distribution(os.path.join(path, "PopProbTraj.csv"))

    def save_model(self, path):
        with ExitStack() as stack:
            cfg_file = stack.enter_context(open(os.path.join(path, "model.cfg"), 'w'))
            bnd_file = stack.enter_context(open(os.path.join(path, "model.bnd"), 'w'))
            self.uppModel.model.print_cfg(cfg_file)
            self.uppModel.model.print_bnd(bnd_file)

    def save_population_ratios(self, path):
        (self.pop_ratios*self.uppModel.base_ratio).to_csv(path, header=["PopRatio"], index_label="Step")

    def save_stepwise_probability_distribution(self, path):
        self.get_stepwise_probability_distribution().to_csv(path, index_label="Step")

    def _buildUpdateCfg(self, simulation, prob_traj_line): 

        probTrajListFull = prob_traj_line.split("\t")
        probTrajList = list(probTrajListFull)

        for prob_traj in probTrajListFull:
            if prob_traj[0].isalpha() or prob_traj == "<nil>":
                break
            else:
                probTrajList.pop(0)
            
        normFactor = 0
        deathProb = 0
        divisionProb = 0

        for i in range(0, len(probTrajList), 3):
            t_state = probTrajList[i]

            if nodeIsInState(self.uppModel.death_node, t_state):
                deathProb += float(probTrajList[i+1])
                probTrajList[i+1] = str(0)

            else:
                if t_state == self.uppModel.division_node:
                    divisionProb += float(probTrajList[i+1])
                    probTrajList[i+1] = str(2.0*float(probTrajList[i+1]))
                    probTrajList[i] = "<nil>"

                elif t_state.startswith(self.uppModel.division_node+" "):
                    divisionProb += float(probTrajList[i+1])
                    probTrajList[i+1] = str(2.0*float(probTrajList[i+1]))
                    probTrajList[i] = probTrajList[i].replace(self.uppModel.division_node+" -- ", "")

                elif (" %s " % self.uppModel.division_node) in t_state:
                    divisionProb += float(probTrajList[i+1])
                    probTrajList[i+1] = str(2.0*float(probTrajList[i+1]))
                    probTrajList[i] = probTrajList[i].replace(" -- "+self.uppModel.division_node, "")
            
                elif t_state.endswith(" "+self.uppModel.division_node):
                    divisionProb += float(probTrajList[i+1])
                    probTrajList[i+1] = str(2.0*float(probTrajList[i+1]))
                    probTrajList[i] = probTrajList[i].replace(" -- "+self.uppModel.division_node, "")

                normFactor += float(probTrajList[i+1])

        if self.verbose:
            print("Norm Factor:%g probability of death: %g probability of division: %g" % (normFactor, deathProb, divisionProb))

        if normFactor > 0:
            
            for i in range(0, len(probTrajList), 3):
                probTrajList[i+1] = str(float(probTrajList[i+1])/normFactor)

            parameters = {}

            for parameter, value in simulation.param.items():
                if parameter.startswith("$") and parameter in self.uppModel.update_var.keys():
                    new_value = varDef_Upp(self.uppModel.update_var[parameter], probTrajList)

                    for match in re.findall("#rand", new_value):
                        rand_number = random.uniform(0, 1)
                        new_value = new_value.replace("#rand", str(rand_number), 1)

                    new_value = new_value.replace("#pop_ratio", str(self.pop_ratio))
                    parameters.update({parameter: new_value})
                    if self.verbose:
                        print("Updated variable: %s = %s" % (parameter, new_value))
            
            simulation.param.update(parameters)
            new_istate = self._initCond_Trajline(probTrajList)
            
            simulation.network.set_istate(self.uppModel.node_list, new_istate, warnings=False)
            return simulation

    def _initCond_Trajline(self, proba_traj_list):

        new_istate = {}
        name2idx = {name: i for i, name in enumerate(self.uppModel.node_list)}

        for i in range(0, len(proba_traj_list), 3):
            state = proba_traj_list[i]
            proba = float(proba_traj_list[i+1])

            state_tuple = tuple(_str2state(state, name2idx))

            if state_tuple in new_istate.keys():
                proba += new_istate[state_tuple]
            
            new_istate.update({state_tuple: proba})

        return new_istate

    def _updatePopRatio(self, last_line):

        upPopRatio = 0.0
        probTrajList = last_line.split("\t")
        indexStateTrajList = -1

        for probTraj in probTrajList:
            indexStateTrajList += 1
            if probTraj[0].isalpha() or probTraj == "<nil>":
                break

        for i in range(indexStateTrajList, len(probTrajList), 3):
            t_node = probTrajList[i]

            if not nodeIsInState(self.uppModel.death_node, t_node):
                if nodeIsInState(self.uppModel.division_node, t_node):
                    upPopRatio += 2*float(probTrajList[i+1])
                else:
                    upPopRatio += float(probTrajList[i+1])

        return upPopRatio

def nodeIsInState(node, state):
    return (
        state == node 
        or state.startswith(node+" ") 
        or state.endswith(" "+node) 
        or (" %s " % node) in state
    )

def varDef_Upp(update_line, prob_traj_list):

	res_match = re.findall("p\[[^\[]*\]", update_line)
	if len(res_match) == 0:
		print("Syntax error in the parameter update definition : %s" % update_line, file=sys.stderr)
		exit()
	
	for match in res_match:

		lhs, rhs = match.split("=")
		lhs = lhs.replace("p[", "").replace("]", "").replace("(", "").replace(")", "")
		rhs = rhs.replace("[", "").replace("]", "").replace("(", "").replace(")", "")

		node_list = [token.strip() for token in lhs.split(",")]
		boolVal_list = [token.strip() for token in rhs.split(",")]

		if len(node_list) != len(boolVal_list):
			print("Wrong probability definitions for \"%s\"" % match)
			exit()

		upNodeList = []
		downNodeList = []

		for i, node in enumerate(node_list):
			if float(boolVal_list[i]) == 0.0:
				downNodeList.append(node)
			else:
				upNodeList.append(node)

		probValue = 0.0
		for i in range(0, len(prob_traj_list), 3):
			upNodeProbTraj = prob_traj_list[i].split(" -- ")
			interlength = 0

			for upNodePt in upNodeProbTraj:
				for upNode in upNodeList:
					if upNodePt == upNode:
						interlength += 1

			if interlength == len(upNodeList):
				interlength = 0
				for upNodePt in upNodeProbTraj:
					for downNode in downNodeList:
						if upNodePt == downNode:
							interlength = 1
							break
					
					if interlength == 1:
						break
				if interlength == 0:
					probValue += float(prob_traj_list[i+1])

		update_line = update_line.replace(match, str(probValue), 1)
	update_line += ";"
	return update_line
	
def _get_next_condition_from_trajectory(self, next_model, step=16, pickline=5):
    names = [ n for n in self.uppModel.model.network.names ]
    name2idx = {}
    for i in range(len(names)): name2idx[ names[i] ] = i

    trajfile = self.results[step].get_probtraj_file()
    with open(trajfile) as f:
        last_line = f.readlines()[-1]
        data = last_line.strip("\n").split("\t")
        states = [ _str2state(s,name2idx) for s in data[5::3] ]
        probs = [float(v) for v in data[6::3]]
    probDict = {}
    for state,prob in zip(states, probs):
        probDict[tuple(state)] = prob

    next_model.network.set_istate(names, probDict, warnings=False)


def _str2state(s, name2idx):
    state = [ 0 for n in name2idx]
    if '<nil>' != s:
        for n in s.split(' -- '):
            state[name2idx[n]] = 1
    return state


