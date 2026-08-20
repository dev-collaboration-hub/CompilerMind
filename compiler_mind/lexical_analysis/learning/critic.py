from __future__ import annotations

from dataclasses import dataclass

from .models import VerificationReport


@dataclass(frozen=True, slots=True)
class Critique:
    accepted: bool
    failed_cases: tuple[str, ...]
    summary: str


class LexicalCritic:
    """Turns verification evidence into a compact hypothesis critique."""

    def critique(self, report: VerificationReport) -> Critique:
        failed = tuple(
            result.case_name for result in report.results if not result.passed
        )

        if not failed:
            return Critique(True, (), f"All {report.total} cases passed.")

        return Critique(
            False,
            failed,
            f"{len(failed)} of {report.total} cases failed.",
        )
