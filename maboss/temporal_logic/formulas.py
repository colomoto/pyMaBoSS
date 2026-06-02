from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union

from pyparsing import warnings

from maboss.temporal_logic.custom_exceptions import *


class QueryType(Enum):
    P = "P" # probas of an event
    PMAX = "Pmax" # probas mini of an event
    PMIN = "Pmin" # probas maxi of an event
    T = "T" # time of an event
    TMIN = "Tmin" # time mini of an event (first time it happens)
    TMAX = "Tmax" # time maxi of an event (last time it happens)
    MUTATION = "M"
    INCREASE = "Inc"
    DECREASE = "Dec"

class TargetType(Enum):
    NODE = "node"
    STATE = "state"
    FIXPOINT = "fp"

class Operators(Enum):
    NONE = "/"
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    EQ = "="
    NE = "!="

class LogicalOperators(Enum):
    AND = "&"
    OR = "|"
    NOT = "!"

@dataclass
class Formula:
    type: QueryType
    target: TargetType # a node name, a traj or a state
    target_name: list # a list of names
    operator: Operators
    value: str
    logical_equation: list # the list of the component of the logical equation
    mutation_constraint: list # the list of the component of the mutation constraint
    options: list # the list of the component of the initial state constraint
    expression: str

class FormulaChecker:
    """
    A class that checks the syntax of the formula.
    """
    @staticmethod
    def check_logical_equation_no_float_no_state(logical_equation: list[str]):
        """
        Only checks if the logical equation does not contain float value or state name explicitly. Does not check the syntax.
        :param logical_equation:
        :return: nothing
        :raise: FloatValueInFixpointLogicalEquation, StateNameInFixpointLogicalEquation
        """
        for member in logical_equation:
            if isinstance(member, list):
                FormulaChecker.check_logical_equation_no_float_no_state(member)
            else:
                try:
                    float(member)
                    raise FloatValueInFixpointLogicalEquation(f"Fixpoint target cannot contain float value in the logical equation : {member}")
                except ValueError:
                    pass

                if str(member).__contains__("--") or str(member).__contains__("state:"):
                    raise StateNameInFixpointLogicalEquation(f"Fixpoint logical equation cannot contain state name : {member}. Try 'node:name' or 'name'.")


    @staticmethod
    def check_formula(formula: Formula):
        """
        checks that all the formula (query) is respecting the syntax.
        :param formula: the parsed query
        :return: nothing if everything is ok, raise an exception otherwise
        """

        if formula.type == QueryType.T or formula.type == QueryType.TMAX or formula.type == QueryType.TMIN:
            if formula.target == TargetType.FIXPOINT:
                raise FormulaException(f"The fixpoint target type for this operation: {formula.type} is not supported.")

        if not (formula.type == QueryType.INCREASE or formula.type == QueryType.DECREASE):
            if "comb" not in formula.options and formula.target == TargetType.FIXPOINT:
                raise FormulaException(f"The fixpoint target type for this operation: {formula.type} is supported only with 'comb' option.")
            if "transient" in formula.options:
                raise FormulaException(f"The transient option is not supported for this operation: {formula.type}, only for Dec and Inc")
            if "compare" in formula.options:
                raise FormulaException(f"The compare option is not supported for this operation: {formula.type}, only for Dec and Inc")

        if formula.type == QueryType.DECREASE or formula.type == QueryType.INCREASE: #node, fp or state and Inc or Dec
            if formula.target == TargetType.NODE or formula.target == TargetType.STATE:
                if formula.logical_equation:
                    raise FormulaException(f"The logical equation cannot be filled for this evaluation : {formula.type} and target {formula.target}")
            if formula.logical_equation and formula.target == TargetType.FIXPOINT:
                try:
                    FormulaChecker.check_logical_equation_no_float_no_state(formula.logical_equation)
                except (FloatValueInFixpointLogicalEquation, StateNameInFixpointLogicalEquation) as e:
                    raise FormulaException(e.message)
            if formula.mutation_constraint is None or formula.mutation_constraint == []:
                raise ErrorInIncreaseDecreaseEvaluation(f"The mutation constraint cannot be empty for this evaluation : {formula.type}")

        if formula.target_name is None or formula.target_name == []:
            raise EmptyNameException()
        if len(formula.target_name) > 1:
            if formula.type == QueryType.PMIN or formula.type == QueryType.PMAX:
                raise ErrorMinMaxOnlyForOneEntity("A min/max operation can only be performed on one entity, e.g: P(node:name) ... ")
            for name in formula.target_name:
                if name == "":
                    raise EmptyNameException()
        else:
            if formula.target_name[0] == "":
                raise EmptyNameException()

            if formula.target_name[0] == "*":
                if formula.type != QueryType.P and formula.type != QueryType.T:
                    raise ErrorMinMaxOnlyForOneEntity(
                        "A min/max operation can only be performed on one entity, e.g: P(node:name) ... ")

        if formula.operator == Operators.NE:
            warnings.warn("Operator \"!=\" may produce very broad results, consider using \"<\", \"<=\", \">=\" or \">\" instead")
        if formula.operator == Operators.NONE and not (formula.type == QueryType.INCREASE or
                                                       formula.type == QueryType.DECREASE):
            raise WrongGrammarException("Operator is required except for Inc, Dec that require \'/\' and no value.")
        if formula.operator != Operators.NONE and (formula.type == QueryType.INCREASE or
                                                       formula.type == QueryType.DECREASE):
            raise WrongGrammarException("Operator is not required for Inc, Dec.")

        if formula.value is None or formula.value == "":
            if not ((formula.type == QueryType.INCREASE or formula.type == QueryType.DECREASE or formula.type == QueryType.MUTATION) and formula.operator == Operators.NONE):
                raise EmptyValueException()

        if formula.value == "?":
            if formula.logical_equation is None or formula.logical_equation ==[]: raise WrongGrammarException("Value is \"?\" but the logical equation is empty")
            if formula.operator.value != Operators.EQ.value : raise WrongGrammarException("Value is \"?\" but the operator is not \"=\"")
            if formula.type != QueryType.P:
                raise WrongValueAccordingToType("Only query P handles \"?\"")

        if formula.value != "?" and not (None or formula.value==""):
            try:
                float(formula.value)
            except Exception:
                raise WrongSymbolForValue("Wrong symbol for value, it must be a number or \"?\"")

            if formula.type != QueryType.INCREASE and formula.type != QueryType.DECREASE:
                if float(formula.value) > 1 :
                    raise WrongValueAccordingToType("Value is greater than 1, the formula must be a probability : between 0 and 1")
                if float(formula.value) < 0:
                    raise ValueError("Value can not be negative")

            if formula.operator.value == Operators.EQ.value:
                warnings.warn("Value is not \"?\" but the operator is \"=\", there is a possibility of no result")

        if formula.value == "":
            if not( formula.type == QueryType.INCREASE or formula.type == QueryType.DECREASE):
                raise EmptyValueException()