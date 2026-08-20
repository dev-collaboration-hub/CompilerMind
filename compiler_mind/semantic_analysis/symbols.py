from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .types import SemanticType


class SymbolKind(str, Enum):
    VARIABLE = "variable"
    PARAMETER = "parameter"
    FUNCTION = "function"


@dataclass(frozen=True, slots=True)
class Symbol:
    name: str
    kind: SymbolKind
    type: SemanticType
    parameter_types: tuple[SemanticType, ...] = ()


@dataclass(slots=True)
class Scope:
    name: str
    parent: "Scope | None" = None
    symbols: dict[str, Symbol] = field(default_factory=dict)

    def declare(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def resolve_local(self, name: str) -> Symbol | None:
        return self.symbols.get(name)

    def resolve(self, name: str) -> Symbol | None:
        scope: Scope | None = self
        while scope is not None:
            symbol = scope.symbols.get(name)
            if symbol is not None:
                return symbol
            scope = scope.parent
        return None


@dataclass(frozen=True, slots=True)
class ScopeSnapshot:
    name: str
    symbols: tuple[Symbol, ...]


class SymbolTable:
    def __init__(self) -> None:
        self.global_scope = Scope("global")
        self.current_scope = self.global_scope
        self._scopes: list[Scope] = [self.global_scope]

    def enter_scope(self, name: str) -> Scope:
        scope = Scope(name, self.current_scope)
        self._scopes.append(scope)
        self.current_scope = scope
        return scope

    def exit_scope(self) -> Scope:
        if self.current_scope.parent is None:
            raise RuntimeError("Cannot exit the global scope.")
        exited = self.current_scope
        self.current_scope = self.current_scope.parent
        return exited

    def declare(self, symbol: Symbol) -> bool:
        return self.current_scope.declare(symbol)

    def resolve(self, name: str) -> Symbol | None:
        return self.current_scope.resolve(name)

    def resolve_global(self, name: str) -> Symbol | None:
        return self.global_scope.resolve_local(name)

    def snapshots(self) -> tuple[ScopeSnapshot, ...]:
        return tuple(
            ScopeSnapshot(scope.name, tuple(scope.symbols.values()))
            for scope in self._scopes
        )
