from __future__ import annotations

from compiler_mind.semantic_analysis.nodes import (
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

from .model import IRProgram, Quadruple


class IRGenerationError(ValueError):
    """Raised when a semantic AST cannot be lowered into IR."""


class IRGenerator:
    """Lower CompilerMind's semantic AST into deterministic quadruple IR."""

    def __init__(self) -> None:
        self._instructions: list[Quadruple] = []
        self._temp_counter = 0
        self._label_counter = 0
        self._function_returns: dict[str, str] = {}

    def generate(self, program: Program, *, validate: bool = True) -> IRProgram:
        if validate:
            from compiler_mind.semantic_analysis import SemanticAnalyzer

            report = SemanticAnalyzer().analyze(program)
            if not report.valid:
                messages = "; ".join(
                    diagnostic.message for diagnostic in report.diagnostics
                )
                raise IRGenerationError(f"Semantic analysis failed: {messages}")

        self._instructions = []
        self._temp_counter = 0
        self._label_counter = 0
        self._function_returns = {
            item.name: item.return_type
            for item in program.items
            if isinstance(item, FunctionDecl)
        }

        for item in program.items:
            self._statement(item)

        return IRProgram(tuple(self._instructions))

    def _emit(
        self,
        op: str,
        arg1: str | None = None,
        arg2: str | None = None,
        result: str | None = None,
    ) -> None:
        self._instructions.append(Quadruple(op, arg1, arg2, result))

    def _temp(self) -> str:
        self._temp_counter += 1
        return f"%t{self._temp_counter}"

    def _label(self, stem: str) -> str:
        self._label_counter += 1
        return f"{stem}_{self._label_counter}"

    def _statement(self, node: object) -> None:
        if isinstance(node, VarDecl):
            self._emit("declare", node.type_name, result=node.name)
            if node.initializer is not None:
                value = self._expression(node.initializer)
                self._emit("assign", value, result=node.name)
            return

        if isinstance(node, Assign):
            self._emit("assign", self._expression(node.value), result=node.name)
            return

        if isinstance(node, ExprStmt):
            if (
                isinstance(node.expression, CallExpr)
                and self._function_returns.get(node.expression.name) == "void"
            ):
                self._call(node.expression, want_result=False)
            else:
                self._expression(node.expression)
            return

        if isinstance(node, Block):
            for statement in node.statements:
                self._statement(statement)
            return

        if isinstance(node, IfStmt):
            self._if_statement(node)
            return

        if isinstance(node, WhileStmt):
            self._while_statement(node)
            return

        if isinstance(node, ReturnStmt):
            value = None if node.value is None else self._expression(node.value)
            self._emit("return", value)
            return

        if isinstance(node, FunctionDecl):
            self._function(node)
            return

        raise IRGenerationError(
            f"Unsupported statement node: {type(node).__name__}"
        )

    def _if_statement(self, node: IfStmt) -> None:
        condition = self._expression(node.condition)

        if node.else_branch is None:
            end_label = self._label("if_end")
            self._emit("if_false", condition, result=end_label)
            self._statement(node.then_branch)
            self._emit("label", result=end_label)
            return

        else_label = self._label("else")
        end_label = self._label("if_end")
        self._emit("if_false", condition, result=else_label)
        self._statement(node.then_branch)
        self._emit("goto", result=end_label)
        self._emit("label", result=else_label)
        self._statement(node.else_branch)
        self._emit("label", result=end_label)

    def _while_statement(self, node: WhileStmt) -> None:
        start_label = self._label("while_start")
        end_label = self._label("while_end")

        self._emit("label", result=start_label)
        condition = self._expression(node.condition)
        self._emit("if_false", condition, result=end_label)
        self._statement(node.body)
        self._emit("goto", result=start_label)
        self._emit("label", result=end_label)

    def _function(self, node: FunctionDecl) -> None:
        self._emit("func_begin", result=node.name)
        for parameter in node.parameters:
            self._emit("param_decl", parameter.type_name, result=parameter.name)
        self._statement(node.body)
        self._emit("func_end", result=node.name)

    def _expression(self, node: object) -> str:
        if isinstance(node, IntLiteral):
            return str(node.value)
        if isinstance(node, FloatLiteral):
            return repr(node.value)
        if isinstance(node, BoolLiteral):
            return "true" if node.value else "false"
        if isinstance(node, CharLiteral):
            return repr(node.value)
        if isinstance(node, Identifier):
            return node.name

        if isinstance(node, BinaryExpr):
            left = self._expression(node.left)
            right = self._expression(node.right)
            temporary = self._temp()
            self._emit(node.operator, left, right, temporary)
            return temporary

        if isinstance(node, UnaryExpr):
            operand = self._expression(node.operand)
            temporary = self._temp()
            self._emit(f"u{node.operator}", operand, result=temporary)
            return temporary

        if isinstance(node, CallExpr):
            return self._call(node, want_result=True)

        raise IRGenerationError(
            f"Unsupported expression node: {type(node).__name__}"
        )

    def _call(self, node: CallExpr, *, want_result: bool) -> str:
        arguments = [self._expression(argument) for argument in node.arguments]
        for argument in arguments:
            self._emit("param", argument)

        if not want_result:
            self._emit("call", node.name, str(len(arguments)))
            return "void"

        temporary = self._temp()
        self._emit("call", node.name, str(len(arguments)), temporary)
        return temporary
