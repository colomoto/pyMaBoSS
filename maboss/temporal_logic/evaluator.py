import operator

from maboss.temporal_logic.formulas import TargetType
from maboss.temporal_logic.temporal_parser import Parser
from maboss.temporal_logic.formulas import Operators, QueryType

class MaBoSSEvaluator:
    OPERATIONS = {
        Operators.LT: operator.lt,  # <
        Operators.LE: operator.le,  # <=
        Operators.EQ: operator.eq,  # = or ==
        Operators.NE: operator.ne,  # !=
        Operators.GE: operator.ge,  # >=
        Operators.GT: operator.gt,  # >
    }

    simulation_results = None
    query_input = None
    query_type = None
    target = None
    target_name = None
    operator_query = None
    value = None

    @staticmethod
    def help(): # todo little manual
        return True

    @staticmethod
    def querying(query,results): # maybe pass the results as an array to compute more than one simulation
        if query == "" or query is None:
            raise ValueError("Query is empty")
        if results is None:
            raise ValueError("Results are empty")

        simulation_results = results
        query_input = query

        # Decomposition of the query
        parsed_query = Parser.parse_query(query_input)
        MaBoSSEvaluator.query_type = parsed_query.type #todo differentiate between Pmax and Pmin, P and S
        MaBoSSEvaluator.target = parsed_query.target
        MaBoSSEvaluator.target_name = parsed_query.target_name
        MaBoSSEvaluator.operator_query = parsed_query.operator
        MaBoSSEvaluator.value = parsed_query.value

        #Selection of the df to use depending of the target
        df_target = MaBoSSEvaluator.get_df_target(MaBoSSEvaluator.target)

        # Selection of the columns regarding the name of the target
        df_target = MaBoSSEvaluator.get_df_target_name(df_target, MaBoSSEvaluator.target_name)

        #Comparing the value to the value passed by the query
        filtered_data = MaBoSSEvaluator.get_df_target_value(df_target, MaBoSSEvaluator.value)

        return filtered_data



    @staticmethod
    def get_df_target(target):
        match target:
            case TargetType.NODE:
                return MaBoSSEvaluator.simulation_results.get_nodes_probtraj()
            case TargetType.STATE:
                return MaBoSSEvaluator.simulation_results.get_states_probtraj()
            case TargetType.TRAJ:
                return MaBoSSEvaluator.simulation_results.get_trajectories_probtraj()
            case _:
                raise ValueError("Target is not supported, try node, state or traj")

    @staticmethod
    def get_df_target_name(df, target_name):
        if df is None:
            raise ValueError(f"The dataframe is empty for target \"{MaBoSSEvaluator.target}\"")
        if target_name in df.columns:
            return df[[target_name]]
        else:
            raise ValueError(f"Target name \"{target_name}\" has not been found in the dataframe")

    @staticmethod
    def get_df_target_value(df, value):
        if df is None:
            raise ValueError(f"The dataframe is empty for target \"{MaBoSSEvaluator.target}\" with name \"{MaBoSSEvaluator.target_name}")
        match MaBoSSEvaluator.operator_query:
            case Operators.LT:
                return df[df[MaBoSSEvaluator.target_name] < value]
            case Operators.EQ:
                return df[df[MaBoSSEvaluator.target_name] == value]
            case Operators.GT:
                return df[df[MaBoSSEvaluator.target_name] > value]
            case Operators.LE:
                return df[df[MaBoSSEvaluator.target_name] <= value]
            case Operators.GE:
                return df[df[MaBoSSEvaluator.target_name] >= value]
            case Operators.NE:
                return df[df[MaBoSSEvaluator.target_name] != value]
            case _:
                raise ValueError("Operator is not supported, try <, <=, =, !=, >=, >")

            # todo continue


    @staticmethod
    def evaluate():

        # todo : implement the evaluation of the query
        # 1. Extract the right data to treat (formula.target)
        # 2. Extract the value of the query (formula.value)
        # 3. Extract the operator (formula.operator)
        # 4. Compare the value of the query with the value of the right data
        # 5. Compute the result of this query


        return True


