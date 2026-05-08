"""
Class to compute the logical expression. Returns dataframes containing the columns needed
accordingly to the logical expression.

Author: Oscar Dufossez
Date: 2026-04
"""

import pandas as pd
import operator
from pandas import Series as series

from pyparsing import warnings
from maboss.temporal_logic.formulas import Operators
from maboss.temporal_logic.custom_exceptions import ErrorInLogicalExpression
from maboss.temporal_logic.extractors import Extractor


class ComputeLogicalExpression:
    OPERATOR_MAP = {
        Operators.LT: operator.lt,  # <
        Operators.LE: operator.le,  # <=
        Operators.GT: operator.gt,  # >
        Operators.GE: operator.ge,  # >=
        Operators.EQ: operator.eq,  # == (or =)
        Operators.NE: operator.ne,  # !=
    }

    @staticmethod
    def compute_logical_expression(logical_expression, simulation_results):
        """
        Main function for the data retrieving logic. Treat each member of the logical expression and merge the results.
        Check if the name exists in the dataframes, handles notation 'node:name' and 'state:name'
        :param logical_expression: the logical expression to be evaluated
        :param simulation_results: the results of the simulation
        :return: a dataframe containing the results of the logical expression that will be later used to compute the final result
        """

        try:
            ComputeLogicalExpression.check_logical_expression(logical_expression)
        except ErrorInLogicalExpression:
            raise ErrorInLogicalExpression("")

        work_df = pd.DataFrame()
        temp = pd.DataFrame()
        nodes_df = simulation_results[0]
        states_df = simulation_results[1]
        fusion = True
        op = operator.gt
        name_checker = [False, False] #0: nodes, 1: states
        is_node = False
        is_state = False
        member_name = ''
        logical_no = False
        is_number = False
        value = 0.0

        if states_df is not None:
            states_df = states_df.rename(columns={c: f"{c}_state" for c in states_df.columns if c != 'Time'})

        for member in logical_expression:
            #print(f"\nMember : {member} ----------------------------------------")
            if isinstance(member, list):
                temp = ComputeLogicalExpression.compute_logical_expression(member, simulation_results)
                if fusion:
                    work_df = ComputeLogicalExpression.merge_or(work_df, temp,nodes_df, states_df)
                else:
                    work_df = ComputeLogicalExpression.merge_and(work_df, temp, nodes_df, states_df)
                temp = pd.DataFrame()
            elif ComputeLogicalExpression.is_any_symb_check(member):
                match member:
                    case '&':
                        fusion = False
                    case '|':
                        fusion = True
                    case _: op = Operators(member)
            else:
                try:
                    value = float(member)
                    is_number = True
                except ValueError:
                    is_number = False

                #print(f"Is number: {is_number} and value: {value}")

                if is_number:
                    if value > 1.0 or value < 0.0:
                        raise ErrorInLogicalExpression("The value of the logical expression must be between 0 and 1")
                    #print(f"work_df before extract column numerical : \n {work_df} \n ")
                    work_df = Extractor.extract_column_numerical(work_df, member_name, simulation_results, op, value, logical_no, is_state=is_state )
                    #print(f"Numerical value : {member} , work_df : \n {work_df} \n")
                    return work_df
                else:
                    # check if the name exists in at least one of the dfs
                    name_checker = ComputeLogicalExpression.check_name_exist(member, nodes_df, states_df)
                    if name_checker[0] == False and name_checker[1] == False:
                        raise ErrorInLogicalExpression(f"Node or state name not found : {member}")

                    # check if the name is a node or a state
                    if str.__contains__(member, 'node:'):
                        is_node = True
                        is_state = False
                        member_name = member[5:]
                    elif str.__contains__(member, 'state:'):
                        #print("AKT2 must be here")
                        is_node = False
                        is_state = True
                        member_name = member[6:]
                    else:
                        is_node = False
                        is_state = False
                        member_name = member

                    #print(f"{member_name} loop")

                    # Logical no
                    logical_no = ComputeLogicalExpression.check_logical_no(member)
                    member_name = member_name[1:] if logical_no else member_name
                    #print(f"Logical no : {logical_no} for {member_name}")
                    #print(f"is_node : {is_node} is_state : {is_state} for {member_name}")

                    # if it is indicated what the name is, extract the column from the dataframe, else looks in both df
                    if is_node:
                        if name_checker[0]:
                            temp = Extractor.extract_column(nodes_df, member_name, False)
                        else:
                            warnings.warn(f"The name {member_name} has been provided for a node but no node with that "
                                          f"name has been found in the dataframe")

                    if is_state:
                        if name_checker[1]:

                            temp = Extractor.extract_column(states_df, member_name, logical_no, is_state=True)
                            #print(f"State temp : {temp}")
                        else:
                            warnings.warn(f"The name {member_name} has been provided for a state but no state with that "
                                          f"name has been found in the dataframe")

                    #print(f"{member_name} : Data temp before merge and :\n {temp}\n Data work before merge fusion: {fusion} :\n {work_df} \n")

                    if temp.empty:
                        if name_checker[0] and not name_checker[1] and not logical_no: # node only getting the column if is activated
                            temp = Extractor.extract_column(nodes_df, member_name, False)
                        elif not name_checker[0] and name_checker[1]: # state
                            temp = Extractor.extract_column(states_df, member_name, logical_no, is_state=True)
                        else:
                            if not logical_no: # same here, only getting the column if activated (!name does not get the column)
                                temp = Extractor.extract_column(nodes_df, member_name, False)
                            #print(f"{member_name} : Data temp before merge or:\n {temp}")
                            temp = ComputeLogicalExpression.merge_or(temp, Extractor.extract_column(states_df,
                                                                                                    member_name,
                                                                                                    logical_no),
                                                                     nodes_df, states_df,True)

                    if fusion:
                        work_df = ComputeLogicalExpression.merge_or(work_df, temp, nodes_df, states_df)
                    else:
                        work_df = ComputeLogicalExpression.merge_and(work_df, temp, nodes_df, states_df)

                    #print(f"{member_name}: Data :\n {work_df}")

                    temp = pd.DataFrame()

        work_df.dropna(inplace=True, ignore_index=True)
        #print(f"Logical expression: {logical_expression} \n Result: \n {work_df} \n")
        return work_df

    @staticmethod
    def compute_logical_fixpoint(logical_expression, df_in):
        #todo tester
        fusion = True
        work_df = pd.DataFrame()
        try:
            ComputeLogicalExpression.check_logical_exp_fixpoint(logical_expression)
        except ErrorInLogicalExpression:
            raise ErrorInLogicalExpression("")

        for m in logical_expression:
            if isinstance(m, list):
                temp = ComputeLogicalExpression.compute_logical_fixpoint(m, df_in)
                if fusion:
                    work_df = ComputeLogicalExpression.merge_or_on_lines(work_df,temp)
                else:
                    work_df = ComputeLogicalExpression.merge_and_on_lines(work_df,temp)
                temp = pd.DataFrame()
            elif ComputeLogicalExpression.is_logical_symb(m):
                if m== '&':
                    fusion=False
                elif m== '|':
                    fusion=True
                else:
                    raise ValueError("Logical symb must be '&' or '|'")
            else:
                try:
                    ComputeLogicalExpression.check_name_in_fp(m, df_in)
                except ValueError:
                    raise ErrorInLogicalExpression(f"Node or state name not found : {m}")

                logical_no = ComputeLogicalExpression.check_logical_no(m)
                temp = Extractor.extract_lines(df_in, logical_no, m)

                if fusion:
                    work_df = ComputeLogicalExpression.merge_or_on_lines(work_df,temp)
                else:
                    work_df = ComputeLogicalExpression.merge_and_on_lines(work_df,temp)
                temp = pd.DataFrame()

        return work_df

    @staticmethod
    def parse_logical_expression(logical_expression: list[str]):
        """
        Parse the logical expression as lists so the inner expressions are kept together. Removes the (,) and the spaces.
        Intrications are possible on more than 2 levels of nesting. (e.g.: A & ( ( B | C ) & D ). SPACES ARE OBLIGATORY
        SO THE PARSING IS CORRECTLY DONE !!!!
        It is called in the TemporalParser class.
        :param logical_expression: the logical expression to be parsed, it can be a sub expression of the main expression, the
        function is blind to this.
        :return: a list of strings with possible sub lists of strings.
        """
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
        """
        If the expression starts with a '!', it is a logical no.
        :param expression: a name of the expression, for example, 'A' or '!B'
        :return: True if the name starts with ! else False
        """
        if expression.startswith("!"):
            return True
        return False

    @staticmethod
    def check_logical_expression(logical_expression):
        """
        Checks if the logical expression is valid. It is not a complete check, it only checks the syntax.
        Checks for the following:
        - Two symbols in a row
        - Two nodes in a row
        - Two states in a row
        - Expression starts or ends with a logical symbol
        It raises an ErrorInLogicalExpression if the expression is not valid and the computing stops
        It uses a recursion logic to check the inner expressions, thus why the try except
        NB: It does NOT check for the good parenthesis. It is checked elsewhere
        :param logical_expression: the expression to be verified
        :return: nothing, only raises an error if an error occurs
        """
        #print(logical_expression)
        last_member = logical_expression[-1]
        first_member = logical_expression[0]

        if first_member == last_member: return

        if ComputeLogicalExpression.is_any_symb_check(first_member) :
            raise ErrorInLogicalExpression("Formula cannot start with '&', '|' or value comparator symbol, it must start with a node or state name (V1)")

        if ComputeLogicalExpression.is_any_symb_check(last_member):
            raise ErrorInLogicalExpression("Formula cannot end with '&' or '|' or value comparator symbol, it must end with a node or state name (V1)")

        last_member_is_logical_symb = False
        for m in logical_expression:
            if m == first_member:
                continue
            if isinstance(m, list):
                try:
                    ComputeLogicalExpression.check_logical_expression(m)
                except ErrorInLogicalExpression:
                    raise ErrorInLogicalExpression("")

            if ComputeLogicalExpression.is_any_symb_check(m) and last_member_is_logical_symb:
                raise ErrorInLogicalExpression("Formula cannot contain two logical symbols in a row")
            elif ComputeLogicalExpression.is_any_symb_check(m) and not last_member_is_logical_symb:
                last_member_is_logical_symb = True
            elif not ComputeLogicalExpression.is_any_symb_check(m) and not last_member_is_logical_symb:
                raise ErrorInLogicalExpression("Formula cannot contain two nodes in a row")
            else:
                last_member_is_logical_symb = False

    @staticmethod
    def is_any_symb_check(symb: str):
        """
        Check if the provided symbol is a logical symbol like '&' or '|'
        Handles all numerical operators (e.g., <, >, =, ==, =, <=, >=)
        Basically, it replaces an if of the form : if(symb == '&' or symb == '|' or ...)
        :param symb a symbol to be checked
        :return: return True if the symbol is a logical symbol, False otherwise
        """
        return symb == '&' or symb == '|' or symb == '>' or symb == '<' or symb == '=' or symb == '!=' or symb == '>=' or symb == '<=' or symb == '=='

    @staticmethod
    def is_logical_symb(symb: str):
        return symb == '&' or symb == '|'

    @staticmethod
    def check_name_exist(name: str, nodes_df, states_df):
        """
        Checks if the provided name exists in the dataframes.
        There are three possible checks :
        - The name is indicated as a node (node: name), only checks in :param nodes_df
        :param name: the name to be checked
        :param nodes_df: the nodes dataframe used for the computing
        :param states_df: the states dataframe used for the computing
        :return: a list of two booleans, the first one indicates if the name is present in the nodes, the second one if it is present in the states
        """
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
    def merge_or(df1, df2, nodes_df, state_df, keep_times_df1 = False):
        """
        Merge two dataframes on the time column following an OR logic. Meaning it keeps the values of both the df without
        causing doubling.
        The end of the function sorts the df by column types (nodes or state) then by alphabetical order
        :param keep_times_df1:
        :param state_df:
        :param df1:
        :param df2:
        :param nodes_df: the nodes dataframe used for the computing coming from the simulation results
        :return: a dataframe containing the results of the logical expression that will be later used to compute the final result
        """
        if df1.empty: return df2
        if df2.empty: return df1

        # round up the times to 5 decimals to avoid doubles and to avoid the possibility of having the same time in two df
        # with a little variation like: 1.5678912 and 1.5678913
        df1['Time'] = df1['Time'].round(5)
        df2['Time'] = df2['Time'].round(5)

        df1 = df1.rename(columns=lambda x: "".join(x.split()))
        df2 = df2.rename(columns=lambda x: "".join(x.split()))

        df1_idx = df1.set_index('Time')
        df2_idx = df2.set_index('Time')

        result = df1_idx.combine_first(df2_idx).reset_index()

        if keep_times_df1:
            result = result[result['Time'].isin(df1['Time'])] #if true, filter to keep only the times of df1 important for tmin and tmax

        # sorts by column types (nodes or state) then by alphabetical order
        if nodes_df is not None:
            node_cols = []
            state_cols = []

            for c in result.columns:
                if c=='Time':continue

                is_node = ComputeLogicalExpression.check_if_node(c, result[c], nodes_df, state_df)

                if is_node: node_cols.append(c)
                else: state_cols.append(c)

            ordered_cols = ['Time'] + sorted(node_cols) + sorted(state_cols)
            result = result[ordered_cols]

        return result

    @staticmethod
    def merge_and(df1, df2, nodes_df, state_df):
        """
        Merges the two dataframes on the time column following an AND logic. Meaning it keeps only the common values
        of both the df.
        Ends by sorting the columns by column types (nodes or state) then by alphabetical order
        :param state_df:
        :param df1:
        :param df2:
        :param nodes_df: the nodes dataframe used for the computing coming from the simulation results,
        used to determine which columns to keep and which columns are from nodes and which are from states
        :return: a dataframe result of the logical expression that will be later used to compute the final result
        """
        df1['Time'] = df1['Time'].round(5)
        df2['Time'] = df2['Time'].round(5)

        # Removes the spaces
        df1 = df1.rename(columns=lambda x: "".join(x.split()))
        df2 = df2.rename(columns=lambda x: "".join(x.split()))

        # Merge with suffixes to handle different data on the same column name
        merged = pd.merge(df1, df2, on='Time', how='inner', suffixes=('_df1', '_df2'))

        # to identify the columns to keep, nodes are all kept, states only if they are in both dfs
        node_cols = []
        state_cols = []

        # A list of all the columns present in df1 and df2
        all_source_cols = set(df1.columns).union(set(df2.columns))
        all_source_cols.remove('Time')

        for col in all_source_cols:
            #identify from where the column comes
            m_name = col
            if col + '_df1' in merged.columns:
                m_name = col + '_df1'

            # is the name a column node or column state ?
            is_node = ComputeLogicalExpression.check_if_node(col, merged[m_name], nodes_df, state_df)

            if is_node:
                if col not in node_cols:
                    node_cols.append(col)
                    merged = merged.rename(columns={m_name: col})
            else:
                # AND logic, the state must be in both df
                if col in df1.columns and col in df2.columns:
                    if col not in state_cols:
                        state_cols.append(col)
                        merged = merged.rename(columns={m_name: col})

        # Sort the columns by type (nodes or states) and alphabetically
        ordered_cols = ['Time'] + sorted(node_cols) + sorted(state_cols)
        res = merged[ordered_cols].copy()

        # Returns the result without touching the _state suffixes here
        return res.loc[:, ~res.columns.duplicated()].copy()

    @staticmethod
    def check_if_node(name: str, col, nodes_df, state_df):
        if name.endswith('_state'): return False

        in_nodes = nodes_df is not None and name in nodes_df.columns

        state_ref = None
        if state_df is not None:
            if name in state_df.columns:
                state_ref = name
            elif f"{name}_state" in state_df.columns:
                state_ref = f"{name}_state"

        in_states = state_ref is not None

        if in_nodes and in_states:
            try:
                act_val = float(col.dropna().iloc[0])
                node_ref_val = float(nodes_df[name].dropna().iloc[0])
                state_ref_val = float(state_df[state_ref].dropna().iloc[0])

                if abs(act_val - node_ref_val) < abs(act_val - state_ref_val): return True
                return False
            except Exception:
                return True
        return in_nodes

    @staticmethod
    def check_logical_exp_fixpoint(logical_expression):
        last_member = logical_expression[-1]
        first_member = logical_expression[0]

        if first_member == last_member: return

        if ComputeLogicalExpression.is_any_symb_check(first_member):
            raise ErrorInLogicalExpression(
                "Formula cannot start with '&', '|' it must start with a node or state name (V1)")

        if ComputeLogicalExpression.is_any_symb_check(last_member):
            raise ErrorInLogicalExpression(
                "Formula cannot end with '&' or '|', it must end with a node or state name (V1)")

        last_member_is_logical_symb = False
        for m in logical_expression:
            if m == first_member:
                continue
            if isinstance(m, list):
                try:
                    ComputeLogicalExpression.check_logical_expression(m)
                except ErrorInLogicalExpression:
                    raise ErrorInLogicalExpression("")

            if ComputeLogicalExpression.is_any_symb_check(m) and last_member_is_logical_symb:
                raise ErrorInLogicalExpression("Formula cannot contain two logical symbols in a row")
            elif ComputeLogicalExpression.is_any_symb_check(m) and not last_member_is_logical_symb:
                if not ComputeLogicalExpression.is_logical_symb(m):
                    raise ErrorInLogicalExpression("Query type Inc and Dec do not handle comparator value")
                last_member_is_logical_symb = True
            elif not ComputeLogicalExpression.is_any_symb_check(m) and not last_member_is_logical_symb:
                raise ErrorInLogicalExpression("Formula cannot contain two nodes in a row")
            else:
                last_member_is_logical_symb = False

    @staticmethod
    def merge_or_on_lines(df1,df2):
        if df1.empty: return df2
        if df2.empty: return df1

        df_out = pd.concat([df1,df2])
        df_out = df_out.drop_duplicates(ignore_index=True).dropna(ignore_index=True)

        return df_out

    @staticmethod
    def merge_and_on_lines(df1,df2):
        df_out = pd.merge(df1,df2, how="inner")
        return df_out

    @staticmethod
    def check_name_in_fp(name: str, fixpoint_df):
        if name.startswith("!"):
            name = name[1:]

        if "State" not in fixpoint_df.columns:
            raise ValueError("The fixpoint dataframe does not have a State column.")

        if name not in fixpoint_df["State"].values:
            raise ValueError(f"The name {name} is not in the fixpoint dataframe.")