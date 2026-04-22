from unittest import TestCase
import os
from maboss.temporal_logic.evaluator import MaBoSSEvaluator
from maboss.temporal_logic.formulas import *
from maboss.temporal_logic.custom_exceptions import *
from maboss.temporal_logic.temporal_parser import *
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

class TestEvaluator(TestCase):
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
        #print(result)
        assert list(result.columns) == ["Time", "AKT2"]

    def test_get_df_target_value(self):
        df = pd.read_csv(get_test_path('test_data.csv'))
        MaBoSSEvaluator.operator_query = Operators.GT
        MaBoSSEvaluator.target_name = "AKT3"
        df = df[["Time", "AKT3"]]
        result = MaBoSSEvaluator.get_df_target_value_proba(df, 0.5)
        expected = pd.read_csv(get_test_path('expected_data_target_value.csv'))
        #print(result)
        #print(expected)
        assert result.reset_index(drop=True).equals(expected)

    def test_get_all_columns_name(self):
        df = pd.read_csv(get_test_path('test_data.csv'))
        result = MaBoSSEvaluator.get_df_target_name(df, ["AKT1", "AKT2", "AKT3"])
        assert list(result.columns) == ["Time", "AKT1", "AKT2", "AKT3"]

    def test_get_df_name_not_found(self):
        df = pd.read_csv(get_test_path('test_data.csv'))
        self.assertRaises(NoNameValidException, MaBoSSEvaluator.get_df_target_name, df, ["AKT4"])

    def test_get_df_full_process_no_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        #print(f"Nodes : \n{df_nodes}")
        #print(f"States : \n{df_states}")
        result = MaBoSSEvaluator.querying(QUERY_FOUND_BY_NAME, FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [1.0],
            'AKT1' : [0.678],
        })
        #print(f"Results: \n{result}")
        #print(f"Expected : \n{expected}")
        assert result.equals(expected)

    def test_get_df_full_process_2(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        res = MaBoSSEvaluator.querying("P(node:AKT1) > 0.3 [ AKT2 | AKT3 ]", FakeResult(df_nodes, df_states, None))
        res.to_csv("test/test_data_result.csv", index=False)
        expected= pd.DataFrame({

        })
        #print(f"Results: \n{res}")
        #print(f"Expected : \n{expected}")
        #assert res.equals(expected)

    def test_full_process_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        res = MaBoSSEvaluator.querying("P(node:AKT1) > 0.3 [ ( AKT2 >= 0.2 ) | AKT3 ]", FakeResult(df_nodes, df_states, None))
        res.to_csv("test/test_data_result.csv", index=False)

    def test_all_columns(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        res = MaBoSSEvaluator.querying("P(node:*) > 0.2", FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [1.0],
            'AKT1' : [0.678],
            'AKT2' : [0.332],
            'AKT3' : [0.941],
        })
        #print(f"Results: \n{res}")
        assert res.equals(expected)

    def test_all_states(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        res = MaBoSSEvaluator.querying("P(state:*) <= 0.4", FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [1.0],
            '<nil>' : [0.4],
            'AKT1 -- AKT3' : [0.2],
            'AKT1 -- AKT2 -- AKT3' : [0.15],
            'AKT2' : [0.05],
        })

        assert res.equals(expected)

    def test_all_states_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        res = MaBoSSEvaluator.querying("P(state:*) <= 0.4 [ AKT1 | AKT2 ]", FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [1.0],
            'AKT1' : [0.678],
            'AKT2' : [0.332],
            '<nil>' : [0.4],
            'AKT1--AKT2--AKT3': [0.15],
            'AKT1--AKT3' : [0.2],
            'AKT2_state': [0.05],
        })
        res.to_csv("test/test_data_result.csv", index=False)
        assert res.equals(expected)

    def test_all_states_with_logical_2(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        res = MaBoSSEvaluator.querying("P(state:*) <= 0.4 [ AKT1 | state:AKT2 ]", FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time': [1.0],
            'AKT1': [0.678],
            'AKT2': [0.05],
            '<nil>': [0.4],
            'AKT1--AKT2--AKT3': [0.15],
            'AKT1--AKT3': [0.2],
        })
        res.to_csv("test/test_data_result.csv", index=False)
        assert res.equals(expected)

    def test_time_query(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        res = MaBoSSEvaluator.querying("T(node:AKT1) > 1.0", FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [2.0],
            'AKT1' : [0.115],
        })

        assert res.equals(expected)

    def test_time_query_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        res = MaBoSSEvaluator.querying("T(node:AKT1) >= 1.0 [ AKT2 | AKT3 ]", FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [1.0,2.0],
            'AKT1' : [0.678,0.115],
            'AKT2' : [0.332,0.567],
            'AKT3' : [0.941,0.443],
            'AKT1--AKT2--AKT3': [0.15,0.11],
            'AKT1--AKT3' : [0.2,0.11],
            'AKT2_state' : [0.05,0.11]
        })

        assert res.equals(expected)