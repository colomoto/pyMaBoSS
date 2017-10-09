"""utilitary functions to manipulate boolean expressions."""


from sys import stderr
import pyparsing as pp

logExp = pp.Forward()
boolCst = pp.oneOf("True False")
boolNot = pp.oneOf("! NOT")
boolAnd = pp.oneOf("&& & AND")
boolOr = pp.oneOf("|| | OR")
boolXor = pp.oneOf("^ XOR")
varName = (~boolAnd + ~boolOr + ~boolXor + ~boolNot + ~boolCst
           + pp.Word(pp.alphas, pp.alphanums+'_'))
lparen = pp.Suppress('(')
rparen = pp.Suppress(')')
logTerm = (pp.Optional(boolNot)
            +( boolCst | varName | pp.Group(lparen + logExp + rparen)))
logAnd = pp.Group(logTerm + pp.ZeroOrMore(boolAnd + logTerm))
logOr = pp.Group(logAnd + pp.ZeroOrMore(boolOr + logAnd))
logExp << pp.Group(logOr + pp.ZeroOrMore(boolXor + logOr))


def _check_logic_syntax(string):
    """Return True iff string is a syntaxically correct boolean expression."""
    return logExp.matches(string)


def _check_logic_defined(name_list, logic_list):
    """Check if the list of logic is consistant.

    Return True iff all expression in logic_list are syntaxically correct and
    all contains only variables present in name_list.
    """
    _check_logic_defined.failed = False

    # We modify the behaviour of boolExp.parseString so that the parsing also
    # check if variables exist.
    def check_var(var):
        if var[0] not in name_list:
            print("Error: unkown varriable %s" % var[0], file=stderr)
            _check_logic_defined.failed = True
        return var

    varName.setParseAction(check_var)

    for string in logic_list:
        if not _check_logic_syntax(string):
            print("Error: syntax error %s" % string, file=stderr)
            return False
        if _check_logic_defined.failed:
            varName.setParseAction(lambda x: x)
            return False

    varName.setParseAction(lambda x: x)
    return True
