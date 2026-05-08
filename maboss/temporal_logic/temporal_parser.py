import re
from maboss.temporal_logic.formulas import *
from maboss.temporal_logic.logical_expression_compute import ComputeLogicalExpression


class Parser:
    QUERY_PATTERN = \
        r"^(Pmax|Pmin|P|T|Tmin|Tmax|D|M|Inc|Dec)\((node|state|fp)\:(.+?)\)(?:\s*(<=|>=|<|>|=|==|!=|/)\s*(0(?:\.\d+)?|1(?:\.0+)?|\?|\d+|))?(?:\s*\[(.+?)\])?(?:\s*\[(.+?)\])?(?:\s*\[(.+?)\])?"

    @staticmethod
    def parse_query(input: str) -> Formula:
        match = re.match(Parser.QUERY_PATTERN, input.strip())

        if not match:
            raise ValueError(f"Invalid query format, the query should be of the form: "
                             f"P([targetType]:[name]) <= 0.5 [ [logic equation optional] ] [ [mutation constraint optional] ] [ [Initial State optional] ]. "
                             f"More info : MaBoSSEvaluator.help()\n Input : {input}")

        #print(f"\nInput : {input}\n Match : {match.group(0)}\n Match groups :\n {match.groups()}")
        query_type = match.group(1)
        target = match.group(2)
        target_name = match.group(3)
        operator = match.group(4)
        value = match.group(5)
        logical_equation = match.group(6)
        mutation_param = match.group(7)
        initial_state = match.group(8)
        #print(f"Query type : {query_type}, target : {target}, target name : {target_name}, operator : {operator}, value : {value}, logical equation : {logical_equation}, mutation param : {mutation_param}")

        if target_name.__contains__(","):
            names_list = [n.strip() for n in target_name.split(",")]
        else:
            names_list = [target_name]

        if logical_equation is None:
            logical_equation_components = []
        else:
            logical_equation_striped = [n.strip() for n in logical_equation.split(" ")]
            logical_equation_components = ComputeLogicalExpression.parse_logical_expression(logical_equation_striped)
            count_members = len(list(filter(lambda m: m != '(' and m != ')' and m != '', logical_equation_striped)))
            #print(count_members, Parser.counting_members_logical_query(logical_equation_components))
            if Parser.counting_members_logical_query(logical_equation_components) != count_members:
                raise ErrorInLogicalExpressionNonOpeningParenthesis(
                    ("An error has occurred in the logical equation, please check it. "
                     "A parenthesis is not opened or a space might be missing. Result : ",
                     logical_equation_components))

    # ----- This might need reworking, for the moment this part of the query is not used. -----------------------
        if mutation_param is None:
            mutation_param_final = []
        else:
            mutation_param_final = []
            #print(mutation_param)
            mutations_striped = [n.strip() for n in mutation_param.split(" ")]
            for m in iter(mutations_striped):
                if m == '':
                    mutations_striped.remove(m)
            #print(mutations_striped)
            if len(mutations_striped) == 0:
                raise ValueError("Mutation parameter cannot be empty")
            for mut in mutations_striped:
                mutation_param_striped = [n.strip() for n in mut.split(":")]
                if mutation_param_striped[1] not in ["ON", "OFF"]:
                    raise ValueError(f"Mutation parameter \"{mutation_param_striped[1]}\" is not supported, try ON or OFF")
                mutation_param_final.append([mutation_param_striped[0], mutation_param_striped[1]]) #0 being name of the mutation, 1 being the value (OFF or ON)
        # -----------------------------------------------------------------------------------------------------------

        if initial_state is None:
            initial_state_final = []
        else:
            initial_state_final = []
            i_s_striped = [n.strip() for n in initial_state.split(" ")]
            for i_s in iter(i_s_striped):
                i_s_param = [n.strip() for n in i_s.split(":")]
                if i_s_param[1] not in ["ON", "OFF"]:
                    raise ValueError(f"Initial state parameter \"{i_s_param[1]}\" is not supported, try ON or OFF")
                initial_state_final.append([i_s_param[0], i_s_param[1]])

        # Conversion of types, with try/catch to handle errors
        try:
            _type = QueryType(query_type)
        except ValueError:
            raise ValueError(f"Query type \"{query_type}\" is not supported, try P, T, Pmax, Pmin, Tmax, Tmin, M, D, "
                             f"Inc or Dec")

        try:
            #print(operator)
            _op = Operators(operator)
        except ValueError:
            raise ValueError(f"Operator \"{operator}\" is not supported, try <, <=, =, !=, >=, >, /")

        try:
            _target = TargetType(target)
        except ValueError:
            raise ValueError(f"Target \"{target}\" is not supported, try node, state or fixpoint")

        return Formula(
            type=_type,
            target=_target,
            target_name=names_list,  # an array of names
            operator=_op,
            value=str(value),
            logical_equation=logical_equation_components,
            mutation_constraint=mutation_param_final,
            initial_state_constraint=initial_state_final,

            expression=input,
        )

    @staticmethod
    def counting_members_logical_query(logical_query, count=0):
        #print(logical_query)
        for m in logical_query:
            if isinstance(m, list):
                count = Parser.counting_members_logical_query(m, count)
            else:
                count += 1
        return count
