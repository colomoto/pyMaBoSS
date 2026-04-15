from maboss.temporal_logic.temporal_parser import *
from maboss.temporal_logic.formulas import *
from unittest import TestCase

QUERY = "P(node:name) > 0.623"

class TestParser(TestCase):
    def test_parse(self):
        assert parse(QUERY).type == QueryType.P
        assert parse(QUERY).target == TargetType.NODE
        assert parse(QUERY).operator == Operators.GT
        assert parse(QUERY).value == 0.623
        assert parse(QUERY).target_name == "name"
