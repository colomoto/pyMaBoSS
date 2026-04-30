from maboss.temporal_logic import MaBoSSEvaluator
from maboss.temporal_logic.logical_expression_compute import ComputeLogicalExpression
from maboss.temporal_logic.temporal_parser import *
from maboss.temporal_logic.formulas import *
from maboss.temporal_logic.custom_exceptions import *
from unittest import TestCase
import os
import pandas as pd
import operator

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

    def test_parsing_with_numerical(self):
        parsed_logical = [n.strip() for n in "( A >= 0.5 ) | B".split(" ")]
        res = ComputeLogicalExpression.parse_logical_expression(parsed_logical)
        assert res == [['A', '>=', '0.5'], '|', 'B']

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

        merged = ComputeLogicalExpression.merge_or(df1, df2,nodes_df=pd.DataFrame(columns=['A', 'B', 'C']),state_df=pd.DataFrame(columns=['A', 'C']))
        print("\n", merged)

    def test_merge_and(self):
        nodes_df = pd.read_csv(get_test_path("test_data.csv"))
        state_df = pd.read_csv(get_test_path("test_data_states.csv"))
        df1 = pd.DataFrame({
            'Time': [0.0, 1.0, 2.0],
            'AKT1' : [0.421, 0.678, 0.115],
            'AKT2' : [0.854, 0.332, 0.567],
            'AKT2_state' : [0.00479, 0.05, 0.11]
        })
        df2 = pd.DataFrame({
            'Time': [0.0, 1.0, 2.0],
            'AKT1' : [0.421, 0.678, 0.115],
            'AKT2_state' : [0.00479, 0.05, 0.11]
        })

        res = ComputeLogicalExpression.merge_and(df1, df2, nodes_df, state_df)
        print(f"Res : \n{res}\n")


    def test_compute_logical_expression_return_df(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.read_csv(get_test_path("expected_compute_data.csv"))
        fake = FakeResult(df_nodes, df_states, None)
        results = ComputeLogicalExpression.compute_logical_expression(['AKT1','&','AKT2'], fake)
        print(f"Résultats : \n{results}\n Expected : \n{expected}")
        assert results.equals(expected)

    def test_compute_with_no(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 , 2.0],
            'AKT1' : [0.421,0.678,0.115],
            'AKT1--AKT3_state' : [0.07521 ,0.2,0.11],
        })
        fake = FakeResult(df_nodes, df_states, None)
        results = ComputeLogicalExpression.compute_logical_expression(['AKT1', '&', '!AKT2'], fake)

        results.to_csv("test/compute_with_no.csv")
        print(f"Résultats : \n{results}")
        assert results.equals(expected)

    def test_compute_with_no_and(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time': [0.0, 1.0, 2.0],
            'AKT2': [0.854, 0.332, 0.567],
            'AKT2_state' : [0.00479, 0.05, 0.11],
        })
        fake = FakeResult(df_nodes, df_states, None)
        results = ComputeLogicalExpression.compute_logical_expression(['AKT2', '&', '!AKT3'], fake)

        results.to_csv("test/compute_with_no.csv")
        print(f"Résultats : \n{results}")
        assert results.equals(expected)

    def test_compute_with_no_and_2(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time': [0.0, 1.0, 2.0],
            'AKT1': [0.421, 0.678, 0.115]
        })
        fake = FakeResult(df_nodes, df_states, None)
        results = ComputeLogicalExpression.compute_logical_expression(['AKT1', '&', '!AKT3'], fake)

        results.to_csv("test/compute_with_no.csv")
        print(f"Résultats : \n{results}")
        assert results.equals(expected)

    def test_compute_with_or(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 , 2.0],
            'AKT1' : [0.421,0.678,0.115],
            'AKT2' : [0.854,0.332,0.567],
            'AKT1--AKT2--AKT3_state': [0.6, 0.15, 0.11],
            'AKT1--AKT3_state' : [0.07521 ,0.2,0.11],
            'AKT2_state' : [0.00479,0.05,0.11]
        })
        fake = FakeResult(df_nodes, df_states, None)
        results = ComputeLogicalExpression.compute_logical_expression(['AKT1' , '|', 'AKT2'], fake)
        #results.to_csv("compute_with_or.csv")
        assert results.equals(expected)

    def test_compute_with_no_or(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 , 2.0],
            'AKT1' : [0.421,0.678,0.115],
            '<nil>_state' : [0.32,0.4,0.67],
            'AKT1--AKT2--AKT3_state': [0.6, 0.15, 0.11],
            'AKT1--AKT3_state' : [0.07521 ,0.2,0.11]
        })
        fake = FakeResult(df_nodes,df_states,None)
        results = ComputeLogicalExpression.compute_logical_expression(['!AKT2' , '|', 'AKT1'], fake)
        results.to_csv("compute_with_or_not.csv")
        assert results.equals(expected)

    def test_compute_intrication(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 , 2.0],
            'AKT1' : [0.421,0.678,0.115],
            'AKT2' : [0.854,0.332,0.567],
            'AKT3' : [0.12,0.941,0.443],
            'AKT1--AKT2--AKT3_state': [0.6, 0.15, 0.11],
            'AKT1--AKT3_state' : [0.07521 ,0.2,0.11]
        })
        fake = FakeResult(df_nodes, df_states, None)
        results = ComputeLogicalExpression.compute_logical_expression(['AKT1' , '|', ['AKT2' , '&' , 'AKT3']], fake)
        results.to_csv("test/compute_intrication.csv")
        assert results.equals(expected)

    def test_compute_full_process_simple_and(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 , 2.0],
            'AKT1' : [0.421,0.678,0.115],
            'AKT2' : [0.854,0.332,0.567],
            'AKT1--AKT2--AKT3_state': [0.6, 0.15, 0.11],
        })

        res = ComputeLogicalExpression.compute_logical_expression(['AKT1', '&' , 'AKT2'], FakeResult(df_nodes, df_states, None))
        res.to_csv("test/compute_full_process_simple_and.csv")
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert res.equals(expected)

    def test_compute_full_process_simple_or(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 , 2.0],
            'AKT1' : [0.421,0.678,0.115],
            'AKT2' : [0.854,0.332,0.567],
            'AKT1--AKT2--AKT3_state': [0.6, 0.15, 0.11],
            'AKT1--AKT3_state' : [0.07521 ,0.2,0.11],
            'AKT2_state' : [0.00479,0.05,0.11]
        })

        res = ComputeLogicalExpression.compute_logical_expression(['AKT1' , '|' , 'AKT2'], FakeResult(df_nodes, df_states, None))
        assert res.equals(expected)

    def test_simple_value_numerical(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0],
            'AKT1' : [0.421,0.678],
            'AKT1--AKT2--AKT3_state': [0.6, 0.15],
            'AKT1--AKT3_state' : [0.07521 ,0.2],
        })

        res = ComputeLogicalExpression.compute_logical_expression(['AKT1' , '>' , '0.4'], FakeResult(df_nodes, df_states, None))
        #print(res)
        assert res.equals(expected)

    def test_simple_value_numerical_with_no(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 2.0],
            '<nil>_state' : [0.32,0.67],
            'AKT2_state' : [0.00479,0.11],
        })
        res = ComputeLogicalExpression.compute_logical_expression([['!AKT1' , '>' , '0.4']], FakeResult(df_nodes, df_states, None))
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert expected.equals(res)

    def test_simple_value_numerical_with_or(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0 ],
            'AKT1' : [0.421,0.678],
            'AKT2' : [0.854,0.332],
            'AKT1--AKT2--AKT3_state': [0.6, 0.15],
            'AKT1--AKT3_state' : [0.07521 ,0.2],
            'AKT2_state' : [0.00479,0.05]
        })
        log_exp = [['AKT1' , '>' , '0.4'] , '|' , 'AKT2' ]
        res = ComputeLogicalExpression.compute_logical_expression(log_exp, FakeResult(df_nodes, df_states, None))
        assert expected.equals(res)

    def test_expression_more_complex(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0],
            'AKT1' : [0.421,0.678],
            'AKT2' : [0.854,0.332],
            'AKT3' : [0.12,0.941],
            'AKT1--AKT2--AKT3_state': [0.6, 0.15],
            'AKT1--AKT3_state' : [0.07521 ,0.2]
        })
        log_exp = [['AKT1' , '>' , '0.4'] , '|' , ['AKT2' , '&' , 'AKT3']]
        res = ComputeLogicalExpression.compute_logical_expression(log_exp, FakeResult(df_nodes, df_states, None))
        res.to_csv("test/test_expression_more_complex.csv")
        assert expected.equals(res)

    def test_expression_more_complex_with_no(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 2.0],
            'AKT2' : [0.854,0.567],
            'AKT3' : [0.12,0.443],
            '<nil>_state' : [0.32,0.67],
            'AKT1--AKT2--AKT3_state': [0.6, 0.11],
            'AKT2_state' : [0.00479,0.11] #it is here because !AKT1 returns all the columns where AKT1 is inactive
        })

        log_exp = [['!AKT1' , '>' , '0.4'] , '|' , ['AKT2' , '&' , 'AKT3']]
        res = ComputeLogicalExpression.compute_logical_expression(log_exp, FakeResult(df_nodes, df_states, None))
        #print(f"Results : \n{res}\n Expected : \n{expected}")
        assert expected.equals(res)

    def test_akt2_and_akt3(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        expected = pd.DataFrame({
            'Time' : [0.0 , 1.0, 2.0],
            'AKT2' : [0.854,0.332,0.567],
            'AKT3' : [0.12,0.941, 0.443],
            'AKT1--AKT2--AKT3_state': [0.6, 0.15, 0.11],
        })

        log_exp = [['AKT2' , '&' , 'AKT3']]
        res = ComputeLogicalExpression.compute_logical_expression(log_exp, FakeResult(df_nodes, df_states, None))
        res.to_csv("test/test_akt2_and_akt3.csv")
        print(f"Results : \n{res}\n Expected : \n{expected}")
        assert expected.equals(res)


    def test_check_logical_expression_numerical(self):
        exp = ['AKT1' , '>' , '0.4']

        try:
            ComputeLogicalExpression.check_logical_expression(exp)
        except ErrorInLogicalExpression:
            self.fail(("Erreur lors de l'analyse de l'expression logique " , exp))

    def test_check_handling_symb(self):
        symbols = ['&', '|', '>', '<', '==', '>=', '<=', '=']
        for s in symbols:
            print(s)
            assert True == ComputeLogicalExpression.is_any_symb_check(s)

    def test_operator_map(self):
        symbol = '>'
        print(Operators(symbol))
        #print(ComputeLogicalExpression.OPERATOR_MAP.get(Operators(symbol)))
        assert ComputeLogicalExpression.OPERATOR_MAP.get(Operators(symbol)) == operator.gt

    def test_logical_with_node(self):
        df_nodes = pd.read_csv(get_test_path("test_data.csv"))
        df_states = pd.read_csv(get_test_path("test_data_states.csv"))
        log_exp = ['state:AKT2' , '>=' , '0.1']
        res = ComputeLogicalExpression.compute_logical_expression(log_exp, FakeResult(df_nodes, df_states, None))
        expected = pd.DataFrame({
            'Time' : [2.0],
            'AKT2' : [0.11],
        })
        print(f"Result : \n{res} \n Expected : \n{expected}")
        assert res.equals(expected)