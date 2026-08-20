from __future__ import annotations

from .grammar import EPSILON, Grammar, Production


def remove_left_recursion(grammar: Grammar) -> Grammar:
    """Remove indirect and direct left recursion using ordered substitution."""

    rules: dict[str, list[Production]] = {
        lhs: list(alternatives) for lhs, alternatives in grammar.productions.items()
    }
    order = list(grammar.productions)

    for index, current in enumerate(order):
        alternatives = rules[current]

        for previous in order[:index]:
            expanded: list[Production] = []
            for production in alternatives:
                if production and production[0] == previous:
                    suffix = production[1:]
                    for previous_production in rules[previous]:
                        prefix = () if previous_production == (EPSILON,) else previous_production
                        combined = prefix + suffix
                        expanded.append(combined or (EPSILON,))
                else:
                    expanded.append(production)
            alternatives = expanded

        rules[current] = alternatives
        _remove_direct_for(current, rules)

    return Grammar.from_rules(
        grammar.start_symbol,
        {lhs: tuple(alternatives) for lhs, alternatives in rules.items()},
    )


def left_factor(grammar: Grammar) -> Grammar:
    """Repeatedly factor the longest common production prefix."""

    rules: dict[str, list[Production]] = {
        lhs: list(alternatives) for lhs, alternatives in grammar.productions.items()
    }
    queue = list(grammar.productions)

    while queue:
        lhs = queue.pop(0)

        while True:
            prefix = _longest_shared_prefix(rules[lhs])
            if not prefix:
                break

            grouped = [
                production
                for production in rules[lhs]
                if _starts_with(production, prefix)
            ]
            if len(grouped) < 2:
                break

            helper = _unique_helper(lhs, rules)
            ungrouped = [
                production
                for production in rules[lhs]
                if not _starts_with(production, prefix)
            ]
            ungrouped.append(prefix + (helper,))
            rules[lhs] = ungrouped

            helper_alternatives: list[Production] = []
            for production in grouped:
                suffix = production[len(prefix) :]
                helper_alternatives.append(suffix or (EPSILON,))

            rules[helper] = helper_alternatives
            queue.append(helper)

    return Grammar.from_rules(
        grammar.start_symbol,
        {lhs: tuple(alternatives) for lhs, alternatives in rules.items()},
    )


def _remove_direct_for(
    lhs: str,
    rules: dict[str, list[Production]],
) -> None:
    recursive: list[Production] = []
    nonrecursive: list[Production] = []

    for production in rules[lhs]:
        if production and production[0] == lhs:
            suffix = production[1:]
            if not suffix:
                raise ValueError(
                    f"Degenerate production {lhs} -> {lhs} cannot be transformed safely."
                )
            recursive.append(suffix)
        else:
            nonrecursive.append(production)

    if not recursive:
        return

    if not nonrecursive:
        raise ValueError(
            f"Cannot remove left recursion from {lhs!r} without a non-recursive alternative."
        )

    helper = _unique_helper(lhs, rules)

    rewritten_lhs: list[Production] = []
    for production in nonrecursive:
        beta = () if production == (EPSILON,) else production
        rewritten_lhs.append(beta + (helper,))

    rewritten_helper = [
        alpha + (helper,) for alpha in recursive
    ]
    rewritten_helper.append((EPSILON,))

    rules[lhs] = rewritten_lhs
    rules[helper] = rewritten_helper


def _longest_shared_prefix(
    alternatives: list[Production],
) -> Production:
    best: Production = ()

    for left_index, left in enumerate(alternatives):
        if left == (EPSILON,):
            continue
        for right in alternatives[left_index + 1 :]:
            if right == (EPSILON,):
                continue

            length = 0
            limit = min(len(left), len(right))
            while length < limit and left[length] == right[length]:
                length += 1

            if length > len(best):
                best = left[:length]

    return best


def _starts_with(production: Production, prefix: Production) -> bool:
    return len(production) >= len(prefix) and production[: len(prefix)] == prefix


def _unique_helper(base: str, rules: dict[str, list[Production]]) -> str:
    candidate = f"{base}'"
    while candidate in rules:
        candidate += "'"
    return candidate
