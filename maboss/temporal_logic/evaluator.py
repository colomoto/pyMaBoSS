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
            raise ValueError(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\"")

        # Selection of the columns regarding the name of the target
        df_target = MaBoSSEvaluator.get_df_target_name(df_target, parsed_query.target_name)

        # Selection of the rows depending of what is looking for
        match parsed_query.type.value:
            case QueryType.P.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_proba(df_target, MaBoSSEvaluator.parsed_query.value)
            case QueryType.T.value:
                filtered_data = MaBoSSEvaluator.get_df_target_value_time(df_target, MaBoSSEvaluator.parsed_query.value)
            case _:
                raise ValueError("Query type is not supported, try P or T")

        return filtered_data


    @staticmethod
    def get_df_target(target):
        if target.value == TargetType.NODE.value:
            print("matched NODE")
            return MaBoSSEvaluator.simulation_results.get_nodes_probtraj()
        elif target.value == TargetType.STATE.value:
            print("matched STATE")
            return MaBoSSEvaluator.simulation_results.get_states_probtraj()
        else:
            print("matched default")
            raise ValueError("Target is not supported, try node or state")


    @staticmethod
    def get_df_target_name(df, target_name):
        if df is None :
            raise ValueError(f"The dataframe is empty for target \"{MaBoSSEvaluator.parsed_query.target}\"")

        for name in target_name:
            if name not in df.columns:
                df.drop(name, axis=1, inplace=True)
                raise Warning(f"Target name \"{name}\" has not been found in the dataframe, removed from the query")

        new_df = pd.DataFrame()

        new_df["Time"] = df["Time"]

        for name in target_name:
            new_df[name] = df[name]

        if new_df.columns.size == 1:
            raise ValueError("The dataframe is empty after dropping the unwanted columns")

        return new_df


    @staticmethod
    def get_df_target_value_proba(df, value):
        op = MaBoSSEvaluator.parsed_query.operator
        new_df = pd.DataFrame()
        for name in df.columns:
            match op:
                case Operators.LT:
                    new_df[name] = df[name] < float(value)
                case Operators.EQ:
                    new_df[name] = df[name] == float(value)
                case Operators.GT:
                    new_df[name] = df[name] > float(value)
                case Operators.LE:
                    new_df[name] = df[name] <= float(value)
                case Operators.GE:
                    new_df[name] = df[name] >= float(value)
                case Operators.NE:
                    new_df[name] = df[name] != float(value)
                case _:
                    raise ValueError("Operator is not supported, try <, <=, =, !=, >=, >")

        new_df = new_df.dropna() # removing all the lines with NaN values because it means all the columns does not respect the condition
        return new_df

    @staticmethod
    def get_df_target_value_time(df, value):

        value = float(value)
        match MaBoSSEvaluator.parsed_query.operator_query:
            case Operators.LT:
                return df[df[df.Time] < value]
            case Operators.EQ:
                return df[df[df.Time] == value]
            case Operators.GT:
                return df[df[df.Time] > value]
            case Operators.LE:
                return df[df[df.Time] <= value]
            case Operators.GE:
                return df[df[df.Time] >= value]
            case Operators.NE:
                return df[df[df.Time] != value]
            case _:
                raise ValueError("Operator is not supported, try <, <=, =, !=, >=, >")