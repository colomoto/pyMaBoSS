from maboss.temporal_logic.logical_expression_compute import ComputeLogicalExpression
from maboss.temporal_logic.temporal_parser import *
from maboss.temporal_logic.formulas import *
from maboss.temporal_logic.custom_exceptions import *
from unittest import TestCase


QUERY_LOGICAL_SIMPLE = "A & B | !C"
EXPECTED_LOGICAL_SIMPLE = ['A', '&', 'B', '|', '!C']

QUERY_LOGICAL_ONE_INTRICATE = "A & B | ( C & D )"
EXPECTED_LOGICAL_ONE_INTRICATE = ['A', '&', 'B', '|', ['C', '&', 'D']]

QUERY_LOGICAL_MULTIPLE_INTRICATE = "A & ( B | ( C & D ) )"
EXPECTED_LOGICAL_MULTIPLE_INTRICATE = ['A', '&', ['B', '|', ['C', '&', 'D']]]

class TestLogicalCompute(TestCase):
    def test_compute_logical_expression(self):
        parsed_logical = [n.strip() for n in QUERY_LOGICAL_SIMPLE.split(" ")]
        res = ComputeLogicalExpression.parse_logical_expression(parsed_logical)
        assert res == EXPECTED_LOGICAL_SIMPLE

    def test_compute_logical_expression_one_intricate(self):
        parsed_logical = [n.strip() for n in QUERY_LOGICAL_ONE_INTRICATE.split(" ")]
        res = ComputeLogicalExpression.parse_logical_expression(parsed_logical)
        assert res == EXPECTED_LOGICAL_ONE_INTRICATE

    def test_compute_logical_expression_multiple_intricate(self):
        parsed_logical = [n.strip() for n in QUERY_LOGICAL_MULTIPLE_INTRICATE.split(" ")]
        res = ComputeLogicalExpression.parse_logical_expression(parsed_logical)
        assert res == EXPECTED_LOGICAL_MULTIPLE_INTRICATE

    def test_handling_non_closing_parenthesis(self):
        parsed_logical = [n.strip() for n in "A & ( B | ( C & D )".split(" ")]
        res = ComputeLogicalExpression.parse_logical_expression(parsed_logical)
        assert res == ['A', '&', ['B', '|', ['C', '&', 'D']]]