from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ParseNode:
    """A small parse-tree node shared by top-down and bottom-up parsers."""

    symbol: str
    children: list["ParseNode"] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "children": [child.to_dict() for child in self.children],
        }

    def leaves(self) -> tuple[str, ...]:
        if not self.children:
            return (self.symbol,)
        result: list[str] = []
        for child in self.children:
            result.extend(child.leaves())
        return tuple(result)
