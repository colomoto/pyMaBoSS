import pandas as pd
from numpy.ma.core import logical_not
from pyparsing import warnings
from scipy.stats import false_discovery_control

import maboss.temporal_logic
from maboss.temporal_logic.custom_exceptions import ErrorInLogicalExpression
from maboss.temporal_logic.extractors import Extractor


class ComputeLogicalExpression:

    @staticmethod
    def compute_logical_expression(logical_expression, simulation_results):

        try:
            ComputeLogicalExpression.check_logical_expression(logical_expression)
        except ErrorInLogicalExpression:
            raise ErrorInLogicalExpression("")

        work_df = pd.DataFrame()
        temp = pd.DataFrame()
        nodes_df = simulation_results.get_nodes_probtraj()
        states_df = simulation_results.get_states_probtraj()
        fusion = True
        name_checker = [False, False] #0: nodes, 1: states
        is_node = False
        is_state = False
        member_name = ''
        logical_no = False

        for member in logical_expression:
            if isinstance(member, list):
                temp = ComputeLogicalExpression.compute_logical_expression(member, simulation_results)
                if fusion:
                    work_df = ComputeLogicalExpression.merge_or(work_df, temp)
                else:
                    work_df = ComputeLogicalExpression.merge_and(work_df, temp, nodes_df)
                temp = pd.DataFrame()
            elif member == '&' or member == '|':
                if member == '&':
                    fusion = False
                else:
                    fusion = True
            else:
                # check if the name exists in at least one of the dfs
                name_checker = ComputeLogicalExpression.check_name_exist(member, nodes_df, states_df)
                if name_checker[0] == False and name_checker[1] == False:
                    raise ErrorInLogicalExpression("Node or state name not found")

                # check if the name is a node or a state
                if str.__contains__(member, 'node:'):
                    is_node = True
                    is_state = False
                    member_name = member[5:]
                elif str.__contains__(member, 'state:'):
                    is_node = False
                    is_state = True
                    member_name = member[6:]
                else:
                    is_node = False
                    is_state = False
                    member_name = member

                print(f"{member_name} loop")

                # Logical no
                logical_no = ComputeLogicalExpression.check_logical_no(member)
                member_name = member_name[1:] if logical_no else member_name
                print(f"Logical no : {logical_no} for {member_name}")
                print(f"is_node : {is_node} is_state : {is_state} for {member_name}")

                if is_node:
                    if name_checker[0]:
                        temp = Extractor.extract_column(nodes_df, member_name, False)
                    else:
                        warnings.warn(f"The name {member_name} has been provided for a node but no node with that name has been found in the dataframe")

                if is_state:
                    if name_checker[1]:
                        temp = Extractor.extract_column(states_df, member_name, logical_no)
                    else:
                        warnings.warn(f"The name {member_name} has been provided for a state but no state with that name has been found in the dataframe")

                if temp.empty:
                    if name_checker[0] and not name_checker[1] and not logical_no: # node
                        temp = Extractor.extract_column(nodes_df, member_name, False)
                    elif not name_checker[0] and name_checker[1]: # state
                        temp = Extractor.extract_column(states_df, member_name, logical_no)
                    else:
                        temp = Extractor.extract_column(nodes_df, member_name, False)
                        print(f"{member_name} : Data temp before merge or:\n {temp}")
                        temp = ComputeLogicalExpression.merge_or(temp, Extractor.extract_column(states_df, member_name, logical_no))

                print(f"{member_name} : Data temp after merge or :\n {temp}")

                if fusion:
                    work_df = ComputeLogicalExpression.merge_or(work_df, temp)
                else:
                    work_df = ComputeLogicalExpression.merge_and(work_df, temp, nodes_df)

                print(f"{member_name} : Data :\n {work_df}")
                temp = pd.DataFrame()
                is_state = False
                is_node = False
                member_name = ''
                logical_no = False

        return work_df

        # todo continue

    @staticmethod
    def parse_logical_expression(logical_expression: list[str]):
        out = []
        it = iter(logical_expression) if isinstance(logical_expression, list) else logical_expression
        for c in it:
            if c == '' or c == ' ':
                continue
            elif c == '(':
                out.append(ComputeLogicalExpression.parse_logical_expression(it))
            else:
                if c == ')':
                    return out
                else:
                    out.append(c)
        return out

    @staticmethod
    def check_logical_no(expression: str):
        if expression.startswith("!"):
            return True
        return False

    @staticmethod
    def check_logical_expression(logical_expression):
        print(logical_expression)
        last_member = logical_expression[-1]
        first_member = logical_expression[0]

        if first_member == '&' or first_member == '|':
            raise ErrorInLogicalExpression("Formula cannot start with '&' or '|', it must start with a node name (V1)")

        if last_member == '&' or last_member == '|':
            raise ErrorInLogicalExpression("Formula cannot end with '&' or '|', it must end with a node name (V1)")

        last_member_is_logical_symb = False
        for m in logical_expression:
            if m == first_member:
                continue
            if isinstance(m, list):
                try:
                    ComputeLogicalExpression.check_logical_expression(m)
                except ErrorInLogicalExpression:
                    raise ErrorInLogicalExpression("")

            if (m == '&' or m == '|') and last_member_is_logical_symb:
                raise ErrorInLogicalExpression("Formula cannot contain two logical symbols in a row")
            elif (m == '&' or m == '|') and not last_member_is_logical_symb:
                last_member_is_logical_symb = True
            elif (m != '&' and m != '|') and not last_member_is_logical_symb:
                raise ErrorInLogicalExpression("Formula cannot contain two nodes in a row")
            else:
                last_member_is_logical_symb = False

    @staticmethod
    def check_name_exist(name: str, nodes_df, states_df):
        out = [False, False]
        if name.startswith("!"):
            new_name = name[1:]
        else:
            new_name = name

        if new_name.startswith('node:'):
            new_name = new_name[5:]
        elif new_name.startswith('state:'):
            new_name = new_name[6:]

        if nodes_df is not None:
            out[0] = new_name in nodes_df.columns
        if states_df is not None:
            for col in states_df.columns:
                if str.__contains__(col, new_name):
                    out[1] = True
                    break
        return out

    @staticmethod
    def merge_or(df1, df2):
        if df1.empty: return df2
        if df2.empty: return df1

        df1['Time'] = df1['Time'].round(5)
        df2['Time'] = df2['Time'].round(5)

        df1_idx = df1.set_index('Time')
        df2_idx = df2.set_index('Time')

        result = df1_idx.combine_first(df2_idx).reset_index()

        return result

    @staticmethod
    def merge_and(df1, df2, nodes_df):
        df1['Time'] = df1['Time'].round(5)
        df2['Time'] = df2['Time'].round(5)

        merged = pd.merge(df1, df2, on='Time', how='inner', suffixes=('', '_dup'))
        node_cols = nodes_df.columns.tolist()

        final_cols = ['Time']
        for col in merged.columns:
            if col.endswith('_dup') or col == 'Time': continue

            # if it is a node: keep
            if col in node_cols: final_cols.append(col)
            elif col in df1.columns and col in df2.columns:
                final_cols.append(col)

        node_cols_present = [c for c in final_cols if c in nodes_df.columns and c != 'Time']
        state_cols_present = [c for c in final_cols if c not in nodes_df.columns and c != 'Time']
        ordered_cols = ['Time'] + sorted(node_cols_present) + sorted(state_cols_present)

        return merged[ordered_cols].copy()
