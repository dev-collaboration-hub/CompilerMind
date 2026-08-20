from __future__ import annotations

from collections.abc import Iterable

from ..errors import LexicalError
from ..lexer import Lexer
from ..rules import DEFAULT_IDENTIFIER_RULE, IdentifierRule
from .models import (
    ExpectedToken,
    LexicalTestCase,
    VerificationReport,
    VerificationResult,
)


class LexicalVerifier:
    """Runs lexical experiments and compares expected behaviour with reality."""

    def verify(
        self,
        case: LexicalTestCase,
        *,
        identifier_rule: IdentifierRule = DEFAULT_IDENTIFIER_RULE,
    ) -> VerificationResult:
        try:
            tokens = Lexer(
                case.source,
                identifier_rule=identifier_rule,
            ).tokenize()
        except LexicalError as error:
            if case.expected_error_character is None:
                return VerificationResult(
                    case.name,
                    False,
                    (
                        f"Unexpected lexical error {error.character!r} "
                        f"at {error.line}:{error.column}."
                    ),
                )

            passed = error.character == case.expected_error_character
            message = (
                "Expected lexical error observed."
                if passed
                else (
                    f"Expected error {case.expected_error_character!r}, "
                    f"got {error.character!r}."
                )
            )
            return VerificationResult(case.name, passed, message)

        if case.expected_error_character is not None:
            return VerificationResult(
                case.name,
                False,
                (
                    f"Expected lexical error {case.expected_error_character!r}, "
                    "but tokenization succeeded."
                ),
            )

        actual = tuple(ExpectedToken(token.kind, token.lexeme) for token in tokens)
        if actual == case.expected_tokens:
            return VerificationResult(case.name, True, "Token stream matched.")

        return VerificationResult(
            case.name,
            False,
            f"Token mismatch. expected={case.expected_tokens!r}, actual={actual!r}",
        )

    def verify_all(
        self,
        cases: Iterable[LexicalTestCase],
        *,
        identifier_rule: IdentifierRule = DEFAULT_IDENTIFIER_RULE,
    ) -> VerificationReport:
        return VerificationReport(
            tuple(
                self.verify(case, identifier_rule=identifier_rule)
                for case in cases
            )
        )
