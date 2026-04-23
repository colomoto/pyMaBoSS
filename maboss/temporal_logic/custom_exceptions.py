class FormulaException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class EmptyTargetException(FormulaException):
    def __init__(self):
        super().__init__("Target name is empty, the formula must apply to node or state")

class EmptyNameException(FormulaException):
    def __init__(self):
        super().__init__("One of the target name is empty, the formula must apply to one or multiple columns")

class NoNameException(FormulaException):
    def __init__(self):
        super().__init__("No target name is given, the formula must apply to one or multiple columns. For all columns type : *")

class NoNameValidException(FormulaException):
    def __init__(self):
        super().__init__("No valid target name was given, the formula must apply to one or multiple columns")

class EmptyValueException(FormulaException):
    def __init__(self):
        super().__init__("Value is empty, , must put a float number or a \"?\"")

class WrongSymbolForValue(FormulaException):
    def __init__(self, message):
        super().__init__(message)

class WrongGrammarException(FormulaException):
    def __init__(self, message):
        super().__init__(message)

class WrongValueAccordingToType(FormulaException):
    def __init__(self, message):
        super().__init__(message)

class DataFrameIsEmpty(FormulaException):
    def __init__(self, message):
        super().__init__(message)

class ErrorInLogicalExpression(FormulaException):
    def __init__(self, message):
        super().__init__(message)

class ErrorInLogicalExpressionNonOpeningParenthesis(FormulaException):
    def __init__(self, message):
        super().__init__(message)

class ErrorMinMaxOnlyForOneEntity(FormulaException):
    def __init__(self, message):
        super().__init__(message)
