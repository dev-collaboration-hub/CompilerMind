from __future__ import annotations

from collections.abc import Iterable

from .errors import LexicalError
from .tokens import Token, TokenKind


DEFAULT_KEYWORDS = frozenset(
    {
        "let",
        "fn",
        "if",
        "else",
        "return",
        "while",
        "for",
        "int",
        "float",
        "char",
        "void",
    }
)

OPERATORS = {
    "==": TokenKind.OPERATOR,
    "!=": TokenKind.OPERATOR,
    "<=": TokenKind.OPERATOR,
    ">=": TokenKind.OPERATOR,
    "->": TokenKind.OPERATOR,
    "+": TokenKind.OPERATOR,
    "-": TokenKind.OPERATOR,
    "*": TokenKind.OPERATOR,
    "/": TokenKind.OPERATOR,
    "%": TokenKind.OPERATOR,
    "=": TokenKind.OPERATOR,
    "<": TokenKind.OPERATOR,
    ">": TokenKind.OPERATOR,
    "!": TokenKind.OPERATOR,
    "&": TokenKind.OPERATOR,
    "|": TokenKind.OPERATOR,
}

DELIMITERS = {
    ";": TokenKind.SEMICOLON,
    ",": TokenKind.COMMA,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
    "{": TokenKind.LBRACE,
    "}": TokenKind.RBRACE,
    "[": TokenKind.LBRACKET,
    "]": TokenKind.RBRACKET,
    ":": TokenKind.COLON,
}


class Lexer:
    """Deterministic, character-by-character lexer for CompilerMind."""

    def __init__(
        self,
        source: str,
        *,
        keywords: Iterable[str] = DEFAULT_KEYWORDS,
    ) -> None:
        self.source = source
        self.keywords = frozenset(keywords)
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []

        while not self._at_end():
            current = self._peek()

            if current.isspace():
                self._consume_whitespace()
                continue

            if current.isalpha() or current == "_":
                tokens.append(self._scan_identifier_or_keyword())
                continue

            if current.isdigit():
                tokens.append(self._scan_integer())
                continue

            if self._starts_line_comment():
                self._consume_line_comment()
                continue

            operator = self._scan_operator()
            if operator is not None:
                tokens.append(operator)
                continue

            if current in DELIMITERS:
                line, column = self.line, self.column
                lexeme = self._advance()
                tokens.append(Token(DELIMITERS[lexeme], lexeme, line, column))
                continue

            raise LexicalError(
                character=current,
                line=self.line,
                column=self.column,
            )

        return tokens

    def _scan_identifier_or_keyword(self) -> Token:
        line, column = self.line, self.column
        start = self.index

        self._advance()
        while not self._at_end():
            current = self._peek()
            if not (current.isalnum() or current == "_"):
                break
            self._advance()

        lexeme = self.source[start:self.index]
        kind = TokenKind.KEYWORD if lexeme in self.keywords else TokenKind.IDENTIFIER
        return Token(kind, lexeme, line, column)

    def _scan_integer(self) -> Token:
        line, column = self.line, self.column
        start = self.index

        while not self._at_end() and self._peek().isdigit():
            self._advance()

        return Token(TokenKind.INTEGER, self.source[start:self.index], line, column)

    def _scan_operator(self) -> Token | None:
        line, column = self.line, self.column

        for width in (2, 1):
            candidate = self.source[self.index:self.index + width]
            if candidate in OPERATORS:
                for _ in range(width):
                    self._advance()
                return Token(OPERATORS[candidate], candidate, line, column)

        return None

    def _starts_line_comment(self) -> bool:
        return self.source.startswith("//", self.index)

    def _consume_line_comment(self) -> None:
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _consume_whitespace(self) -> None:
        while not self._at_end() and self._peek().isspace():
            self._advance()

    def _peek(self) -> str:
        return self.source[self.index]

    def _advance(self) -> str:
        current = self.source[self.index]
        self.index += 1

        if current == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return current

    def _at_end(self) -> bool:
        return self.index >= len(self.source)
