import unittest
import pandas as pd
import os

from sklearn.inspection import permutation_importance

from maboss.temporal_logic.extractors import Extractor
from maboss.temporal_logic.formulas import Operators, LogicalOperators
from maboss.temporal_logic.logical_expression_compute import ComputeLogicalExpression
from test.test_compute_logical import FakeResult


def get_test_data_path():
    return os.path.join(os.path.dirname(__file__), "test_data.csv")

def get_expected_data_path(name= "expected_result_extractor.csv"):
    return os.path.join(os.path.dirname(__file__),name )

class TestExtractor(unittest.TestCase):
    def test_extract_column(self):
        df = pd.read_csv(get_test_data_path())
        expected = pd.read_csv(get_expected_data_path())

        df = Extractor.extract_column(df, "AKT1")
        assert expected.equals(df)

    def test_extract_column_exclusion(self):
        df = pd.read_csv(get_test_data_path())
        expected = pd.read_csv(get_expected_data_path("expected_extractor_exclusion_data.csv"))
        print(expected)
        df = Extractor.extract_column(df, "AKT1", True)
        print(df)
        assert expected.equals(df)

    def test_extract_column_state_exclusion(self):
        df = pd.read_csv(get_expected_data_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 , 2.0],
            '<nil>' : [0.32,0.4,0.67],
            'AKT1 -- AKT3' : [0.07521 ,0.2,0.11]
        })
        df = Extractor.extract_column(df, "AKT2", True)
        print("\n",df)
        assert expected.equals(df)

    def test_extract_row_with_numerical_value(self):
        df_nodes = pd.read_csv(get_expected_data_path("test_data.csv"))
        df_states = pd.read_csv(get_expected_data_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0],
            'AKT1':[0.421,0.678],
        })

        # AKT1 > 0.4
        df_akt1 = pd.DataFrame({
            'Time': [0.0, 1.0, 2.0],
            'AKT1' : [0.421,0.678,0.115],
        })
        res = Extractor.extract_column_numerical(df_akt1, "AKT1", FakeResult(df_nodes, df_states, None), Operators.GT, 0.4)
        print(f"res : \n{res}\n Expected : \n{expected}")
        assert expected.equals(res)

    def test_merge_and_with_numerical_value(self):
        df_nodes = pd.read_csv(get_expected_data_path("test_data.csv"))
        df_states = pd.read_csv(get_expected_data_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 2.0],
            'AKT1':[0.421,0.115],
            'AKT2':[0.854,0.567],
            'AKT1--AKT2--AKT3_state': [0.6, 0.11],
        })
        #like doing AKT1 & ( AKT2 > 0.4 )
        fake = FakeResult(df_nodes, df_states, None)
        akt1 = ComputeLogicalExpression.compute_logical_expression(['AKT1'] , fake)
        # print(akt1)
        akt2 = ComputeLogicalExpression.compute_logical_expression(['AKT2'] , fake)
        akt2 = Extractor.extract_column_numerical(akt2, "AKT2", FakeResult(df_nodes, df_states, None), Operators.GT, 0.4)
        #print(akt2)
        res = ComputeLogicalExpression.merge_and(akt1, akt2, df_nodes, df_states)
        print(f"Res : \n {res} \n Expected : \n {expected}")
        assert expected.equals(res)

    def test_extractor_state(self):
        df_nodes = pd.read_csv(get_expected_data_path("test_data.csv"))
        df_states = pd.read_csv(get_expected_data_path("test_data_states.csv"))
        res = Extractor.extract_column(df_states, "AKT2", is_state=True)
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 , 2.0],
            'AKT2' : [0.00479,0.05,0.11],
        })
        print(f"Res : \n {res} \n Expected : \n {expected}")
        assert expected.round(5).equals(res.round(5))

    def test_extractor_num_value_with_state(self):
        df_nodes = pd.read_csv(get_expected_data_path("test_data.csv"))
        df_states = pd.read_csv(get_expected_data_path("test_data_states.csv"))
        df_akt2 = pd.DataFrame({
            'Time': [0.0, 1.0, 2.0],
            'AKT2' : [0.854,0.332,0.567],
        })
        res = Extractor.extract_column_numerical(df_akt2, "AKT2",
                                                 FakeResult(df_nodes, df_states, None), Operators.GT,
                                                 0.1, is_state=True)
        expected = pd.DataFrame({
            'Time' : [2.0],
            'AKT2' : [0.567],
        })
        print(f"Res : \n {res} \n Expected : \n {expected}")
        assert expected.round(5).equals(res.round(5))

    def test_extractor_num_value_with_node(self):
        df_nodes = pd.read_csv(get_expected_data_path("test_data.csv"))
        df_states = pd.read_csv(get_expected_data_path("test_data_states.csv"))
        res = Extractor.extract_column_numerical(df_nodes, "AKT2",
                                                 FakeResult(df_nodes, df_states, None), Operators.GT,
                                                 0.1, is_state=False)
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 , 2.0],
            'AKT1' : [0.421,0.678,0.115],
            'AKT2' : [0.854,0.332,0.567],
            'AKT3' : [0.120,0.941,0.443],
        })

        print(f"Res : \n {res} \n Expected : \n {expected}")
        assert expected.round(5).equals(res.round(5))


if __name__ == '__main__':
    unittest.main()
