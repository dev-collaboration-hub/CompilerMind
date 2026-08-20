import unittest

from compiler_mind.lexical_analysis import TokenKind
from compiler_mind.lexical_analysis.learning import (
    ExpectedToken,
    LexicalExperimenter,
    LexicalTestCase,
    LexicalVerifier,
)


class LexicalLearningTests(unittest.TestCase):
    def test_default_experiments_pass(self) -> None:
        cases = LexicalExperimenter().default_suite()
        report = LexicalVerifier().verify_all(cases)

        self.assertTrue(report.all_passed)
        self.assertEqual((report.total, report.passed, report.failed), (5, 5, 0))

    def test_verifier_detects_wrong_expected_token(self) -> None:
        case = LexicalTestCase(
            name="intentional-mismatch",
            source="let",
            expected_tokens=(ExpectedToken(TokenKind.IDENTIFIER, "let"),),
        )

        result = LexicalVerifier().verify(case)

        self.assertFalse(result.passed)
        self.assertIn("Token mismatch", result.message)

    def test_verifier_checks_expected_error(self) -> None:
        case = LexicalTestCase(
            name="invalid-character",
            source="@",
            expected_error_character="@",
        )

        result = LexicalVerifier().verify(case)

        self.assertTrue(result.passed)

    def test_identifier_suite_is_generated_and_verified(self) -> None:
        cases = LexicalExperimenter().identifier_suite()
        report = LexicalVerifier().verify_all(cases)

        self.assertEqual(report.total, 5)
        self.assertTrue(report.all_passed)

    def test_case_cannot_expect_tokens_and_error(self) -> None:
        with self.assertRaises(ValueError):
            LexicalTestCase(
                name="invalid-expectation",
                source="x",
                expected_tokens=(ExpectedToken(TokenKind.IDENTIFIER, "x"),),
                expected_error_character="@",
            )


if __name__ == "__main__":
    unittest.main()
