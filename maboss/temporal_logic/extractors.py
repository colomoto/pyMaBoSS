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
    def extract_column_numerical(df, column_name: str, op: Operators, value: float):
        mask = Extractor.OPERATOR_MAP[op](df[column_name], value)
        out_df = df.loc[mask].copy()
        return out_df
