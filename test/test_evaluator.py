import unittest
import os
from maboss.temporal_logic.evaluator import MaBoSSEvaluator
from maboss.temporal_logic.formulas import *
from maboss.temporal_logic.custom_exceptions import *
from maboss.temporal_logic.temporal_parser import *
from maboss import result
import pandas as pd


QUERY = "P(node:name) <= 0.623"
QUERY_FOUND_BY_NAME = "P(node:AKT1) > 0.623"

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

# DO NOT REMOVE ELSE BUGS -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def get_test_path(filename):
    return os.path.join(BASE_DIR, filename)
# -------------------------------------------------

class EvaluatorTest(unittest.TestCase):
    # -------------------- TEST WITH PROBAS AND NODES ------------------------------------------
    def test_get_df_target_node(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        fake = FakeResult(df_nodes, None, None)
        MaBoSSEvaluator.simulation_results = fake
        df = MaBoSSEvaluator.get_df_target(TargetType.NODE)

        assert df.equals(df_nodes)

    def test_get_df_target_name(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        result = MaBoSSEvaluator.get_df_target_name(df_nodes, ["AKT2"])
        print(result)
        assert list(result.columns) == ["Time", "AKT2"]

    def test_get_df_target_value(self):
        df = pd.read_csv(get_test_path('test_data.csv'))
        MaBoSSEvaluator.operator_query = Operators.GT
        MaBoSSEvaluator.target_name = "AKT3"
        df = df[["Time", "AKT3"]]
        result = MaBoSSEvaluator.get_df_target_value_proba(df, 0.5)
        expected = pd.read_csv(get_test_path('expected_data_target_value.csv'))
        print(result)
        print(expected)
        assert result.reset_index(drop=True).equals(expected)

    def test_get_all_columns_name(self):
        df = pd.read_csv(get_test_path('test_data.csv'))
        result = MaBoSSEvaluator.get_df_target_name(df, ["AKT1", "AKT2", "AKT3"])
        assert list(result.columns) == ["Time", "AKT1", "AKT2", "AKT3"]

    def test_get_df_name_not_found(self):
        df = pd.read_csv(get_test_path('test_data.csv'))
        self.assertRaises(NoNameValidException, MaBoSSEvaluator.get_df_target_name, df, ["AKT4"])

    def test_get_df_full_process(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        result = MaBoSSEvaluator.querying(QUERY_FOUND_BY_NAME, FakeResult(df_nodes, None, None))
        expected = pd.read_csv(get_test_path('expected_data_full_process.csv'))
        print(result)
        print(expected)
        assert result.reset_index(drop=True).equals(expected)


if __name__ == '__main__':
    unittest.main()
