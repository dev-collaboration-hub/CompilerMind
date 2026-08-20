from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping, Sequence

from .errors import LL1Conflict, LL1ConflictError, ParserError
from .first_follow import first_of_sequence, first_sets, follow_sets
from .grammar import ENDMARKER, EPSILON, Grammar, Production
from .parse_tree import ParseNode


@dataclass(frozen=True, slots=True)
class LL1Table:
    grammar: Grammar
    entries: Mapping[tuple[str, str], Production]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", MappingProxyType(dict(self.entries)))

    def production_for(self, nonterminal: str, terminal: str) -> Production | None:
        return self.entries.get((nonterminal, terminal))

    def expected_for(self, nonterminal: str) -> frozenset[str]:
        return frozenset(
            terminal
            for (lhs, terminal), _ in self.entries.items()
            if lhs == nonterminal
        )


def build_ll1_table(grammar: Grammar) -> LL1Table:
    first = first_sets(grammar)
    follow = follow_sets(grammar, first)
    entries: dict[tuple[str, str], Production] = {}

    for lhs, alternatives in grammar.productions.items():
        for production in alternatives:
            production_first = first_of_sequence(production, grammar, first)
            targets = set(production_first - {EPSILON})
            if EPSILON in production_first:
                targets.update(follow[lhs])

            for terminal in targets:
                key = (lhs, terminal)
                existing = entries.get(key)
                if existing is not None and existing != production:
                    raise LL1ConflictError(
                        LL1Conflict(lhs, terminal, existing, production)
                    )
                entries[key] = production

    return LL1Table(grammar, entries)


class PredictiveParser:
    def __init__(self, grammar: Grammar, table: LL1Table | None = None) -> None:
        self.grammar = grammar
        self.table = table or build_ll1_table(grammar)

    def parse(self, terminals: Sequence[str]) -> ParseNode:
        stream = tuple(terminals) + (ENDMARKER,)
        root = ParseNode(self.grammar.start_symbol)
        stack: list[tuple[str, ParseNode | None]] = [
            (ENDMARKER, None),
            (self.grammar.start_symbol, root),
        ]
        position = 0

        while stack:
            symbol, node = stack.pop()
            lookahead = stream[position]

            if symbol == ENDMARKER:
                if lookahead != ENDMARKER:
                    raise ParserError(
                        position=position,
                        lookahead=lookahead,
                        expected=frozenset({ENDMARKER}),
                        context="end of input",
                    )
                position += 1
                continue

            if symbol not in self.grammar.nonterminals:
                if symbol != lookahead:
                    raise ParserError(
                        position=position,
                        lookahead=lookahead,
                        expected=frozenset({symbol}),
                        context=symbol,
                    )
                position += 1
                continue

            production = self.table.production_for(symbol, lookahead)
            if production is None:
                raise ParserError(
                    position=position,
                    lookahead=lookahead,
                    expected=self.table.expected_for(symbol),
                    context=symbol,
                )

            assert node is not None
            if production == (EPSILON,):
                node.children.append(ParseNode(EPSILON))
                continue

            children = [ParseNode(part) for part in production]
            node.children.extend(children)
            for part, child in reversed(tuple(zip(production, children))):
                stack.append((part, child))

        if position != len(stream):
            lookahead = stream[position] if position < len(stream) else ENDMARKER
            raise ParserError(
                position=position,
                lookahead=lookahead,
                expected=frozenset({ENDMARKER}),
                context="end of input",
            )
        return root


class RecursiveDescentParser:
    """Generic recursive-descent executor for an LL(1) grammar."""

    def __init__(self, grammar: Grammar, table: LL1Table | None = None) -> None:
        self.grammar = grammar
        self.table = table or build_ll1_table(grammar)

    def parse(self, terminals: Sequence[str]) -> ParseNode:
        self._stream = tuple(terminals) + (ENDMARKER,)
        self._position = 0
        root = self._parse_nonterminal(self.grammar.start_symbol)
        if self._lookahead() != ENDMARKER:
            raise ParserError(
                position=self._position,
                lookahead=self._lookahead(),
                expected=frozenset({ENDMARKER}),
                context="end of input",
            )
        self._position += 1
        return root

    def _parse_nonterminal(self, nonterminal: str) -> ParseNode:
        lookahead = self._lookahead()
        production = self.table.production_for(nonterminal, lookahead)
        if production is None:
            raise ParserError(
                position=self._position,
                lookahead=lookahead,
                expected=self.table.expected_for(nonterminal),
                context=nonterminal,
            )

        node = ParseNode(nonterminal)
        if production == (EPSILON,):
            node.children.append(ParseNode(EPSILON))
            return node

        for symbol in production:
            if symbol in self.grammar.nonterminals:
                node.children.append(self._parse_nonterminal(symbol))
                continue

            lookahead = self._lookahead()
            if lookahead != symbol:
                raise ParserError(
                    position=self._position,
                    lookahead=lookahead,
                    expected=frozenset({symbol}),
                    context=nonterminal,
                )
            node.children.append(ParseNode(symbol))
            self._position += 1

        return node

    def _lookahead(self) -> str:
        return self._stream[self._position]
