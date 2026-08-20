import unittest

from compiler_mind.lexical_analysis import Lexer, LexicalError, TokenKind


class LexerTests(unittest.TestCase):
    def test_tokenizes_basic_program(self) -> None:
        tokens = Lexer("let total = price + 10;").tokenize()

        self.assertEqual(
            [(token.kind, token.lexeme) for token in tokens],
            [
                (TokenKind.KEYWORD, "let"),
                (TokenKind.IDENTIFIER, "total"),
                (TokenKind.OPERATOR, "="),
                (TokenKind.IDENTIFIER, "price"),
                (TokenKind.OPERATOR, "+"),
                (TokenKind.INTEGER, "10"),
                (TokenKind.SEMICOLON, ";"),
            ],
        )

    def test_tracks_line_and_column(self) -> None:
        tokens = Lexer("let x = 1;\nvalue = x;").tokenize()
        value = tokens[5]

        self.assertEqual((value.lexeme, value.line, value.column), ("value", 2, 1))

    def test_skips_line_comments(self) -> None:
        tokens = Lexer("let x = 1; // note\nx = x + 1;").tokenize()

        self.assertEqual(tokens[5].lexeme, "x")
        self.assertEqual(tokens[5].line, 2)

    def test_reports_invalid_character_position(self) -> None:
        with self.assertRaises(LexicalError) as context:
            Lexer("let x = @5;").tokenize()

        self.assertEqual(context.exception.character, "@")
        self.assertEqual((context.exception.line, context.exception.column), (1, 9))

    def test_uses_longest_operator_first(self) -> None:
        tokens = Lexer("a == b").tokenize()

        self.assertEqual(tokens[1].lexeme, "==")


if __name__ == "__main__":
    unittest.main()
