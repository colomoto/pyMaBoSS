import pandas as pd
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
        out_df = pd.DataFrame()
        nodes_df = simulation_results.get_nodes_probtraj()
        states_df = simulation_results.get_states_probtraj()
        logical_no_applying = False
        temp_df = pd.DataFrame()
        fusion = True

        for m in logical_expression:
            if isinstance(m, list):
                pass
                # fusion de workdf avec le return de compute_logical_expression
                # work_df = ComputeLogicalExpression.compute_logical_expression(m, simulation_results)
            elif m == '&' or m == '|':
                match m:
                    case '&':
                        fusion = False
                    case '|':
                        fusion = True
                    case _:
                        raise ValueError(
                            "Logical operator is not supported, try & or |. ! is supported without space between it and the node or state to apply to")
            else:
                logical_no_applying = ComputeLogicalExpression.check_logical_no(m)
                Extractor.extract_column(states_df, m, logical_no_applying)

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
