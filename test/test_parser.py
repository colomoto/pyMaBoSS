import pandas as pd

from maboss.temporal_logic.logical_expression_compute import ComputeLogicalExpression
from maboss.temporal_logic.temporal_parser import *
from maboss.temporal_logic.formulas import *
from maboss.temporal_logic.custom_exceptions import *
from unittest import TestCase

# Parser test queries
QUERY = "P(node:name) <= 0.623"
QUERY_INTERROGATION = "T(state:name) = ? [ !A & B | C ]"
QUERY_MULTIPLE_NAMES = "P(node:name,name2,name3) <= 0.5 "
QUERY_INTRICATE_CONDITION = "P(node:name) > 0.5 [ B | ( C & D ) ]"
QUERY_FOUND_BY_NAME = "P(node:AKT1) > 0.623"
QUERY_MULTIPLE_NAMES_AND_CONDITION = "P(node:A,B,C) <= 0.4 [ A | !B & C ]"
QUERY_MULTIPLE_NAMES_AND_INTRICATE_CONDITION = "P(node:A,B,C) >= 0.5 [ B | ( C & D ) ]"

# FORMULA CHECKER test Formulas
NO_ERROR_FORMULA_PROBA = Formula(QueryType.P, TargetType.NODE , ["name"], Operators.LE, "1", [], QUERY)
NO_ERROR_FORMULA_TIME = Formula(QueryType.T, TargetType.STATE , ["name"], Operators.EQ, "?", ['A','&','B'], "T(state:name) = ?")
NO_ERROR_INTERROGATION = Formula(QueryType.T, TargetType.STATE , ["name"], Operators.EQ, "?", ['!A','&','B','|','C'], "T(state:name) = ? [ !A & B | C ]")

ERROR_FORMULA_VALUE_EMPTY = Formula(QueryType.P, TargetType.NODE , ["name"], Operators.LE, "", [], QUERY)
ERROR_FORMULA_VALUE_WRONG_SYMBOL = Formula(QueryType.P, TargetType.NODE , ["name"], Operators.LE, "!", [], QUERY)
ERROR_FORMULA_VALUE_NOT_A_NUMBER = Formula(QueryType.P, TargetType.NODE , ["name"], Operators.LE, "a", [], QUERY)

ERROR_FORMULA_TARGET_EMPTY_TAB = Formula(QueryType.P, TargetType.NODE , [], Operators.LE, "0.567", [], QUERY)
ERROR_FORMULA_TARGET_EMPTY_NAME = Formula(QueryType.P, TargetType.NODE , [""], Operators.LE, "0.567", [], QUERY)
ERROR_FORMULA_TARGET_EMPTY_MULTIPLE_NAMES = Formula(QueryType.P, TargetType.NODE , ["name","","name2"], Operators.LE, "0.567", [], QUERY)

ERROR_FORMULA_INTERROGATION_GRAMMAR =  Formula(QueryType.T, TargetType.STATE , ["name"], Operators.LE, "?", [], "T(state:name) = ? [ !A & B | C ]")
ERROR_FORMULA_INTERROGATION_GRAMMAR_NO_CONDITIONS = Formula(QueryType.T, TargetType.STATE , ["name"], Operators.EQ, "?", [], "T(state:name) = ?")

ERROR_VALUE_OVER_ONE_FOR_PROBA = Formula(QueryType.P, TargetType.NODE , ["name"], Operators.LE, "1.1", [], QUERY)
ERROR_VALUE_UNDER_ZERO = Formula(QueryType.P, TargetType.NODE , ["name"], Operators.LE, "-0.1", [], QUERY)

QUERY_ERROR_TYPE = "V(node:name) > 0.5"
QUERY_ERROR_OPERATOR = "P(node:name) !< 0.5"
QUERY_ERROR_TARGET = "P(traj:name) <= 0.5"

LOGICAL_EXPRESSION_SIMPLE_NO_ERROR = ['A','&', '!B']
LOGICAL_EXPRESSION_INTRICATE_NO_ERROR = ['A','|', ['B','&','C']]

LOGICAL_EXPRESSION_ERROR_NODES = ['A','|', 'B','&','C','D']
LOGICAL_EXPRESSION_ERROR_SYMBOL = ['A', '|' , '&', 'B']
LOGICAL_EXPRESSION_ERROR_FIRST_MEMBER_SYMBOL = ['&','A', '|', 'B']
LOGICAL_EXPRESSION_ERROR_LAST_MEMBER_SYMBOL = ['A', '|', '&', 'B', '|']
LOGICAL_EXPRESSION_ERROR_NODES_INTRICATE = ['A','|', ['B','&','C','D']]


# -------------------------- TESTS PARSER --------------------------------------

class TestParser(TestCase):
    def test_parse_simple_query(self):
        formula1 = Parser.parse_query(QUERY)
        assert formula1.type == QueryType.P
        assert formula1.operator == Operators.LE
        assert formula1.value == str(0.623)
        assert formula1.target_name == ['name']
        assert formula1.logical_equation == []

    def test_parse_interrogation_query_one_name(self):
        formula2 = Parser.parse_query(QUERY_INTERROGATION)
        assert formula2.type == QueryType.T
        assert formula2.target == TargetType.STATE
        assert formula2.operator == Operators.EQ
        assert formula2.value == "?"
        assert formula2.target_name == ['name']
        assert formula2.logical_equation == ['!A', '&', 'B', '|', 'C']

    def test_parse_multiple_names(self):
        formula3 = Parser.parse_query(QUERY_MULTIPLE_NAMES)
        assert formula3.type == QueryType.P
        assert formula3.operator == Operators.LE
        assert formula3.value == str(0.5)
        assert formula3.target_name == ['name', 'name2', 'name3']
        assert formula3.logical_equation == []

    def test_parse_intricate_condition(self):
        formula4 = Parser.parse_query(QUERY_INTRICATE_CONDITION)
        assert formula4.type == QueryType.P
        assert formula4.operator == Operators.GT
        assert formula4.value == str(0.5)
        assert formula4.target_name == ['name']
        assert formula4.logical_equation == ['B', '|', ['C', '&', 'D']]

    def test_parse_multiple_names_and_condition(self):
        formula5 = Parser.parse_query(QUERY_MULTIPLE_NAMES_AND_CONDITION)
        assert formula5.type == QueryType.P
        assert formula5.operator == Operators.LE
        assert formula5.value == str(0.4)
        assert formula5.target_name == ['A', 'B', 'C']
        assert formula5.logical_equation == ['A', '|', '!B', '&', 'C']

    def test_parse_multiple_names_and_intricate_condition(self):
        formula6 = Parser.parse_query(QUERY_MULTIPLE_NAMES_AND_INTRICATE_CONDITION)
        assert formula6.type == QueryType.P
        assert formula6.operator == Operators.GE
        assert formula6.value == str(0.5)
        assert formula6.target_name == ['A', 'B', 'C']
        assert formula6.logical_equation == ['B', '|', ['C', '&', 'D']]

    def test_main_query_parser_check_values(self):
        self.assertRaises(ValueError, Parser.parse_query, QUERY_ERROR_TYPE)
        self.assertRaises(ValueError, Parser.parse_query, QUERY_ERROR_OPERATOR)
        self.assertRaises(ValueError, Parser.parse_query, QUERY_ERROR_TARGET)

# -------------------------------- FORMULA CHECKER TESTS -------------------------------------
    def test_formula_checker_no_error(self):
        try:
            FormulaChecker.check_formula(NO_ERROR_FORMULA_PROBA)
        except FormulaException:
            self.fail("FormulaChecker.check_formula() PROBA raised an unexpected ValueError")

        try:
            FormulaChecker.check_formula(NO_ERROR_FORMULA_TIME)
        except FormulaException:
            self.fail("FormulaChecker.check_formula() TIME raised an unexpected ValueError")

        try:
            FormulaChecker.check_formula(NO_ERROR_INTERROGATION)
        except FormulaException:
            self.fail("FormulaChecker.check_formula() INTERROGATION raised an unexpected ValueError")

    def test_formula_checker_error_value(self):
        self.assertRaises(EmptyValueException, FormulaChecker.check_formula, ERROR_FORMULA_VALUE_EMPTY)
        self.assertRaises(WrongSymbolForValue, FormulaChecker.check_formula, ERROR_FORMULA_VALUE_WRONG_SYMBOL)
        self.assertRaises(WrongSymbolForValue, FormulaChecker.check_formula, ERROR_FORMULA_VALUE_NOT_A_NUMBER)

    def test_formula_checker_error_target_name_empty(self):
        self.assertRaises(EmptyNameException, FormulaChecker.check_formula, ERROR_FORMULA_TARGET_EMPTY_TAB)
        self.assertRaises(EmptyNameException, FormulaChecker.check_formula, ERROR_FORMULA_TARGET_EMPTY_NAME)
        self.assertRaises(EmptyNameException, FormulaChecker.check_formula, ERROR_FORMULA_TARGET_EMPTY_MULTIPLE_NAMES)

    def test_formula_grammar(self):
        self.assertRaises(WrongGrammarException, FormulaChecker.check_formula, ERROR_FORMULA_INTERROGATION_GRAMMAR)
        self.assertRaises(WrongGrammarException, FormulaChecker.check_formula, ERROR_FORMULA_INTERROGATION_GRAMMAR_NO_CONDITIONS)

    def test_formula_value_strict_pos(self):
        self.assertRaises(WrongValueAccordingToType, FormulaChecker.check_formula, ERROR_VALUE_OVER_ONE_FOR_PROBA)
        self.assertRaises(ValueError, FormulaChecker.check_formula, ERROR_VALUE_UNDER_ZERO)

# ---------------------------- TESTS FOR COMPUTATION OF LOGICAL EXPRESSION -----------------------
    def test_expression_no_error(self):
        try:
            ComputeLogicalExpression.check_logical_expression(LOGICAL_EXPRESSION_SIMPLE_NO_ERROR)
        except ErrorInLogicalExpression:
            self.fail("ComputeLogicalExpression.check_logical_expression() raised an unexpected ValueError on SIMPLE")

        try:
            ComputeLogicalExpression.check_logical_expression(LOGICAL_EXPRESSION_INTRICATE_NO_ERROR)
        except ErrorInLogicalExpression:
            self.fail("ComputeLogicalExpression.check_logical_expression() raised an unexpected ValueError on INTRICATE")

    def test_expression_error(self):
        self.assertRaises(ErrorInLogicalExpression, ComputeLogicalExpression.check_logical_expression, LOGICAL_EXPRESSION_ERROR_NODES)
        self.assertRaises(ErrorInLogicalExpression, ComputeLogicalExpression.check_logical_expression, LOGICAL_EXPRESSION_ERROR_SYMBOL)
        self.assertRaises(ErrorInLogicalExpression, ComputeLogicalExpression.check_logical_expression, LOGICAL_EXPRESSION_ERROR_FIRST_MEMBER_SYMBOL)
        self.assertRaises(ErrorInLogicalExpression, ComputeLogicalExpression.check_logical_expression, LOGICAL_EXPRESSION_ERROR_LAST_MEMBER_SYMBOL)
        self.assertRaises(ErrorInLogicalExpression, ComputeLogicalExpression.check_logical_expression, LOGICAL_EXPRESSION_ERROR_NODES_INTRICATE)

    def test_counting_members_logical_query(self):
        assert Parser.counting_members_logical_query(LOGICAL_EXPRESSION_SIMPLE_NO_ERROR) == 3
        assert Parser.counting_members_logical_query(LOGICAL_EXPRESSION_INTRICATE_NO_ERROR) == 5
        assert Parser.counting_members_logical_query(['B', '|', ['C', '&', 'D']]) == 5
        assert Parser.counting_members_logical_query([['AKT2','>=','0.2'],'|','AKT3']) == 5

