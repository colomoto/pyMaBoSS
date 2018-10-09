"""Function to import the ginsim out in Python.

The ginsim output is a special case of MaBoSS format. This parser uses
the very specific structure of the ginsim output and not able to parse every
MaBoSS file.
"""

import sys
from sys import stderr
from os.path import isfile
import pyparsing as pp
from .logic import varName, logExp
from contextlib import ExitStack
from .network import Node, Network
from .simulation import Simulation
externVar = pp.Suppress('$') + ~pp.White() + varName
externVar.setParseAction(lambda token: token[0])
import uuid

# ====================
# bnd grammar
# ====================
internal_var_decl = pp.Group(varName('lhs') + pp.Suppress('=')
                             + pp.SkipTo(';')('rhs') + pp.Suppress(';'))
node_decl = pp.Group(pp.Suppress(pp.CaselessKeyword("Node")) + varName("name") + pp.Suppress('{')
                     + pp.OneOrMore(internal_var_decl)('interns')
                     + pp.Suppress('}'))
bnd_grammar = pp.OneOrMore(node_decl)
bnd_grammar.ignore('//' + pp.restOfLine)

# =====================
# cfg grammar
# =====================

intPart = pp.Word(pp.nums)
intPart.setParseAction(lambda token: int(token[0]))
floatNum = pp.Word(pp.nums + '.' + 'E' + 'e' + '-' + '+')
floatNum.setParseAction(lambda token: float(token[0]))
booleanStr = (pp.oneOf('0 1')
              | pp.CaselessLiteral("True") | pp.CaselessLiteral("False"))


def booleanStrAction(token):
    if pp.CaselessLiteral("True").matches(token):
        return '1'
    elif pp.CaselessLiteral("False").matches(token):
        return '0'
    else:
        return token


booleanStr.setParseAction(lambda token: booleanStrAction(token[0]))
numOrBool = (floatNum | booleanStr)("value")

var_decl = pp.Group(externVar("lhs") + pp.Suppress('=')
                    + pp.SkipTo(';')("rhs") + pp.Suppress(';'))


param_decl = pp.Group(varName("param") + pp.Suppress('=')
                      + numOrBool + pp.Suppress(';'))

stateSet = (pp.Suppress('[') + pp.Group(pp.delimitedList(intPart))
            + pp.Suppress(']'))
stateSet.setParseAction(lambda token: list(token))

stateProb = floatNum('proba') + stateSet("states")
stateProb.setParseAction(lambda token: (token.proba, token.states))

istate_decl = pp.Group(pp.Suppress('[') + pp.delimitedList(varName)("nodes")
                       + pp.Suppress('].istate') + pp.Suppress('=')
                       + pp.delimitedList(stateProb)('attrib') + pp.Suppress(';'))

oneIstate_decl = pp.Group(varName("nd_i") + ~pp.White() + pp.Suppress('.istate')
                          + pp.Suppress('=') + booleanStr('istate_val')
                          + pp.Suppress(';'))

internal_decl = pp.Group(varName("node") + ~pp.White()
                         + pp.Suppress(".is_internal") + pp.Suppress('=')
                         + booleanStr("is_internal_val")
                         + pp.Suppress(';'))

refstate_decl = pp.Group(varName("node") + ~pp.White()
                         + pp.Suppress(".refstate") + pp.Suppress('=')
                         + booleanStr("refstate_val")
                         + pp.Suppress(';'))

cfg_decl = (var_decl | istate_decl | param_decl | internal_decl
            | oneIstate_decl | refstate_decl)
cfg_grammar = pp.ZeroOrMore(cfg_decl)
cfg_grammar.ignore('//' + pp.restOfLine)


def load(bnd_filename, cfg_filename):
    """Loads a network from a MaBoSS format file.

    :param str bnd_filename: Network file
    :param str cfg_filename: Configuraton file
    :keyword str simulation_name: name of the returned :py:class:`.Simulation` object
    :rtype: :py:class:`.Simulation`
    """
    assert bnd_filename.lower().endswith(".bnd"), "wrong extension for bnd file"
    assert cfg_filename.lower().endswith(".cfg"), "wrong extension for cfg file"

    with ExitStack() as stack:
        bnd_file = stack.enter_context(open(bnd_filename, 'r'))
        cfg_file = stack.enter_context(open(cfg_filename, 'r'))
        bnd_content = bnd_file.read()
        cfg_content = cfg_file.read()

        (variables, parameters, is_internal_list,
         istate_list, refstate_list) = _read_cfg(cfg_content)

        nodes = _read_bnd(bnd_content, is_internal_list)

        # Some boolean variables can be defined in the .cfg and used in the .bnd
        # We need to know about them when checking the logical formulae.
        boolean_variables = ["$%s" % var for var, value in variables.items() if value in ['TRUE', 'FALSE']]

        net = Network(nodes, boolean_variables)
        for istate in istate_list:
            net.set_istate(istate, istate_list[istate])
        for v in variables:
            lhs = '$'+v
            parameters[lhs] = variables[v]
        ret = Simulation(net, **parameters)
        ret.refstate = refstate_list
        return ret


def _read_cfg(string):
        variables = {}
        parameters = {}
        is_internal_list = {}
        istate_list = {}
        refstate_list = {}
        parse_cfg = cfg_grammar.parseString(string)
        for token in parse_cfg:
            if token.lhs:  # True if token is var_decl
                variables[token.lhs] = token.rhs
            if token.is_internal_val:  # True if token is internal_decl
                is_internal_list[token.node] = token.is_internal_val
            if token.refstate_val:
                refstate_list[token.node] = token.refstate_val
            if token.param:  # True if token is param_decl
                parameters[token.param] = float(token.value)
            if token.nd_i:
                istate_list[token.nd_i] = {0: 1 - int(token.istate_val),
                                           1: int(token.istate_val)}
            if token.attrib:  # True if token is istate_decl
                # TODO check if lens are consistent
                if len(token.nodes) == 1:
                    istate_list[token.nodes[0]] = {int(t[1][0]): t[0]
                                                   for t in token.attrib}
                else:
                    nodes = tuple(token.nodes)
                    istate_list[nodes] = {tuple(t[1]): t[0]
                                          for t in token.attrib}

        return (variables, parameters, is_internal_list, istate_list,
                refstate_list)


def _read_bnd(string, is_internal_list):
        nodes = []
        parse_bnd = bnd_grammar.parseString(string)

        for token in parse_bnd:
            interns = {v.lhs: v.rhs for v in token.interns}
            logic = interns.pop('logic') if 'logic' in interns else None
            rate_up = interns.pop('rate_up')
            rate_down = interns.pop('rate_down')

            internal = (is_internal_list[token.name]
                        if token.name in is_internal_list
                        else False)
            nodes.append(Node(token.name, logic, rate_up, rate_down,
                              internal, interns))
        return nodes
