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

class TargetType(Enum):
    NODE = "node"
    STATE = "state"

class Operators(Enum):
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
    expression: str

class FormulaChecker:
    @staticmethod
    def check_formula(formula: Formula):

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

        if formula.value is None or formula.value == "":
            raise EmptyValueException()

        # checking the value
        if formula.value == "?" and (formula.logical_equation is None or formula.logical_equation ==[]):
            raise WrongGrammarException("Value is \"?\" but the logical equation is empty")
        if formula.value == "?" and formula.operator.value != Operators.EQ.value:
            raise WrongGrammarException("Value is \"?\" but the operator is not \"=\"")
        if formula.value != "?" and formula.operator.value == Operators.EQ.value:
            warnings.warn("Value is not \"?\" but the operator is \"=\", there is a possibility of no result")

        if formula.operator == Operators.NE:
            warnings.warn("Operator \"!=\" may produce very broad results, consider using \"<\", \"<=\", \">=\" or \">\" instead")

        if formula.value != "?":
            try:
                float(formula.value)
            except Exception:
                raise WrongSymbolForValue("Wrong symbol for value, it must be a number or \"?\"")

            if float(formula.value) > 1 and (formula.type.value == QueryType.P.value or
                                             formula.type.value == QueryType.TMAX.value or
                                             formula.type.value == QueryType.TMIN.value) :
                raise WrongValueAccordingToType("Value is greater than 1, the formula must be a probability : between 0 and 1")
            if float(formula.value) < 0:
                raise ValueError("Value can not be negative")