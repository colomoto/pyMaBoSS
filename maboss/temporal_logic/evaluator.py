import warnings
from itertools import combinations
from unittest import case

from jedi.inference.compiled import value
from pexpect import expect
from scipy.signal import lsim


from IPython.display import display

import maboss
import numpy as np

from maboss import Result, Network
from maboss.temporal_logic.custom_exceptions import DataFrameIsEmpty, NoNameException, NoNameValidException, \
    FormulaException, NoCommonTimes, ErrorInLogicalExpression
from maboss.temporal_logic.logical_expression_compute import ComputeLogicalExpression
from maboss.temporal_logic.temporal_parser import Parser
from maboss.temporal_logic.formulas import Operators, QueryType, TargetType, FormulaChecker, Formula
import pandas as pd


class MaBoSSEvaluator:
    """
    The main class that evaluates the query and assemble and compute the results
    """
    simulation_results = None
    simulation_results_raw = None
    parsed_query = None

    # Options
    percentage_value_int = 0
    threshold = 0.05  # sensibility on variations across time
    optimum = 0.1  # sensibility of max/min value for transient evaluation, authorised difference between compare and mut
    start = 0.1  # sensibility of start value of transient evaluation, authorised difference between compare and mut
    end = 0.1  # sensibility of end value of transient evaluation, authorised difference between compare and mut
    digits = 4  # number of digits after the dot to take into account for computing
    compare_to = 'master'  # name of the results to compare to
    transient = False  # the evaluation has something to check across time
    combination = False  # the nodes that were passed have to be check in combination, if TargetType is STATE, do not look for a name but for names where the nodes passed are in

    @staticmethod
    def help():
        print("MaBoSSEvaluator help :")
        print(
            "To evaluate one or multiple queries based on ONE already run simulation (v1.0), use the following syntax :")
        print("MaBoSSEvaluator.evaluate_query([query], results)")
        print(
            "query : the query to evaluate, a list of strings : [\"query1\",\"query2\"], results] , [\"query\"], results]")
        print("results : the results of the simulation, a SimulationResults object (one that maboss returns)")
        print(
            "--------------------------------------------------------------------------------------------------------")
        print("HELP FOR THE QUERY")
        print(
            "The query is a string that contains the following elements : [type]([target_type]:name1,name2...) [operator] [value] [logical_equation (optional)] [mutations (opt)] [options]")
        print("[type] : The type of operation to perform, can be P (probability) or T (time).")
        print("\t - P : will compare the probability of the target to the value. Only one to handle \'?\' value")
        print("\t - T : will return the periods of time where the target probability is meeting the criteria of value.")
        print(
            "\t - Pmax : will return the highest value of the target probability while meeting the criteria of value.")
        print("\t - Pmin : will return the lowest value of the target probability while meeting the criteria of value.")
        print(
            "\t - Tmax : will return the last period of time where the target probability is meeting the criteria of value.")
        print(
            "\t - Tmin : will return the first period of time where the target probability is meeting the criteria of value.")
        print(
            "\t - D : will check if the two nodes passed in parameters are always activate at the same time. Names must be separated by commas.")
        print(
            "\t - Inc : check if the node or the state passed in parameters sees its probability increase on the last time period after the mutation. Mutation constraint are required.")
        print(
            "\t - Dec : check if the node or the state passed in parameters sees its probability decrease on the last time period after the mutation. Mutation constraint are required.")
        print("[target_type] : The type of target to look for, can be node, state or a fixpoint.")
        print("\t - node : will look for the probability of the target node.")
        print("\t - state : will look for the probability of the target state.")
        print("\t - ")
        print("[name] : The name of the target to look for. If target_type is node, name is the name of the node."
              "If target_type is state, name is the name of the state. No spaces or \"\". For all targets use *. Can handle multiple names separated by commas, no spaces or \"\" even for multiple names."
              "If target_type is state you can pass a list of nodes' name if you also put 'comb' in the options.")
        print("[operator] : The operator to use to compare the target to the value. Can be <, <=, =, !=, >=, > or /.")
        print("Note that != might return very broad results and = might not return anything.")
        print("\t - < : the probability of the target must be less than the value.")
        print("\t - <= : the probability of the target must be less than or equal to the value.")
        print("\t - = : the probability of the target must be equal to the value.")
        print("\t - != : the probability of the target must not be equal to the value.")
        print("\t - >= : the probability of the target must be greater than or equal to the value.")
        print("\t - > : the probability of the target must be greater than the value.")
        print("\t - / : only for query type D, M, Inc and Dec. No value or operator is required.")
        print(
            "[value] : The value to compare the target to. Can be a number between 0 and 1 or \"?\" ONLY IF the operator used is \'=\' and query type P. If value is \"?\", the query will return the probability of the target.")
        print(
            "With a value of \'?\' the logical equation must not be empty. The value must be empty for Dec or Inc type.")
        print(
            "[logical_equation] : An optional logical equation to apply to the results. Can be a string or a list of strings.")
        print(
            "\t - The logical equation is a string that contains the following elements : [ [name] [operator] [value] ]")
        print("\t - The operator can be &, | (pipe). A logical-not ! can be used in front of a name : !name.")
        print("\t - The name can referenced to a node or a state, by default the result will be the probability "
              "of the node or state, thus returning both. For less columns in output, use : node:name or state:name."
              " To appy a logical-not in this condition do : node:!name or state:!name.")
        print(
            "\t - The logical equation can contain a numerical evaluation. This one must be placed in between parentheses or strange results may occur.")
        print(
            "\t - The logical equation can have multiple conditions intricate on numerous levels: [ ( condition A ) | ( ( condition B ) | ( ( condition C ) ) ) ]")
        print(
            "\t - It is really important to separate each member by a space so the parser reads it correctly and not raises an Exception.")
        print("[mutations]: Optional except for Inc and Dec operations that compare two simulations of the same model.")
        print("\tMultiple mutations can be passed, all mutation must be write like: node_name:ON or node_name:OFF and multiple couples must be separate by a space.")
        print("[options]: ")
        print("\t - digits:int : option to restrain the amount of digits after the dot in the computations and ouput. e.g: digits:3 DEFAULT VALUE IS 4.")
        print("\t - compare:mut:state,mut2:state: option to compare the computation with this mutation instead of the master simulation. The mutation must be a string like \"node_name:ON\" or \"state_name:OFF\". Multiple mutations can be passed and must be separated by a comma without spaces.")
        print("\t - int%: option to require a minimum difference between the two probabilities of the target. e.g: 10% DEFAULT VALUE IS 0.")
        print("\t - transient: special option to check for variations during the simulation and not only a difference at the end. It has the following sub-options:")
        print("\t\t - threshold:val : general minimal change value for the evolution comparisons, DEFAULT: 0.05")
        print("\t\t - start:val : minimal change value for the evolution comparisons at the beginning of the simulation, DEFAULT: 0.1")
        print("\t\t - end:val : minimal change value for the evolution comparisons at the end of the simulation, DEFAULT: 0.1")
        print("\t\t - optimum:val : minimal change value to consider reaching a min or max value in the evolution. DEFAULT 0.1")
        print("\t example of options: [ 5% digits:2 compare:AKT:OFF,BRAF:ON transient:threshold:0.05,start:0.1,end:0.1 ]")
        print("\t NB: the order is not relevant.")
        print("------------------------------------------------------------------------------------------------------")
        print("Examples :")
        print("P(node:A) > 0.5 : returns all the rows where the probability of node A is greater than 0.5")
        print("P(node:A,B) < 0.4 : returns all the rows where the probability of node A and node B is less than 0.4")
        print(
            "P(node:A) = ? [ node:B & C ] : returns the probabilities of node A to be active in one state while B and C are also active (joint probability)")
        print(
            "P(state:A) = ? [ ( node:B > 0.3 ) | C ] : returns the probabilities of state A to be active in one state while B has a probability greater than 0.3 or while C is active.")
        print(
            "T(state:A) >= 0.6 : returns all the periods of time where state A has a probability greater than or equal to 0.6.")
        print(
            "Tmin(node:A,B) >= 0.3 : returns the first period of time where node A and node B are active with a probability greater than or equal to 0.3.")
        print(
            "Tmax(node:A,B) <= 0.7 : returns the last period of time where node A and node B are active with a probability less than or equal to 0.7.")
        print(
            "Pmax(node:A) >= 0.5 : returns the greatest probability of node A being above 0.5 in any period of time. Can return nothing.")
        print(
            "Pmin(node:A) <= 0.5 : returns the lowest probability of node A being under 0.5 in any period of time. Can return nothing.")
        print(
            "Inc(node:A) / [ ] [ B:ON ] : returns the last time code comparison and a print saying if the node A was increased or not.")
        print(
            "Dec(node:A) / [ A & C ] [ B:ON ] : returns the last time code comparison and print saying if the node A was decreased or not. The logical equation is applied before the comparison.")
        print(
            "Inc(state:A--B) / [ ] [ B:ON ] : returns the last time code comparison and print saying if the state A--B was increased or not.")
        print("------------------------------------------------------------------------------------------------------")
        print("Example of questions and the query to provide : ")
        print(
            "What is the probability of node A and B being active at the same time while C is inactive and D above 0.5 ?\n\t -> P(node:A,B) = ? [ node:!C & ( D > 0.5 ) ]")
        print(
            "What are all the moments my simulation is on the state A--B with C inactive ?\n\t -> T(state:A--B) >= 0.0 [ !C ]")
        print(
            "What probability for the state A--B to be active if C, D or E is active and F is inactive ?\n\t -> P(state:A--B) = ? [ ( C | D | E ) & !F ]")
        print("When does the probability of state <nil> exceeds 0.5 ?\n\t -> T(state:<nil>) >= 0.5")
        print(
            "When does the probability of state <nil> exceeds 0.5 for the first time ?\n\t -> Tmin(state:<nil>) >= 0.5")
        print(
            "When does the probability of state <nil> exceeds 0.5 for the last time ?\n\t -> Tmax(state:<nil>) >= 0.5")
        print(
            "Does the probability for A--B state increase when C is activated ?\n\t -> Inc(state:A--B) / [ ] [ C:ON ]")
        print(
            "--------------------------------------------------------------------------------------------------------")
        print(
            "For more exemples and output exemples you can check the test_evaluator.py file. Check the notebook Tuto Temporal Logic for more info.")
        print("In case of any question or bug you can contact me at : oscardufossez@gmail.com or by my GitHub: ODufossez")

    @staticmethod
    def reset_default_values():
        MaBoSSEvaluator.digits = 4
        MaBoSSEvaluator.threshold = 0.05
        MaBoSSEvaluator.optimum = 0.1
        MaBoSSEvaluator.start = 0.1
        MaBoSSEvaluator.end = 0.1
        MaBoSSEvaluator.percentage_value_int = 0
        MaBoSSEvaluator.compare_to = 'master'
        MaBoSSEvaluator.transient = False
        MaBoSSEvaluator.combination = False

    @staticmethod
    def mutation_to_string(mutation_constraint: list[str]):
        """
        Simple method that returns the mutation as string. Basically concatenates the two members.
        Format: "node_name:state" (e.g., "A:ON B:OFF")
        When multiple constraints, they are sorted alphabetically by node_name.
        :param mutation_constraint: a list with two members, the first being the node's name, the second ON or OFF
        :return: a string of the mutation in format "node_name:state"
        """
        if not mutation_constraint:
            return ""
        else:
            return f"{mutation_constraint[0]}:{mutation_constraint[1]}"

    @staticmethod
    def format_mutation_key(mutation_constraints: list[list[str]]):
        """
        Formats the mutation key by creating a string from all mutation constraints,
        with node names sorted alphabetically.
        :param mutation_constraints: a list of mutation constraints, each being [node_name, state]
        :return: a formatted string like "A:ON B:OFF C:ON"
        """
        if not mutation_constraints:
            return ""

        # Convert each constraint to "node:state" format
        formatted_mutations = [MaBoSSEvaluator.mutation_to_string(c) for c in mutation_constraints]

        # Sort alphabetically by the full "node:state" string
        formatted_mutations.sort()

        # Join with spaces
        return " ".join(formatted_mutations)

    @staticmethod
    def parsing_options(options: list[str], res_master: Result, list_results: dict, model_sim):
        for opt in options:
            if opt == "": continue
            if "digits:" in opt or "digit:" in opt:
                val = opt.split(":")[1]
                if MaBoSSEvaluator.digits != 4:
                    warnings.warn(
                        f"Two digits options were passed in the same query, the second one will be used. Options : {opt} and {MaBoSSEvaluator.digits} digits")
                try:
                    MaBoSSEvaluator.digits = int(val)
                except ValueError:
                    print(f"Digits value must be an integer, digits set to 4")

            elif "%" in opt:
                val = opt.split("%")[0]
                if MaBoSSEvaluator.percentage_value_int != 0:
                    warnings.warn(
                        f"Two percentages options were passed in the same query, the second one will be used. Options : {opt} and {MaBoSSEvaluator.percentage_value_int}%")
                try:
                    MaBoSSEvaluator.percentage_value_int = int(val)
                except ValueError:
                    print(f"Percentage value must be an integer, percentage set to 0")

            elif "transient" in opt:
                if 'transient:' in opt:
                    parsed_opt = opt.split('transient:')[1]
                    for p_opt in parsed_opt.split(','):
                        name, value_opt_transient = p_opt.split(':')
                        try:
                            match name:
                                case 'threshold':
                                    MaBoSSEvaluator.threshold = float(value_opt_transient)
                                case 'start':
                                    MaBoSSEvaluator.start = float(value_opt_transient)
                                case 'end':
                                    MaBoSSEvaluator.end = float(value_opt_transient)
                                case 'optimum':
                                    MaBoSSEvaluator.optimum = float(value_opt_transient)
                                case _:
                                    print(
                                        f"{name} is not a transient's option. Options : threshold, start, end, optimum. Value : {value_opt_transient}")
                        except ValueError:
                            print(
                                f"Invalid value for transient option. Value must be a float. Value : {value_opt_transient}")
                MaBoSSEvaluator.transient = True
                # if only transient is passed, the threshold, start, end and optimum values stay the same as the default values

            elif "compare" in opt:  # only handles one mutation rn
                parsed_opt = opt.split('compare:')[1]
                # print(f"parsed_opt : {parsed_opt}, parsed_split: {parsed_opt.split(',')}")
                mutation_constraints = []
                for mut in parsed_opt.split(','):
                    if mut == "": continue
                    # print(f"mut : {mut}")
                    node_name, state = mut.split(':')
                    # print(f"node:{node_name}, state:{state}")
                    if state not in ['ON', 'OFF']:
                        print(f"Invalid state for compare option. State must be ON or OFF. State : {state}")
                        continue
                    if node_name not in res_master.get_nodes_probtraj().columns.tolist():
                        print(f"Node {node_name} not found in the results. Check the name and try again.")
                        continue

                    mutation_constraints.append([node_name, state])

                mutation_key = MaBoSSEvaluator.format_mutation_key(mutation_constraints)
                # print(f"mutation key (options) : {mutation_key}")
                if not mutation_key in list_results.keys():
                    try:
                        mutated_model = model_sim.copy()
                        for mut in parsed_opt.split(','):
                            if mut == "": continue
                            # print(f"mut : {mut}")
                            node_name, state = mut.split(':')
                            mutated_model.mutate(node_name, state)
                        list_results[mutation_key] = mutated_model.run()
                    except Exception as e:
                        print(f"Error while mutating the model : {e}")
                        continue
                MaBoSSEvaluator.compare_to = mutation_key

            elif "comb" in opt:
                MaBoSSEvaluator.combination = True

    @staticmethod
    def querying(queries: list[str], sim_cfg, sim_bnd, initial_state: list[dict] = None):
        """
        Interaction method between the user and the program.
        First it runs all the necessary simulations, a dictionary avoids two identical simulations to be run twice. It always
        run the master simulation (aka, the simulation without any mutation)
        Then for all the queries that were passed in the parameter query, the method parses it, checks the grammar, checks
        for mutation, runs a simulation if needed and sorts the validate query in the right places to link the simulation
        results to it.
        For all the queries that were'nt containing any grammar mistakes, gets the query, the simulation results (master
        and mutation if needed) and passes them all to the evaluation methods depending on the query type (P, T ...)
        Finally, the results of the evaluation are all appended in a list that is returned at the end of the function.

        :param queries: a list of string each being an assertion or query to be evaluated, contains a lot of information regarding
        the simulation to which it is linked (see formula)
        :param sim_cfg: the config file of the simulation
        :param sim_bnd: the binarie file of the simulation
        :param initial_state: optionnal, if you want to set some nodes in certain states at the beginning of the simulation.
        This state will be used for all the simulations relative to the list of queries passed
        :return: a list of dataframes that are the results of the evaluations
        """
        list_of_df = []  # results of computation and evaluation
        checked_query = []  # queries that are checked for errors

        sim_results = {}  # dictionary associating the name's mutation with its result
        query_to_sim = {}  # dictionary associating each query with the simulation it is related to
        query_to_compare = {}
        query_options = {}
        query_digits = {}
        query_combination = {}

        # Running the simulations and stocked the results
        model_sim = maboss.load(bnd_filename=sim_bnd, cfg_filename=sim_cfg)
        if initial_state:
            for e in initial_state:
                maboss.set_nodes_istate(model_sim, [e['node']], e['istate'])
        res_master = model_sim.run()
        sim_results['master_simulation'] = res_master
        # sim_results['master_simulation'].plot_piechart()

        # Reading of the queries and launching the simulation for a mutation if it was not done before
        for q in queries:
            # print(f"Query to parse : {q}")
            parsed_query = Parser.parse_query(q)
            try:
                FormulaChecker.check_formula(parsed_query)
                checked_query.append(q)
            except FormulaException as fe:
                print(fe.with_traceback())
                warnings.warn(
                    f"Formula is not correct : {q} , will not be evaluated. This error occurred : {fe.message}")
                continue

            if parsed_query.mutation_constraint:
                col_name = MaBoSSEvaluator.format_mutation_key(parsed_query.mutation_constraint)
                # if the simulation was not done yet for this mutation
                if col_name not in sim_results:
                    mutated_model = model_sim.copy()
                    list_genes = []
                    for g in parsed_query.mutation_constraint:
                        list_genes.append(g[0])
                    # mutated_model.network.set_output(list_genes) #necessary ???
                    for c in parsed_query.mutation_constraint:
                        mutated_model.mutate(c[0], str(c[1]))
                    sim_results[col_name] = mutated_model.run()
                query_to_sim[q] = col_name
            else:
                query_to_sim[q] = 'master_simulation'

            # print(f"Simulation results columns : {sim_results}")
            if parsed_query.options:
                # print(f"Query: {q} for options {parsed_query.options}")
                MaBoSSEvaluator.parsing_options(parsed_query.options, res_master, sim_results, model_sim)
            # if there are no options, default values are kept.
            # print(f"Simulation results columns : {sim_results}")

            if MaBoSSEvaluator.compare_to == 'master':
                query_to_compare[q] = 'master_simulation'
            else:
                query_to_compare[q] = MaBoSSEvaluator.compare_to  # name was changed in parse_options

            query_options[q] = [MaBoSSEvaluator.transient, MaBoSSEvaluator.threshold,
                                MaBoSSEvaluator.percentage_value_int, MaBoSSEvaluator.start, MaBoSSEvaluator.end,
                                MaBoSSEvaluator.optimum, MaBoSSEvaluator.combination]
            query_digits[q] = MaBoSSEvaluator.digits
            MaBoSSEvaluator.reset_default_values()

        for q in checked_query:
            try:
                #print(f"query : {q}")
                sim_key = query_to_sim[q]
                res = sim_results[sim_key]
                # print(f"Nodes for this query : {res.get_nodes_probtraj()}")
                parsed_query = Parser.parse_query(q)
                tab_options_query = query_options[q]

                if parsed_query.type in [QueryType.P, QueryType.PMAX, QueryType.PMIN, QueryType.T, QueryType.TMAX, QueryType.TMIN]:
                    # print(f"query is not a dependency, increase or decrease: {q}")
                    if query_options[q][6]:
                        if parsed_query.logical_equation: warnings.warn("Logical equation will be ignored for this evaluation.")
                        list_of_df.append(MaBoSSEvaluator.evaluate_query_combinatory(parsed_query, res))
                    else:
                        list_of_df.append(MaBoSSEvaluator.evaluate_query(parsed_query, res, tab_options_query, query_digits[q]))
                else:
                    # print(f"Query is a dependency, increase or decrease: {q}")
                    match parsed_query.type:
                        case QueryType.INCREASE | QueryType.DECREASE:
                            # get the simulation results that must be compared to this one

                            compare_key = query_to_compare.get(q, 'master_simulation')
                            # print(f"Query: {q}")
                            #print(f"Main simulation key: {sim_key}")
                            #print(f"Compare simulation key: {compare_key}")


                            #print(f"Combination : {tab_options_query[6]}")
                            # print(f"  Digits: {query_digits[q]}")
                            list_of_df.append(MaBoSSEvaluator.evaluate_increase_decrease(parsed_query,
                                                                                         res, sim_results[compare_key],
                                                                                         query_digits[q],
                                                                                         tab_options_query
                                                                                         ))
                        case _:
                            warnings.warn(f"Query type {parsed_query.type} is not supported yet, query ignored.")
                            continue
            except FormulaException as fe:
                print(f"Formula is not correct : {q} , will not be evaluated. This error occurred : {fe.message}")
                continue

        for i, df in enumerate(list_of_df):
            if df is None:
                print(f"df {i} is empty. Query was : {checked_query[i]}")

        MaBoSSEvaluator.reset_default_values()
        print("Evaluations done !")
        return list_of_df

    @staticmethod
    def evaluate_increase_decrease(parsed_query_input, results_mutation, results_master, digits: int = 4, options=None):
        """
        Method of evaluation specifically for INCREASE and DECREASE query types. A utilitary method in into this one
        just used to get the dataframe that is needed and apply the logical expression to it.
        Different logics are applied whether the target type is a node/state or a fixpoint. In fixpoint the name that the
        loop is currently on is automatically searched, and if a single node state is detected, both outcomes are processed.
        (see test_last_state_inc_dec_with_single_node_state in test_evaluator.py).

        :param options:
        :param parsed_query_input: the query currently treated in a parsed form
        :param results_mutation: the result of the mutation that was applied to the model
        :param results_master: the results of the master simulation
        :param digits: sensibility of the digits after dot for the probability numbers.
        :return: a dataframe of the evaluated data
        """
        if results_mutation is None or results_master is None:
            raise ValueError("Results are empty")

        if options:
            MaBoSSEvaluator.transient = options[0]
            MaBoSSEvaluator.threshold = options[1]
            MaBoSSEvaluator.percentage_value_int = options[2]
            MaBoSSEvaluator.start = options[3]
            MaBoSSEvaluator.end = options[4]
            MaBoSSEvaluator.optimum = options[5]
            MaBoSSEvaluator.combination = options[6]

        else:
            MaBoSSEvaluator.reset_default_values()

        evaluate_on_percentage = MaBoSSEvaluator.percentage_value_int
        # print(f"percentage : {evaluate_on_percentage}")
        # print(f"digits : {digits}")

        name_target = []
        for name in parsed_query_input.target_name:
            name_target.append(name.strip().replace(' ', ''))

        def prepare_df(results):
            MaBoSSEvaluator.simulation_results_raw = results
            MaBoSSEvaluator.parsed_query = parsed_query_input

            if parsed_query_input.target == TargetType.FIXPOINT:
                df = MaBoSSEvaluator.get_df_target(parsed_query_input.target, True, False)
            else:
                df = MaBoSSEvaluator.get_df_target(parsed_query_input.target, False, True)

            if df.empty or df is None:
                raise DataFrameIsEmpty(f"The dataframe is empty for target \"{parsed_query_input.target}\"")

            df = df.dropna().copy()
            # removing the spaces on the values
            df.columns = df.columns.str.replace(' ', '')

            if 'State' in df.columns:
                df['State'] = df['State'].astype(str).str.replace(' ', '')

            if parsed_query_input.target == TargetType.FIXPOINT and parsed_query_input.logical_equation:
                try:
                    ComputeLogicalExpression.check_logical_exp_fixpoint(parsed_query_input.logical_equation)
                except ErrorInLogicalExpression as e:
                    print(f"Error in the logical expression : {e.message}. Logical expression not applied.")

                df = ComputeLogicalExpression.compute_logical_fixpoint(parsed_query_input.logical_equation, df)

            # print(f"df from prepare df:\n{df}")
            return df

        # the table for each of the results
        df_mutation = prepare_df(results_mutation)
        df_master = prepare_df(results_master)

        # print(f"Fixpoints table for mutation : \n {df_mutation} \n")
        # print(f"Fixpoints table for master : \n {df_master} \n")

        data_out = {}

        if parsed_query_input.target == TargetType.FIXPOINT:
            # print("Computing fixpoint")
            for name in name_target:
                found_state = False
                try:
                    # getting the probability of the state in each simulation
                    proba_master = df_master.loc[df_master["State"] == name, "Proba"].values[0].round(digits)
                    proba_mutation = df_mutation.loc[df_mutation["State"] == name, "Proba"].values[0].round(digits)
                    found_state = True
                except (KeyError, IndexError):
                    pass

                if name not in df_master.columns or name not in df_mutation.columns:
                    found_node = False
                else:
                    found_node = True

                # print(f"founds node and state : {found_node} and {found_state} \n")

                if not found_node and not found_state: raise NoNameValidException(f"Name : {name} has not been found "
                                                                                  f"in results neither has a state nor node.")
                if found_state:
                    # print(f"Proba master : {proba_master}\n Proba mutation : {proba_mutation}\n")
                    res_diff_state = proba_mutation - proba_master
                    data_out[f"{name} state from master"] = [proba_master]
                    data_out[f"{name} state from mutation"] = [proba_mutation]
                    percentage = (res_diff_state / proba_master) if proba_master != 0 else 0.0
                    data_out[f"Difference state {name}"] = [res_diff_state.round(digits)]
                    data_out[f"Percentage state {name}"] = [f"{percentage:.2%}"]
                    val_mutation = proba_mutation
                    val_master = proba_master
                    if parsed_query_input.type == QueryType.INCREASE:
                        data_out[f"Increase {name} state"] = MaBoSSEvaluator.evaluate_increase_decrease_value(
                            "increase", evaluate_on_percentage, val_master, val_mutation)
                    else:
                        data_out[f"Decrease {name} state"] = MaBoSSEvaluator.evaluate_increase_decrease_value(
                            'decrease', evaluate_on_percentage, val_master, val_mutation)

                # keeping the lines where node is 1 and summing all the probas
                sum_master = df_master.loc[df_master[name].astype(float) == 1, 'Proba'].round(digits).sum()
                sum_mutation = df_mutation.loc[df_mutation[name].astype(float) == 1, 'Proba'].round(digits).sum()
                data_out[f"P({name}) cumul from master"] = [sum_master]
                data_out[f"P({name}) cumul from mutation"] = [sum_mutation]
                res_diff = (sum_mutation - sum_master).round(digits)
                proba_master = sum_master
                proba_mutation = sum_mutation
                percentage = (res_diff / proba_master) if proba_master != 0 else 0.0
                data_out[f"Difference {name}"] = [res_diff]
                data_out[f"Percentage {name}"] = [f"{percentage:.2%}"]

                # print(f"query type : {parsed_query_input.type}, percentage = {evaluate_on_percentage} ")

                if parsed_query_input.type == QueryType.INCREASE:
                    data_out[f"Increase {name}"] = MaBoSSEvaluator.evaluate_increase_decrease_value("increase",
                                                                                                    evaluate_on_percentage,
                                                                                                    proba_master,
                                                                                                    proba_mutation)
                else:
                    data_out[f"Decrease {name}"] = MaBoSSEvaluator.evaluate_increase_decrease_value('decrease',
                                                                                                    evaluate_on_percentage,
                                                                                                    proba_master,
                                                                                                    proba_mutation)

                # print(f"Data_out :\n{data_out}")
        else:  # if not fixpoint
            if parsed_query_input.target == TargetType.NODE:
                for name in name_target:
                    if name not in df_master.columns:
                        val_master = 0.0
                    else:
                        val_master = df_master[name].values[0].round(digits)
                    if name not in df_mutation.columns:
                        val_mutation = 0.0
                    else:
                        val_mutation = df_mutation[name].values[0].round(digits)
                    # print(f"val_master : {val_master} \n val_mutation : {val_mutation}")
                    data_out[f"{name} from master"] = [val_master]
                    data_out[f"{name} from mutation"] = [val_mutation]
                    # print(f"Data out : \n {data_out}")
                    res_diff = val_mutation - val_master
                    percentage = (res_diff / val_master) if val_master != 0 else 0.0
                    data_out[f"Difference {name}"] = [res_diff]
                    data_out[f"Percentage {name}"] = [f"{percentage:.2%}"]

                    if parsed_query_input.type == QueryType.INCREASE:
                        data_out[f"Increase {name}"] = MaBoSSEvaluator.evaluate_increase_decrease_value("increase",
                                                                                                    evaluate_on_percentage,
                                                                                                    val_master,
                                                                                                    val_mutation)
                    else:
                        data_out[f"Decrease {name}"] = MaBoSSEvaluator.evaluate_increase_decrease_value('decrease',
                                                                                                    evaluate_on_percentage,
                                                                                                    val_master,
                                                                                                    val_mutation)
                    if MaBoSSEvaluator.transient:
                        data_out.update(MaBoSSEvaluator.check_transient(df_master, df_mutation, name))

                    if MaBoSSEvaluator.combination:
                        df_states_master = results_master.get_last_states_probtraj()
                        df_states_mutation = results_mutation.get_last_states_probtraj()

                        df_states_master.columns = df_states_master.columns.str.replace(' ', '')
                        df_states_mutation.columns = df_states_mutation.columns.str.replace(' ', '')

                        matching_cols = [col for col in df_states_master.columns if all(name in col for name in name_target)]
                        val_cumul_master = df_states_master[matching_cols].iloc[0].sum()

                        matching_cols = [col for col in df_states_mutation.columns if all(name in col for name in name_target)]
                        val_cumul_mutation = df_states_mutation[matching_cols].iloc[0].sum()

                        data_out[f"P_cumul({','.join(name_target)}) master"] = val_cumul_master.round(digits)
                        data_out[f"P_cumul({','.join(name_target)}) mutation"] = val_cumul_mutation.round(digits)
                        res_diff = val_cumul_mutation - val_cumul_master
                        percentage = (res_diff / val_cumul_master) if val_cumul_master != 0 else 0.0
                        data_out[f"Difference cumul"] = [res_diff.round(digits)]
                        data_out[f"Percentage cumul"] = [f"{percentage:.2%}"]

                        if parsed_query_input.type == QueryType.INCREASE:
                            data_out[f"Increase cumul"] = MaBoSSEvaluator.evaluate_increase_decrease_value("increase",
                                                                                                           evaluate_on_percentage,
                                                                                                           val_cumul_master,
                                                                                                           val_cumul_mutation)
                        else:
                            data_out[f"Decrease cumul"] = MaBoSSEvaluator.evaluate_increase_decrease_value("decrease",
                                                                                                           evaluate_on_percentage,
                                                                                                           val_cumul_master,
                                                                                                           val_cumul_mutation)

            else:  # if STATE
                df_master.columns = df_master.columns.str.replace(' ', '')
                df_mutation.columns = df_mutation.columns.str.replace(' ', '')

                if MaBoSSEvaluator.combination:
                    matching_cols = [col for col in df_master.columns if
                                     all(name in col for name in name_target)]
                    val_cumul_master = df_master[matching_cols].iloc[0].sum().round(digits)

                    matching_cols = [col for col in df_mutation.columns if
                                     all(name in col for name in name_target)]
                    val_cumul_mutation = df_mutation[matching_cols].iloc[0].sum().round(digits)

                    data_out[f"P_cumul({','.join(name_target)}) master"] = val_cumul_master
                    data_out[f"P_cumul({','.join(name_target)}) mutation"] = val_cumul_mutation

                    if parsed_query_input.type == QueryType.INCREASE:
                        data_out[f"Increase cumul"] = [MaBoSSEvaluator.evaluate_increase_decrease_value("increase",
                                                                                                       evaluate_on_percentage,
                                                                                                       val_cumul_master,
                                                                                                       val_cumul_mutation)]
                    else:
                        data_out[f"Decrease cumul"] = [MaBoSSEvaluator.evaluate_increase_decrease_value("decrease",
                                                                                                       evaluate_on_percentage,
                                                                                                       val_cumul_master,
                                                                                                       val_cumul_mutation)]
                else:  # an exact state name was passed
                    for name in name_target:
                        try:
                            val_master = df_master[name].values[0].round(digits)
                        except KeyError:
                            val_master = 0.0
                        try:
                            val_mutation = df_mutation[name].values[0].round(digits)
                        except KeyError:
                            val_mutation = 0.0
                        data_out[f"{name} from master"] = [val_master]
                        data_out[f"{name} from mutation"] = [val_mutation]
                        res_diff = (val_mutation - val_master)
                        percentage = (res_diff / val_master) if val_master != 0 else 0.0
                        data_out[f"Difference {name}"] = [res_diff.__round__(digits)]
                        data_out[f"Percentage {name}"] = [f"{percentage:.2%}"]

                        if parsed_query_input.type == QueryType.INCREASE:
                            data_out[f"Increase {name}"] = MaBoSSEvaluator.evaluate_increase_decrease_value("increase",
                                                                                                            evaluate_on_percentage,
                                                                                                            val_master,
                                                                                                            val_mutation)
                        else:
                            data_out[f"Decrease {name}"] = MaBoSSEvaluator.evaluate_increase_decrease_value("decrease",
                                                                                                            evaluate_on_percentage,
                                                                                                            val_master,
                                                                                                            val_mutation)
                        if MaBoSSEvaluator.transient:
                            data_out.update(MaBoSSEvaluator.check_transient(df_master, df_mutation, name))
        return pd.DataFrame(data_out)

    @staticmethod
    def evaluate_query(parsed_query_input: Formula, results, options=[], digits=4):  # maybe pass the results as an array to compute more than one simulation
        """
        This method might need reformating for more cleanliness (11th may 2026)
        Method to evaluate query of any other query type aside of Dec and Inc.
        It first clean the columns' name, then things are going to be treated :
        - first the right dataframe is get (nodes for node target, states for state target)
        - then the comparisons based on values
        - if the query requires it, a filter on the name is applied (P or T)
        - if a logical equation was passed, it is applied (it removes mainly time codes)
        - in the end, if the value was not a float but the "?", the result is computed
        Then the results are returned.
        :param digits:
        :param options:
        :param parsed_query_input: the query that is evaluated, already parsed
        :param results: the results of the simulation to evaluate the query on. The program does not care if it is
        a mutation or a master simulation.
        :return: a dataframe of the evaluated data
        """

        if options:
            MaBoSSEvaluator.transient = options[0]
            MaBoSSEvaluator.threshold = options[1]
            MaBoSSEvaluator.percentage_value_int = options[2]
            MaBoSSEvaluator.start = options[3]
            MaBoSSEvaluator.end = options[4]
            MaBoSSEvaluator.optimum = options[5]
            MaBoSSEvaluator.combination = options[6]
        else:
            MaBoSSEvaluator.reset_default_values()

        MaBoSSEvaluator.digits = digits

        if results is None:
            raise ValueError("Results are empty")

        if not "Time" in results.get_states_probtraj().columns:
            df_states = results.get_states_probtraj().copy()
            df_states["Time"] = df_states.index
        else:
            df_states = results.get_states_probtraj().copy()

        df_states.columns = df_states.columns.str.replace(" ", "", regex=False)

        if not "Time" in results.get_nodes_probtraj().columns:
            df_nodes = results.get_nodes_probtraj().copy()
            df_nodes["Time"] = df_nodes.index
        else:
            df_nodes = results.get_nodes_probtraj().copy()

        MaBoSSEvaluator.simulation_results_raw = results
        MaBoSSEvaluator.simulation_results = [df_nodes, df_states]
        query_input = parsed_query_input
        MaBoSSEvaluator.parsed_query = parsed_query_input

        # Selection of the simulation result df to use depending on the target
        df_target = MaBoSSEvaluator.get_df_target(parsed_query_input.target)
        if df_target.empty:
            raise DataFrameIsEmpty(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\"")
        # print(f"DF after target selection : \n {df_target}")
        # Selection of the rows depending on what is looking for
        match query_input.type.value:
            case QueryType.P.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_proba(df_target, MaBoSSEvaluator.parsed_query.value)
            case QueryType.T.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_time(df_target, MaBoSSEvaluator.parsed_query.value)
            case QueryType.PMAX.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_proba(df_target, MaBoSSEvaluator.parsed_query.value,
                                                                          QueryType.PMAX)
            case QueryType.PMIN.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_proba(df_target, MaBoSSEvaluator.parsed_query.value,
                                                                          QueryType.PMIN)
            case QueryType.TMAX.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_time_minmax(df_target,
                                                                                MaBoSSEvaluator.parsed_query.value,
                                                                                QueryType.TMAX)
            case QueryType.TMIN.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_time_minmax(df_target,
                                                                                MaBoSSEvaluator.parsed_query.value,
                                                                                QueryType.TMIN)
            case _:
                raise ValueError("Query type is not supported, try P, Pmin, Pmax or T, Tmin, Tmax, Inc or Dec")

        # print(f"DF after value selection : \n {filtered_data}")

        if query_input.type == QueryType.P or query_input.type == QueryType.T:
            # print(f"DF in treatment for P or T type\n Filtered_data columns : \n{filtered_data.columns}\n")
            # Selection of the columns regarding the name of the target if type P or T strictly. If type in a min max logic, keep all the columns
            filtered_data = MaBoSSEvaluator.get_df_target_name(filtered_data, query_input.target_name)

        # print(f"DF after name selection : \n {filtered_data}")

        if query_input.logical_equation:
            # print(f"DF in treatment for logical equation")
            log_df = ComputeLogicalExpression.compute_logical_expression(query_input.logical_equation,
                                                                         MaBoSSEvaluator.simulation_results)
            # print(f"DF after logical equation : \n {log_df} \n Will be merged with :\n {filtered_data}\n")
            filtered_data = ComputeLogicalExpression.merge_or(filtered_data, log_df,
                                                              MaBoSSEvaluator.simulation_results[0],
                                                              MaBoSSEvaluator.simulation_results[1]
                                                              .rename(columns={c: f"{c}_state" for c in
                                                                               MaBoSSEvaluator.simulation_results[
                                                                                   1].columns if c != 'Time'}), True)

        if filtered_data.empty:
            raise DataFrameIsEmpty(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\" "
                                   f"with name \"{MaBoSSEvaluator.parsed_query.target_name}\" and logical equation "
                                   f"\"{MaBoSSEvaluator.parsed_query.logical_equation}\"")
        if filtered_data.size > 2:
            filtered_data = MaBoSSEvaluator.remove_double_columns(filtered_data)

        # todo put here the call of the computation function (returns a new df with the new columns and the filtered_data)
        if MaBoSSEvaluator.parsed_query.value == '?':
            # print(f"filtered_data : \n {filtered_data} \n")
            computed_values = MaBoSSEvaluator.compute_interrogation_proba(filtered_data, MaBoSSEvaluator.parsed_query,
                                                                          MaBoSSEvaluator.simulation_results[0],
                                                                          MaBoSSEvaluator.simulation_results[1])
            return computed_values

        return filtered_data.dropna(inplace=False, ignore_index=True).round(digits)

    @staticmethod
    def evaluate_query_combinatory(parsed_query_input: Formula, sim_res):
        name_target = parsed_query_input.target_name
        data_out = {}

        if parsed_query_input.target == TargetType.STATE or parsed_query_input.target == TargetType.NODE:
            # check all names exists
            df_nodes = sim_res.get_nodes_probtraj().columns.tolist()
            if not all(name in df_nodes for name in name_target):
                warnings.warn(f"Not all name were found in the results, combinatory probability : 0.0")
                data_out[f"Combinatory {', '.join(name_target)}"] = 0.0
                return pd.DataFrame(data_out)

            df_states = sim_res.get_states_probtraj()
            #match columns in state df
            matching_columns = [col for col in df_states.columns if all(name in col for name in name_target)]

            data_out[f"Combinatory {', '.join(name_target)}"] = df_states[matching_columns].sum(axis=1)
            data_out["Time"] = df_states["Time"]
            #print(data_out)
            df_out = pd.DataFrame(data_out).dropna(ignore_index=True)
            # move the time column to first position
            col = df_out.pop("Time")
            df_out.insert(0, "Time", col)

            #applying the constraint on the value
            value = parsed_query_input.value
            try:
                value = float(value)
            except ValueError:
                return df_out

            match parsed_query_input.operator:
                case Operators.GE: mask = (df_out[f"Combinatory {', '.join(name_target)}"] >= value)
                case Operators.GT: mask = (df_out[f"Combinatory {', '.join(name_target)}"] > value)
                case Operators.LE: mask = (df_out[f"Combinatory {', '.join(name_target)}"] <= value)
                case Operators.LT: mask = (df_out[f"Combinatory {', '.join(name_target)}"] < value)
                case Operators.EQ: mask = (df_out[f"Combinatory {', '.join(name_target)}"] == value)
                case Operators.NE: mask = (df_out[f"Combinatory {', '.join(name_target)}"] != value)
                case _: raise ValueError("Operator is not supported, try >=, >, <=, <, = or !=")

            df_out = df_out[mask]
        else: #fixpoints
            df_fp = sim_res.get_fptable()

            # check all the names exists
            if not all(name in df_fp for name in name_target):
                warnings.warn(f"Not all name were found in the results, combinatory probability : 0.0")
                data_out[f"Combinatory {', '.join(name_target)}"] = 0.0
                return pd.DataFrame(data_out)

            matching_lines = df_fp[(df_fp[name_target] == 1).all(axis=1)]
            # print(f"\n{matching_lines}")
            cumul_proba = matching_lines["Proba"].sum()
            data_out[f"P_cumul({','.join(name_target)})"] = [cumul_proba]


            try:
                val = float(parsed_query_input.value)
                match parsed_query_input.operator:
                    case Operators.GE: data_out["Comparison value"] = (cumul_proba >= val)
                    case Operators.GT: data_out["Comparison value"] = (cumul_proba > val)
                    case Operators.LE: data_out["Comparison value"] = (cumul_proba <= val)
                    case Operators.LT: data_out["Comparison value"] = (cumul_proba < val)
                    case Operators.EQ: data_out["Comparison value"] = (cumul_proba == val)
                    case Operators.NE: data_out["Comparison value"] = (cumul_proba != val)
                    case _: raise ValueError()
            except ValueError:
                df_out = pd.DataFrame(data_out)
                return df_out

            df_out = pd.DataFrame(data_out)
        return df_out


    @staticmethod
    def get_df_target(target: TargetType, fp: bool = False, get_last: bool = False):
        """
        A method to return the right type of dataframe depending on the query
        :param target: the target type passed in the query (node, state or fp)
        :param fp: if the dataframe required is the fixpoint one (bool)
        :param get_last: if the dataframe required is the "last_nodes/states_probtraj" (bool)
        :return: the dataframe that was computed by the simulation
        """
        if fp and not get_last:
            return MaBoSSEvaluator.simulation_results_raw.get_fptable()
        elif get_last and not fp:
            # print("should appear")
            if target == TargetType.NODE:
                return MaBoSSEvaluator.simulation_results_raw.get_last_nodes_probtraj()
            elif target == TargetType.STATE:
                return MaBoSSEvaluator.simulation_results_raw.get_last_states_probtraj()
            else:
                raise ValueError("Target is not supported, try node or state")
        else:
            if target.value == TargetType.NODE.value:
                return MaBoSSEvaluator.simulation_results[0]
            elif target.value == TargetType.STATE.value:
                return (MaBoSSEvaluator.simulation_results[1]
                        .rename(
                    columns={c: f"{c}_state" for c in MaBoSSEvaluator.simulation_results[1].columns if c != 'Time'}))
            else:
                raise ValueError("Target is not supported, try node or state")

    @staticmethod
    def get_df_target_name(df, target_name):
        """
        A method to return a dataframe that only has as columns the names that were requested.
        :param df: the dataframe to truncate
        :param target_name: the names to keep
        :return: a dataframe filtered
        """
        if df is None:
            raise ValueError(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\"")

        try:
            cols_to_check = MaBoSSEvaluator.get_the_cols_to_check(df)
        except NoNameValidException:
            raise NoNameValidException()

        new_df = pd.DataFrame()

        if target_name[0] != '*':
            new_df["Time"] = df["Time"]
            for name in cols_to_check:
                new_df[name] = df[name]
        else:
            new_df = df.copy()

        return new_df

    @staticmethod
    def get_df_target_value_proba(df, value, query_type=QueryType.P):
        """
        Method that is called when the query requests a comparison on the probability of a node or a state to be active
        :param df: the dataframe to look on
        :param value: the value to compare to
        :param query_type: the type of query (P, T...)
        :return: a filtered dataframe
        """
        op = MaBoSSEvaluator.parsed_query.operator
        # print(f"target_name : {MaBoSSEvaluator.parsed_query.target_name}")

        cols_to_check = MaBoSSEvaluator.get_the_cols_to_check(df)
        # print(f"cols to check after verification: {cols_to_check}")

        # todo here do the check "?"
        try:
            value = float(value)
            is_number = True
        except ValueError:
            is_number = False

        out_df = pd.DataFrame()
        # print(f"Received df : \n{df}\n")

        if is_number:
            match op:
                case Operators.LT:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        if MaBoSSEvaluator.percentage_value_int == 0:
                            mask = (df[cols_to_check] < value).any(
                                axis=1)  # just check the value, any column checking it as good passes the test
                        else:
                            perc = MaBoSSEvaluator.percentage_value_int/100
                            mask = (value-df[cols_to_check] > perc).any(axis=1)
                    else:
                        if MaBoSSEvaluator.percentage_value_int == 0:
                            mask = (df[cols_to_check] < value).all(
                                axis=1)  # all the values on the line must be less than the value
                        else:
                            perc = MaBoSSEvaluator.percentage_value_int/100
                            mask = (value-df[cols_to_check] > perc).all(axis=1)
                case Operators.EQ:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        if MaBoSSEvaluator.percentage_value_int==0:
                            mask = (df[cols_to_check] == value).any(axis=1)
                        else:
                            mask = (abs(df[cols_to_check] - value) < MaBoSSEvaluator.percentage_value_int/100).any(axis=1)
                    else:
                        if MaBoSSEvaluator.percentage_value_int==0:
                            mask = (df[cols_to_check] == value).all(axis=1)
                        else:
                            mask = (abs(df[cols_to_check] - value) < MaBoSSEvaluator.percentage_value_int/100).all(axis=1)
                case Operators.GT:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        if MaBoSSEvaluator.percentage_value_int == 0:
                            mask = (df[cols_to_check] > value).any(axis=1)
                        else:
                            perc = MaBoSSEvaluator.percentage_value_int/100
                            mask = (df[cols_to_check]-value > perc).any(axis=1)
                    else:
                        if MaBoSSEvaluator.percentage_value_int==0:
                            mask = (df[cols_to_check] > value).all(axis=1)
                        else:
                            perc = MaBoSSEvaluator.percentage_value_int/100
                            mask = (df[cols_to_check]-value > value).all(axis=1)
                case Operators.LE:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        if MaBoSSEvaluator.percentage_value_int==0:
                            mask = (df[cols_to_check] <= value).any(axis=1)
                        else:
                            perc = MaBoSSEvaluator.percentage_value_int/100
                            mask = (df[cols_to_check]-value <= perc).any(axis=1)
                    else:
                        if MaBoSSEvaluator.percentage_value_int==0:
                            mask = (df[cols_to_check] <= value).all(axis=1)
                        else:
                            perc = MaBoSSEvaluator.percentage_value_int/100
                            mask = (df[cols_to_check]-value <= perc).all(axis=1)
                case Operators.GE:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        if MaBoSSEvaluator.percentage_value_int==0:
                            mask = (df[cols_to_check] >= value).any(axis=1)
                        else:
                            perc = MaBoSSEvaluator.percentage_value_int/100
                            mask = (df[cols_to_check]-value >= perc).any(axis=1)
                    else:
                        if MaBoSSEvaluator.percentage_value_int==0:
                            mask = (df[cols_to_check] >= value).all(axis=1)
                        else:
                            perc = MaBoSSEvaluator.percentage_value_int/100
                            mask = (df[cols_to_check]-value >= perc).all(axis=1)
                case Operators.NE:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        if MaBoSSEvaluator.percentage_value_int == 0:
                            mask = (df[cols_to_check] != value).any(axis=1)
                        else:
                            mask = (abs(df[cols_to_check] - value) > MaBoSSEvaluator.percentage_value_int / 100).any(
                                axis=1)
                    else:
                        if MaBoSSEvaluator.percentage_value_int == 0:
                            mask = (df[cols_to_check] != value).all(axis=1)
                        else:
                            mask = (abs(df[cols_to_check] - value) > MaBoSSEvaluator.percentage_value_int / 100).all(
                                axis=1)
                case _:
                    raise ValueError("Operator is not supported, try <, <=, =, !=, >=, >")

            out_df = df[mask].copy()
            out_df["Time"] = df["Time"]  # restablish the correct time values

            # print(f" value_proba, {MaBoSSEvaluator.parsed_query.target_name} with type {query_type} : \n {out_df} \n")

            out_df = out_df.dropna(subset=out_df.columns.difference(['Time']), axis=0, how='all',
                                   ignore_index=True)  # remove the rows with all nan values

            # print(f" value_proba, {MaBoSSEvaluator.parsed_query.target_name} with type {query_type} after dropna : \n {out_df} \n")
            if TargetType.STATE == MaBoSSEvaluator.parsed_query.target:
                name_to_search = MaBoSSEvaluator.parsed_query.target_name[0] + "_state"
            else:
                name_to_search = MaBoSSEvaluator.parsed_query.target_name[0]

            if query_type == QueryType.P:
                return out_df
            elif query_type == QueryType.PMAX:  # last time it happens
                if name_to_search not in df.columns:
                    raise NoNameValidException()
                idx_max = out_df.loc[:, [name_to_search]].max(axis=1).idxmax()
                return out_df.loc[[idx_max]]
            else:
                if name_to_search not in df.columns:  # first time it happens
                    raise NoNameValidException()
                idx_min = out_df.loc[:, [name_to_search]].min(axis=1).idxmin()
                return out_df.loc[[idx_min]]
        else:
            # print(f"value is not a number")
            out_df["Time"] = df["Time"]
            for col in cols_to_check:
                out_df[col] = df[col]
            # print(f"out_df : \n {out_df}")
            return out_df

    @staticmethod
    def get_df_target_value_time(df, value):
        """
        A method to create a dataframe containing the interval(s) of time that meet the value's requirement
        :param df: the df to compute
        :param value: the value to compare
        :return: a dataframe of time sequences
        """
        op = MaBoSSEvaluator.parsed_query.operator
        # todo here do the check "?"
        value = float(value)
        target_names = MaBoSSEvaluator.parsed_query.target_name
        target_type = MaBoSSEvaluator.parsed_query.target

        # print(f"get_df_target_value_time :{value}, {op}, {MaBoSSEvaluator.parsed_query.target_name}")

        if TargetType.STATE == target_type:
            cols_to_check = [f"{name}_state" for name in target_names if f"{name}_state" in df.columns]
        else:
            cols_to_check = [n for n in target_names if n in df.columns]

        def apply_mask(c, v, o):
            match o:
                case Operators.LT:
                    m = (df[c] < v)
                case Operators.EQ:
                    m = (df[c] == v)
                case Operators.GT:
                    m = (df[c] > v)
                case Operators.LE:
                    m = (df[c] <= v)
                case Operators.GE:
                    m = (df[c] >= v)
                case Operators.NE:
                    m = (df[c] != v)
                case _:
                    raise ValueError("Operator not supported")
            return m.all(axis=1)

        mask = apply_mask(cols_to_check, value, op)

        if not mask.any():
            print(
                f"No value found for {MaBoSSEvaluator.parsed_query.target_name} with type Time (T) and operator {op} and value {value}")
            return pd.DataFrame(columns=df.columns)

        return df[mask].copy()

    @staticmethod
    def get_df_target_value_time_minmax(df, value, query_type=QueryType.TMIN):
        """
        A method to do a dataframe that contains the first (TMIN) or the last (TMAX) moments where the value meets the
        requirements
        :param df: the dataframe to compute
        :param value: the value to compare to
        :param query_type: the type of query (TMIN or TMAX)
        :return: a dataframe
        """
        # todo here the "?" check
        value = float(value)
        query_type = query_type.value
        op = MaBoSSEvaluator.parsed_query.operator
        target_names = MaBoSSEvaluator.parsed_query.target_name

        # print(f"get_df_target_value_time_minmax :{value}, {query_type}, {op}, {MaBoSSEvaluator.parsed_query.target_name}")

        cols_to_check = MaBoSSEvaluator.get_the_cols_to_check(df)

        def apply_mask(c, v, o):
            match o:
                case Operators.LT:
                    m = (df[c] < v)
                case Operators.EQ:
                    m = (df[c] == v)
                case Operators.GT:
                    m = (df[c] > v)
                case Operators.LE:
                    m = (df[c] <= v)
                case Operators.GE:
                    m = (df[c] >= v)
                case Operators.NE:
                    m = (df[c] != v)
                case _:
                    raise ValueError("Operator not supported")
            return m.all(axis=1)

        mask = apply_mask(cols_to_check, value, op)

        if not mask.any():
            print(
                f"No value found for {MaBoSSEvaluator.parsed_query.target_name} with type {query_type} and operator {op} and value {value}")
            return pd.DataFrame(columns=df.columns)

        # TMIN
        if query_type == QueryType.TMIN:
            start_idx = mask.idxmax()  # the first time the condition is true
            after_start = mask.loc[start_idx:]
            first_false_idx = after_start[~after_start].index

            if first_false_idx.empty:  # if there is no false value after the start index, we return the whole df - true all the time
                return df.loc[start_idx:].copy()
            return df.loc[start_idx: first_false_idx[0]].iloc[:-1].copy()

        # TMAX
        else:
            last_true_idx = mask[::-1].idxmax()
            before_last = mask.loc[:last_true_idx][::-1]
            first_false_backward = before_last[~before_last].index

            if first_false_backward.empty:
                return df.loc[:last_true_idx].copy()
            return df.loc[first_false_backward[0]: last_true_idx].iloc[1:].copy()

    @staticmethod
    def remove_double_columns(df):
        """
        Does exactly what it is said, handles the possibility of a node column and a state column having the same name
        (single node state) so it keeps both columns with _state at the end of the state one.
        :param df: the dataframe to clean
        :return: a cleaned dataframe
        """
        # print(isinstance(df,pd.DataFrame))
        df = df.rename(columns=lambda x: "".join(x.split()))
        current_cols = list(df.columns)
        rename_map = {}

        for col in current_cols:
            if col.endswith("_state"):
                base_name = col[:-6]
                if base_name in current_cols:
                    try:
                        # we compute the difference max between the two columns
                        diff = (df[col].astype(float) - df[base_name].astype(float)).abs().max()
                        if diff < 1e-10:
                            rename_map[col] = base_name
                    except Exception:
                        if df[col].equals(df[base_name]):
                            rename_map[col] = base_name
                else:
                    # if the base name is not in the columns, we keep the column so it is clearer
                    rename_map[col] = base_name
        # applying the rename
        df = df.rename(columns=rename_map)
        # delete the columns that became identical
        df = df.loc[:, ~df.columns.duplicated()].copy()
        df.dropna(inplace=True, ignore_index=True)
        # print(df)

        return df

    @staticmethod
    def compute_interrogation_proba(filtered_data, parsed_query, df_nodes, df_states):
        """
        Compute the probability when the query asks to compute it. (value = "?"). It computes a joint probability
        :param filtered_data: the data that will be used to compute
        :param parsed_query: the parsed query to have all the information
        :param df_nodes: the dataframe containing the nodes_probtraj
        :param df_states: the dataframe containing the states_probtraj
        :return: a dataframe containing the probability of the query
        """
        filtered_data.reset_index(inplace=True, drop=True)
        valid_times = filtered_data["Time"].values
        out_df = pd.DataFrame({"Time": valid_times})

        df_states_filtered = df_states[df_states["Time"].isin(valid_times)].copy()
        df_states_filtered.columns = df_states_filtered.columns.str.replace(" ", "")

        # print(f"df_states_filtered : \n{df_states_filtered}")

        for target in parsed_query.target_name:
            if parsed_query.target == TargetType.STATE:
                col_name = target if target in df_states_filtered.columns else f"{target}_state"

                if col_name in df_states_filtered.columns:
                    out_df[f"P({target})"] = df_states_filtered[col_name].values
                else:
                    out_df[f"P({target})"] = 0.0

            elif parsed_query.target == TargetType.NODE:
                # proba = sum of all the states where the node is in
                joint_proba = np.zeros(len(out_df))
                for col in df_states_filtered.columns:
                    if col == "Time": continue
                    # print(f"Col : {col}")
                    nodes_in_state = col.replace("_state", "").replace(" ", "").split("--")
                    # print(f"Nodes in state : {nodes_in_state} , target : {target} is in nodes_in_state : {target in nodes_in_state}")
                    if target in nodes_in_state:
                        joint_proba += df_states_filtered[col].values

                out_df[f"P({target})"] = joint_proba

        return out_df

    @staticmethod
    def get_the_cols_to_check(df):
        """
        Utility method to get all the columns where a comparison is needed. Whether with a name of a value
        :param df: the dataframe where the columns are
        :return: a list of names
        """
        df.columns = df.columns.str.replace(' ', '')
        # print(df.columns)
        if MaBoSSEvaluator.parsed_query.target_name[0] == '*':
            cols_to_check = [c for c in df.columns if c != "Time"]
        else:
            cols_to_check = MaBoSSEvaluator.parsed_query.target_name
            if MaBoSSEvaluator.parsed_query.target == TargetType.STATE:
                cols_to_check = [f"{name}_state" for name in cols_to_check]

            for name in MaBoSSEvaluator.parsed_query.target_name:
                # print(f"name : {name}")
                if MaBoSSEvaluator.parsed_query.target == TargetType.STATE:
                    if name + "_state" not in df.columns:
                        cols_to_check.remove(name + "_state")
                        warnings.warn(
                            f"Target name \"{name}\" has not been found in the dataframe, removed from the query")
                else:
                    if name not in df.columns:
                        cols_to_check.remove(name)
                        warnings.warn(
                            f"Target name \"{name}\" has not been found in the dataframe, removed from the query")

        if not cols_to_check:
            raise NoNameValidException()
        else:
            return cols_to_check

    @staticmethod
    def check_transient(df_compare_to, df_mut, node):
        """
        Does the computing to check if an expected transition is occurring.
        :param df_compare_to: the reference dataframe
        :param df_mut: the mutated dataframe
        :param node: the node that is checked for a non linear evolution
        :return: a Series (pandas) containing the result of the check
        """
        threshold = MaBoSSEvaluator.threshold
        optimum = MaBoSSEvaluator.optimum
        end = MaBoSSEvaluator.end
        start = MaBoSSEvaluator.start
        digits = MaBoSSEvaluator.digits
        data_out = {}

        # print("in transient")

        i_val_compare = df_compare_to[node].iloc[0].round(digits)
        f_val_compare = df_compare_to[node].tail(10).mean().round(digits)
        peak_compare = df_compare_to[node].max().round(
            digits) if MaBoSSEvaluator.parsed_query.type == QueryType.INCREASE else df_compare_to[node].min().round(
            digits)
        move_compare = abs(peak_compare - i_val_compare) > threshold  # checking it is moving enough
        return_to_normal_compare = abs(f_val_compare - i_val_compare) < threshold  # checking end of movement

        i_val_mut = df_mut[node].iloc[0].round(digits)
        f_val_mut = df_mut[node].tail(10).mean().round(digits)
        peak_mut = df_mut[node].max().round(digits) if MaBoSSEvaluator.parsed_query.type == QueryType.INCREASE else \
        df_mut[node].min().round(digits)
        move_mut = abs(peak_mut - i_val_mut) > threshold
        return_to_normal_mut = abs(f_val_mut - i_val_mut) < threshold

        data_out[f"Initial {node} value reference"] = i_val_compare
        data_out[f"Initial {node} value mutation"] = i_val_mut
        data_out[f"Difference {node} initial value"] = abs(i_val_compare - i_val_mut) < start

        data_out["Final value reference"] = f_val_compare
        data_out["Final value mutation"] = f_val_mut
        data_out[f"Difference {node} final value"] = abs(f_val_compare - f_val_mut) < end

        data_out[f"Peak {node} reference value"] = peak_compare
        data_out[f"Peak {node} mutation value"] = peak_mut
        data_out[f"Difference {node} peak value"] = abs(peak_compare - peak_mut) < optimum

        data_out[f"Movement {node} reference"] = move_compare
        data_out[f"Movement {node} mutation"] = move_mut
        data_out[f"Both simulation have moved"] = move_compare and move_mut

        data_out[f"Return to normal {node} reference"] = return_to_normal_compare
        data_out[f"Return to normal {node} mutation"] = return_to_normal_mut
        data_out[f"Both simulation have returned to normal"] = return_to_normal_compare and return_to_normal_mut

        return data_out

    @staticmethod
    def evaluate_increase_decrease_value(direction: str, min_diff, val_ref: float, val_mut: float):
        """

        :param direction:
        :param min_diff: a percentage
        :param val_ref:
        :param val_mut:
        :return:
        """
        if min_diff is None: min_diff = 0
        if direction == "increase":
            res = val_ref < val_mut and abs(val_ref - val_mut)*100 >= min_diff
            if not res:
                res = val_ref > val_mut and abs(val_ref - val_mut)*100 >= min_diff
                if not res:
                    return "Stable"
                else:
                    return "False"
            else:
                return "True"
        else:
            res = val_ref > val_mut and abs(val_ref - val_mut)*100 >= min_diff
            if not res:
                res = val_ref < val_mut and abs(val_ref - val_mut)*100 >= min_diff
                if not res:
                    return "Stable"
                else:
                    return "False"
            return "True"