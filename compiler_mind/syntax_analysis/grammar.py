from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping, Sequence

EPSILON = "ε"
ENDMARKER = "$"

Production = tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Grammar:
    """Immutable context-free grammar representation."""

    start_symbol: str
    productions: Mapping[str, tuple[Production, ...]]

    def __post_init__(self) -> None:
        if not self.start_symbol:
            raise ValueError("start_symbol cannot be empty.")

        normalized: dict[str, tuple[Production, ...]] = {}
        for lhs, alternatives in self.productions.items():
            if not lhs:
                raise ValueError("Non-terminal names cannot be empty.")
            if lhs in {EPSILON, ENDMARKER}:
                raise ValueError(f"{lhs!r} cannot be used as a non-terminal.")

            normalized_alternatives: list[Production] = []
            for alternative in alternatives:
                production = tuple(alternative)
                if not production:
                    production = (EPSILON,)
                if EPSILON in production and production != (EPSILON,):
                    raise ValueError(
                        f"{EPSILON!r} must appear alone in an epsilon production."
                    )
                normalized_alternatives.append(production)

            if not normalized_alternatives:
                raise ValueError(f"Non-terminal {lhs!r} must have a production.")
            normalized[lhs] = tuple(normalized_alternatives)

        if self.start_symbol not in normalized:
            raise ValueError("start_symbol must have at least one production.")

        object.__setattr__(self, "productions", MappingProxyType(normalized))

    @property
    def nonterminals(self) -> frozenset[str]:
        return frozenset(self.productions)

    @property
    def terminals(self) -> frozenset[str]:
        symbols = {
            symbol
            for alternatives in self.productions.values()
            for production in alternatives
            for symbol in production
        }
        return frozenset(symbols - self.nonterminals - {EPSILON})

    def alternatives(self, nonterminal: str) -> tuple[Production, ...]:
        try:
            return self.productions[nonterminal]
        except KeyError as exc:
            raise KeyError(f"Unknown non-terminal: {nonterminal!r}") from exc

    @classmethod
    def from_rules(
        cls,
        start_symbol: str,
        rules: Mapping[str, Sequence[Sequence[str]]],
    ) -> "Grammar":
        return cls(
            start_symbol=start_symbol,
            productions={
                lhs: tuple(tuple(symbols) for symbols in alternatives)
                for lhs, alternatives in rules.items()
            },
        )
