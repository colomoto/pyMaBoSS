from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union

class QueryType(Enum):
    P = "P" # probas of an event
    PMAX = "Pmax"
    PMIN = "Pmin"
    S = "S"

class TargetType(Enum):
    NODE = "node"
    TRAJ = "traj"
    STATE = "state"

class Operators(Enum):
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    EQ = "=" or "=="
    NE = "!="

@dataclass
class Formula:
    type: QueryType
    target: TargetType # a node name, a traj or a state
    target_name: str
    operator: Operators
    value: float
    expression: str