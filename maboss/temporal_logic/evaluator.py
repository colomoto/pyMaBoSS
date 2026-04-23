import warnings
from unittest import case

from maboss.temporal_logic.custom_exceptions import DataFrameIsEmpty, NoNameException, NoNameValidException
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
    def querying(query, results):  # maybe pass the results as an array to compute more than one simulation
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
            #print(f"DF in treatment for P or T type")
            # Selection of the columns regarding the name of the target if type P or T strictly. If type in a min max logic, keep all the columns
            filtered_data = MaBoSSEvaluator.get_df_target_name(filtered_data, parsed_query.target_name)

        print(f"DF after name selection : \n {filtered_data}")

        if parsed_query.logical_equation:
            #print(f"DF in treatment for logical equation")
            log_df = ComputeLogicalExpression.compute_logical_expression(parsed_query.logical_equation, MaBoSSEvaluator.simulation_results)
            filtered_data = ComputeLogicalExpression.merge_and(log_df, filtered_data, MaBoSSEvaluator.simulation_results.get_nodes_probtraj(), MaBoSSEvaluator.simulation_results.get_states_probtraj())

        if filtered_data.empty:
            raise DataFrameIsEmpty(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\" "
                                   f"with name \"{MaBoSSEvaluator.parsed_query.target_name}\" and logical equation "
                                   f"\"{MaBoSSEvaluator.parsed_query.logical_equation}\"")
        if filtered_data.size > 2:
            filtered_data = MaBoSSEvaluator.remove_double_columns(filtered_data)

        return filtered_data.dropna(inplace=False, ignore_index=True)

    @staticmethod
    def get_df_target(target):
        if target.value == TargetType.NODE.value:
            return MaBoSSEvaluator.simulation_results.get_nodes_probtraj()
        elif target.value == TargetType.STATE.value:
            return MaBoSSEvaluator.simulation_results.get_states_probtraj()
        else:
            raise ValueError("Target is not supported, try node or state")

    @staticmethod
    def get_df_target_name(df, target_name):
        if df is None :
            raise ValueError(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\"")

        if target_name is None or target_name == []:
            raise NoNameException()

        if target_name[0] != '*':
            for name in target_name:
                if name not in df.columns:
                    target_name.remove(name)
                    warnings.warn(f"Target name \"{name}\" has not been found in the dataframe, removed from the query")

        if target_name == []:
            raise NoNameValidException()

        new_df = pd.DataFrame()

        if target_name[0] != '*':
            new_df["Time"] = df["Time"]

            for name in target_name:
                new_df[name] = df[name]

        else:
            new_df = df.copy()

        return new_df


    @staticmethod
    def get_df_target_value_proba(df, value, query_type=QueryType.P):
        op = MaBoSSEvaluator.parsed_query.operator
        print(f"target_name : {MaBoSSEvaluator.parsed_query.target_name}")
        if MaBoSSEvaluator.parsed_query.target_name[0] == '*':
            cols_to_check = [c for c in df.columns if c != "Time"]
        else:
            cols_to_check = MaBoSSEvaluator.parsed_query.target_name
            for name in MaBoSSEvaluator.parsed_query.target_name:
                if name not in df.columns:
                    cols_to_check.remove(name)
                    warnings.warn(f"Target name \"{name}\" has not been found in the dataframe, removed from the query")

            if not cols_to_check:
                raise NoNameValidException()

        print(f"cols to check : {cols_to_check}")

        value = float(value)
        out_df = pd.DataFrame()
        #print(f"Received df : \n{df}\n")

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
        out_df["Time"] = df["Time"] #restablish the correct time values

        #print(f" value_proba , {MaBoSSEvaluator.parsed_query.target_name} with type {query_type} : \n {out_df} \n")

        out_df = out_df.dropna(subset=out_df.columns.difference(['Time']), axis=0, how='all', ignore_index=True) #remove the rows with all nan values

        #print(f" value_proba , {MaBoSSEvaluator.parsed_query.target_name} with type {query_type} after dropna : \n {out_df} \n")

        if query_type == QueryType.P:
            return out_df
        elif  query_type == QueryType.PMAX:
            if MaBoSSEvaluator.parsed_query.target_name[0] not in df.columns:
                raise NoNameValidException()
            idx_max =  out_df[MaBoSSEvaluator.parsed_query.target_name].max(axis=1).idxmax()
            return out_df.iloc[[idx_max]]
        else:
            if MaBoSSEvaluator.parsed_query.target_name[0] not in df.columns:
                raise NoNameValidException()
            idx_min = out_df[MaBoSSEvaluator.parsed_query.target_name].min(axis=1).idxmin()
            return out_df.iloc[[idx_min]]


    @staticmethod
    def get_df_target_value_time(df, value):
        op = MaBoSSEvaluator.parsed_query.operator
        value = float(value)
        match op:
            case Operators.LT:
                mask =  (df['Time'] < value)
            case Operators.EQ:
                mask = (df['Time'] == value)
            case Operators.GT:
                mask = (df['Time'] > value)
            case Operators.LE:
                mask = (df['Time'] <= value)
            case Operators.GE:
                mask = (df['Time'] >= value)
            case Operators.NE:
                mask = (df['Time'] != value)
            case _:
                raise ValueError("Operator is not supported, try <, <=, ==, !=, >=, >")

        return df[mask].copy()

    @staticmethod
    def get_df_target_value_time_minmax(df, value, query_type=QueryType.TMIN):
        value = float(value)
        query_type = query_type.value
        op = MaBoSSEvaluator.parsed_query.operator
        target_names = MaBoSSEvaluator.parsed_query.target_name

        print(f"get_df_target_value_time_minmax :{value}, {query_type}, {op}, {MaBoSSEvaluator.parsed_query.target_name}")

        if target_names[0] == '*':
            cols_to_check = [c for c in df.columns if c != "Time"]
            use_all = True
        else:
            cols_to_check = [n for n in target_names if n in df.columns]
            use_all = False

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
            return m.all(axis=1) if use_all else m.any(axis=1)

        mask = apply_mask(cols_to_check, value, op)

        if not mask.any():
            print(f"No value found for {MaBoSSEvaluator.parsed_query.target_name} with type {query_type} and operator {op} and value {value}")
            return pd.DataFrame(columns=df.columns)

        #TMIN
        if query_type == QueryType.TMIN:
            start_idx = mask.idxmax() #the first time the condition is true
            after_start = mask.loc[start_idx:]
            first_false_idx = after_start[~after_start].index

            if first_false_idx.size == 0:
                return df.loc[start_idx:].copy
            return df.loc[start_idx: first_false_idx[0]].iloc[-1].copy()
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
