from __future__ import annotations

from dataclasses import dataclass

from .errors import LL1ConflictError, SLRConflictError
from .grammar import EPSILON, Grammar


@dataclass(frozen=True, slots=True)
class ParserHypothesis:
    code: str
    explanation: str
    evidence: str


class ParserHypothesisGenerator:
    """Create testable explanations for parser conflicts instead of guessing."""

    def for_ll1_conflict(
        self,
        grammar: Grammar,
        error: LL1ConflictError,
    ) -> tuple[ParserHypothesis, ...]:
        hypotheses: list[ParserHypothesis] = []
        conflict = error.conflict
        lhs = conflict.nonterminal

        if any(
            production != (EPSILON,) and production[0] == lhs
            for production in grammar.alternatives(lhs)
        ):
            hypotheses.append(
                ParserHypothesis(
                    "left-recursion",
                    "Direct left recursion may be preventing predictive parsing.",
                    lhs,
                )
            )

        first_symbols = [
            production[0]
            for production in grammar.alternatives(lhs)
            if production != (EPSILON,) and production
        ]
        duplicates = sorted(
            symbol for symbol in set(first_symbols) if first_symbols.count(symbol) > 1
        )
        if duplicates:
            hypotheses.append(
                ParserHypothesis(
                    "left-factoring",
                    "Alternatives share a visible prefix and may need left factoring.",
                    ", ".join(duplicates),
                )
            )

        hypotheses.append(
            ParserHypothesis(
                "not-ll1",
                "The grammar may remain non-LL(1) because competing productions "
                "select the same lookahead.",
                f"{lhs} on {conflict.terminal}",
            )
        )
        return tuple(hypotheses)

    def for_slr_conflict(
        self,
        grammar: Grammar,
        error: SLRConflictError,
    ) -> tuple[ParserHypothesis, ...]:
        conflict = error.conflict
        return (
            ParserHypothesis(
                "not-slr",
                "The grammar may require a stronger LR method or grammar rewrite.",
                f"state {conflict.state}, lookahead {conflict.terminal}",
            ),
            ParserHypothesis(
                "ambiguity-or-precedence",
                "A shift/reduce or reduce/reduce conflict can indicate ambiguity "
                "or missing precedence/associativity constraints.",
                f"{conflict.existing} vs {conflict.incoming}",
            ),
        )
