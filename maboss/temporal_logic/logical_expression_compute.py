from numpy.ma.core import isarray

import maboss.temporal_logic
from maboss.temporal_logic.custom_exceptions import ErrorInLogicalExpression


class ComputeLogicalExpression:

    @staticmethod
    def compute_logical_expression(logical_expression, simulation_results):
        pass

    @staticmethod
    def identify_members(logical_expression):
        pass

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
            if isinstance(m,list):
                try:
                    ComputeLogicalExpression.check_logical_expression(m)
                except ErrorInLogicalExpression:
                    raise ErrorInLogicalExpression("")

            if (m == '&' or m == '|') and last_member_is_logical_symb:
                raise ErrorInLogicalExpression("Formula cannot contain two logical symbols in a row")
            elif (m== '&' or m == '|') and not last_member_is_logical_symb:
                last_member_is_logical_symb = True
            elif (m!='&' and m!='|') and not last_member_is_logical_symb:
                raise ErrorInLogicalExpression("Formula cannot contain two nodes in a row")
            else:
                last_member_is_logical_symb = False







