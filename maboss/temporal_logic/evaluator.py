import warnings

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
        return True

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

        # Selection of the simulation result df to use depending of the target
        df_target = MaBoSSEvaluator.get_df_target(parsed_query.target)
        if df_target.empty:
            raise DataFrameIsEmpty(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\"")

        # Selection of the columns regarding the name of the target
        df_target = MaBoSSEvaluator.get_df_target_name(df_target, parsed_query.target_name)

        # Selection of the rows depending of what is looking for
        match parsed_query.type.value:
            case QueryType.P.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_proba(df_target, MaBoSSEvaluator.parsed_query.value)
            case QueryType.T.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_time(df_target, MaBoSSEvaluator.parsed_query.value)
            case QueryType.PMAX:
                filtered_data = MaBoSSEvaluator.get_df_target_value_proba(df_target, MaBoSSEvaluator.simulation_results.get_max_prob())
            case QueryType.PMIN:
                filtered_data = MaBoSSEvaluator.get_df_target_value_proba(df_target, MaBoSSEvaluator.simulation_results.get_min_prob())
            case QueryType.TMAX:
                filtered_data = MaBoSSEvaluator.get_df_target_value_time(df_target, MaBoSSEvaluator.simulation_results.get_max_time())
            case QueryType.TMIN:
                filtered_data = MaBoSSEvaluator.get_df_target_value_time(df_target, MaBoSSEvaluator.simulation_results.get_min_time())
            case _:
                raise ValueError("Query type is not supported, try P or T")

        if parsed_query.logical_equation:
            log_df = ComputeLogicalExpression.compute_logical_expression(parsed_query.logical_equation, MaBoSSEvaluator.simulation_results)
            filtered_data = ComputeLogicalExpression.merge_or(log_df, filtered_data, MaBoSSEvaluator.simulation_results.get_nodes_probtraj())
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
    def get_df_target_value_proba(df, value):
        op = MaBoSSEvaluator.parsed_query.operator
        cols_to_check = [c for c in df.columns if c != "Time"]
        value = float(value)

        match op:
            case Operators.LT:
                mask = (df[cols_to_check] < value).all(axis=1)
            case Operators.EQ:
                mask = (df[cols_to_check] == value).all(axis=1)
            case Operators.GT:
                mask = (df[cols_to_check] > value).all(axis=1)
            case Operators.LE:
                mask = (df[cols_to_check] <= value).all(axis=1)
            case Operators.GE:
                mask = (df[cols_to_check] >= value).all(axis=1)
            case Operators.NE:
                mask = (df[cols_to_check] != value).all(axis=1)
            case _:
                raise ValueError("Operator is not supported, try <, <=, =, !=, >=, >")

        return df[mask].copy()

    @staticmethod
    def get_df_target_value_time(df, value):

        value = float(value)
        match MaBoSSEvaluator.parsed_query.operator:
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
    def remove_double_columns(df):
        print(isinstance(df,pd.DataFrame))
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
        print(df)

        return df
