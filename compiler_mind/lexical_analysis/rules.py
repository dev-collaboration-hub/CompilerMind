from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IdentifierRule:
    """Configurable identifier rule used by both the lexer and learner."""

    allow_leading_underscore: bool = True
    allow_digits_after_first: bool = True
    allow_underscore_after_first: bool = True

    def can_start(self, character: str) -> bool:
        return character.isalpha() or (
            self.allow_leading_underscore and character == "_"
        )

    def can_continue(self, character: str) -> bool:
        if character.isalpha():
            return True
        if character.isdigit():
            return self.allow_digits_after_first
        if character == "_":
            return self.allow_underscore_after_first
        return False


DEFAULT_IDENTIFIER_RULE = IdentifierRule()
