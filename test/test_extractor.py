import unittest
import pandas as pd
import os
from maboss.temporal_logic.extractors import Extractor

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

if __name__ == '__main__':
    unittest.main()
