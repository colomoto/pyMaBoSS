from maboss.temporal_logic.evaluator import MaBoSSEvaluator
from maboss.temporal_logic.temporal_parser import *
from maboss.temporal_logic.formulas import *
from maboss.results.probtrajresult import ProbTrajResult
from maboss.results.statdistresult import StatDistResult
from unittest import TestCase
from unittest.mock import patch
import pandas as pd
import numpy as np

#Generation of a random dataframe
class FakeResult:
    def __init__(self, nodes_df, states_df, traj_df):
        self._nodes_df = nodes_df
        self._states_df = states_df
        self._traj_df = traj_df

    def get_nodes_probtraj(self):
        return self._nodes_df

    def get_states_probtraj(self):
        return self._states_df

    def get_probtraj(self):
        return self._traj_df

QUERY = "P(node:name) > 0.623"
QUERY_FOUND_BY_NAME = "P(node:AKT1) > 0.623"

class TestParser(TestCase):
    def test_parse(self):
        assert Parser.parse_query(QUERY).type == QueryType.P
        assert Parser.parse_query(QUERY).target == TargetType.NODE
        assert Parser.parse_query(QUERY).operator == Operators.GT
        assert Parser.parse_query(QUERY).value == 0.623
        assert Parser.parse_query(QUERY).target_name == "name"

    def test_get_df_target_node(self):
        df_nodes = pd.DataFrame({"name": ["AKT1", "AKT2", "AKT3"], "P(AKT1)": [0.1, 0.2, 0.3]})
        fake = FakeResult(df_nodes,None,None)

        MaBoSSEvaluator.simulation_results = fake
        df = MaBoSSEvaluator.get_df_target(TargetType.NODE)

        assert df.equals(df_nodes)

    def test_get_df_target_name(self):
        df = pd.DataFrame({"A": [0.1, 0.7], "B": [0.9, 0.3]})
        result = MaBoSSEvaluator.get_df_target_name(df, "A")

        assert list(result.columns) == ["A"]

    def test_get_df_target_value(self):
        df = pd.DataFrame({"A": [0.1, 0.7, 0.5]})

        MaBoSSEvaluator.operator_query = Operators.GT
        MaBoSSEvaluator.target_name = "A"

        result = MaBoSSEvaluator.get_df_target_value(df, 0.5)

        expected = pd.DataFrame({"A": [0.7]})
        assert result.reset_index(drop=True).equals(expected)

