import pandas as pd
from joblib.memory import extract_first_line

from maboss.temporal_logic.formulas import Operators
import operator


class Extractor(object):
    """
    A class that extracts the columns or lines that are needed to compute the formula.
    """
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
        """
        Extract a column depending on its name and whether it is an exclusion or not.
        :param df: the df to modify
        :param column_name:
        :param exclusion: if true, the column is excluded thus not added to the final df
        :param is_state: the name of the column is related to a state
        :return: a dataframe with the column that was extracted
        """
        cols_to_keep = ["Time"]
        #print(f"column_name : {column_name}, is_state : {is_state}, exclusion : {exclusion}")

        for col_name in df.columns:
            #print(f"col_name : {col_name}")
            if col_name == "Time": continue

            if not is_state:
                if exclusion and column_name not in col_name:
                    cols_to_keep.append(col_name)
                elif not exclusion and column_name in col_name:
                    cols_to_keep.append(col_name)
            else:
                clean_col_name = col_name.replace(" ", "").replace("_state", "")
                if (clean_col_name == column_name and not exclusion) or (clean_col_name != column_name and exclusion):
                    cols_to_keep.append(col_name)

        return df[cols_to_keep]

    @staticmethod
    def extract_column_last_states(df: pd.DataFrame, node_name: str, exclusion=False):
        """
        Extracts a column from a dataframe that contains the last step of the simulation so all the states and all the nodes
        :param df: the dataframe to modify
        :param node_name: the node name to extract. If the node is in a state name, column is kept (if exclusion is False) or excluded (if exclusion is True)
        :param exclusion: if true, the column is excluded thus not added to the final df
        :return: the dataframe with the column that was extracted
        """
        cols_to_keep = []
        if exclusion: node_name = node_name.replace("!", "")
        for col_name in df.columns:
            list_nodes = col_name.replace(" ","").split("--")
            if node_name in list_nodes and not exclusion:
                cols_to_keep.append(col_name)
            elif node_name not in list_nodes and exclusion:
                cols_to_keep.append(col_name)

        #print(f"(extractors) cols_to_keep :\n {df[cols_to_keep].copy()}")
        return df[cols_to_keep]


    @staticmethod
    def extract_column_numerical(df, column_name: str, sim_res, op: Operators, value: float, exclusion: bool = False, is_state: bool = False):
        """
        extract from a column, the rows that meet the condition
        :param df:
        :param column_name:
        :param sim_res: the results of the simulation (for comparison purpose)
        :param op: the operator to use
        :param value: the value to compare (float between 0 and 1)
        :param exclusion: if the column is excluded or not
        :param is_state: the column is related to a state
        :return: a dataframe containing the rows that meet the condition on the column
        """
        print("Entering extract_column_numerical")
        #print(f"df : \n {df}\n")
        #print("col name:", column_name)
        #print(f"is_state : {is_state}")
        if sim_res is not None:
            df_nodes = sim_res[0]
            df_states = sim_res[1]
            #print(f"df_states : {df_states}")
            if is_state:
                clean_col_name = column_name.replace(" ", "").replace("_state", "")
                #print(f"clean_col_name : {clean_col_name}")
                df_name = Extractor.extract_column(df_states, clean_col_name, is_state=True)
                #print(f"df_name : {df_name}")
            else:
                df_name = Extractor.extract_column(df_nodes, column_name)
            #print(f"df_name : {df_name}")

        if is_state: column_name = column_name+"_state"

        #print(f"column_name : {column_name}, op : {op}, value : {value}, exclusion : {exclusion}")

        if exclusion:
            prob_not_active = 1 - df_name[column_name]
            #keep only the columns that check this: 1 - df_final[column_name] op value
            mask = Extractor.OPERATOR_MAP[op](prob_not_active, value)
            #keep only the rows that check this: df.loc[mask] which only contains values that meets : 1 - df_final[column_name] op value
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

    @staticmethod
    def extract_lines(fp_df, exclusion: bool, name: str):
        """
        extract a line from the fixpoint dataframe containing the name of the node or state
        :param fp_df: fixpoint dataframe where the model does not evolve anymore
        :param exclusion: the line to extract is the one that is excluded
        :param name: the name of the state that we want to extract
        :return: a dataframe containing the line that was extracted
        """
        if exclusion:
            return fp_df[fp_df[name] == 0].reset_index(drop=True)
        else:
            return fp_df[fp_df[name] == 1].reset_index(drop=True)