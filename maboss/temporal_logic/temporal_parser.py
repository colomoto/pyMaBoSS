import re
from maboss.temporal_logic.formulas import *

class Parser:
    QUERY_PATTERN = \
        r"^(Pmax|Pmin|P|T|Tmin|Tmax)\((node|state)\:(.+?)\)(?:\s*(<=|>=|<|>|=|==|!=)\s*(0(?:\.\d+)?|1(?:\.0+)?|\?))?\s*(?:\[(.+?)\])?"

    @staticmethod
    def parse_query(input: str) -> Formula:
        match = re.match(Parser.QUERY_PATTERN, input.strip())

        if not match:
            raise ValueError(f"Invalid query format, the query should be of the form: "
                             f"P([targetType]:[name]) <= 0.5 [ [logic equation optionnal] ]. "
                             f"More info : MaBoSSEvaluator.help()\n Input : {input}")

        query_type, target, target_name, operator, value, logical_equation = match.groups()
        print(query_type, target, target_name, operator, value, logical_equation)

        if target_name.__contains__(","):
            names_list = [n.strip() for n in target_name.split(",")]
        else :
            names_list = [target_name]

        if logical_equation is None:
            logical_equation_components = []
        else:
            logical_equation_striped = [n.strip() for n in logical_equation.split(" ")]
            logical_equation_components = []
            in_sub = False
            for c in logical_equation_striped:
                if c == '': # ignore the spaces
                    pass
                elif c == '(':
                    in_sub = True
                    sub_array = []
                else: # c is any other char
                    if in_sub:
                        if c == ')':
                            if len(sub_array) == 0:
                                warnings.warn("Empty sub-array in logical equation, removed")
                            else:
                                logical_equation_components.append(sub_array)
                            in_sub = False
                        else:
                            sub_array.append(c)
                    else: # if in major equation
                        logical_equation_components.append(c)

        # Conversion of types, with try/catch to handle errors
        try:
            _type = QueryType(query_type)
        except ValueError:
            raise ValueError(f"Query type \"{query_type}\" is not supported, try P, T, Pmax, Pmin, Tmax, Tmin")

        try:
            _op = Operators(operator)
        except ValueError:
            raise ValueError(f"Operator \"{operator}\" is not supported, try <, <=, =, !=, >=, >")

        try:
            _target = TargetType(target)
        except ValueError:
            raise ValueError(f"Target \"{target}\" is not supported, try node, state")

        return Formula(
            type=_type,
            target=_target,
            target_name=names_list, # an array of names
            operator=_op,
            value=str(value),
            logical_equation = logical_equation_components,
            expression=input
        )
    