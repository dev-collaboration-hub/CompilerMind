import tempfile
import unittest
from pathlib import Path

from compiler_mind.lexical_analysis import IdentifierRule, Lexer, LexicalError
from compiler_mind.lexical_analysis.learning import (
    ExperienceMemory,
    LexicalExperimenter,
    LexicalLearningLoop,
    default_identifier_hypotheses,
)


class M2CLearningTests(unittest.TestCase):
    def test_identifier_rule_can_change_lexer_behaviour(self) -> None:
        strict = IdentifierRule(allow_leading_underscore=False)

        with self.assertRaises(LexicalError):
            Lexer("_temp", identifier_rule=strict).tokenize()

    def test_loop_rejects_weak_hypotheses_and_learns_verified_rule(self) -> None:
        experimenter = LexicalExperimenter()
        discovery, verification = experimenter.identifier_learning_split()
        memory = ExperienceMemory()

        outcome = LexicalLearningLoop(memory=memory).learn_identifier_rule(
            hypotheses=default_identifier_hypotheses(),
            discovery_cases=discovery,
            verification_cases=verification,
        )

        self.assertTrue(outcome.learned)
        self.assertEqual(
            outcome.selected_hypothesis.hypothesis_id,
            "identifier-standard",
        )
        self.assertEqual(
            [attempt.status for attempt in outcome.attempts],
            ["rejected", "rejected", "verified"],
        )
        self.assertEqual(len(memory.verified), 1)

    def test_no_hypothesis_is_learned_without_verification_evidence(self) -> None:
        experimenter = LexicalExperimenter()
        discovery, _ = experimenter.identifier_learning_split()

        with self.assertRaises(ValueError):
            LexicalLearningLoop().learn_identifier_rule(
                hypotheses=default_identifier_hypotheses(),
                discovery_cases=discovery,
                verification_cases=(),
            )

    def test_memory_persists_verified_and_rejected_experience(self) -> None:
        experimenter = LexicalExperimenter()
        discovery, verification = experimenter.identifier_learning_split()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experience.json"
            LexicalLearningLoop(memory=ExperienceMemory(path)).learn_identifier_rule(
                hypotheses=default_identifier_hypotheses(),
                discovery_cases=discovery,
                verification_cases=verification,
            )

            restored = ExperienceMemory(path)
            self.assertEqual(len(restored.records), 3)
            self.assertEqual(
                restored.verified[0].hypothesis_id,
                "identifier-standard",
            )


if __name__ == "__main__":
    unittest.main()
