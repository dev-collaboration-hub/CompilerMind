from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SemanticType:
    name: str
    numeric_rank: int | None = None
    logical: bool = False
    void: bool = False
    error: bool = False

    @property
    def numeric(self) -> bool:
        return self.numeric_rank is not None


CHAR = SemanticType("char", numeric_rank=0)
INT = SemanticType("int", numeric_rank=1)
FLOAT = SemanticType("float", numeric_rank=2)
BOOL = SemanticType("bool", logical=True)
VOID = SemanticType("void", void=True)
ERROR = SemanticType("<error>", error=True)

BUILTIN_TYPES = {
    item.name: item
    for item in (CHAR, INT, FLOAT, BOOL, VOID)
}


def resolve_type(name: str) -> SemanticType | None:
    return BUILTIN_TYPES.get(name)


def is_assignable(target: SemanticType, source: SemanticType) -> bool:
    if target.error or source.error:
        return True
    if target == source:
        return True
    if target.numeric and source.numeric:
        return source.numeric_rank <= target.numeric_rank  # type: ignore[operator]
    return False


def common_numeric_type(left: SemanticType, right: SemanticType) -> SemanticType | None:
    if not left.numeric or not right.numeric:
        return None
    return left if left.numeric_rank >= right.numeric_rank else right  # type: ignore[operator]


def binary_result_type(
    operator: str,
    left: SemanticType,
    right: SemanticType,
) -> SemanticType | None:
    if left.error or right.error:
        return ERROR

    if operator in {"+", "-", "*", "/"}:
        return common_numeric_type(left, right)

    if operator == "%":
        if left in {CHAR, INT} and right in {CHAR, INT}:
            return INT
        return None

    if operator in {"<", "<=", ">", ">="}:
        return BOOL if common_numeric_type(left, right) is not None else None

    if operator in {"==", "!="}:
        if left == right:
            return BOOL
        if left.numeric and right.numeric:
            return BOOL
        return None

    if operator in {"&&", "||"}:
        return BOOL if left == BOOL and right == BOOL else None

    return None


def unary_result_type(operator: str, operand: SemanticType) -> SemanticType | None:
    if operand.error:
        return ERROR
    if operator in {"+", "-"} and operand.numeric:
        return operand
    if operator == "!" and operand == BOOL:
        return BOOL
    return None
