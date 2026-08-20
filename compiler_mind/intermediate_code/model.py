from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Quadruple:
    """Canonical four-field intermediate representation instruction."""

    op: str
    arg1: str | None = None
    arg2: str | None = None
    result: str | None = None

    def to_tac(self) -> str:
        """Render this instruction as readable three-address code."""

        if self.op == "label":
            return f"{self.result}:"
        if self.op == "goto":
            return f"goto {self.result}"
        if self.op == "if_false":
            return f"ifFalse {self.arg1} goto {self.result}"
        if self.op == "assign":
            return f"{self.result} = {self.arg1}"
        if self.op == "declare":
            return f"declare {self.arg1} {self.result}"
        if self.op == "param":
            return f"param {self.arg1}"
        if self.op == "param_decl":
            return f"param {self.arg1} {self.result}"
        if self.op == "call":
            call = f"call {self.arg1}, {self.arg2}"
            return f"{self.result} = {call}" if self.result else call
        if self.op == "return":
            return "return" if self.arg1 is None else f"return {self.arg1}"
        if self.op == "func_begin":
            return f"function {self.result}:"
        if self.op == "func_end":
            return f"end function {self.result}"
        if self.op.startswith("u"):
            return f"{self.result} = {self.op[1:]}{self.arg1}"
        if self.result is not None and self.arg2 is not None:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        raise ValueError(f"Unsupported quadruple for TAC rendering: {self!r}")


@dataclass(frozen=True, slots=True)
class Triple:
    """Three-field representation whose result is its instruction index."""

    index: int
    op: str
    arg1: str | None = None
    arg2: str | None = None


@dataclass(frozen=True, slots=True)
class IRProgram:
    instructions: tuple[Quadruple, ...]

    def tac(self) -> tuple[str, ...]:
        return tuple(instruction.to_tac() for instruction in self.instructions)

    def triples(self) -> tuple[Triple, ...]:
        """Derive triples from canonical quadruples.

        Compiler-generated temporary references are replaced by the index of
        the triple that produced them. User identifiers are never rewritten.
        """

        temporary_results: dict[str, str] = {}
        triples: list[Triple] = []

        for index, quad in enumerate(self.instructions):
            def reference(value: str | None) -> str | None:
                if value is None:
                    return None
                return temporary_results.get(value, value)

            arg1 = reference(quad.arg1)
            arg2 = reference(quad.arg2)

            if quad.op == "assign":
                triple = Triple(index, "=", arg1, quad.result)
            elif quad.op == "declare":
                triple = Triple(index, "declare", quad.arg1, quad.result)
            elif quad.op == "param_decl":
                triple = Triple(index, "param_decl", quad.arg1, quad.result)
            elif quad.op in {"label", "goto", "func_begin", "func_end"}:
                triple = Triple(index, quad.op, quad.result, None)
            elif quad.op == "if_false":
                triple = Triple(index, quad.op, arg1, quad.result)
            elif quad.op in {"return", "param"}:
                triple = Triple(index, quad.op, arg1, None)
            elif quad.op == "call":
                triple = Triple(index, quad.op, quad.arg1, quad.arg2)
            else:
                triple = Triple(index, quad.op, arg1, arg2)

            triples.append(triple)

            if quad.result and quad.result.startswith("%t"):
                temporary_results[quad.result] = f"({index})"

        return tuple(triples)
