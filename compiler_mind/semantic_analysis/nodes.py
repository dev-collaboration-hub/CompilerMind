from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IntLiteral:
    value: int


@dataclass(frozen=True, slots=True)
class FloatLiteral:
    value: float


@dataclass(frozen=True, slots=True)
class BoolLiteral:
    value: bool


@dataclass(frozen=True, slots=True)
class CharLiteral:
    value: str

    def __post_init__(self) -> None:
        if len(self.value) != 1:
            raise ValueError("CharLiteral requires exactly one character.")


@dataclass(frozen=True, slots=True)
class Identifier:
    name: str


@dataclass(frozen=True, slots=True)
class BinaryExpr:
    operator: str
    left: object
    right: object


@dataclass(frozen=True, slots=True)
class UnaryExpr:
    operator: str
    operand: object


@dataclass(frozen=True, slots=True)
class CallExpr:
    name: str
    arguments: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class VarDecl:
    name: str
    type_name: str
    initializer: object | None = None


@dataclass(frozen=True, slots=True)
class Assign:
    name: str
    value: object


@dataclass(frozen=True, slots=True)
class ExprStmt:
    expression: object


@dataclass(frozen=True, slots=True)
class Block:
    statements: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class IfStmt:
    condition: object
    then_branch: Block
    else_branch: Block | None = None


@dataclass(frozen=True, slots=True)
class WhileStmt:
    condition: object
    body: Block


@dataclass(frozen=True, slots=True)
class ReturnStmt:
    value: object | None = None


@dataclass(frozen=True, slots=True)
class Parameter:
    name: str
    type_name: str


@dataclass(frozen=True, slots=True)
class FunctionDecl:
    name: str
    parameters: tuple[Parameter, ...]
    return_type: str
    body: Block


@dataclass(frozen=True, slots=True)
class Program:
    items: tuple[object, ...] = ()
