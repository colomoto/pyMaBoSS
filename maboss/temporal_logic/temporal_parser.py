import re
from maboss.temporal_logic.formulas import *

class Parser:
    QUERY_PATTERN = r"^(Pmax|Pmin|P|S)\((node|traj|fp)\:(.+?)\)\s*(<=|>=|<|>|=|==|!=)\s*(0(?:\.\d+)?|1(?:\.0+)?)" # pour le moment seulement les assertions

@staticmethod
def parse(input: str) -> Formula:
    match = re.match(Parser.QUERY_PATTERN, input.strip())

    if not match:
        raise ValueError(f"Invalid query format, the query should be of the form: Pmax([targetType]:[name]) <= 0.5.\n Input : {input}")

    query_type, target, target_name, operator, value = match.groups()

    return Formula(
        type=QueryType(query_type),
        target=TargetType(target),
        target_name=str(target_name),
        operator=Operators(operator),
        value=float(value),
        expression=input,
    )
    