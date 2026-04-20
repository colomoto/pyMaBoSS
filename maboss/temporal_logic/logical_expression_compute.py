import pandas as pd
from pyparsing import warnings

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
        nodes_df = simulation_results.get_nodes_probtraj()
        states_df = simulation_results.get_states_probtraj()
        fusion = True
        name_checker = [False, False] #0: nodes, 1: states

        for member in logical_expression:
            if isinstance(member, list):
                temp = ComputeLogicalExpression.compute_logical_expression(member, simulation_results)
                if fusion:  # |
                    # merge the two dataframes, order by time, drop duplicates
                    work_df = ComputeLogicalExpression.merge_or(work_df, temp)
                else:  # &
                    work_df = ComputeLogicalExpression.merge_and(work_df, temp, nodes_df)
                temp = pd.DataFrame()
                continue
            if member == '&' or member == '|':
                match member:
                    case '&':
                        fusion = False
                    case '|':
                        fusion = True
                    case _:
                        raise ValueError(
                            ("A non expected value passed in the member check in compute_logical_expression : ",
                             member))
                continue
            else:
                if str.__contains__(member, 'node:'):
                    if not ComputeLogicalExpression.check_name_exists_simple(member, nodes_df):
                        name_checker = [True, False]
                        continue

                elif str.__contains__(member, 'state:'):
                    if not ComputeLogicalExpression.check_name_exists_simple(member, states_df):
                        name_checker = [False, True]
                        continue
                else:
                    name_checker = ComputeLogicalExpression.check_name_exist(member, nodes_df, states_df)

                print(f"{member} is {name_checker}")

                if not name_checker[0] and not name_checker[1]:
                    warnings.warn(
                        f"The name {member} does not exist in the nodes nor in the states dataframe, it will be ignored")
                    continue

                if name_checker[0] and not name_checker[1]:
                    temp = Extractor.extract_column(nodes_df, member, ComputeLogicalExpression.check_logical_no(member))
                elif not name_checker[0] and name_checker[1]:
                    temp = Extractor.extract_column(states_df, member, ComputeLogicalExpression.check_logical_no(member))
                else:
                    temp = Extractor.extract_column(nodes_df, member, ComputeLogicalExpression.check_logical_no(member))
                    temp = ComputeLogicalExpression.merge_or(temp, Extractor.extract_column(states_df, member, ComputeLogicalExpression.check_logical_no(member)))
                    #print(f"{member} :\n {temp}")

                if fusion:
                    work_df = ComputeLogicalExpression.merge_or(work_df, temp)
                else:
                    work_df = ComputeLogicalExpression.merge_and(work_df, temp, nodes_df)
                temp = pd.DataFrame()
                #print(f"{member} :\n {work_df}")

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
        if nodes_df is not None:
            out[0] = name in nodes_df.columns
        if states_df is not None:
            for col in states_df.columns:
                if str.__contains__(col, name):
                    out[1] = True
                    break
        return out

    @staticmethod
    def check_name_exists_simple(name: str, df):
        return name in df.columns

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
