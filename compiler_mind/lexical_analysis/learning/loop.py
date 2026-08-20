from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .critic import LexicalCritic
from .hypothesis import IdentifierHypothesis
from .memory import ExperienceMemory, ExperienceRecord
from .models import LexicalTestCase, VerificationReport
from .verifier import LexicalVerifier


@dataclass(frozen=True, slots=True)
class LearningAttempt:
    hypothesis_id: str
    status: str
    discovery_report: VerificationReport
    verification_report: VerificationReport | None


@dataclass(frozen=True, slots=True)
class LearningOutcome:
    learned: bool
    selected_hypothesis: IdentifierHypothesis | None
    attempts: tuple[LearningAttempt, ...]


class LexicalLearningLoop:
    """Try hypotheses, falsify weak ones, and remember only verified rules."""

    def __init__(
        self,
        *,
        verifier: LexicalVerifier | None = None,
        critic: LexicalCritic | None = None,
        memory: ExperienceMemory | None = None,
    ) -> None:
        self.verifier = verifier or LexicalVerifier()
        self.critic = critic or LexicalCritic()
        self.memory = memory or ExperienceMemory()

    def learn_identifier_rule(
        self,
        *,
        hypotheses: Iterable[IdentifierHypothesis],
        discovery_cases: Iterable[LexicalTestCase],
        verification_cases: Iterable[LexicalTestCase],
    ) -> LearningOutcome:
        discovery_cases = tuple(discovery_cases)
        verification_cases = tuple(verification_cases)
        attempts: list[LearningAttempt] = []

        if not discovery_cases or not verification_cases:
            raise ValueError(
                "Learning requires both discovery and verification evidence."
            )

        for hypothesis in hypotheses:
            discovery = self.verifier.verify_all(
                discovery_cases,
                identifier_rule=hypothesis.rule,
            )
            discovery_critique = self.critic.critique(discovery)

            if not discovery_critique.accepted:
                self.memory.record(
                    ExperienceRecord(
                        hypothesis_id=hypothesis.hypothesis_id,
                        status="rejected",
                        discovery_passed=discovery.passed,
                        discovery_total=discovery.total,
                        verification_passed=0,
                        verification_total=len(verification_cases),
                        note=discovery_critique.summary,
                    )
                )
                attempts.append(
                    LearningAttempt(
                        hypothesis.hypothesis_id,
                        "rejected",
                        discovery,
                        None,
                    )
                )
                continue

            verification = self.verifier.verify_all(
                verification_cases,
                identifier_rule=hypothesis.rule,
            )
            verification_critique = self.critic.critique(verification)

            if not verification_critique.accepted:
                self.memory.record(
                    ExperienceRecord(
                        hypothesis_id=hypothesis.hypothesis_id,
                        status="rejected",
                        discovery_passed=discovery.passed,
                        discovery_total=discovery.total,
                        verification_passed=verification.passed,
                        verification_total=verification.total,
                        note=(
                            "Independent verification failed: "
                            f"{verification_critique.summary}"
                        ),
                    )
                )
                attempts.append(
                    LearningAttempt(
                        hypothesis.hypothesis_id,
                        "rejected",
                        discovery,
                        verification,
                    )
                )
                continue

            self.memory.record(
                ExperienceRecord(
                    hypothesis_id=hypothesis.hypothesis_id,
                    status="verified",
                    discovery_passed=discovery.passed,
                    discovery_total=discovery.total,
                    verification_passed=verification.passed,
                    verification_total=verification.total,
                    note="Discovery and independent verification passed.",
                )
            )
            attempts.append(
                LearningAttempt(
                    hypothesis.hypothesis_id,
                    "verified",
                    discovery,
                    verification,
                )
            )
            return LearningOutcome(True, hypothesis, tuple(attempts))

        return LearningOutcome(False, None, tuple(attempts))
