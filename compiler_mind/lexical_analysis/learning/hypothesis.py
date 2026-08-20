from __future__ import annotations

from dataclasses import dataclass

from ..rules import IdentifierRule


@dataclass(frozen=True, slots=True)
class IdentifierHypothesis:
    hypothesis_id: str
    description: str
    rule: IdentifierRule


def default_identifier_hypotheses() -> tuple[IdentifierHypothesis, ...]:
    return (
        IdentifierHypothesis(
            hypothesis_id="identifier-alpha-only",
            description="Identifiers start with a letter and continue with letters only.",
            rule=IdentifierRule(
                allow_leading_underscore=False,
                allow_digits_after_first=False,
                allow_underscore_after_first=False,
            ),
        ),
        IdentifierHypothesis(
            hypothesis_id="identifier-alpha-digit",
            description="Identifiers start with a letter and may continue with letters or digits.",
            rule=IdentifierRule(
                allow_leading_underscore=False,
                allow_digits_after_first=True,
                allow_underscore_after_first=False,
            ),
        ),
        IdentifierHypothesis(
            hypothesis_id="identifier-standard",
            description=(
                "Identifiers start with a letter or underscore and may continue "
                "with letters, digits, or underscores."
            ),
            rule=IdentifierRule(),
        ),
    )
