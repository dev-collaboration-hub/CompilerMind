from __future__ import annotations

from dataclasses import dataclass

from ..tokens import TokenKind


@dataclass(frozen=True, slots=True)
class ExpectedToken:
    kind: TokenKind
    lexeme: str


@dataclass(frozen=True, slots=True)
class LexicalTestCase:
    name: str
    source: str
    expected_tokens: tuple[ExpectedToken, ...] = ()
    expected_error_character: str | None = None

    def __post_init__(self) -> None:
        if self.expected_error_character is not None and self.expected_tokens:
            raise ValueError(
                "A lexical test case cannot expect both tokens and an error."
            )


@dataclass(frozen=True, slots=True)
class VerificationResult:
    case_name: str
    passed: bool
    message: str


@dataclass(frozen=True, slots=True)
class VerificationReport:
    results: tuple[VerificationResult, ...]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(result.passed for result in self.results)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def all_passed(self) -> bool:
        return self.failed == 0
