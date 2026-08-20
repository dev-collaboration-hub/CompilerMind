from __future__ import annotations

from dataclasses import dataclass

from .grammar import Production


class ParserError(ValueError):
    """Raised when an input terminal stream cannot be parsed."""

    def __init__(
        self,
        *,
        position: int,
        lookahead: str,
        expected: frozenset[str],
        context: str,
    ) -> None:
        self.position = position
        self.lookahead = lookahead
        self.expected = expected
        self.context = context
        expected_text = ", ".join(sorted(expected)) or "<none>"
        super().__init__(
            f"Syntax error at token {position}: got {lookahead!r}; "
            f"expected one of [{expected_text}] while parsing {context}."
        )


@dataclass(frozen=True, slots=True)
class LL1Conflict:
    nonterminal: str
    terminal: str
    existing: Production
    incoming: Production


class LL1ConflictError(ValueError):
    def __init__(self, conflict: LL1Conflict) -> None:
        self.conflict = conflict
        super().__init__(
            "LL(1) conflict for "
            f"({conflict.nonterminal!r}, {conflict.terminal!r}): "
            f"{conflict.existing!r} vs {conflict.incoming!r}"
        )


@dataclass(frozen=True, slots=True)
class SLRConflict:
    state: int
    terminal: str
    existing: str
    incoming: str


class SLRConflictError(ValueError):
    def __init__(self, conflict: SLRConflict) -> None:
        self.conflict = conflict
        super().__init__(
            f"SLR conflict in state {conflict.state} on {conflict.terminal!r}: "
            f"{conflict.existing} vs {conflict.incoming}"
        )
