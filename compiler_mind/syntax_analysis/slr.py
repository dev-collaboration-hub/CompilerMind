from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping, Sequence

from .errors import ParserError, SLRConflict, SLRConflictError
from .first_follow import follow_sets
from .grammar import ENDMARKER, EPSILON, Grammar, Production
from .parse_tree import ParseNode


@dataclass(frozen=True, slots=True, order=True)
class LR0Item:
    lhs: str
    rhs: Production
    dot: int

    @property
    def complete(self) -> bool:
        return self.dot >= len(self.rhs)

    @property
    def next_symbol(self) -> str | None:
        return None if self.complete else self.rhs[self.dot]

    def advance(self) -> "LR0Item":
        if self.complete:
            return self
        return LR0Item(self.lhs, self.rhs, self.dot + 1)


@dataclass(frozen=True, slots=True)
class SLRAction:
    kind: str
    value: int | tuple[str, Production] | None = None

    def describe(self) -> str:
        if self.kind == "shift":
            return f"shift {self.value}"
        if self.kind == "reduce":
            lhs, rhs = self.value  # type: ignore[misc]
            return f"reduce {lhs} -> {' '.join(rhs)}"
        return self.kind


@dataclass(frozen=True, slots=True)
class SLRTable:
    grammar: Grammar
    states: tuple[frozenset[LR0Item], ...]
    actions: Mapping[tuple[int, str], SLRAction]
    gotos: Mapping[tuple[int, str], int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "actions", MappingProxyType(dict(self.actions)))
        object.__setattr__(self, "gotos", MappingProxyType(dict(self.gotos)))

    def expected_for(self, state: int) -> frozenset[str]:
        return frozenset(
            terminal for (item_state, terminal) in self.actions if item_state == state
        )


def _augmented_symbol(grammar: Grammar) -> str:
    candidate = f"{grammar.start_symbol}'"
    while candidate in grammar.nonterminals or candidate in grammar.terminals:
        candidate += "'"
    return candidate


def _normalized_rhs(rhs: Production) -> Production:
    return () if rhs == (EPSILON,) else rhs


def build_slr_table(grammar: Grammar) -> SLRTable:
    augmented = _augmented_symbol(grammar)
    productions: dict[str, tuple[Production, ...]] = {
        lhs: tuple(_normalized_rhs(rhs) for rhs in alternatives)
        for lhs, alternatives in grammar.productions.items()
    }
    productions[augmented] = ((grammar.start_symbol,),)
    nonterminals = frozenset(productions)

    def closure(items: frozenset[LR0Item]) -> frozenset[LR0Item]:
        result = set(items)
        changed = True
        while changed:
            changed = False
            for item in tuple(result):
                symbol = item.next_symbol
                if symbol not in nonterminals:
                    continue
                for rhs in productions[symbol]:
                    candidate = LR0Item(symbol, rhs, 0)
                    if candidate not in result:
                        result.add(candidate)
                        changed = True
        return frozenset(result)

    def goto(items: frozenset[LR0Item], symbol: str) -> frozenset[LR0Item]:
        advanced = frozenset(
            item.advance() for item in items if item.next_symbol == symbol
        )
        return closure(advanced) if advanced else frozenset()

    start = closure(frozenset({LR0Item(augmented, (grammar.start_symbol,), 0)}))
    states: list[frozenset[LR0Item]] = [start]
    state_index = {start: 0}
    transitions: dict[tuple[int, str], int] = {}

    cursor = 0
    symbols = tuple(sorted(grammar.terminals | grammar.nonterminals))
    while cursor < len(states):
        state = states[cursor]
        for symbol in symbols:
            target = goto(state, symbol)
            if not target:
                continue
            if target not in state_index:
                state_index[target] = len(states)
                states.append(target)
            transitions[(cursor, symbol)] = state_index[target]
        cursor += 1

    actions: dict[tuple[int, str], SLRAction] = {}
    gotos: dict[tuple[int, str], int] = {}
    follow = follow_sets(grammar)

    def put_action(key: tuple[int, str], action: SLRAction) -> None:
        existing = actions.get(key)
        if existing is not None and existing != action:
            raise SLRConflictError(
                SLRConflict(
                    key[0],
                    key[1],
                    existing.describe(),
                    action.describe(),
                )
            )
        actions[key] = action

    for (state, symbol), target in transitions.items():
        if symbol in grammar.terminals:
            put_action((state, symbol), SLRAction("shift", target))
        elif symbol in grammar.nonterminals:
            gotos[(state, symbol)] = target

    for state_id, state in enumerate(states):
        for item in state:
            if not item.complete:
                continue
            if item.lhs == augmented:
                put_action((state_id, ENDMARKER), SLRAction("accept"))
                continue
            original_rhs = (EPSILON,) if not item.rhs else item.rhs
            for terminal in follow[item.lhs]:
                put_action(
                    (state_id, terminal),
                    SLRAction("reduce", (item.lhs, original_rhs)),
                )

    return SLRTable(grammar, tuple(states), actions, gotos)


class SLRParser:
    def __init__(self, grammar: Grammar, table: SLRTable | None = None) -> None:
        self.grammar = grammar
        self.table = table or build_slr_table(grammar)

    def parse(self, terminals: Sequence[str]) -> ParseNode:
        stream = tuple(terminals) + (ENDMARKER,)
        states = [0]
        nodes: list[ParseNode] = []
        position = 0

        while True:
            state = states[-1]
            lookahead = stream[position]
            action = self.table.actions.get((state, lookahead))
            if action is None:
                raise ParserError(
                    position=position,
                    lookahead=lookahead,
                    expected=self.table.expected_for(state),
                    context=f"SLR state {state}",
                )

            if action.kind == "shift":
                nodes.append(ParseNode(lookahead))
                states.append(int(action.value))
                position += 1
                continue

            if action.kind == "reduce":
                lhs, rhs = action.value  # type: ignore[misc]
                pop_count = 0 if rhs == (EPSILON,) else len(rhs)
                children = (
                    [ParseNode(EPSILON)]
                    if pop_count == 0
                    else nodes[-pop_count:]
                )
                if pop_count:
                    del nodes[-pop_count:]
                    del states[-pop_count:]
                node = ParseNode(lhs, list(children))
                target = self.table.gotos.get((states[-1], lhs))
                if target is None:
                    raise RuntimeError(
                        f"Missing SLR goto from state {states[-1]} for {lhs!r}."
                    )
                nodes.append(node)
                states.append(target)
                continue

            if action.kind == "accept":
                if position != len(stream) - 1 or len(nodes) != 1:
                    raise RuntimeError("Invalid SLR accept state.")
                return nodes[0]

            raise RuntimeError(f"Unknown SLR action: {action.kind!r}.")
