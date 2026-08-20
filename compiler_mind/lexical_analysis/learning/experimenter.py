from __future__ import annotations

from ..tokens import TokenKind
from .models import ExpectedToken, LexicalTestCase


def _token(kind: TokenKind, lexeme: str) -> ExpectedToken:
    return ExpectedToken(kind, lexeme)


class LexicalExperimenter:
    """Creates deterministic edge cases that exercise known lexer behaviour."""

    def default_suite(self) -> tuple[LexicalTestCase, ...]:
        return (
            LexicalTestCase(
                name="basic-program",
                source="let total = price + 10;",
                expected_tokens=(
                    _token(TokenKind.KEYWORD, "let"),
                    _token(TokenKind.IDENTIFIER, "total"),
                    _token(TokenKind.OPERATOR, "="),
                    _token(TokenKind.IDENTIFIER, "price"),
                    _token(TokenKind.OPERATOR, "+"),
                    _token(TokenKind.INTEGER, "10"),
                    _token(TokenKind.SEMICOLON, ";"),
                ),
            ),
            LexicalTestCase(
                name="identifier-boundaries",
                source="_temp x2 __",
                expected_tokens=(
                    _token(TokenKind.IDENTIFIER, "_temp"),
                    _token(TokenKind.IDENTIFIER, "x2"),
                    _token(TokenKind.IDENTIFIER, "__"),
                ),
            ),
            LexicalTestCase(
                name="longest-operator",
                source="a == b",
                expected_tokens=(
                    _token(TokenKind.IDENTIFIER, "a"),
                    _token(TokenKind.OPERATOR, "=="),
                    _token(TokenKind.IDENTIFIER, "b"),
                ),
            ),
            LexicalTestCase(
                name="line-comment",
                source="let x = 1; // ignored\nx = x + 1;",
                expected_tokens=(
                    _token(TokenKind.KEYWORD, "let"),
                    _token(TokenKind.IDENTIFIER, "x"),
                    _token(TokenKind.OPERATOR, "="),
                    _token(TokenKind.INTEGER, "1"),
                    _token(TokenKind.SEMICOLON, ";"),
                    _token(TokenKind.IDENTIFIER, "x"),
                    _token(TokenKind.OPERATOR, "="),
                    _token(TokenKind.IDENTIFIER, "x"),
                    _token(TokenKind.OPERATOR, "+"),
                    _token(TokenKind.INTEGER, "1"),
                    _token(TokenKind.SEMICOLON, ";"),
                ),
            ),
            LexicalTestCase(
                name="invalid-character",
                source="let x = @5;",
                expected_error_character="@",
            ),
        )

    def identifier_suite(
        self,
        valid_identifiers: tuple[str, ...] = ("a", "_a", "x2", "abc_25", "__"),
    ) -> tuple[LexicalTestCase, ...]:
        return tuple(
            LexicalTestCase(
                name=f"identifier-{index}",
                source=identifier,
                expected_tokens=(_token(TokenKind.IDENTIFIER, identifier),),
            )
            for index, identifier in enumerate(valid_identifiers, start=1)
        )
