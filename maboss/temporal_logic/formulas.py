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
    DEPENDENCIE = "D"
    MUTATION = "M"
    INCREASE = "Inc"
    DECREASE = "Dec"

class TargetType(Enum):
    NODE = "node"
    STATE = "state"

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
    mutation_constraint: list
    expression: str

class FormulaChecker:
    @staticmethod
    def check_formula(formula: Formula):

        if formula.type == QueryType.INCREASE or formula.type == QueryType.DECREASE:
            if formula.mutation_constraint is None or formula.mutation_constraint == []:
                raise ErrorInIncreaseDecreaseEvaluation(f"The mutation constraint cannot be empty for this evaluation : {formula.type}")

        if formula.type == QueryType.MUTATION:
            if formula.mutation_constraint is not None and formula.mutation_constraint != []:
                raise ErrorInMutationEvaluation(f"The mutation constraint cannot be filled for this evaluation : {formula.type}")
            if formula.logical_equation is None or formula.logical_equation == []:
                raise ErrorInMutationEvaluation(f"The logical equation cannot be empty for this evaluation : {formula.type}")

        if formula.target_name is None or formula.target_name == []:
            raise EmptyNameException()
        if len(formula.target_name) > 1:
            if formula.type == QueryType.PMIN or formula.type == QueryType.PMAX:
                raise ErrorMinMaxOnlyForOneEntity("A min/max operation can only be performed on one entity, e.g: P(node:name) ... ")
            if formula.type == QueryType.DEPENDENCIE and len(formula.target_name) != 2:
                raise ErrorInDependencieEvaluation("A dependencie evaluation must have 2 names exactly.")
            if formula.type == QueryType.MUTATION :
                raise ErrorInMutationEvaluation("A mutation evaluation can only have \'?\' has name.")
            if formula.type == QueryType.INCREASE or formula.type == QueryType.DECREASE:
                raise ErrorInIncreaseDecreaseEvaluation("An increase/decrease evaluation must have 1 name exactly.")
            for name in formula.target_name:
                if name == "":
                    raise EmptyNameException()
        else:
            if formula.target_name[0] == "":
                raise EmptyNameException()

            if formula.target_name[0] != "?" and formula.type == QueryType.MUTATION:
                raise ErrorInMutationEvaluation("A mutation evaluation can only have \'?\' has name.")

            if formula.target_name[0] == "*":
                if formula.type != QueryType.P and formula.type != QueryType.T:
                    raise ErrorMinMaxOnlyForOneEntity(
                        "A min/max operation can only be performed on one entity, e.g: P(node:name) ... ")

        if formula.type == QueryType.DEPENDENCIE:
            if len(formula.target_name) != 2:
                raise ErrorInDependencieEvaluation("A dependencie evaluation must have 2 names")

        if formula.operator == Operators.NE:
            warnings.warn("Operator \"!=\" may produce very broad results, consider using \"<\", \"<=\", \">=\" or \">\" instead")
        if formula.operator == Operators.NONE and not (formula.type == QueryType.INCREASE or
                                                       formula.type == QueryType.DECREASE or
                                                       formula.type == QueryType.MUTATION or
                                                       formula.type == QueryType.DEPENDENCIE):
            raise WrongGrammarException("Operator is required except for Inc, Dec, M and D that require \'/\' and no value")
        if formula.operator != Operators.NONE and (formula.type == QueryType.INCREASE or
                                                       formula.type == QueryType.DECREASE or
                                                       formula.type == QueryType.MUTATION or
                                                       formula.type == QueryType.DEPENDENCIE):
            raise WrongGrammarException("Operator is not required for Inc, Dec, M and D")

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

            if float(formula.value) > 1 :
                raise WrongValueAccordingToType("Value is greater than 1, the formula must be a probability : between 0 and 1")
            if float(formula.value) < 0:
                raise ValueError("Value can not be negative")

            if formula.operator.value == Operators.EQ.value:
                warnings.warn("Value is not \"?\" but the operator is \"=\", there is a possibility of no result")

        if formula.value == "":
            if not( formula.type == QueryType.INCREASE or formula.type == QueryType.DECREASE or formula.type == QueryType.MUTATION):
                raise EmptyValueException()