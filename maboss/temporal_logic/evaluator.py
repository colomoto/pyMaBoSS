
import warnings
import maboss
import numpy as np

from maboss import Result
from maboss.temporal_logic.custom_exceptions import DataFrameIsEmpty, NoNameException, NoNameValidException, \
    FormulaException, NoCommonTimes
from maboss.temporal_logic.logical_expression_compute import ComputeLogicalExpression
from maboss.temporal_logic.temporal_parser import Parser
from maboss.temporal_logic.formulas import Operators, QueryType, TargetType, FormulaChecker, Formula
import pandas as pd

class MaBoSSEvaluator:

    simulation_results = None
    parsed_query = None

    @staticmethod
    def help():
        print("MaBoSSEvaluator help :")
        print("To evaluate one or multiple queries based on ONE already run simulation (v1.0), use the following syntax :")
        print("MaBoSSEvaluator.evaluate_query([query], results)")
        print("query : the query to evaluate, a list of strings : [\"query1\",\"query2\"], results] , [\"query\"], results]")
        print("results : the results of the simulation, a SimulationResults object (one that maboss returns)")
        print("--------------------------------------------------------------------------------------------------------")
        print("HELP FOR THE QUERY")
        print("The query is a string that contains the following elements : [type]([target_type]:name1,name2...) [operator] [value] [logical_equation (optional)]")
        print("[type] : The type of operation to perform, can be P (probability) or T (time).")
        print("\t - P : will compare the probability of the target to the value. Only one to handle \'?\' value")
        print("\t - T : will return the periods of time where the target probability is meeting the criteria of value.")
        print("\t - Pmax : will return the highest value of the target probability while meeting the criteria of value.")
        print("\t - Pmin : will return the lowest value of the target probability while meeting the criteria of value.")
        print("\t - Tmax : will return the last period of time where the target probability is meeting the criteria of value.")
        print("\t - Tmin : will return the first period of time where the target probability is meeting the criteria of value.")
        print("\t - D : will check if the two nodes passed in parameters are always activate at the same time. Names must be separated by commas.")
        print("\t - Inc : check if the node or the state passed in parameters sees its probability increase on the last time period after the mutation. Mutation constraint are required.")
        print("\t - Dec : check if the node or the state passed in parameters sees its probability decrease on the last time period after the mutation. Mutation constraint are required.")
        print("[target_type] : The type of target to look for, can be node or state.")
        print("\t - node : will look for the probability of the target node.")
        print("\t - state : will look for the probability of the target state.")
        print("[name] : The name of the target to look for. If target_type is node, name is the name of the node. "
              "If target_type is state, name is the name of the state. No spaces or \"\". For all targets use *. Can handle multiple names separated by commas, no spaces or \"\" even for multiple names.")
        print("[operator] : The operator to use to compare the target to the value. Can be <, <=, =, !=, >=, > or /.")
        print("Note that != might return very broad results and = might not return anything.")
        print("\t - < : the probability of the target must be less than the value.")
        print("\t - <= : the probability of the target must be less than or equal to the value.")
        print("\t - = : the probability of the target must be equal to the value.")
        print("\t - != : the probability of the target must not be equal to the value.")
        print("\t - >= : the probability of the target must be greater than or equal to the value.")
        print("\t - > : the probability of the target must be greater than the value.")
        print("\t - / : only for query type D, M, Inc and Dec. No value or operator is required.")
        print("[value] : The value to compare the target to. Can be a number between 0 and 1 or \"?\" ONLY IF the operator used is \'=\' and query type P. If value is \"?\", the query will return the probability of the target.")
        print("With a value of \'?\' the logical equation must not be empty. The value must be empty for D, M, Dec or Inc type.")
        print("[logical_equation] : An optional logical equation to apply to the results. Can be a string or a list of strings.")
        print("\t - The logical equation is a string that contains the following elements : [ [name]  [operator] [value] ]")
        print("\t - The operator can be &, | (pipe). A logical-not ! can be used in front of a name : !name.")
        print("\t - The name can referenced to a node or a state, by default the result will be the probability "
              "of the node or state, thus returning both. For less columns in output, use : node:name or state:name."
              " To appy a logical-not in this condition do : node:!name or state:!name.")
        print("\t - The logical equation can contain a numerical evaluation. This one must be placed in between parentheses or strange results may occur.")
        print("\t - The logical equation can have multiple conditions intricated on numerous levels: [ ( condition A ) | ( ( condition B ) | ( ( condition C ) ) ) ]")
        print("\t - It is really important to separate each member by a space so the parser reads it correctly and not raises an Exception.")
        print("------------------------------------------------------------------------------------------------------")
        print("Examples :")
        print("P(node:A) > 0.5 : returns all the rows where the probability of node A is greater than 0.5")
        print("P(node:A,B) < 0.4 : returns all the rows where the probability of node A and node B is less than 0.4")
        print("P(node:A) = ? [ node:B & C ] : returns the probabilities of node A to be active in one state while B and C are also active (joint probability)")
        print("P(state:A) = ? [ ( node:B > 0.3 ) | C ] : returns the probabilities of state A to be active in one state while B has a probability greater than 0.3 or while C is active.")
        print("T(state:A) >= 0.6 : returns all the periods of time where state A has a probability greater than or equal to 0.6.")
        print("Tmin(node:A,B) >= 0.3 : returns the first period of time where node A and node B are active with a probability greater than or equal to 0.3.")
        print("Tmax(node:A,B) <= 0.7 : returns the last period of time where node A and node B are active with a probability less than or equal to 0.7.")
        print("Pmax(node:A) >= 0.5 : returns the greatest probability of node A being above 0.5 in any period of time. Can return nothing.")
        print("Pmin(node:A) <= 0.5 : returns the lowest probability of node A being under 0.5 in any period of time. Can return nothing.")
        print("Inc(node:A) / [ ] [ B:ON ] : returns the last time code comparison and a print saying if the node A was increased or not.")
        print("Dec(node:A) / [ A & C ] [ B:ON ] : returns the last time code comparison and print saying if the node A was decreased or not. The logical equation is applied before the comparison.")
        print("Inc(state:A--B) / [ ] [ B:ON ] : returns the last time code comparison and print saying if the state A--B was increased or not.")
        print("------------------------------------------------------------------------------------------------------")
        print("Exemple of questions and the query to provide : ")
        print("What is the probability of node A and B being active at the same time while C is inactive and D above 0.5 ?\n\t -> P(node:A,B) = ? [ node:!C & ( D > 0.5 ) ]")
        print("What are all the moments my simulation is on the state A--B with C inactive ?\n\t -> T(state:A--B) >= 0.0 [ !C ]")
        print("What probability for the state A--B to be active if C, D or E is active and F is inactive ?\n\t -> P(state:A--B) = ? [ ( C | D | E ) & !F ]")
        print("When does the probability of state <nil> exceeds 0.5 ?\n\t -> T(state:<nil>) >= 0.5")
        print("When does the probability of state <nil> exceeds 0.5 for the first time ?\n\t -> Tmin(state:<nil>) >= 0.5")
        print("When does the probability of state <nil> exceeds 0.5 for the last time ?\n\t -> Tmax(state:<nil>) >= 0.5")
        print("Does the probability for A--B state increase when C is activated ?\n\t -> Inc(state:A--B) / [ ] [ C:ON ]")
        print("--------------------------------------------------------------------------------------------------------")
        print("For more exemples and output exemples you can check the test_evaluator.py file. Check the notebook Tuto Temporal Logic for more info.")
        print("In case of any question you can contact me at : oscardufossez@gmail.com")

    @staticmethod
    def mutation_to_string(mutation_constraint: list[str]):
        if not mutation_constraint:
            return ""
        else:
            return f"{mutation_constraint[0]} {mutation_constraint[1]}"

    @staticmethod
    def querying(query, sim_cfg, sim_bnd):
        list_of_df = [] #results of computation and evaluation
        checked_query = [] #queries that are checked for errors
        df_sorted_mutations = pd.DataFrame({
            'master_simulation ' : [] #the master simulation is the simulation run without any mutation or changed param
        })

        # Running the simulations and stocked the results
        model_sim = maboss.load(sim_cfg, sim_bnd)
        res_master = model_sim.run()
        df_sim_results = pd.DataFrame({
            'master_simulation ': [res_master]
        })

        # Reading of the queries and launching the simulation for a mutation if it was not done before
        for q in query:
            parsed_query = Parser.parse_query(q)
            try:
                FormulaChecker.check_formula(parsed_query)
                checked_query.append(q)
            except FormulaException:
                warnings.warn(f"Formula is not correct : {q} , will not be evaluated.")
                continue
            if parsed_query.mutation_constraint:
                mutated_model = model_sim.copy()
                col_name = ""
                for c in parsed_query.mutation_constraint:
                    col_name += MaBoSSEvaluator.mutation_to_string(c) + " __ "
                    mutated_model.mutate(c[0], str(c[1]))
                if col_name not in df_sorted_mutations.columns:
                    df_sorted_mutations[col_name] = []
                    res_mutated = mutated_model.run()
                    df_sim_results[col_name] = [res_mutated]
                df_sorted_mutations[col_name] = (df_sorted_mutations[col_name].append(q))
            else:
                df_sorted_mutations['master_simulation'] = df_sorted_mutations['master_simulation'].append(q)

        for q in checked_query:
            try:
                col_query = df_sorted_mutations.columns[(df_sorted_mutations == q).any()].tolist()
                results = df_sim_results[col_query[0]]
                if Parser.parse_query(q).type not in [QueryType.DEPENDENCIE, QueryType.MUTATION, QueryType.INCREASE, QueryType.DECREASE]:
                    list_of_df.append(MaBoSSEvaluator.evaluate_query(Parser.parse_query(q), results))
                else:
                    match Parser.parse_query(q).type:
                        case QueryType.DEPENDENCIE: pass
                        case QueryType.MUTATION: pass
                        case QueryType.INCREASE:
                            list_of_df.append(MaBoSSEvaluator.evaluate_increase_decrease(Parser.parse_query(q), results, res_master, q))
                            break
                        case QueryType.DECREASE:
                            list_of_df.append(MaBoSSEvaluator.evaluate_increase_decrease(Parser.parse_query(q), results, res_master, q))
                            break
                        case _:
                            raise ValueError("Query type is not supported, for comparison over mutation, try increase (Inc) or decrease (Dec)")


            except FormulaException:
                raise FormulaException(f"Formula is not correct : {q}")

        for i,df in enumerate(list_of_df):
            if df is None:
                print(f"df {i} is empty. Query was : {query[i]}")

        return list_of_df

    @staticmethod
    def evaluate_increase_decrease(parsed_query_input, results_mutation, results_master, query):
        if results_mutation is None or results_master is None:
            raise ValueError("Results are empty")

        name_target = parsed_query_input.target_name[0].strip().replace(' ', '') #cleaning the name to avoid spaces

        def prepare_df(results):
            MaBoSSEvaluator.simulation_results = results
            MaBoSSEvaluator.parsed_query = parsed_query_input

            df = MaBoSSEvaluator.get_df_target(parsed_query_input.target, True)

            if df.empty:
                raise DataFrameIsEmpty(f"The dataframe is empty for target \"{parsed_query_input.target}\"")

            df = df.dropna().copy()
            #removing the spaces on the values
            df.columns = df.columns.str.replace(' ', '')

            if 'State' in df.columns:
                df['State'] = df['State'].astype(str).str.replace(' ', '')
            return df

        #the fixpoints table for each of the results
        df_mutation = prepare_df(results_mutation)
        df_master = prepare_df(results_master)

        data_out = {}

        if parsed_query_input.target == TargetType.STATE:
            try:
                #getting the probability of the state in each simulation
                proba_master = df_master.loc[df_master["State"] == name_target, "Proba"].values[0]
                proba_mutation = df_mutation.loc[df_mutation["State"] == name_target, "Proba"].values[0]
            except (KeyError, IndexError):
                raise NoNameValidException(f"State {name_target} not found")


            res_diff = proba_mutation - proba_master
            data_out[f"{name_target} from master"] = [proba_master]
            data_out[f"{name_target} from mutation"] = [proba_mutation]

        else:
            if name_target not in df_master.columns or name_target not in df_mutation.columns:
                raise NoNameValidException(f"Node column '{name_target}' not found in results")

            # keeping the lines where node is 1 and summing all the probas
            sum_master = df_master.loc[df_master[name_target].astype(float) == 1, 'Proba'].sum()
            sum_mutation = df_mutation.loc[df_mutation[name_target].astype(float) == 1, 'Proba'].sum()

            data_out[f"{name_target} prob_cumul_master"] = [sum_master]
            data_out[f"{name_target} prob_cumul_mutant"] = [sum_mutation]
            res_diff = sum_mutation - sum_master
            proba_master = sum_master
            proba_mutation = sum_mutation

        percentage = (res_diff / proba_master) if proba_master != 0 else 0.0
        data_out["Difference"] = [res_diff]
        data_out["Percentage"] = [f"{percentage:.2%}"]

        if QueryType.INCREASE == parsed_query_input.type:
            data_out[f"Increase {name_target}"] = proba_mutation > proba_master
        else:
            data_out[f"Decrease {name_target}"] = proba_mutation < proba_master

        return pd.DataFrame(data_out)


    @staticmethod
    def evaluate_query(parsed_query_input: Formula, results):  # maybe pass the results as an array to compute more than one simulation

        if results is None:
            raise ValueError("Results are empty")

        if not "Time" in results.get_states_probtraj().columns:
            df_states = results.get_states_probtraj().copy()
            df_states["Time"] = df_states.index
        else : df_states = results.get_states_probtraj().copy()

        df_states.columns = df_states.columns.str.replace(" ","",regex=False)

        if not "Time" in results.get_nodes_probtraj().columns:
            df_nodes = results.get_nodes_probtraj().copy()
            df_nodes["Time"] = df_nodes.index
        else: df_nodes = results.get_nodes_probtraj().copy()

        MaBoSSEvaluator.simulation_results = [df_nodes,df_states]
        query_input = parsed_query_input

        # Selection of the simulation result df to use depending on the target
        df_target = MaBoSSEvaluator.get_df_target(parsed_query_input.target)
        if df_target.empty:
            raise DataFrameIsEmpty(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\"")
        #print(f"DF after target selection : \n {df_target}")
        # Selection of the rows depending on what is looking for
        match query_input.type.value:
            case QueryType.P.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_proba(df_target, MaBoSSEvaluator.parsed_query.value)
            case QueryType.T.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_time(df_target, MaBoSSEvaluator.parsed_query.value)
            case QueryType.PMAX.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_proba(df_target, MaBoSSEvaluator.parsed_query.value, QueryType.PMAX)
            case QueryType.PMIN.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_proba(df_target, MaBoSSEvaluator.parsed_query.value, QueryType.PMIN)
            case QueryType.TMAX.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_time_minmax(df_target, MaBoSSEvaluator.parsed_query.value, QueryType.TMAX)
            case QueryType.TMIN.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_time_minmax(df_target, MaBoSSEvaluator.parsed_query.value, QueryType.TMIN)
            case _:
                raise ValueError("Query type is not supported, try P, Pmin, Pmax or T, Tmin, Tmax")

        #print(f"DF after value selection : \n {filtered_data}")

        if query_input.type == QueryType.P or query_input.type == QueryType.T:
            #print(f"DF in treatment for P or T type\n Filtered_data columns : \n{filtered_data.columns}\n")
            # Selection of the columns regarding the name of the target if type P or T strictly. If type in a min max logic, keep all the columns
            filtered_data = MaBoSSEvaluator.get_df_target_name(filtered_data, query_input.target_name)

        #print(f"DF after name selection : \n {filtered_data}")

        if query_input.logical_equation:
            #print(f"DF in treatment for logical equation")
            log_df = ComputeLogicalExpression.compute_logical_expression(query_input.logical_equation, MaBoSSEvaluator.simulation_results)
            #print(f"DF after logical equation : \n {log_df} \n Will be merged with :\n {filtered_data}\n")
            filtered_data = ComputeLogicalExpression.merge_or(filtered_data, log_df, MaBoSSEvaluator.simulation_results[0],
                                                               MaBoSSEvaluator.simulation_results[1]
                                                               .rename(columns={c: f"{c}_state" for c in MaBoSSEvaluator.simulation_results[1].columns if c != 'Time'}),True)

        if filtered_data.empty:
            raise DataFrameIsEmpty(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\" "
                                   f"with name \"{MaBoSSEvaluator.parsed_query.target_name}\" and logical equation "
                                   f"\"{MaBoSSEvaluator.parsed_query.logical_equation}\"")
        if filtered_data.size > 2:
            filtered_data = MaBoSSEvaluator.remove_double_columns(filtered_data)

        #todo put here the call of the computation function (returns a new df with the new columns and the filtered_data)
        if MaBoSSEvaluator.parsed_query.value == '?':
            #print(f"filtered_data : \n {filtered_data} \n")
            computed_values = MaBoSSEvaluator.compute_interrogation_proba(filtered_data, MaBoSSEvaluator.parsed_query,MaBoSSEvaluator.simulation_results[0],MaBoSSEvaluator.simulation_results[1])
            return computed_values

        return filtered_data.dropna(inplace=False, ignore_index=True)

    @staticmethod
    def get_df_target(target, fp: bool=False):
        if fp:
            return MaBoSSEvaluator.simulation_results.get_fptable()
        else:
            if target.value == TargetType.NODE.value:
                return MaBoSSEvaluator.simulation_results[0]
            elif target.value == TargetType.STATE.value:
                return (MaBoSSEvaluator.simulation_results[1]
                        .rename(columns={c: f"{c}_state" for c in MaBoSSEvaluator.simulation_results.get_states_probtraj().columns if c != 'Time'}))
            else:
                raise ValueError("Target is not supported, try node or state")

    @staticmethod
    def get_df_target_name(df, target_name):
        if df is None :
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
        op = MaBoSSEvaluator.parsed_query.operator
        #print(f"target_name : {MaBoSSEvaluator.parsed_query.target_name}")

        cols_to_check = MaBoSSEvaluator.get_the_cols_to_check(df)
        #print(f"cols to check after verification: {cols_to_check}")

        #todo here do the check "?"
        try:
            value = float(value)
            is_number = True
        except ValueError:
            is_number = False

        out_df = pd.DataFrame()
        #print(f"Received df : \n{df}\n")

        if is_number:
            match op:
                case Operators.LT:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        mask = (df[cols_to_check] < value).any(axis=1) #just check the value, any column checking it is good passes the test
                    else:
                        mask = (df[cols_to_check] < value).all(axis=1) #all the values on the line must be less than the value
                case Operators.EQ:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        mask = (df[cols_to_check] == value).any(axis=1)
                    else:
                        mask = (df[cols_to_check] == value).all(axis=1)
                case Operators.GT:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        mask = (df[cols_to_check] > value).any(axis=1)
                    else:
                        mask = (df[cols_to_check] > value).all(axis=1)
                case Operators.LE:
                        if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                            mask = (df[cols_to_check] <= value).any(axis=1)
                        else:
                            mask = (df[cols_to_check] <= value).all(axis=1)
                case Operators.GE:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        mask = (df[cols_to_check] >= value).any(axis=1)
                    else:
                        mask = (df[cols_to_check] >= value).all(axis=1)
                case Operators.NE:
                    if MaBoSSEvaluator.parsed_query.target_name[0] != '*':
                        mask = (df[cols_to_check] != value).any(axis=1)
                    else:
                        mask = (df[cols_to_check] != value).all(axis=1)
                case _:
                    raise ValueError("Operator is not supported, try <, <=, =, !=, >=, >")

            out_df = df[mask].copy()
            out_df["Time"] = df["Time"]  # restablish the correct time values

            # print(f" value_proba , {MaBoSSEvaluator.parsed_query.target_name} with type {query_type} : \n {out_df} \n")

            out_df = out_df.dropna(subset=out_df.columns.difference(['Time']), axis=0, how='all',
                                   ignore_index=True)  # remove the rows with all nan values

            # print(f" value_proba , {MaBoSSEvaluator.parsed_query.target_name} with type {query_type} after dropna : \n {out_df} \n")
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
            #print(f"value is not a number")
            out_df["Time"] = df["Time"]
            for col in cols_to_check:
                out_df[col] = df[col]
            #print(f"out_df : \n {out_df}")
            return out_df

    @staticmethod
    def get_df_target_value_time(df, value):
        op = MaBoSSEvaluator.parsed_query.operator
        #todo here do the check "?"
        value = float(value)
        target_names = MaBoSSEvaluator.parsed_query.target_name
        target_type = MaBoSSEvaluator.parsed_query.target

        #print(f"get_df_target_value_time :{value}, {op}, {MaBoSSEvaluator.parsed_query.target_name}")

        if TargetType.STATE == target_type:
            cols_to_check = [f"{name}_state" for name in target_names if f"{name}_state" in df.columns]
        else:
            cols_to_check = [n for n in target_names if n in df.columns]

        def apply_mask(c,v,o):
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
            print(f"No value found for {MaBoSSEvaluator.parsed_query.target_name} with type Time (T) and operator {op} and value {value}")
            return pd.DataFrame(columns=df.columns)

        return df[mask].copy()

    @staticmethod
    def get_df_target_value_time_minmax(df, value, query_type=QueryType.TMIN):
        #todo here the "?" check
        value = float(value)
        query_type = query_type.value
        op = MaBoSSEvaluator.parsed_query.operator
        target_names = MaBoSSEvaluator.parsed_query.target_name

        #print(f"get_df_target_value_time_minmax :{value}, {query_type}, {op}, {MaBoSSEvaluator.parsed_query.target_name}")

        cols_to_check = MaBoSSEvaluator.get_the_cols_to_check(df)

        def apply_mask(c,v,o):
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
            print(f"No value found for {MaBoSSEvaluator.parsed_query.target_name} with type {query_type} and operator {op} and value {value}")
            return pd.DataFrame(columns=df.columns)

        #TMIN
        if query_type == QueryType.TMIN:
            start_idx = mask.idxmax() #the first time the condition is true
            after_start = mask.loc[start_idx:]
            first_false_idx = after_start[~after_start].index

            if first_false_idx.empty: #if there is no false value after the start index, we return the whole df - true all the time
                 return df.loc[start_idx:].copy()
            return df.loc[start_idx : first_false_idx[0]].iloc[:-1].copy()

        #TMAX
        else:
            last_true_idx = mask[::-1].idxmax()
            before_last = mask.loc[:last_true_idx][::-1]
            first_false_backward = before_last[~before_last].index

            if first_false_backward.empty:
                return df.loc[:last_true_idx].copy()
            return df.loc[first_false_backward[0]: last_true_idx].iloc[1:].copy()


    @staticmethod
    def remove_double_columns(df):
        #print(isinstance(df,pd.DataFrame))
        df = df.rename(columns=lambda x: "".join(x.split()))
        current_cols = list(df.columns)
        rename_map = {}

        for col in current_cols:
            if col.endswith("_state"):
                base_name = col[:-6]
                if base_name in current_cols:
                    try:
                        #we compute the difference max between the two columns
                        diff = (df[col].astype(float) - df[base_name].astype(float)).abs().max()
                        if diff < 1e-10:
                            rename_map[col] = base_name
                    except Exception:
                        if df[col].equals(df[base_name]):
                            rename_map[col] = base_name
                else:
                    #if the base name is not in the columns, we keep the column so it is clearer
                    rename_map[col] = base_name
        #applying the rename
        df = df.rename(columns=rename_map)
        #delete the columns that became identical
        df = df.loc[:, ~df.columns.duplicated()].copy()
        df.dropna(inplace=True, ignore_index=True)
        #print(df)

        return df

    @staticmethod
    def compute_interrogation_proba(filtered_data, parsed_query, df_nodes, df_states):
        filtered_data.reset_index(inplace=True, drop=True)
        valid_times = filtered_data["Time"].values
        out_df = pd.DataFrame({"Time" : valid_times})

        df_states_filtered = df_states[df_states["Time"].isin(valid_times)].copy()
        df_states_filtered.columns = df_states_filtered.columns.str.replace(" ", "")

        #print(f"df_states_filtered : \n{df_states_filtered}")

        for target in parsed_query.target_name:
            if parsed_query.target == TargetType.STATE:
                col_name = target if target in df_states_filtered.columns else f"{target}_state"

                if col_name in df_states_filtered.columns:
                    out_df[f"P({target})"] = df_states_filtered[col_name].values
                else : out_df[f"P({target})"] = 0.0

            elif parsed_query.target == TargetType.NODE:
                #proba = sum of all the states where the node is in
                joint_proba = np.zeros(len(out_df))
                for col in df_states_filtered.columns:
                    if col == "Time": continue
                    #print(f"Col : {col}")
                    nodes_in_state = col.replace("_state", "").replace(" ", "").split("--")
                    #print(f"Nodes in state : {nodes_in_state} , target : {target} is in nodes_in_state : {target in nodes_in_state}")
                    if target in nodes_in_state:
                        joint_proba += df_states_filtered[col].values

                out_df[f"P({target})"] = joint_proba

        return out_df


    @staticmethod
    def get_the_cols_to_check(df):
        df.columns = df.columns.str.replace(' ', '')
        #print(df.columns)
        if MaBoSSEvaluator.parsed_query.target_name[0] == '*':
            cols_to_check = [c for c in df.columns if c != "Time"]
        else:
            cols_to_check = MaBoSSEvaluator.parsed_query.target_name
            if MaBoSSEvaluator.parsed_query.target == TargetType.STATE:
                cols_to_check = [f"{name}_state" for name in cols_to_check]

            for name in MaBoSSEvaluator.parsed_query.target_name:
                #print(f"name : {name}")
                if MaBoSSEvaluator.parsed_query.target == TargetType.STATE:
                    if name + "_state" not in df.columns:
                            cols_to_check.remove(name+"_state")
                            warnings.warn(f"Target name \"{name}\" has not been found in the dataframe, removed from the query")
                else:
                    if name not in df.columns:
                        cols_to_check.remove(name)
                        warnings.warn(
                            f"Target name \"{name}\" has not been found in the dataframe, removed from the query")

        if not cols_to_check:
            raise NoNameValidException()
        else:
            return cols_to_check