import operator
import temporal_parser
from formulas import Operators, QueryType


class MaBoSSEvaluator:
    OPERATIONS = {
        Operators.LT: operator.lt,  # <
        Operators.LE: operator.le,  # <=
        Operators.EQ: operator.eq,  # = or ==
        Operators.NE: operator.ne,  # !=
        Operators.GE: operator.ge,  # >=
        Operators.GT: operator.gt,  # >
    }

    @staticmethod
    def help(): # todo little manual
        return True

    @staticmethod
    def querying(query,results):
        if query == "" or query is None:
            raise ValueError("Query is empty")
        if results is None:
            raise ValueError("Results are empty")

        #todo continue

    @staticmethod
    def compare(left, right, operator):
        return MaBoSSEvaluator.OPERATIONS[operator](left, right) # left of the operator is P or S and right is the value

    @staticmethod
    def extract_values(result, formula):
        """
        Extract the value of the formula to compare
        with the result and the result value also extracted
        :param result:
        :param formula:
        :return: the float needed to be compared
        """
        formula_value = temporal_parser.parse(formula).value

        #todo extraction of the value of the result

        return [result, formula_value]

    @staticmethod
    def evaluate(result, formula):
        """
        Compare the query with the result of the simulation
        :param query: the assertion to be evaluated
        :param state: the state
        :return: boolean
        """
        extracted_values = MaBoSSEvaluator.extract_values(result, formula)

        # todo : implement the evaluation of the query
        # get all the probas of the states
        # compare the state with the query
        return True


