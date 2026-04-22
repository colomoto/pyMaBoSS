import pandas as pd
from maboss.temporal_logic.formulas import Operators
import operator


class Extractor(object):
    OPERATOR_MAP = {
        Operators.LT: operator.lt,  # <
        Operators.LE: operator.le,  # <=
        Operators.GT: operator.gt,  # >
        Operators.GE: operator.ge,  # >=
        Operators.EQ: operator.eq,  # == (ou = dans ton Enum)
        Operators.NE: operator.ne,  # !=
    }

    @staticmethod
    def extract_column(df, column_name, exclusion: bool = False):
        out_df = df[["Time"]].copy()

        for col_name in df.columns:
            if col_name == "Time":
                continue

            if exclusion and column_name not in col_name:
                out_df[col_name] = df[col_name]
            elif not exclusion and column_name in col_name:
                out_df[col_name] = df[col_name]

        return out_df

    @staticmethod
    def extract_column_numerical(df, column_name: str, sim_res, op: Operators, value: float, exclusion: bool = False):
        if sim_res is not None:
            from maboss.temporal_logic.logical_expression_compute import ComputeLogicalExpression
            df_nodes = sim_res.get_nodes_probtraj()
            df_states = sim_res.get_states_probtraj()
            df_name = Extractor.extract_column(df_nodes, column_name)
            df_final = ComputeLogicalExpression.merge_or(df_states, Extractor.extract_column(df_nodes, column_name), df_nodes)
        else:
            raise ValueError("No simulation result provided")

        out_df = pd.DataFrame()
        if exclusion:
            if df_final is None:
                raise ValueError("Something went wrong with the merge of the states and the nodes")
            prob_not_active = 1 - df_final[column_name]
            #keep only the columns that check this : 1 - df_final[column_name] op value
            mask = Extractor.OPERATOR_MAP[op](prob_not_active, value)
            #keep only the rows that check this : df.loc[mask] which only contains values that meets : 1 - df_final[column_name] op value
            out_df = df.loc[mask].copy()
        else:
            cols_match = df.columns[df.columns.str.contains(column_name)]
            mask = Extractor.OPERATOR_MAP[op](df[cols_match], value).any(axis=1)
            out_df = df.loc[mask].copy()

        return out_df
