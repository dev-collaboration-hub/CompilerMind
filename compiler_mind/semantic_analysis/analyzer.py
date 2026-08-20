from __future__ import annotations

from .errors import SemanticDiagnostic, SemanticReport
from .nodes import (
    Assign,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    CharLiteral,
    ExprStmt,
    FloatLiteral,
    FunctionDecl,
    Identifier,
    IfStmt,
    IntLiteral,
    Program,
    ReturnStmt,
    UnaryExpr,
    VarDecl,
    WhileStmt,
)
from .symbols import Symbol, SymbolKind, SymbolTable
from .types import (
    BOOL,
    CHAR,
    ERROR,
    FLOAT,
    INT,
    VOID,
    SemanticType,
    binary_result_type,
    is_assignable,
    resolve_type,
    unary_result_type,
)


class SemanticAnalyzer:
    """Deterministic semantic analyzer for CompilerMind's semantic AST."""

    def __init__(self) -> None:
        self.symbols = SymbolTable()
        self._diagnostics: list[SemanticDiagnostic] = []
        self._return_type: SemanticType | None = None
        self._scope_counter = 0

    def analyze(self, program: Program) -> SemanticReport:
        self.symbols = SymbolTable()
        self._diagnostics = []
        self._return_type = None
        self._scope_counter = 0

        for item in program.items:
            if isinstance(item, FunctionDecl):
                self._declare_function_signature(item)

        for item in program.items:
            self._analyze_statement(item)

        return SemanticReport(tuple(self._diagnostics))

    def _diagnose(self, code: str, message: str) -> None:
        self._diagnostics.append(SemanticDiagnostic(code, message))

    def _type_from_name(self, name: str, context: str) -> SemanticType:
        semantic_type = resolve_type(name)
        if semantic_type is None:
            self._diagnose("UNKNOWN_TYPE", f"Unknown type {name!r} in {context}.")
            return ERROR
        return semantic_type

    def _declare_function_signature(self, function: FunctionDecl) -> None:
        return_type = self._type_from_name(
            function.return_type,
            f"function {function.name!r} return type",
        )
        parameter_types = tuple(
            self._type_from_name(
                parameter.type_name,
                f"parameter {parameter.name!r} of function {function.name!r}",
            )
            for parameter in function.parameters
        )
        symbol = Symbol(
            function.name,
            SymbolKind.FUNCTION,
            return_type,
            parameter_types,
        )
        if not self.symbols.global_scope.declare(symbol):
            self._diagnose(
                "DUPLICATE_DECLARATION",
                f"Duplicate global declaration {function.name!r}.",
            )

    def _analyze_statement(self, statement: object) -> None:
        if isinstance(statement, VarDecl):
            self._analyze_var_decl(statement)
            return
        if isinstance(statement, Assign):
            self._analyze_assignment(statement)
            return
        if isinstance(statement, ExprStmt):
            self._expression_type(statement.expression)
            return
        if isinstance(statement, Block):
            self._analyze_block(statement)
            return
        if isinstance(statement, IfStmt):
            self._require_bool(statement.condition, "if condition")
            self._analyze_block(statement.then_branch)
            if statement.else_branch is not None:
                self._analyze_block(statement.else_branch)
            return
        if isinstance(statement, WhileStmt):
            self._require_bool(statement.condition, "while condition")
            self._analyze_block(statement.body)
            return
        if isinstance(statement, ReturnStmt):
            self._analyze_return(statement)
            return
        if isinstance(statement, FunctionDecl):
            self._analyze_function(statement)
            return
        self._diagnose(
            "UNSUPPORTED_NODE",
            f"Unsupported semantic node {type(statement).__name__}.",
        )

    def _analyze_block(self, block: Block, *, create_scope: bool = True) -> None:
        if create_scope:
            self._scope_counter += 1
            self.symbols.enter_scope(f"block:{self._scope_counter}")
        try:
            for statement in block.statements:
                self._analyze_statement(statement)
        finally:
            if create_scope:
                self.symbols.exit_scope()

    def _analyze_var_decl(self, declaration: VarDecl) -> None:
        declared_type = self._type_from_name(
            declaration.type_name,
            f"declaration {declaration.name!r}",
        )
        if declared_type == VOID:
            self._diagnose(
                "INVALID_VARIABLE_TYPE",
                f"Variable {declaration.name!r} cannot have type void.",
            )
            declared_type = ERROR

        symbol = Symbol(declaration.name, SymbolKind.VARIABLE, declared_type)
        if not self.symbols.declare(symbol):
            self._diagnose(
                "DUPLICATE_DECLARATION",
                f"{declaration.name!r} is already declared in this scope.",
            )

        if declaration.initializer is not None:
            initializer_type = self._expression_type(declaration.initializer)
            if not is_assignable(declared_type, initializer_type):
                self._diagnose(
                    "TYPE_MISMATCH",
                    f"Cannot initialize {declaration.name!r} of type "
                    f"{declared_type.name} with {initializer_type.name}.",
                )

    def _analyze_assignment(self, assignment: Assign) -> None:
        symbol = self.symbols.resolve(assignment.name)
        value_type = self._expression_type(assignment.value)
        if symbol is None:
            self._diagnose(
                "UNDEFINED_IDENTIFIER",
                f"Identifier {assignment.name!r} is not declared.",
            )
            return
        if symbol.kind == SymbolKind.FUNCTION:
            self._diagnose(
                "NOT_ASSIGNABLE",
                f"Function {assignment.name!r} cannot be assigned to.",
            )
            return
        if not is_assignable(symbol.type, value_type):
            self._diagnose(
                "TYPE_MISMATCH",
                f"Cannot assign {value_type.name} to {assignment.name!r} "
                f"of type {symbol.type.name}.",
            )

    def _analyze_function(self, function: FunctionDecl) -> None:
        symbol = self.symbols.resolve_global(function.name)
        if symbol is None or symbol.kind != SymbolKind.FUNCTION:
            return

        previous_return_type = self._return_type
        self._return_type = symbol.type
        self.symbols.enter_scope(f"function:{function.name}")
        try:
            for parameter, parameter_type in zip(
                function.parameters,
                symbol.parameter_types,
            ):
                if parameter_type == VOID:
                    self._diagnose(
                        "INVALID_PARAMETER_TYPE",
                        f"Parameter {parameter.name!r} cannot have type void.",
                    )
                    parameter_type = ERROR
                if not self.symbols.declare(
                    Symbol(parameter.name, SymbolKind.PARAMETER, parameter_type)
                ):
                    self._diagnose(
                        "DUPLICATE_DECLARATION",
                        f"Duplicate parameter {parameter.name!r} in "
                        f"function {function.name!r}.",
                    )
            self._analyze_block(function.body, create_scope=False)
        finally:
            self.symbols.exit_scope()
            self._return_type = previous_return_type

    def _analyze_return(self, statement: ReturnStmt) -> None:
        if self._return_type is None:
            self._diagnose(
                "RETURN_OUTSIDE_FUNCTION",
                "Return statement used outside a function.",
            )
            if statement.value is not None:
                self._expression_type(statement.value)
            return

        if statement.value is None:
            if self._return_type != VOID and not self._return_type.error:
                self._diagnose(
                    "RETURN_TYPE_MISMATCH",
                    f"Expected return value of type {self._return_type.name}.",
                )
            return

        value_type = self._expression_type(statement.value)
        if self._return_type == VOID:
            self._diagnose(
                "RETURN_TYPE_MISMATCH",
                "Void function cannot return a value.",
            )
            return
        if not is_assignable(self._return_type, value_type):
            self._diagnose(
                "RETURN_TYPE_MISMATCH",
                f"Cannot return {value_type.name} from function returning "
                f"{self._return_type.name}.",
            )

    def _require_bool(self, expression: object, context: str) -> None:
        expression_type = self._expression_type(expression)
        if expression_type not in {BOOL, ERROR}:
            self._diagnose(
                "CONDITION_TYPE",
                f"{context} must be bool, got {expression_type.name}.",
            )

    def _expression_type(self, expression: object) -> SemanticType:
        if isinstance(expression, IntLiteral):
            return INT
        if isinstance(expression, FloatLiteral):
            return FLOAT
        if isinstance(expression, BoolLiteral):
            return BOOL
        if isinstance(expression, CharLiteral):
            return CHAR
        if isinstance(expression, Identifier):
            symbol = self.symbols.resolve(expression.name)
            if symbol is None:
                self._diagnose(
                    "UNDEFINED_IDENTIFIER",
                    f"Identifier {expression.name!r} is not declared.",
                )
                return ERROR
            if symbol.kind == SymbolKind.FUNCTION:
                self._diagnose(
                    "NOT_VALUE",
                    f"Function {expression.name!r} must be called to produce a value.",
                )
                return ERROR
            return symbol.type
        if isinstance(expression, BinaryExpr):
            left = self._expression_type(expression.left)
            right = self._expression_type(expression.right)
            result = binary_result_type(expression.operator, left, right)
            if result is None:
                self._diagnose(
                    "INVALID_OPERANDS",
                    f"Operator {expression.operator!r} cannot be applied to "
                    f"{left.name} and {right.name}.",
                )
                return ERROR
            return result
        if isinstance(expression, UnaryExpr):
            operand = self._expression_type(expression.operand)
            result = unary_result_type(expression.operator, operand)
            if result is None:
                self._diagnose(
                    "INVALID_OPERAND",
                    f"Operator {expression.operator!r} cannot be applied to "
                    f"{operand.name}.",
                )
                return ERROR
            return result
        if isinstance(expression, CallExpr):
            return self._call_type(expression)

        self._diagnose(
            "UNSUPPORTED_EXPRESSION",
            f"Unsupported expression {type(expression).__name__}.",
        )
        return ERROR

    def _call_type(self, call: CallExpr) -> SemanticType:
        symbol = self.symbols.resolve(call.name)
        argument_types = tuple(self._expression_type(arg) for arg in call.arguments)
        if symbol is None:
            self._diagnose(
                "UNDEFINED_IDENTIFIER",
                f"Function {call.name!r} is not declared.",
            )
            return ERROR
        if symbol.kind != SymbolKind.FUNCTION:
            self._diagnose(
                "NOT_CALLABLE",
                f"{call.name!r} is not a function.",
            )
            return ERROR

        if len(argument_types) != len(symbol.parameter_types):
            self._diagnose(
                "ARGUMENT_COUNT",
                f"Function {call.name!r} expects {len(symbol.parameter_types)} "
                f"arguments, got {len(argument_types)}.",
            )
        for index, (actual, expected) in enumerate(
            zip(argument_types, symbol.parameter_types),
            start=1,
        ):
            if not is_assignable(expected, actual):
                self._diagnose(
                    "ARGUMENT_TYPE",
                    f"Argument {index} of {call.name!r} expects {expected.name}, "
                    f"got {actual.name}.",
                )
        return symbol.type
