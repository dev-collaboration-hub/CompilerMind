from __future__ import annotations


class LexicalError(ValueError):
    def __init__(self, *, character: str, line: int, column: int) -> None:
        self.character = character
        self.line = line
        self.column = column
        super().__init__(
            f"Unexpected character {character!r} at line {line}, column {column}"
        )
