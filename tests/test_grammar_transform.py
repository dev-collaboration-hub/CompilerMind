import unittest

from compiler_mind.syntax_analysis import EPSILON, Grammar, left_factor, remove_left_recursion


class GrammarTransformTests(unittest.TestCase):
    def test_removes_direct_left_recursion(self) -> None:
        grammar = Grammar.from_rules(
            "E",
            {
                "E": (("E", "+", "T"), ("T",)),
                "T": (("id",),),
            },
        )

        transformed = remove_left_recursion(grammar)

        self.assertEqual(transformed.alternatives("E"), (("T", "E'"),))
        self.assertEqual(
            transformed.alternatives("E'"),
            (("+", "T", "E'"), (EPSILON,)),
        )

    def test_removes_indirect_left_recursion(self) -> None:
        grammar = Grammar.from_rules(
            "S",
            {
                "S": (("A", "a"), ("b",)),
                "A": (("S", "c"), ("d",)),
            },
        )

        transformed = remove_left_recursion(grammar)

        for lhs, alternatives in transformed.productions.items():
            for production in alternatives:
                self.assertFalse(production and production[0] == lhs)

        self.assertIn("A'", transformed.nonterminals)

    def test_left_factors_shared_prefix(self) -> None:
        grammar = Grammar.from_rules(
            "S",
            {
                "S": (
                    ("if", "E", "then", "S", "else", "S"),
                    ("if", "E", "then", "S"),
                    ("other",),
                ),
            },
        )

        transformed = left_factor(grammar)

        self.assertEqual(
            transformed.alternatives("S"),
            (("other",), ("if", "E", "then", "S", "S'")),
        )
        self.assertEqual(
            transformed.alternatives("S'"),
            (("else", "S"), (EPSILON,)),
        )

    def test_left_factoring_repeats_for_nested_prefixes(self) -> None:
        grammar = Grammar.from_rules(
            "A",
            {
                "A": (
                    ("a", "b", "c"),
                    ("a", "b", "d"),
                    ("a", "e"),
                ),
            },
        )

        transformed = left_factor(grammar)

        self.assertEqual(len(transformed.alternatives("A")), 1)
        self.assertGreaterEqual(len(transformed.nonterminals), 3)

    def test_rejects_degenerate_self_loop(self) -> None:
        grammar = Grammar.from_rules(
            "A",
            {
                "A": (("A",), ("x",)),
            },
        )

        with self.assertRaises(ValueError):
            remove_left_recursion(grammar)


if __name__ == "__main__":
    unittest.main()
