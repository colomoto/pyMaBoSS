from __future__ import print_function
import os
import sys
import re
import random
import pandas as pd
import numpy as np
if sys.version_info[0] < 3:
    from contextlib2 import ExitStack
else:
    from contextlib import ExitStack
import glob
from ..results.storedresult import StoredResult
from ..server import MaBoSSClient
import shutil
from multiprocessing import Pool


class UpdatePopulationResults:
    def __init__(self, uppModel, verbose=False, workdir=None, overwrite=False, previous_run=None, previous_run_step=-1, host=None, port=7777, nodes_init=None):
        """UpdatePopulationResults class
        :param uppModel: UppMaBoSS model
        :param verbose: boolean to activate verbose mode, default to False        
        :param workdir: working directoy, default to None
        :param overwrite: overwrite previous results, default to False
        :param previous_run: previous run used to initialize starting probability
        distribution, default to None
        :param previous_run_step: step used to initialize starting probability
        distribution from previous run, default to -1 (last)
        """
        self.uppModel = uppModel
        self.pop_ratios = pd.Series()
        self.stepwise_probability_distribution = None
        self.nodes_stepwise_probability_distribution = None
        self.nodes_list_stepwise_probability_distribution = None

        self.nodes_init = nodes_init
        self.results = []
        self.verbose = verbose
        self.workdir = workdir
        self.overwrite = overwrite
        self.pop_ratio = uppModel.pop_ratio

        self.host = host
        self.port = port   

        if workdir is not None and os.path.exists(workdir) and not self.overwrite:
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
                _get_next_condition_from_trajectory(previous_run, self.uppModel.model, step=previous_run_step)

        else:
            if workdir is not None:
                if os.path.exists(workdir):
                    shutil.rmtree(workdir)
                os.makedirs(workdir)

            if previous_run:
                # Load the previous run final state
                _get_next_condition_from_trajectory(previous_run, self.uppModel.model, step=previous_run_step)

            self._run()

    def _run(self):
        
        if self.verbose:
            print("Run MaBoSS step 0")

        sim_workdir = os.path.join(self.workdir, "Step_0") if self.workdir is not None else None
        
        if self.host is None:
            result = self.uppModel.model.run(workdir=sim_workdir)
        else:
            mbcli = MaBoSSClient(self.host, self.port)
            result = mbcli.run(self.uppModel.model)
            mbcli.close()

        self.results.append(result)
        self.pop_ratios[self.uppModel.time_shift] = self.pop_ratio
    
        modelStep = self.uppModel.model.copy()

        for stepIndex in range(1, self.uppModel.step_number+1):
            #
            # Update pop ratio and construct the new version of model
            #
            with result._get_probtraj_fd() as result_probtraj_fd:
                modelStep = self._buildUpdateCfg(modelStep, result_probtraj_fd, stepIndex)
            
            if modelStep is None:
                if self.verbose:
                    print("No cells left")

                break

            else:
                if self.verbose:
                    print("Running MaBoSS for step %d" % stepIndex)

                sim_workdir = os.path.join(self.workdir, "Step_%d" % stepIndex) if self.workdir is not None else None
                
                if self.host is None:
                    result = modelStep.run(workdir=sim_workdir)
                else:
                    mbcli = MaBoSSClient(self.host, self.port)
                    result = mbcli.run(modelStep)
                    mbcli.close()

                self.results.append(result)

        if self.workdir is not None:
            self.save_population_ratios(os.path.join(self.workdir, "PopRatios.csv"))

    def get_population_ratios(self, name=None):
        if name:
            self.pop_ratios.name = name
        return self.pop_ratios*self.uppModel.base_ratio

    def get_stepwise_probability_distribution(self, nb_cores=1, include=None, exclude=None):
        if self.stepwise_probability_distribution is None:
            if nb_cores > 1:
                tables = []
                with Pool(processes=nb_cores) as pool:
                    tables = pool.map(
                        make_stepwise_probability_distribution_line, self.results
                    )

            else:
                tables = [result.get_last_states_probtraj() for result in self.results]
            
            self.stepwise_probability_distribution = pd.concat(tables, axis=0, sort=False)
            self.stepwise_probability_distribution.fillna(0, inplace=True)
            self.stepwise_probability_distribution.set_index([list(range(0, len(tables)))], inplace=True)
            self.stepwise_probability_distribution.insert(
                0, column='PopRatio', value=(self.pop_ratios*self.uppModel.base_ratio).values
            )
            
        if include is None and include is None:
            return self.stepwise_probability_distribution
        else:
            states_filtered = self.stepwise_probability_distribution.columns
            
            if include is not None:
                states_filtered = [state for state in states_filtered if set(include).issubset(set(state.split(" -- ")))]
    
            if exclude is not None:
                states_filtered = [state for state in states_filtered if set(exclude).isdisjoint(set(state.split(" -- ")))]
           
            return self.stepwise_probability_distribution.loc[:, states_filtered]

    def get_nodes_stepwise_probability_distribution(self, nodes=None, nb_cores=1):
        if self.nodes_stepwise_probability_distribution is None or set(nodes) != self.nodes_list_stepwise_probability_distribution:
            
            table = self.get_stepwise_probability_distribution(nb_cores=nb_cores)
            
            states = table.columns.values[1:].tolist()
            if "<nil>" in states:
                states.remove("<nil>")

            if nodes is None:
                nodes = get_nodes(states)
            else:
                nodes = set(nodes)
            
            self.nodes_list_stepwise_probability_distribution = nodes

            node_dict = {}
            for state in states:
                t_nodes = state.split(" -- ")
                t_nodes = [node for node in t_nodes if node in nodes]
                if len(t_nodes) > 0:
                    node_dict.update({state: t_nodes})

            if nb_cores > 1:
                self.nodes_stepwise_probability_distribution = make_nodes_table_parallel(table, nodes, node_dict, nb_cores)
            else:
                self.nodes_stepwise_probability_distribution = make_nodes_table(table, nodes, node_dict)

            self.nodes_stepwise_probability_distribution.insert(0, column='PopRatio', value=(self.pop_ratios*self.uppModel.base_ratio).values)

        return self.nodes_stepwise_probability_distribution

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
        nb_cores = int(self.uppModel.model.param["thread_count"])
        self.get_stepwise_probability_distribution(nb_cores=nb_cores).to_csv(path, index_label="Step")

    def _buildUpdateCfg(self, simulation, traj_fd, stepIndex):
        """Configure the MaBoSS model for the next run of UppMaBoss.
        In practice, _buildUpdateCfg uses the previous simulation result
        to compute pop ratio, death, division, parameters, nodes formulas 
        and sets the init state of the model for the next step of simulation
        :param simulation: MaBoSS simulation
        :param traj_file: trajectory file of previous run        
        :param stepIndex: current step of the UppMaBoss simulation
        """
        #
        # Read first and last line, extract last states with respective probs
        #
        first_line, last_line = read_first_last_lines_from_trajectory (traj_fd)
        states, probs = get_states_probs_from_trajectory_line (first_line, last_line)                                                            
        #
        # Update pop ratio
        #
        self.pop_ratio *= self._updatePopRatio (states, probs)
        new_time = self.uppModel.time_shift + self.uppModel.time_step*stepIndex
        self.pop_ratios[new_time] = self.pop_ratio
        #
        # Normalize
        #
        states, probs = self.normalize_with_death_and_division (states, probs)
        if states is None:
            return None        
        #
        # Compute formulas for parameters and nodes 
        # 
        parameters = self.compute_parameters(simulation, states, probs)
        nodes_with_formula = self.compute_nodes_formula (states, probs)
        #
        # Apply new values for parameters 
        # 
        simulation.param.update(parameters)
        #
        # Init states
        #
        nodes_to_init, new_istate = self._initCond_Trajline (states, probs)
        simulation.network.set_istate (nodes_to_init, new_istate, warnings=False)
        #
        # Init nodes having a formula
        #
        for a_node in nodes_with_formula.keys():
            new_val = nodes_with_formula[a_node]
            simulation.network.set_istate(a_node, [1-new_val,new_val], warnings=False)
        return simulation 
    
    def normalize_with_death_and_division(self, states, probs): 
        """
        Take into account impact of death and division and normalize
        NB: if no death, nor division is defined, do nothing
        :param states: list of states extracted from the trajectory
        :param probs: list of states probabilities extracted from the trajectory  
        """
        #
        # speed up programm when no death, nor division
        # 
        if not self.uppModel.death_node and not self.uppModel.division_node:
            return states, probs
        #
        # if death or division
        #
        norm_factor = 0
        death_prob = 0
        division_prob = 0
    
        states_ret = []
        probs_ret = []
        for one_state, one_prob in zip(states, probs):
            one_state_ret = one_state.copy()
            one_prob_ret = one_prob
            
            if self.uppModel.death_node in one_state_ret:
                death_prob += one_prob_ret
                one_prob_ret = 0
            else:
                if self.uppModel.division_node in one_state_ret:
                    division_prob += one_prob_ret
                    one_prob_ret *= 2.0
                    one_state_ret.remove(self.uppModel.division_node)
                norm_factor += one_prob_ret
                
            states_ret.append (one_state_ret)
            probs_ret.append (one_prob_ret)
    
        if self.verbose:
            print("Norm Factor:%g probability of death: %g probability of division: %g"  \
                  % (norm_factor, death_prob, division_prob))
        #
        # if norm_factor <= 0, no more cells
        #
        if norm_factor <= 0:
            return None, None
        #
        # If norm_factor > 0, normalize 
        #
        probs_ret = np.array(probs_ret, dtype = float)
        probs_ret = (probs_ret / norm_factor).tolist()
        return states_ret, probs_ret

    def compute_parameters(self, simulation, states, probs): 
        """
        Computer parameters
        :param simulation: MaBoss model (containing the defining of parameters) 
        :param states: list of states extracted from the trajectory
        :param probs: list of states probabilities extracted from the trajectory  
        """
        parameters = {}
        for parameter, value in simulation.param.items():
            if parameter.startswith("$") and parameter in self.uppModel.update_var.keys():
                formula = self.uppModel.update_var[parameter]
                new_value = varDef_Upp(formula, states, probs)
                for match in re.findall("#rand", new_value):
                    rand_number = random.uniform(0, 1)
                    new_value = new_value.replace("#rand", str(rand_number), 1)
    
                new_value = new_value.replace("#pop_ratio", str(self.pop_ratio))
                parameters.update({parameter: new_value})
                if self.verbose:
                    print("Updated variable: %s = %s" % (parameter, new_value))
        return parameters

    def compute_nodes_formula (self, states, probs): 
        """
        Computer nodes formula to be used as init values for next run
        :param states: list of states extracted from the trajectory
        :param probs: list of states probabilities extracted from the trajectory  
        """
        all_node_upd = {}
        for node_upd in self.uppModel.nodes_formula.keys():
            node_formula = self.uppModel.nodes_formula[node_upd]
            new_value = varDef_Upp(node_formula, states, probs)
            
            for match in re.findall("#rand", new_value):
                rand_number = random.uniform(0, 1)
                new_value = new_value.replace("#rand", str(rand_number), 1)
    
            new_value = new_value.replace("#pop_ratio", str(self.pop_ratio))
            #
            # Remove trailing ';' added by varDef_Upp, compute formula via eval 
            # and convert to proba
            #
            new_value = float (eval(new_value[:-1]))
            new_value = np.clip(new_value, 0, 1)
               
            all_node_upd.update({node_upd: new_value})
            if self.verbose:
                print("Updated node:", node_upd, "=", new_value)
        return all_node_upd

    def _initCond_Trajline(self, states, probs):
        """
        Return the list of states to be initialized from states and probs
        The function excludes from states the nodes with formulas
        or (for the first run) nodes with init value supplied as parameter
        :param states: list of states extracted from the trajectory
        :param probs: list of states probabilities extracted from the trajectory  
        :param nodes_init: dict of nodes values of the form { "NODE1" : TrueValue1, "NODE2" : TrueValue2, ... }.
        Nodes to exclude from InitCond as these nodes have a specific init value
        """
        new_istate = {}
        #
        # Remove from the list of nodes the ones having a rule or an init value
        #
        nodes_to_exclude = set(self.uppModel.nodes_formula.keys()) 
        if self.nodes_init:
            nodes_to_exclude= nodes_to_exclude | set(self.nodes_init.keys())

        list_nodes_to_set = list( set(self.uppModel.node_list) - nodes_to_exclude )
        # Not necessary for MaBoss, only to have visually an ouput always in the same order
        list_nodes_to_set.sort()
        #
        # Associate an index to each node
        #
        name2idx = {name: i for i, name in enumerate(list_nodes_to_set)}
        #
        # Exclude nodes with formula or with specific init from states
        #
        states = exclude_nodes_from_states (states, nodes_to_exclude)
        #
        # Construct a list of states (each state is tuple of nodes on/off)
        # with the probability of each state
        #
        for state, prob in zip(states, probs):
            #
            # Inclusion of modified _str2state code
            #
            str2state = [ 0 ] * len(name2idx)
            if '<nil>' not in state:
                for node in state:
                    str2state[name2idx[node]] = 1
            
            state_tuple = tuple(str2state)

            if state_tuple in new_istate.keys():
                prob += new_istate[state_tuple]
            
            new_istate.update({state_tuple: prob})

        return list_nodes_to_set, new_istate

    def _updatePopRatio (self, states, probs):
        """
        Return update population ratio using nodes having death or division
        :param states: states extracted from the trajectory
        :param probs: probabilities of states extracted from the trajectory  
        """
        upd_pop_ratio = 0.0
        for a_state, a_prob in zip(states, probs):
            if self.uppModel.death_node not in a_state:
                if self.uppModel.division_node in a_state:
                    upd_pop_ratio += 2 * a_prob
                else:
                    upd_pop_ratio += a_prob
        return upd_pop_ratio

def varDef_Upp(update_line, states, probs):
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
		for i in range(0, len(states)):
			upNodeProbTraj = states[i]
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
					probValue += probs[i]

		update_line = update_line.replace(match, str(probValue), 1)
	update_line += ";"
	return update_line

def _get_next_condition_from_trajectory(self, next_model, step=-1):
    """
    Set the values of MaBoss model when resuming from a previous run
    :param next_model : MaBoss model
    :param step: step of the UppMaBoss simulation
    """
    #
    # Extract states and probs from trajectory
    #
    
    with self.results[step]._get_probtraj_fd() as trajfd:
        first_line, last_line = read_first_last_lines_from_trajectory (trajfd)
    states, probs = get_states_probs_from_trajectory_line (first_line, last_line)
    #
    # Compute formulas for nodes 
    # 
    nodes_with_formula = self.compute_nodes_formula (states, probs)
    #
    # Init states
    #
    nodes_to_set, new_istate = self._initCond_Trajline(states, probs)        
    next_model.network.set_istate (nodes_to_set, new_istate, warnings=False)    
    #
    # Init nodes having a formula
    #
    for a_node in nodes_with_formula.keys():
        new_val = nodes_with_formula[a_node]
        next_model.network.set_istate(a_node, [1-new_val,new_val], warnings=False)
    #
    # Init nodes having an init value
    #
    if self.nodes_init:
        for a_node, new_val in self.nodes_init.items():
            next_model.network.set_istate(a_node, [1-new_val,new_val], warnings=False)
            if self.verbose:
                print("Starting init of node:", a_node, "=", new_val)

def read_first_last_lines_from_trajectory (f):
    """Read first and last lines of a trajectory file
    :param traj_file: trajectory file
    """
    first_line = ""
    last_line = ""
    first_pass = True
    # 
    # This loop avoid to load all the file in memory
    #
    for line in f:
        if first_pass:
            first_line = line
            first_pass = False
        else:
            last_line = line
    f.close()
    first_line = first_line.strip("\n")
    last_line = last_line.strip("\n")
    return first_line, last_line

def get_states_probs_from_trajectory_line (first_line, last_line):
    """Extract states and probabilities from the first and last lines 
    of a trajectory file
    :param first_line: first line of trajectory file
    :param last_line: last line of trajectory file
    """
    #
    # Split using tab separator
    #    
    first_line_as_list = first_line.split("\t")
    last_line_as_list = last_line.split("\t")
    #
    # Locate 'State' cols
    #    
    cols_state = next(i for i, col in enumerate (first_line_as_list) if col == "State")
    #
    # Extract state from 'State' cols
    #    
    states = [ s.split(" -- ")  for s in last_line_as_list[cols_state::3] ]
    #
    # Extract probs from 'State' cols + 1
    #    
    probs = [float(v) for v in last_line_as_list[cols_state+1::3]]
    return states, probs
            
def exclude_nodes_from_states (traj_states, nodes_exluded=None):
    """Exclude nodes from states
    :param traj_states: list of states (each state is a liste of nodes)
    :param nodes_exluded: list/set of nodes to remove
    """
    if (not nodes_exluded) or len(nodes_exluded) <= 0:
        return traj_states
    traj_states_ret = []
    for one_traj_states in traj_states:
        new_traj_states = list( set(one_traj_states) - set(nodes_exluded) )
        if len (new_traj_states) <= 0:
            new_traj_states  = ["<nil>"]
        traj_states_ret.append (new_traj_states)
    return traj_states_ret   

def make_stepwise_probability_distribution_line(result):
    return result.get_last_states_probtraj()

def get_nodes(states):
    nodes = set()
    for s in states:
        if s != '<nil>':
            nds = s.split(' -- ')
            for nd in nds:
                nodes.add(nd)
    return nodes

def make_node_line(row, states_table, index, node_dict):
    for state, nd_state in node_dict.items():
        for nd in nd_state:
            row[nd] += states_table.iloc[index, states_table.columns.get_loc(state)]

def make_nodes_table(spd, nodes, node_dict):
    table = pd.DataFrame(
        np.zeros((len(spd.index), len(nodes))),
        index=spd.index.values, columns=nodes
    )

    for index, (_, row) in enumerate(table.iterrows()):
        make_node_line(row, spd, index, node_dict)
        
    return table

def make_node_line_parallel(states_row, nodes, node_dict, row):
    
    table = pd.DataFrame(
        np.zeros((1, len(nodes))),
        index=[row], columns=nodes
    )
    
    for row_index, row_state in states_row.iteritems():
        if row_index in node_dict.keys() and row_state > 0.0:
            for nd in node_dict[row_index]:
                table.loc[row, nd] += row_state
    
    return table

def make_nodes_table_parallel(spd, nodes, node_dict, nb_cores):
    
    tables = []
    with Pool(processes=6) as pool:
        tables = pool.starmap(
            make_node_line_parallel, 
            [(spd.iloc[index, :], nodes, node_dict, row) for index, row in enumerate(spd.index)]
        )

    table = pd.concat(tables, axis=0, sort=False)

    return table
