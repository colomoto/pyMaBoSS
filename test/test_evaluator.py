from unittest import TestCase
import os

from maboss.temporal_logic.evaluator import MaBoSSEvaluator
from maboss.temporal_logic.temporal_parser import *
import pandas as pd
from maboss.temporal_logic import visualiser



QUERY = "P(node:name) <= 0.623"
QUERY_FOUND_BY_NAME = "P(node:AKT1) > 0.623"
QUERY_INTERROGATION = "P(node:AKT1) = ? [ AKT2 | AKT3 ]"

#Generation of a random dataframe
class FakeResult:
    def __init__(self, nodes_df, states_df, fpdf, last_nodes=None, last_states=None):
        self._nodes_df = nodes_df
        self._states_df = states_df
        self._fpdf = fpdf
        self._last_nodes = last_nodes
        self._last_states = last_states

    def get_nodes_probtraj(self):
        return self._nodes_df

    def get_states_probtraj(self):
        return self._states_df

    def get_fptable(self):
        return self._fpdf

    def get_last_nodes_probtraj(self):
        return self._last_nodes

    def get_last_states_probtraj(self):
        return self._last_states

# DO NOT REMOVE ELSE BUGS -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def get_test_path(filename):
    return os.path.join(BASE_DIR, filename)
# -------------------------------------------------
def load_fake_result(nodes_file, states_file, fp_file, last_states_file=None, last_nodes_file=None):
    df_nodes = pd.read_csv(get_test_path(nodes_file))
    df_states = pd.read_csv(get_test_path(states_file))
    df_fp = pd.read_csv(get_test_path(fp_file)) if fp_file else None
    df_last_states = pd.read_csv(get_test_path(last_states_file)) if last_states_file else None
    df_last_nodes = pd.read_csv(get_test_path(last_nodes_file)) if last_nodes_file else None
    return FakeResult(df_nodes, df_states, df_fp, last_states=df_last_states, last_nodes=df_last_nodes)

class TestEvaluator(TestCase):
    # -------------------- TEST WITH PROBAS AND NODES ------------------------------------------
    def test_get_df_target_node(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        fake = [df_nodes,None]
        MaBoSSEvaluator.simulation_results = fake
        df = MaBoSSEvaluator.get_df_target(TargetType.NODE)

        assert df.equals(df_nodes)

    def test_get_df_target_name(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        MaBoSSEvaluator.parsed_query = Formula(QueryType.P,TargetType.NODE,["AKT2"],Operators.GT,'0.5',[],[],[],'P(node:AKT2) > 0.5')
        result = MaBoSSEvaluator.get_df_target_name(df_nodes, ["AKT2"])
        #print(result)
        assert list(result.columns) == ["Time", "AKT2"]

    def test_get_df_target_value_proba(self):
        df = pd.read_csv(get_test_path('test_data.csv'))
        MaBoSSEvaluator.parsed_query = Formula(QueryType.P,TargetType.NODE,["AKT3"],Operators.GT,'0.5',[],[],[],'P(node:AKT3) > 0.5')
        MaBoSSEvaluator.target_name = "AKT3"
        df = df[["Time", "AKT3"]]
        result = MaBoSSEvaluator.get_df_target_value_proba(df, 0.5)
        result.dropna(inplace=True, ignore_index=True)
        expected = pd.read_csv(get_test_path('expected_data_target_value.csv'))
        print(f"Results : \n{result}\n Expected : \n{expected}")
        assert result.equals(expected)

    def test_get_all_columns_name(self):
        df = pd.read_csv(get_test_path('test_data.csv'))
        MaBoSSEvaluator.parsed_query = Formula(QueryType.P,TargetType.NODE,["AKT1","AKT2","AKT3"],Operators.GT,'0.5',[],[], [],'P(node:AKT1,AKT2,AKT3) > 0.5')
        result = MaBoSSEvaluator.get_df_target_name(df, ["AKT1", "AKT2", "AKT3"])
        assert list(result.columns) == ["Time", "AKT1", "AKT2", "AKT3"]

    def test_get_df_name_not_found(self):
        df = pd.read_csv(get_test_path('test_data.csv'))
        MaBoSSEvaluator.parsed_query.target_name = ["AKT4"]
        self.assertRaises(NoNameValidException, MaBoSSEvaluator.get_df_target_name, df, ["AKT4"])

    def test_get_df_full_process_no_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        #print(f"Nodes : \n{df_nodes}")
        #print(f"States : \n{df_states}")
        MaBoSSEvaluator.parsed_query = Parser.parse_query(QUERY_FOUND_BY_NAME)
        result = MaBoSSEvaluator.evaluate_query(Parser.parse_query(QUERY_FOUND_BY_NAME), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [1.0],
            'AKT1' : [0.678],
        })
        print(f"Results: \n{result}")
        print(f"Expected : \n{expected}")
        assert result.equals(expected)

    def test_get_df_full_process_2(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        query = "P(node:AKT1) > 0.3 [ AKT2 | AKT3 ]"
        MaBoSSEvaluator.parsed_query = Parser.parse_query(query)
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query(query), FakeResult(df_nodes, df_states, None))
        res.to_csv("test/test_data_result.csv", index=False)
        expected= pd.DataFrame({
            'Time' : [0.0,1.0],
            'AKT1' : [0.421,0.678],
            'AKT2' : [0.854,0.332],
            'AKT3' : [0.120,0.941],
            'AKT1--AKT2--AKT3': [0.6,0.15],
            'AKT1--AKT3' : [0.07521,0.2],
            'AKT2_state' : [0.00479,0.05],
        })
        print(f"Results: \n{res}")
        print(f"Expected : \n{expected}")
        assert res.equals(expected)

    def test_full_process_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        query = "P(node:AKT1) > 0.3 [ ( AKT2 >= 0.2 ) | AKT3 ]"
        MaBoSSEvaluator.parsed_query = Parser.parse_query(query)
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query(query), FakeResult(df_nodes, df_states, None))
        res.to_csv("test/test_data_result.csv", index=False)
        assert res.equals(pd.DataFrame({
            'Time' : [0.0,1.0],
            'AKT1' : [0.421,0.678],
            'AKT2' : [0.854,0.332],
            'AKT3' : [0.120,0.941],
            'AKT1--AKT2--AKT3': [0.6,0.15],
            'AKT1--AKT3' : [0.07521,0.2],
            'AKT2_state' : [0.00479,0.05],
        }))

    def test_all_columns(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        query = "P(node:*) > 0.2"
        MaBoSSEvaluator.parsed_query = Parser.parse_query(query)
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query(query), FakeResult(df_nodes, df_states, None))
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
        query = "P(state:*) <= 0.4"
        MaBoSSEvaluator.parsed_query = Parser.parse_query(query)
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query(query), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [1.0],
            '<nil>' : [0.4],
            'AKT1--AKT3' : [0.2],
            'AKT1--AKT2--AKT3' : [0.15],
            'AKT2' : [0.05],
        })

        print(f"Results: \n{res}")
        print(f"Expected : \n{expected}")

        assert res.equals(expected)

    def test_all_states_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        query = "P(state:*) <= 0.4 [ AKT1 | AKT2 ]"
        MaBoSSEvaluator.parsed_query = Parser.parse_query(query)
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query(query), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [1.0],
            'AKT1' : [0.678],
            '<nil>' : [0.4],
            'AKT1--AKT2--AKT3': [0.15],
            'AKT1--AKT3' : [0.2],
            'AKT2': [0.332],
            'AKT2_state': [0.05],
        })
        res.to_csv("test/test_data_result.csv", index=False)
        assert res.equals(expected)

    def test_all_states_with_logical_2(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        query = "P(state:*) <= 0.4 [ AKT1 | state:AKT2 ]"
        MaBoSSEvaluator.parsed_query = Parser.parse_query(query)
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query(query), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time': [1.0],
            'AKT1': [0.678],
            '<nil>' : [0.4],
            'AKT1--AKT2--AKT3': [0.15],
            'AKT1--AKT3': [0.2],
            'AKT2': [0.05],
        })
        res.to_csv("test/test_data_result.csv", index=False)
        assert res.equals(expected)

    def test_time_query(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("T(node:AKT1) <= 0.5")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("T(node:AKT1) <= 0.5"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0,2.0],
            'AKT1' : [0.421,0.115],
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_time_query_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("T(node:AKT1) <= 0.5 [ AKT2 | AKT3 ]")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("T(node:AKT1) <= 0.5 [ AKT2 | AKT3 ]"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0,2.0],
            'AKT1' : [0.421,0.115],
            'AKT2': [0.854, 0.567],
            'AKT3' : [0.12,0.443],
            'AKT1--AKT2--AKT3': [0.6,0.11],
            'AKT1--AKT3' : [0.07521,0.11],
            'AKT2_state' : [0.00479,0.11]
        })

        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    # -------------------- TESTS WITH MIN AND MAX ---------------------------------------------
    def test_min_query_node(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Pmin(node:AKT1) > 0.1")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Pmin(node:AKT1) > 0.1"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [2.0],
            'AKT1' : [0.115],
            'AKT2' : [0.567],
            'AKT3' : [0.443],
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_max_query_node(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Pmax(node:AKT1) > 0.1")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Pmax(node:AKT1) > 0.1"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [1.0],
            'AKT1' : [0.678],
            'AKT2' : [0.332],
            'AKT3' : [0.941],
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_min_query_node_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Pmin(node:AKT1) > 0.2 [ AKT2 | AKT3 ]")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Pmin(node:AKT1) > 0.2 [ AKT2 | AKT3 ]"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0],
            'AKT1' : [0.421],
            'AKT2' : [0.854],
            'AKT3' : [0.120],
            'AKT1--AKT2--AKT3': [0.6],
            'AKT1--AKT3' : [0.07521],
            'AKT2_state' : [0.00479]
        })

        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_max_query_node_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Pmax(node:AKT1) < 0.2")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Pmax(node:AKT1) < 0.2 [ AKT2 | AKT3 ]"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [2.0],
            'AKT1' : [0.115],
            'AKT2' : [0.567],
            'AKT3' : [0.443],
            'AKT1--AKT2--AKT3': [0.11],
            'AKT1--AKT3' : [0.11],
            'AKT2_state' : [0.11],
        })

        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_min_query_state_raise_error(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Pmin(state:AKT1) > 0.1")
        self.assertRaises(FormulaException, MaBoSSEvaluator.evaluate_query, Parser.parse_query("Pmin(state:AKT1) > 0.1"), FakeResult(df_nodes, df_states, None))

    def test_max_query_node_raise_error(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Pmax(node:AKT4) > 0.1")
        self.assertRaises(FormulaException, MaBoSSEvaluator.evaluate_query, Parser.parse_query("Pmax(node:AKT4) > 0.1"), FakeResult(df_nodes, df_states, None))

    def test_min_state_query(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Pmin(state:AKT2) < 0.1")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Pmin(state:AKT2) < 0.1"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0],
            '<nil>' : [0.32],
            'AKT1--AKT3': [0.07521],
            'AKT1--AKT2--AKT3': [0.6],
            'AKT2' : [0.00479],
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_max_state_query(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Pmax(state:AKT2) > 0.004")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Pmax(state:AKT2) > 0.004"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [2.0],
            '<nil>' : [0.67],
            'AKT1--AKT3': [0.11],
            'AKT1--AKT2--AKT3': [0.11],
            'AKT2' : [0.11],
        })

        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)


    def test_max_state_query_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Pmax(state:AKT2) > 0.004 [ !AKT1 | AKT3 ]")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Pmax(state:AKT2) > 0.004 [ !AKT1 | AKT3 ]"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [2.0],
            'AKT3' : [0.443],
            '<nil>' : [0.67],
            'AKT1--AKT2--AKT3': [0.11],
            'AKT1--AKT3':[0.11],
            'AKT2' : [0.11],
        })

        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_time_min_query(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Tmin(node:AKT1) > 0.4")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Tmin(node:AKT1) > 0.4"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0,1.0],
            'AKT1' : [0.421,0.678],
            'AKT2' : [0.854,0.332],
            'AKT3' : [0.120,0.941],
        })

        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_time_min_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Tmin(node:AKT1) > 0.4 [ AKT2 | AKT3 ]")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Tmin(node:AKT1) > 0.4 [ AKT2 | AKT3 ]"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0,1.0],
            'AKT1' : [0.421,0.678],
            'AKT2' : [0.854,0.332],
            'AKT3' : [0.120,0.941],
            'AKT1--AKT2--AKT3': [0.6,0.15],
            'AKT1--AKT3' : [0.07521,0.2],
            'AKT2_state' : [0.00479,0.05],
        })

        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_time_max_query(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Tmax(node:AKT1) > 0.4")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Tmax(node:AKT1) > 0.4"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0,1.0],
            'AKT1' : [0.421,0.678],
            'AKT2' : [0.854,0.332],
            'AKT3' : [0.120,0.941],
        })
        assert res.equals(expected)

    def test_time_min_state(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Tmin(state:AKT2) < 0.1")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Tmin(state:AKT2) < 0.1"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0,1.0],
            '<nil>' : [0.32,0.4],
            'AKT1--AKT3': [0.07521,0.2],
            'AKT1--AKT2--AKT3': [0.6,.15],
            'AKT2' : [0.00479,0.05],
        })
        assert res.equals(expected)

    def test_time_min_state_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("Tmin(state:AKT2) < 0.1 [ !AKT1 | AKT3 ]")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("Tmin(state:AKT2) < 0.1 [ !AKT1 | AKT3 ]"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0,1.0],
            'AKT3' : [0.120,0.941],
            '<nil>' : [0.32,0.40],
            'AKT1--AKT2--AKT3': [0.60,0.15],
            'AKT1--AKT3': [0.07521, 0.2],
            'AKT2' : [0.00479,0.05],
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

# ----------------------------------------------- TESTS INTERROGATION --------------------------------------------------
    def test_interrogation(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query(QUERY_INTERROGATION)
        res = MaBoSSEvaluator.get_df_target_value_proba(df_nodes,'?', QueryType.P)
        expected = pd.DataFrame({ #this is only out of one step, not the whole computing
            'Time' : [0.0,1.0,2.0],
            'AKT1' : [0.421,0.678,0.115],
        })
        #print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)
        print("assert 1 success")

        log_df = ComputeLogicalExpression.compute_logical_expression(
            Parser.parse_query(QUERY_INTERROGATION).logical_equation,
            [df_nodes,df_states]
        )

        final_data = ComputeLogicalExpression.merge_or(res,
                                                       log_df,
                                                       df_nodes,
                                                       (df_states.rename(columns={c: f"{c}_state" for c in df_states.columns if c != 'Time'})),
                                                       True)

        final_data = MaBoSSEvaluator.remove_double_columns(final_data)

        #print(f"Results : \n{final_data}\n")
        assert final_data.equals(pd.DataFrame({
            'Time' : [0.0,1.0,2.0],
            'AKT1' : [0.421,0.678,0.115],
            'AKT2' : [0.854,0.332,0.567],
            'AKT3' : [0.120,0.941,0.443],
            'AKT1--AKT2--AKT3': [0.6,0.15,0.11],
            'AKT1--AKT3' : [0.07521,0.2,0.11],
            'AKT2_state' : [0.00479,0.05,0.11],
        }))
        print("assert 2 success")

        # Computation for the probas
        computed_res = MaBoSSEvaluator.compute_interrogation_proba(final_data, MaBoSSEvaluator.parsed_query, df_nodes, df_states)
        print(f"Results : \n{computed_res}\n")

        assert computed_res.round(5).equals(pd.DataFrame({
            'Time' : [0.0,1.0,2.0],
            'P(AKT1)' : [0.67521,0.35,0.22],
        }).round(5))
        print("assert 3 success")


    def test_interrogation_multiple_nodes(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        query = "P(node:AKT1,AKT2) = ? [ AKT1 & AKT3 ]"
        MaBoSSEvaluator.parsed_query = Parser.parse_query(query)
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query(query), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0,1.0,2.0],
            'P(AKT1)' : [0.67521,0.35,0.22],
            'P(AKT2)' : [0.60479,0.20,0.22],
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.round(5).equals(expected.round(5))

    def test_interrogation_state(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("P(state:AKT2) = ? [ AKT1 & AKT3 ]")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("P(state:AKT2) = ? [ AKT1 & AKT3 ]"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [0.0,1.0,2.0],
            'P(AKT2)' : [0.00479,0.05,0.11]
        })
        print(f"Results :\n{res}\n Expected : \n{expected}")
        assert res.round(5).equals(expected.round(5))

    def test_interrogation_state_with_logical_value(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("P(state:AKT2) = ? [ AKT1 & ( AKT3 >= 0.2 ) ]")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("P(state:AKT2) = ? [ AKT1 & ( AKT3 >= 0.2 ) ]"), FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [1.0,2.0],
            'P(AKT2)' : [0.05,0.11], # only AKT2_state as it exists
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.round(5).equals(expected.round(5))

    def test_interrogation_multiple_state_with_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("P(state:AKT2,AKT1--AKT3) = ? [ ( node:AKT1 < 0.2 ) ]")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("P(state:AKT2,AKT1--AKT3) = ? [ ( node:AKT1 < 0.2 ) ]"), FakeResult(df_nodes,df_states,None))
        expected = pd.DataFrame({
            'Time' : [2.0],
            'P(AKT2)' : [0.11],
            'P(AKT1--AKT3)' : [0.11],
        })
        res.to_csv('test/result_multiple_state_with_logical.csv')
        print(f"Result:\n{res}\nExpected:\n{expected}\n")
        assert res.equals(expected)

    def test_interrogation_multiple_node_with_num_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        query = "P(node:AKT1,AKT2) = ? [ ( node:AKT1 > 0.5 ) & AKT3 ]"
        MaBoSSEvaluator.parsed_query = Parser.parse_query(query)
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query(query),FakeResult(df_nodes,df_states,None))
        expected = pd.DataFrame({
            'Time' : [1.0],
            'P(AKT1)' : [0.35],
            'P(AKT2)' : [0.2],
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)


    def test_node_with_state_in_logical(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("P(node:AKT1,AKT3) = ? [ state:AKT2 < 0.1 ]")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("P(node:AKT1,AKT3) = ? [ state:AKT2 < 0.1 ]"), FakeResult(df_nodes,df_states,None))
        expected = pd.DataFrame({
            'Time' : [0.0,1.0],
            #sum of the probas of the states where AKT1 and AKT3 are in
            'P(AKT1)' : [0.67521,0.35],
            'P(AKT3)' : [0.67521,0.35],
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_query_state(self):
        df_nodes = pd.read_csv(get_test_path('test_data.csv'))
        df_states = pd.read_csv(get_test_path('test_data_states.csv'))
        MaBoSSEvaluator.parsed_query = Parser.parse_query("P(state:AKT1--AKT3) > 0.1")
        res = MaBoSSEvaluator.evaluate_query(Parser.parse_query("P(state:AKT1--AKT3) > 0.1"), FakeResult(df_nodes,df_states,None))
        print(f"Result:\n {res}\n")
        res.viz.evolution_over_time()

    def test_mutation_to_string(self):
        mutation_constraints = ["AKT1","ON"]
        res = MaBoSSEvaluator.mutation_to_string(mutation_constraint=mutation_constraints)
        expected = "AKT1 ON"
        assert res == expected


# ------------------------------------------ MUTATION RELATED TESTS -----------------------------------------------
    def test_increase_true(self):
        master_results = load_fake_result('test_data.csv', 'test_data_states.csv', 'test_data_fp_master.csv', 'test_data_last_states_master.csv', 'test_data_last_nodes_master.csv')
        mutant_results = load_fake_result('test_data_mut.csv', 'test_data_states_mut.csv', 'test_data_fp_mut.csv', 'test_data_last_states_mutation.csv', 'test_data_last_nodes_mutation.csv')

        query = "Inc(state:<nil>) / [ ] [ AKT1:ON ]"
        res = MaBoSSEvaluator.evaluate_increase_decrease(Parser.parse_query(query), mutant_results, master_results)

        expected = pd.DataFrame({
            "<nil> from master" : [0.3384],
            "<nil> from mutation" : [0.6],
            "Difference <nil>" : [0.2616],
            "Percentage <nil>" : ["77.30%"],
            "Increase <nil>" : [True],
        })
        res.to_csv('test/result_increase_true.csv')
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.round(5).equals(expected.round(5))

    def test_increase_false_decrease(self):
        master_results = load_fake_result('test_data.csv', 'test_data_states.csv', 'test_data_fp_master.csv', 'test_data_last_states_master.csv', 'test_data_last_nodes_master.csv')
        mutant_results = load_fake_result('test_data_mut.csv', 'test_data_states_mut.csv', 'test_data_fp_mut.csv', 'test_data_last_states_mutation.csv', 'test_data_last_nodes_mutation.csv')

        query = "Inc(state:AKT1--AKT3) / [ ] [ AKT1:OFF ]"
        res = MaBoSSEvaluator.evaluate_increase_decrease(Parser.parse_query(query), mutant_results, master_results)
        expected = pd.DataFrame({
            'AKT1--AKT3 from master' : [0.0568],
            'AKT1--AKT3 from mutation' : [0.0048],
            'Difference AKT1--AKT3' : [-0.052],
            'Percentage AKT1--AKT3' : ["-91.55%"],
            'Increase AKT1--AKT3' : [False],
        })
        res.to_csv('test/result_increase_false.csv')
        assert res.equals(expected)

    def test_increase_false_equality(self):
        master_results = load_fake_result('test_data.csv', 'test_data_states.csv', 'test_data_fp_master.csv', 'test_data_last_states_master.csv', 'test_data_last_nodes_master.csv')

        query = "Inc(state:AKT2) / [ ] [ AKT1:ON ]"
        #using master results twice just for testing equality logic
        res = MaBoSSEvaluator.evaluate_increase_decrease(Parser.parse_query(query), master_results, master_results)
        expected = pd.DataFrame({
            'AKT2 from master' : [0.0048],
            'AKT2 from mutation' : [0.0048],
            'Difference AKT2' : [0.0],
            'Percentage AKT2' : ["0.00%"],
            'Increase AKT2' : [False],
        })
        res.to_csv('test/result_increase_false_equality.csv')
        assert res.equals(expected)

    def test_decrease_true(self):
        master_results = load_fake_result('test_data.csv', 'test_data_states.csv', 'test_data_fp_master.csv', 'test_data_last_states_master.csv', 'test_data_last_nodes_master.csv')
        mutant_results = load_fake_result('test_data_mut.csv', 'test_data_states_mut.csv', 'test_data_fp_mut.csv', 'test_data_last_states_mutation.csv', 'test_data_last_nodes_mutation.csv')

        query = "Dec(state:AKT1--AKT2--AKT3) / [ ] [ AKT1:ON ]"
        res = MaBoSSEvaluator.evaluate_increase_decrease(Parser.parse_query(query), mutant_results, master_results)
        expected = pd.DataFrame({
            'AKT1--AKT2--AKT3 from master' : [0.6],
            'AKT1--AKT2--AKT3 from mutation' : [0.3384],
            'Difference AKT1--AKT2--AKT3' : [-0.2616],
            'Percentage AKT1--AKT2--AKT3' : ["-43.60%"],
            'Decrease AKT1--AKT2--AKT3' : [True],
        })
        res.to_csv('test/result_decrease_true.csv')
        assert res.round(5).equals(expected.round(5))

    def test_decrease_false_increase(self):
        master_results = load_fake_result('test_data.csv', 'test_data_states.csv', 'test_data_fp_master.csv', 'test_data_last_states_master.csv', 'test_data_last_nodes_master.csv')
        mutant_results = load_fake_result('test_data_mut.csv', 'test_data_states_mut.csv', 'test_data_fp_mut.csv', 'test_data_last_states_mutation.csv', 'test_data_last_nodes_mutation.csv')

        query = "Dec(state:<nil>) / [ ] [ AKT1:ON ]"
        res = MaBoSSEvaluator.evaluate_increase_decrease(Parser.parse_query(query), mutant_results, master_results)

        expected = pd.DataFrame({
            "<nil> from master": [0.3384],
            "<nil> from mutation": [0.6],
            "Difference <nil>": [0.2616],
            "Percentage <nil>": ["77.30%"],
            "Decrease <nil>": [False],
        })

        print(f"Results : \n{res}\n Expected : \n{expected}")
        res.to_csv('test/result_decrease_false.csv')
        assert res.round(5).equals(expected.round(5))

    def test_decrease_false_equality(self):
        master_results = load_fake_result('test_data.csv', 'test_data_states.csv', 'test_data_fp_master.csv', 'test_data_last_states_master.csv', 'test_data_last_nodes_master.csv')

        query = "Dec(state:AKT1--AKT2--AKT3) / [ ] [ AKT1:OFF ]"
        #same results twice to test the equality logic
        res = MaBoSSEvaluator.evaluate_increase_decrease(Parser.parse_query(query), master_results, master_results)
        expected = pd.DataFrame({
            "AKT1--AKT2--AKT3 from master": [0.6],
            "AKT1--AKT2--AKT3 from mutation": [0.6],
            "Difference AKT1--AKT2--AKT3": [0.0],
            "Percentage AKT1--AKT2--AKT3": ["0.00%"],
            "Decrease AKT1--AKT2--AKT3": [False],
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)


    def test_node_decrease_false(self):
        master_results = load_fake_result('test_data.csv', 'test_data_states.csv', 'test_data_fp_master.csv', 'test_data_last_states_master.csv', 'test_data_last_nodes_master.csv')
        mutant_results = load_fake_result('test_data_mut.csv', 'test_data_states_mut.csv', 'test_data_fp_mut.csv', 'test_data_last_states_mutation.csv', 'test_data_last_nodes_mutation.csv')

        query = "Dec(node:AKT1) / [ ] [ AKT1:ON ]"
        res = MaBoSSEvaluator.evaluate_increase_decrease(Parser.parse_query(query), mutant_results, master_results)

        expected = pd.DataFrame({
            'AKT1 from master': [0.001],
            'AKT1 from mutation': [0.0345],
            'Difference AKT1' : [0.0335],
            'Percentage AKT1': ["3350.00%"],
            'Decrease AKT1' : [False]
        })
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.round(5).equals(expected.round(5))

    def test_last_state_inc_dec_with_logical(self):
        master_results = load_fake_result('test_data.csv', 'test_data_states.csv', 'test_data_fp_master.csv', 'test_data_last_states_master.csv', 'test_data_last_nodes_master.csv')
        mutant_results = load_fake_result('test_data_mut.csv', 'test_data_states_mut.csv', 'test_data_fp_mut.csv', 'test_data_last_states_mutation.csv', 'test_data_last_nodes_mutation.csv')

        query = "Inc(fp:AKT1) / 2 [ AKT2 & AKT3 ] [ AKT1:ON ]"
        res = MaBoSSEvaluator.evaluate_increase_decrease(Parser.parse_query(query), mutant_results, master_results, 2)
        expected = pd.DataFrame({
            'P(AKT1) cumul from master' : [0.19],
            'P(AKT1) cumul from mutation' : [0.81],
            'Difference AKT1' : [0.62],
            'Percentage AKT1' : ["326.32%"],
            'Increase AKT1' : [True]
        })
        print(f"Res:\n {res}")
        res.to_csv('test/result_last_state_inc_dec_with_logical.csv')
        assert res.equals(expected)

    def test_last_state_inc_dec_with_single_node_state(self):
        master_results = load_fake_result('test_data.csv', 'test_data_states.csv', 'test_data_fp_master.csv',
                                          'test_data_last_states_master.csv', 'test_data_last_nodes_master.csv')
        mutant_results = load_fake_result('test_data_mut.csv', 'test_data_states_mut.csv', 'test_data_fp_mut.csv',
                                          'test_data_last_states_mutation.csv', 'test_data_last_nodes_mutation.csv')

        query = Parser.parse_query("Inc(fp:AKT2) / 2 [ ] [ AKT1:ON ]")
        res = MaBoSSEvaluator.evaluate_increase_decrease(query, mutant_results, master_results, 2)
        expected = pd.DataFrame({
            'AKT2 state from master' : [0.81],
            'AKT2 state from mutation' : [0.19],
            'Difference state AKT2' : [-0.62],
            'Percentage state AKT2' : ["-76.54%"],
            'Increase AKT2 state' : [False],
            'P(AKT2) cumul from master' : [1.0], #may happen for node active in all states
            'P(AKT2) cumul from mutation' : [1.0],
            'Difference AKT2' : [0.0],
            'Percentage AKT2' : ["0.00%"],
            'Increase AKT2' : [False]
        })
        res.to_csv('test/result_last_state_inc_dec_with_single_node_state.csv')
        assert res.equals(expected)