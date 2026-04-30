import re
import warnings
from unittest import case

import numpy as np
from bs4.filter import TagNameMatchRule
from pandas.core.computation.parsing import clean_column_name

from maboss.temporal_logic.custom_exceptions import DataFrameIsEmpty, NoNameException, NoNameValidException, \
    FormulaException
from maboss.temporal_logic.logical_expression_compute import ComputeLogicalExpression
from maboss.temporal_logic.temporal_parser import Parser
from maboss.temporal_logic.formulas import Operators, QueryType, TargetType, FormulaChecker
import pandas as pd

class MaBoSSEvaluator:

    simulation_results = None
    parsed_query = None

    @staticmethod
    def help():  # todo little manual
        print('wip')

    @staticmethod
    def querying(query, results):
        list_of_df = []
        for q in query:
            try:
                list_of_df.append(MaBoSSEvaluator.evaluate_query(q, results))
            except FormulaException:
                raise FormulaException(f"Formula is not correct : {q}")
        for i,df in enumerate(list_of_df):
            if df is None:
                print(f"df {i} is empty. Query was : {query[i]}")

        return list_of_df

    @staticmethod
    def evaluate_query(query, results):  # maybe pass the results as an array to compute more than one simulation
        if query == "" or query is None:
            raise ValueError("Query is empty")
        if results is None:
            raise ValueError("Results are empty")

        MaBoSSEvaluator.simulation_results = results
        query_input = query

        # Decomposition of the query
        parsed_query = Parser.parse_query(query_input)
        FormulaChecker.check_formula(parsed_query) # raise error if the formula is not correct
        MaBoSSEvaluator.parsed_query = parsed_query
        print("Query parsed successfully !")

        # Selection of the simulation result df to use depending on the target
        df_target = MaBoSSEvaluator.get_df_target(parsed_query.target)
        if df_target.empty:
            raise DataFrameIsEmpty(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\"")
        #print(f"DF after target selection : \n {df_target}")
        # Selection of the rows depending on what is looking for
        match parsed_query.type.value:
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
                raise ValueError("Query type is not supported, try P, Pmin, Pmax or T, Tmin, Tmax") #min and max in wip

        #print(f"DF after value selection : \n {filtered_data}")

        if parsed_query.type == QueryType.P or parsed_query.type == QueryType.T:
            #print(f"DF in treatment for P or T type\n Filtered_data columns : \n{filtered_data.columns}\n")
            # Selection of the columns regarding the name of the target if type P or T strictly. If type in a min max logic, keep all the columns
            filtered_data = MaBoSSEvaluator.get_df_target_name(filtered_data, parsed_query.target_name)

        #print(f"DF after name selection : \n {filtered_data}")

        if parsed_query.logical_equation:
            #print(f"DF in treatment for logical equation")
            log_df = ComputeLogicalExpression.compute_logical_expression(parsed_query.logical_equation, MaBoSSEvaluator.simulation_results)
            print(f"DF after logical equation : \n {log_df} \n Will be merged with :\n {filtered_data}\n")
            filtered_data = ComputeLogicalExpression.merge_or(filtered_data, log_df, MaBoSSEvaluator.simulation_results.get_nodes_probtraj(),
                                                               MaBoSSEvaluator.simulation_results.get_states_probtraj()
                                                               .rename(columns={c: f"{c}_state" for c in MaBoSSEvaluator.simulation_results.get_states_probtraj().columns if c != 'Time'}),True)

        if filtered_data.empty:
            raise DataFrameIsEmpty(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\" "
                                   f"with name \"{MaBoSSEvaluator.parsed_query.target_name}\" and logical equation "
                                   f"\"{MaBoSSEvaluator.parsed_query.logical_equation}\"")
        if filtered_data.size > 2:
            filtered_data = MaBoSSEvaluator.remove_double_columns(filtered_data)

        #todo put here the call of the computation function (returns a new df with the new columns and the filtered_data)
        if MaBoSSEvaluator.parsed_query.value == '?':
            print(f"filtered_data : \n {filtered_data} \n")
            computed_values = MaBoSSEvaluator.compute_interrogation_proba(filtered_data, MaBoSSEvaluator.parsed_query,MaBoSSEvaluator.simulation_results.get_nodes_probtraj(),MaBoSSEvaluator.simulation_results.get_states_probtraj())
            return computed_values

        return filtered_data.dropna(inplace=False, ignore_index=True)

    @staticmethod
    def get_df_target(target):
        if target.value == TargetType.NODE.value:
            return MaBoSSEvaluator.simulation_results.get_nodes_probtraj()
        elif target.value == TargetType.STATE.value:
            return (MaBoSSEvaluator.simulation_results.get_states_probtraj()
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
        #print(f"target_name : {MaBoSSEvaluator.parsed_query.target_name} df cols :\n {df.columns}")

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
            print(f"out_df : \n {out_df}")
            return out_df

    @staticmethod
    def get_df_target_value_time(df, value):
        op = MaBoSSEvaluator.parsed_query.operator
        #todo here do the check "?"
        value = float(value)
        target_names = MaBoSSEvaluator.parsed_query.target_name
        target_type = MaBoSSEvaluator.parsed_query.target

        print(f"get_df_target_value_time :{value}, {op}, {MaBoSSEvaluator.parsed_query.target_name}")

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

        print(f"get_df_target_value_time_minmax :{value}, {query_type}, {op}, {MaBoSSEvaluator.parsed_query.target_name}")

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

        print(f"df_states_filtered : \n{df_states_filtered}")

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
        if MaBoSSEvaluator.parsed_query.target_name[0] == '*':
            cols_to_check = [c for c in df.columns if c != "Time"]
        else:
            cols_to_check = MaBoSSEvaluator.parsed_query.target_name
            if MaBoSSEvaluator.parsed_query.target == TargetType.STATE:
                cols_to_check = [f"{name}_state" for name in cols_to_check]

            for name in MaBoSSEvaluator.parsed_query.target_name:
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