from maboss.temporal_logic.logical_expression_compute import ComputeLogicalExpression
from maboss.temporal_logic.temporal_parser import *
from maboss.temporal_logic.formulas import *
from maboss.temporal_logic.custom_exceptions import *
from unittest import TestCase
import os
import pandas as pd

QUERY_LOGICAL_SIMPLE = "A & B | !C"
EXPECTED_LOGICAL_SIMPLE = ['A', '&', 'B', '|', '!C']

QUERY_LOGICAL_ONE_INTRICATE = "A & B | ( C & D )"
EXPECTED_LOGICAL_ONE_INTRICATE = ['A', '&', 'B', '|', ['C', '&', 'D']]

QUERY_LOGICAL_MULTIPLE_INTRICATE = "A & ( B | ( C & D ) )"
EXPECTED_LOGICAL_MULTIPLE_INTRICATE = ['A', '&', ['B', '|', ['C', '&', 'D']]]

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def get_test_path(filename):
    return os.path.join(BASE_DIR, filename)

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

    def test_handling_non_opening_parenthesis(self):
        pass # todo

    def test_check_name_exist(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        NAME = 'AKT1'
        out = ComputeLogicalExpression.check_name_exist(NAME, df_nodes, df_states)
        assert out[0] == True and out[1] == True

    def test_check_name_exist_not_exist(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        NAME = 'AKT4'
        out = ComputeLogicalExpression.check_name_exist(NAME, df_nodes, df_states)
        assert out[0] == False and out[1] == False

    def test_check_name_with_no(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        NAME = '!AKT1'
        out = ComputeLogicalExpression.check_name_exist(NAME, df_nodes, df_states)
        assert out[0] == True and out[1] == True

    def test_check_logical_no(self):
        LOGICAL = '!AKT1'
        assert ComputeLogicalExpression.check_logical_no(LOGICAL) == True

    def test_merge_or(self):
        df1 = pd.DataFrame({
            'Time': [0.4, 0.5, 0.6, 0.7],
            'A': [True, True, True, True],
            'B': [False, False, True, True],
            'C': [False, True, False, True]
        })

        df2 = pd.DataFrame({
            'Time': [0.2, 0.6],
            'A': [False, True],
            'B': [True, True],
            'C': [False, False]
        })

        merged = ComputeLogicalExpression.merge_or(df1, df2)
        print("\n", merged)

    def test_merge_and(self):
        df1 = pd.DataFrame({
            'Time': [0.4, 0.5, 0.6, 0.7],
            'A': [True, True, True, True],
            'B': [False, False, True, True],
            'C': [False, True, False, True]
        })

        df2 = pd.DataFrame({
            'Time': [0.2, 0.6],
            'A': [False, True],
            'B': [True, True],
            'C': [False, False]
        })

        nodes_df = pd.DataFrame(columns=['A', 'B', 'C'])
        merged = ComputeLogicalExpression.merge_and(df1, df2, nodes_df)

        self.assertEqual(len(merged), 1, "Devrait avoir une seule ligne (0.6)")

        print("\n", merged)

    def test_compute_logical_expression_return_df(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.read_csv(get_test_path("expected_compute_data.csv"))
        fake = FakeResult(df_nodes, df_states, None)
        results = ComputeLogicalExpression.compute_logical_expression(['AKT1','&','AKT2'], fake)
        print(f"Résultats : \n{results}")
        assert results.equals(expected)

    def test_compute_with_no(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 , 2.0],
            'AKT1' : [0.421,0.678,0.115],
            'AKT1 -- AKT3' : [0.07521 ,0.2,0.11],
        })
        fake = FakeResult(df_nodes, df_states, None)
        results = ComputeLogicalExpression.compute_logical_expression(['AKT1', '&', '!AKT2'], fake)
        print(f"Résultats : \n{results}")
        #assert results.equals(expected)