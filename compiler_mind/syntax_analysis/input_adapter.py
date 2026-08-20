from __future__ import annotations

from collections.abc import Mapping, Sequence

from compiler_mind.lexical_analysis.tokens import Token, TokenKind


DEFAULT_KIND_TERMINALS: Mapping[TokenKind, str] = {
    TokenKind.IDENTIFIER: "id",
    TokenKind.INTEGER: "num",
}


def tokens_to_terminals(
    tokens: Sequence[Token],
    *,
    kind_terminals: Mapping[TokenKind, str] = DEFAULT_KIND_TERMINALS,
) -> tuple[str, ...]:
    """Convert lexer tokens into grammar terminals.

    Identifiers/integers use abstract grammar terminals by default; keywords,
    operators and delimiters keep their concrete lexeme.
    """

    return tuple(
        kind_terminals.get(token.kind, token.lexeme)
        for token in tokens
    )
