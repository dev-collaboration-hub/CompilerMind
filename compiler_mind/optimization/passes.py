from __future__ import annotations

import ast
import operator
from collections import Counter

from compiler_mind.intermediate_code.model import IRProgram, Quadruple

_MISSING = object()
_BINARY_FOLDERS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "%": operator.mod,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
    "&&": lambda a, b: bool(a) and bool(b),
    "||": lambda a, b: bool(a) or bool(b),
}
_UNARY_FOLDERS = {
    "u+": operator.pos,
    "u-": operator.neg,
    "u!": lambda a: not bool(a),
}
_COMMUTATIVE = {"+", "*", "==", "!=", "&&", "||"}
_BOUNDARY_OPS = {"label", "goto", "if_false", "return", "func_begin", "func_end", "call"}


def _literal(value: str | None):
    if value is None:
        return _MISSING
    if value == "true":
        return True
    if value == "false":
        return False
    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return _MISSING
    if isinstance(parsed, (int, float, str, bool)):
        return parsed
    return _MISSING


def _format_literal(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return repr(value)
    return repr(value)


def _is_temp(value: str | None) -> bool:
    return bool(value and value.startswith("%t"))


def constant_folding(program: IRProgram) -> tuple[IRProgram, int]:
    out: list[Quadruple] = []
    changes = 0
    for ins in program.instructions:
        if ins.op in _BINARY_FOLDERS and ins.result is not None:
            left = _literal(ins.arg1)
            right = _literal(ins.arg2)
            if left is not _MISSING and right is not _MISSING:
                try:
                    value = _BINARY_FOLDERS[ins.op](left, right)
                except (ArithmeticError, TypeError, ValueError):
                    out.append(ins)
                else:
                    out.append(Quadruple("assign", _format_literal(value), result=ins.result))
                    changes += 1
                continue
        if ins.op in _UNARY_FOLDERS and ins.result is not None:
            operand = _literal(ins.arg1)
            if operand is not _MISSING:
                try:
                    value = _UNARY_FOLDERS[ins.op](operand)
                except (ArithmeticError, TypeError, ValueError):
                    out.append(ins)
                else:
                    out.append(Quadruple("assign", _format_literal(value), result=ins.result))
                    changes += 1
                continue
        out.append(ins)
    return IRProgram(tuple(out)), changes


def constant_propagation(program: IRProgram) -> tuple[IRProgram, int]:
    constants: dict[str, str] = {}
    out: list[Quadruple] = []
    changes = 0

    def subst(value: str | None) -> str | None:
        return constants.get(value, value) if value is not None else None

    for ins in program.instructions:
        if ins.op in {"label", "func_begin", "func_end"}:
            constants.clear()

        arg1, arg2 = ins.arg1, ins.arg2
        if ins.op not in {"declare", "param_decl", "call"}:
            arg1 = subst(arg1)
            arg2 = subst(arg2)

        rewritten = Quadruple(ins.op, arg1, arg2, ins.result)
        if rewritten != ins:
            changes += 1
        out.append(rewritten)

        if ins.result is not None:
            constants.pop(ins.result, None)
        if ins.op == "assign" and ins.result is not None and _literal(arg1) is not _MISSING:
            constants[ins.result] = arg1  # type: ignore[index]

        if ins.op in {"goto", "if_false", "return", "call"}:
            constants.clear()

    return IRProgram(tuple(out)), changes


def copy_propagation(program: IRProgram) -> tuple[IRProgram, int]:
    copies: dict[str, str] = {}
    out: list[Quadruple] = []
    changes = 0

    def resolve(value: str | None) -> str | None:
        if value is None:
            return None
        seen: set[str] = set()
        while value in copies and value not in seen:
            seen.add(value)
            value = copies[value]
        return value

    def invalidate(name: str) -> None:
        copies.pop(name, None)
        for key, value in tuple(copies.items()):
            if value == name:
                copies.pop(key, None)

    for ins in program.instructions:
        if ins.op in {"label", "func_begin", "func_end"}:
            copies.clear()

        arg1, arg2 = ins.arg1, ins.arg2
        if ins.op not in {"declare", "param_decl", "call"}:
            arg1 = resolve(arg1)
            arg2 = resolve(arg2)

        rewritten = Quadruple(ins.op, arg1, arg2, ins.result)
        if rewritten != ins:
            changes += 1
        out.append(rewritten)

        if ins.result is not None:
            invalidate(ins.result)
        if (
            ins.op == "assign"
            and ins.result is not None
            and arg1 is not None
            and _literal(arg1) is _MISSING
            and arg1 != ins.result
        ):
            copies[ins.result] = arg1

        if ins.op in {"goto", "if_false", "return", "call"}:
            copies.clear()

    return IRProgram(tuple(out)), changes


def common_subexpression_elimination(program: IRProgram) -> tuple[IRProgram, int]:
    expressions: dict[tuple[str, str | None, str | None], str] = {}
    out: list[Quadruple] = []
    changes = 0

    for ins in program.instructions:
        if ins.op in _BOUNDARY_OPS:
            expressions.clear()

        if ins.op == "assign" and ins.result and not _is_temp(ins.result):
            expressions.clear()

        if ins.op in (set(_BINARY_FOLDERS) | set(_UNARY_FOLDERS)) and ins.result is not None:
            arg1, arg2 = ins.arg1, ins.arg2
            if ins.op in _COMMUTATIVE and arg1 is not None and arg2 is not None and arg2 < arg1:
                arg1, arg2 = arg2, arg1
            key = (ins.op, arg1, arg2)
            existing = expressions.get(key)
            if existing is not None:
                out.append(Quadruple("assign", existing, result=ins.result))
                changes += 1
            else:
                out.append(ins)
                expressions[key] = ins.result
            continue

        out.append(ins)

    return IRProgram(tuple(out)), changes


def peephole_optimization(program: IRProgram) -> tuple[IRProgram, int]:
    stage: list[Quadruple] = []
    changes = 0

    for ins in program.instructions:
        if ins.op == "assign" and ins.arg1 == ins.result:
            changes += 1
            continue

        replacement: Quadruple | None = None
        if ins.result is not None:
            if ins.op == "+":
                if ins.arg2 in {"0", "0.0"}:
                    replacement = Quadruple("assign", ins.arg1, result=ins.result)
                elif ins.arg1 in {"0", "0.0"}:
                    replacement = Quadruple("assign", ins.arg2, result=ins.result)
            elif ins.op == "-" and ins.arg2 in {"0", "0.0"}:
                replacement = Quadruple("assign", ins.arg1, result=ins.result)
            elif ins.op == "*":
                if ins.arg2 in {"1", "1.0"}:
                    replacement = Quadruple("assign", ins.arg1, result=ins.result)
                elif ins.arg1 in {"1", "1.0"}:
                    replacement = Quadruple("assign", ins.arg2, result=ins.result)
                elif ins.arg1 in {"0", "0.0"} or ins.arg2 in {"0", "0.0"}:
                    replacement = Quadruple("assign", "0", result=ins.result)
            elif ins.op == "/" and ins.arg2 in {"1", "1.0"}:
                replacement = Quadruple("assign", ins.arg1, result=ins.result)
            elif ins.op == "&&":
                if ins.arg2 == "true":
                    replacement = Quadruple("assign", ins.arg1, result=ins.result)
                elif ins.arg1 == "true":
                    replacement = Quadruple("assign", ins.arg2, result=ins.result)
                elif ins.arg1 == "false" or ins.arg2 == "false":
                    replacement = Quadruple("assign", "false", result=ins.result)
            elif ins.op == "||":
                if ins.arg2 == "false":
                    replacement = Quadruple("assign", ins.arg1, result=ins.result)
                elif ins.arg1 == "false":
                    replacement = Quadruple("assign", ins.arg2, result=ins.result)
                elif ins.arg1 == "true" or ins.arg2 == "true":
                    replacement = Quadruple("assign", "true", result=ins.result)

        if replacement is not None:
            stage.append(replacement)
            changes += 1
        else:
            stage.append(ins)

    out: list[Quadruple] = []
    for index, ins in enumerate(stage):
        if (
            ins.op == "goto"
            and index + 1 < len(stage)
            and stage[index + 1].op == "label"
            and stage[index + 1].result == ins.result
        ):
            changes += 1
            continue
        out.append(ins)

    return IRProgram(tuple(out)), changes


def control_flow_cleanup(program: IRProgram) -> tuple[IRProgram, int]:
    stage: list[Quadruple] = []
    changes = 0
    for ins in program.instructions:
        if ins.op == "if_false":
            cond = _literal(ins.arg1)
            if cond is True:
                changes += 1
                continue
            if cond is False:
                stage.append(Quadruple("goto", result=ins.result))
                changes += 1
                continue
        stage.append(ins)

    out: list[Quadruple] = []
    skipping = False
    for ins in stage:
        if skipping:
            if ins.op in {"label", "func_begin", "func_end"}:
                skipping = False
                out.append(ins)
            else:
                changes += 1
            continue

        out.append(ins)
        if ins.op in {"goto", "return"}:
            skipping = True

    return IRProgram(tuple(out)), changes


def dead_temporary_elimination(program: IRProgram) -> tuple[IRProgram, int]:
    current = list(program.instructions)
    total_changes = 0
    pure_ops = set(_BINARY_FOLDERS) | set(_UNARY_FOLDERS) | {"assign"}

    while True:
        uses = Counter(
            operand
            for ins in current
            for operand in (ins.arg1, ins.arg2)
            if _is_temp(operand)
        )
        removed = 0
        next_instructions: list[Quadruple] = []
        for ins in current:
            if (
                _is_temp(ins.result)
                and uses[ins.result] == 0
                and ins.op in pure_ops
            ):
                removed += 1
                continue
            if ins.op == "call" and _is_temp(ins.result) and uses[ins.result] == 0:
                next_instructions.append(Quadruple("call", ins.arg1, ins.arg2))
                removed += 1
                continue
            next_instructions.append(ins)
        total_changes += removed
        current = next_instructions
        if removed == 0:
            break

    return IRProgram(tuple(current)), total_changes
