"""utilitary functions to manipulate boolean expressions."""

from __future__ import print_function
import pyparsing as pp

boolCst = pp.oneOf("True False")
boolNot = pp.oneOf("! NOT")
boolAnd = pp.oneOf("&& & AND")
boolOr = pp.oneOf("|| | OR")
boolXor = pp.oneOf("^ XOR")
boolTest = pp.Literal("?")
boolElse = pp.Literal(":")
varName = (~boolAnd + ~boolOr + ~boolXor + ~boolNot + ~boolCst + ~boolTest + ~boolElse
           + ~pp.Literal('Node') + pp.Word(pp.alphas+'$', pp.alphanums+'_'))
varName.setParseAction(lambda token: token[0])
