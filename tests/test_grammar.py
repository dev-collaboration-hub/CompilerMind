import unittest

from compiler_mind.syntax_analysis import (
    ENDMARKER,
    EPSILON,
    Grammar,
    first_of_sequence,
    first_sets,
    follow_sets,
)


class GrammarProcessingTests(unittest.TestCase):
    def expression_grammar(self) -> Grammar:
        return Grammar.from_rules(
            "E",
            {
                "E": (("T", "E'"),),
                "E'": (("+", "T", "E'"), (EPSILON,)),
                "T": (("F", "T'"),),
                "T'": (("*", "F", "T'"), (EPSILON,)),
                "F": (("(", "E", ")"), ("id",)),
            },
        )

    def test_discovers_terminals_and_nonterminals(self) -> None:
        grammar = self.expression_grammar()

        self.assertEqual(grammar.nonterminals, {"E", "E'", "T", "T'", "F"})
        self.assertEqual(grammar.terminals, {"(", ")", "id", "+", "*"})

    def test_first_sets_for_expression_grammar(self) -> None:
        first = first_sets(self.expression_grammar())

        self.assertEqual(first["E"], {"(", "id"})
        self.assertEqual(first["E'"], {"+", EPSILON})
        self.assertEqual(first["T"], {"(", "id"})
        self.assertEqual(first["T'"], {"*", EPSILON})
        self.assertEqual(first["F"], {"(", "id"})

    def test_follow_sets_for_expression_grammar(self) -> None:
        follow = follow_sets(self.expression_grammar())

        self.assertEqual(follow["E"], {ENDMARKER, ")"})
        self.assertEqual(follow["E'"], {ENDMARKER, ")"})
        self.assertEqual(follow["T"], {"+", ENDMARKER, ")"})
        self.assertEqual(follow["T'"], {"+", ENDMARKER, ")"})
        self.assertEqual(follow["F"], {"*", "+", ENDMARKER, ")"})

    def test_nullable_chain(self) -> None:
        grammar = Grammar.from_rules(
            "S",
            {
                "S": (("A", "B"),),
                "A": (("a",), (EPSILON,)),
                "B": (("b",), (EPSILON,)),
            },
        )

        first = first_sets(grammar)
        follow = follow_sets(grammar, first)

        self.assertEqual(first["S"], {"a", "b", EPSILON})
        self.assertEqual(follow["A"], {"b", ENDMARKER})
        self.assertEqual(follow["B"], {ENDMARKER})

    def test_first_of_sequence(self) -> None:
        grammar = Grammar.from_rules(
            "S",
            {
                "S": (("A", "c"),),
                "A": ((EPSILON,), ("a",)),
            },
        )

        first = first_sets(grammar)
        self.assertEqual(first_of_sequence(("A", "c"), grammar, first), {"a", "c"})

    def test_empty_alternative_is_normalized_to_epsilon(self) -> None:
        grammar = Grammar.from_rules("S", {"S": ((),)})

        self.assertEqual(grammar.alternatives("S"), ((EPSILON,),))
        self.assertEqual(first_sets(grammar)["S"], {EPSILON})

    def test_rejects_mixed_epsilon_production(self) -> None:
        with self.assertRaises(ValueError):
            Grammar.from_rules("S", {"S": ((EPSILON, "a"),)})


if __name__ == "__main__":
    unittest.main()
