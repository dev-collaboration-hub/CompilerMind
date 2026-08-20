import unittest

from compiler_mind.lexical_analysis.tokens import Token, TokenKind
from compiler_mind.syntax_analysis import (
    EPSILON,
    Grammar,
    LL1ConflictError,
    ParserError,
    ParserHypothesisGenerator,
    PredictiveParser,
    RecursiveDescentParser,
    SLRParser,
    build_ll1_table,
    build_slr_table,
    tokens_to_terminals,
)


def expression_ll1() -> Grammar:
    return Grammar.from_rules(
        "E",
        {
            "E": [("T", "E'")],
            "E'": [("+", "T", "E'"), (EPSILON,)],
            "T": [("id",)],
        },
    )


class M4ParserTests(unittest.TestCase):
    def test_ll1_table(self) -> None:
        table = build_ll1_table(expression_ll1())
        self.assertEqual(table.production_for("E", "id"), ("T", "E'"))
        self.assertEqual(table.production_for("E'", "$"), (EPSILON,))

    def test_ll1_conflict(self) -> None:
        grammar = Grammar.from_rules(
            "S",
            {"S": [("a", "A"), ("a", "B")], "A": [("x",)], "B": [("y",)]},
        )
        with self.assertRaises(LL1ConflictError):
            build_ll1_table(grammar)

    def test_predictive_parser_builds_tree(self) -> None:
        tree = PredictiveParser(expression_ll1()).parse(("id", "+", "id"))
        self.assertEqual(tree.symbol, "E")
        self.assertEqual(
            tuple(symbol for symbol in tree.leaves() if symbol != EPSILON),
            ("id", "+", "id"),
        )

    def test_predictive_parser_reports_expected_token(self) -> None:
        with self.assertRaises(ParserError) as context:
            PredictiveParser(expression_ll1()).parse(("+", "id"))
        self.assertEqual(context.exception.position, 0)
        self.assertIn("id", context.exception.expected)

    def test_recursive_descent_parser(self) -> None:
        tree = RecursiveDescentParser(expression_ll1()).parse(("id", "+", "id"))
        self.assertEqual(
            tuple(symbol for symbol in tree.leaves() if symbol != EPSILON),
            ("id", "+", "id"),
        )

    def test_recursive_descent_rejects_incomplete_input(self) -> None:
        with self.assertRaises(ParserError):
            RecursiveDescentParser(expression_ll1()).parse(("id", "+"))

    def test_slr_handles_left_recursive_expression_grammar(self) -> None:
        grammar = Grammar.from_rules(
            "E",
            {"E": [("E", "+", "T"), ("T",)], "T": [("id",)]},
        )
        table = build_slr_table(grammar)
        tree = SLRParser(grammar, table).parse(("id", "+", "id"))
        self.assertEqual(tree.symbol, "E")
        self.assertEqual(
            tuple(symbol for symbol in tree.leaves() if symbol != EPSILON),
            ("id", "+", "id"),
        )

    def test_slr_rejects_invalid_input(self) -> None:
        grammar = Grammar.from_rules(
            "E",
            {"E": [("E", "+", "T"), ("T",)], "T": [("id",)]},
        )
        with self.assertRaises(ParserError):
            SLRParser(grammar).parse(("+", "id"))

    def test_slr_supports_epsilon(self) -> None:
        grammar = Grammar.from_rules(
            "S",
            {"S": [("A",)], "A": [("a", "A"), (EPSILON,)]},
        )
        tree = SLRParser(grammar).parse(("a", "a"))
        self.assertEqual(
            tuple(symbol for symbol in tree.leaves() if symbol != EPSILON),
            ("a", "a"),
        )

    def test_hypothesis_generator_detects_left_factoring_candidate(self) -> None:
        grammar = Grammar.from_rules("S", {"S": [("if", "x"), ("if", "y")]})
        with self.assertRaises(LL1ConflictError) as context:
            build_ll1_table(grammar)
        hypotheses = ParserHypothesisGenerator().for_ll1_conflict(
            grammar, context.exception
        )
        self.assertIn("left-factoring", {item.code for item in hypotheses})

    def test_hypothesis_generator_detects_left_recursion(self) -> None:
        grammar = Grammar.from_rules("E", {"E": [("E", "+", "id"), ("id",)]})
        with self.assertRaises(LL1ConflictError) as context:
            build_ll1_table(grammar)
        hypotheses = ParserHypothesisGenerator().for_ll1_conflict(
            grammar, context.exception
        )
        self.assertIn("left-recursion", {item.code for item in hypotheses})

    def test_lexer_token_adapter(self) -> None:
        tokens = [
            Token(TokenKind.KEYWORD, "let", 1, 1),
            Token(TokenKind.IDENTIFIER, "x", 1, 5),
            Token(TokenKind.OPERATOR, "=", 1, 7),
            Token(TokenKind.INTEGER, "10", 1, 9),
        ]
        self.assertEqual(tokens_to_terminals(tokens), ("let", "id", "=", "num"))


if __name__ == "__main__":
    unittest.main()
