from __future__ import annotations

from .grammar import ENDMARKER, EPSILON, Grammar


def first_sets(grammar: Grammar) -> dict[str, frozenset[str]]:
    """Calculate FIRST for every non-terminal in a grammar."""

    first: dict[str, set[str]] = {
        nonterminal: set() for nonterminal in grammar.nonterminals
    }

    changed = True
    while changed:
        changed = False
        for lhs, alternatives in grammar.productions.items():
            for production in alternatives:
                before = len(first[lhs])
                first[lhs].update(_first_of_sequence_mutable(production, grammar, first))
                changed |= len(first[lhs]) != before

    return {symbol: frozenset(values) for symbol, values in first.items()}


def first_of_sequence(
    symbols: tuple[str, ...] | list[str],
    grammar: Grammar,
    first: dict[str, frozenset[str]] | None = None,
) -> frozenset[str]:
    """Calculate FIRST for an arbitrary symbol sequence."""

    if first is None:
        first = first_sets(grammar)

    mutable_first = {symbol: set(values) for symbol, values in first.items()}
    return frozenset(_first_of_sequence_mutable(tuple(symbols), grammar, mutable_first))


def follow_sets(
    grammar: Grammar,
    first: dict[str, frozenset[str]] | None = None,
) -> dict[str, frozenset[str]]:
    """Calculate FOLLOW for every non-terminal in a grammar."""

    if first is None:
        first = first_sets(grammar)

    mutable_first = {symbol: set(values) for symbol, values in first.items()}
    follow: dict[str, set[str]] = {
        nonterminal: set() for nonterminal in grammar.nonterminals
    }
    follow[grammar.start_symbol].add(ENDMARKER)

    changed = True
    while changed:
        changed = False

        for lhs, alternatives in grammar.productions.items():
            for production in alternatives:
                if production == (EPSILON,):
                    continue

                for index, symbol in enumerate(production):
                    if symbol not in grammar.nonterminals:
                        continue

                    suffix = production[index + 1 :]
                    suffix_first = _first_of_sequence_mutable(
                        suffix,
                        grammar,
                        mutable_first,
                    )

                    before = len(follow[symbol])
                    follow[symbol].update(suffix_first - {EPSILON})

                    if not suffix or EPSILON in suffix_first:
                        follow[symbol].update(follow[lhs])

                    changed |= len(follow[symbol]) != before

    return {symbol: frozenset(values) for symbol, values in follow.items()}


def _first_of_sequence_mutable(
    symbols: tuple[str, ...],
    grammar: Grammar,
    first: dict[str, set[str]],
) -> set[str]:
    if not symbols:
        return {EPSILON}

    result: set[str] = set()

    for symbol in symbols:
        if symbol == EPSILON:
            result.add(EPSILON)
            return result

        if symbol in grammar.nonterminals:
            symbol_first = first[symbol]
            result.update(symbol_first - {EPSILON})
            if EPSILON in symbol_first:
                continue
            return result

        result.add(symbol)
        return result

    result.add(EPSILON)
    return result
