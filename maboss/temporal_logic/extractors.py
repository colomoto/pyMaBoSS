import pandas as pd
from joblib.memory import extract_first_line

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
    def extract_column(df, column_name, exclusion: bool = False, is_state: bool = False):
        out_df = df[["Time"]].copy()
        print(f"column_name : {column_name} , df columns : {df.columns}")

        if not is_state:
            for col_name in df.columns:
                if col_name == "Time":
                    continue

                if exclusion and column_name not in col_name:
                    out_df[col_name] = df[col_name]
                elif not exclusion and column_name in col_name:
                    out_df[col_name] = df[col_name]
        else:
            for col_name in df.columns:
                if col_name == "Time":
                    continue
                clean_col_name = col_name.replace(" ", "").replace("_state", "")
                if (clean_col_name == column_name and not exclusion) or (clean_col_name != column_name and exclusion):
                    out_df[col_name] = df[col_name]

        return out_df

    @staticmethod
    def extract_column_numerical(df, column_name: str, sim_res, op: Operators, value: float, exclusion: bool = False, is_state: bool = False):
        #print("Entering extract_column_numerical")
        #print(f"df : \n {df}\n")
        if sim_res is not None:
            df_nodes = sim_res.get_nodes_probtraj()
            df_states = sim_res.get_states_probtraj()
            df_states = df_states.replace(" ","").replace("_state","")
            if is_state:
                clean_col_name = column_name.replace(" ", "").replace("_state", "")
                #print(f"clean_col_name : {clean_col_name}")
                df_name = Extractor.extract_column(df_states, clean_col_name, is_state=True)
            else:
                df_name = Extractor.extract_column(df_nodes, column_name)
            #print(f"df_name : {df_name}")

        else:
            raise ValueError("No simulation result provided")

        out_df = pd.DataFrame()
        if exclusion:
            prob_not_active = 1 - df_name[column_name]
            #keep only the columns that check this : 1 - df_final[column_name] op value
            mask = Extractor.OPERATOR_MAP[op](prob_not_active, value)
            #keep only the rows that check this : df.loc[mask] which only contains values that meets : 1 - df_final[column_name] op value
            out_df = df_name.loc[mask].copy()
            #print(f"out_df : {out_df}")
        else:
            mask = Extractor.OPERATOR_MAP[op](df_name[column_name], value)
            out_df = df_name.loc[mask].copy()
            #print(f"out_df : {out_df}")

        final_df = out_df[["Time", column_name]].reset_index(drop=True).copy()
        res_df = df[df['Time'].isin(final_df['Time'])].reset_index(drop=True).copy()
        #print("Exiting extract_column_numerical")
        return res_df
