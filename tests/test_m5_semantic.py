import unittest

from compiler_mind.semantic_analysis import (
    Assign,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    ExprStmt,
    FloatLiteral,
    FunctionDecl,
    Identifier,
    IfStmt,
    IntLiteral,
    Parameter,
    Program,
    ReturnStmt,
    SemanticAnalyzer,
    VarDecl,
)


class SemanticAnalyzerTests(unittest.TestCase):
    def analyze(self, *items):
        analyzer = SemanticAnalyzer()
        report = analyzer.analyze(Program(tuple(items)))
        return analyzer, report

    def test_valid_program(self):
        add = FunctionDecl(
            "add",
            (Parameter("a", "int"), Parameter("b", "int")),
            "int",
            Block((ReturnStmt(BinaryExpr("+", Identifier("a"), Identifier("b"))),)),
        )
        main = FunctionDecl(
            "main",
            (),
            "int",
            Block((
                VarDecl("x", "int", IntLiteral(2)),
                VarDecl("y", "int", CallExpr("add", (Identifier("x"), IntLiteral(3)))),
                ReturnStmt(Identifier("y")),
            )),
        )
        _, report = self.analyze(add, main)
        self.assertTrue(report.valid, report.diagnostics)

    def test_duplicate_declaration(self):
        _, report = self.analyze(VarDecl("x", "int"), VarDecl("x", "int"))
        self.assertEqual(report.diagnostics[0].code, "DUPLICATE_DECLARATION")

    def test_inner_scope_can_shadow_outer_scope(self):
        _, report = self.analyze(
            VarDecl("x", "int"),
            Block((VarDecl("x", "float", FloatLiteral(1.0)),)),
        )
        self.assertTrue(report.valid)

    def test_undefined_identifier(self):
        _, report = self.analyze(Assign("x", IntLiteral(1)))
        self.assertEqual(report.diagnostics[0].code, "UNDEFINED_IDENTIFIER")

    def test_initializer_type_mismatch(self):
        _, report = self.analyze(VarDecl("flag", "bool", IntLiteral(1)))
        self.assertEqual(report.diagnostics[0].code, "TYPE_MISMATCH")

    def test_numeric_widening_is_allowed(self):
        _, report = self.analyze(VarDecl("x", "float", IntLiteral(1)))
        self.assertTrue(report.valid)

    def test_condition_must_be_bool(self):
        _, report = self.analyze(IfStmt(IntLiteral(1), Block(())))
        self.assertEqual(report.diagnostics[0].code, "CONDITION_TYPE")

    def test_function_argument_count(self):
        fn = FunctionDecl(
            "f", (Parameter("x", "int"),), "int", Block((ReturnStmt(Identifier("x")),))
        )
        _, report = self.analyze(fn, ExprStmt(CallExpr("f", ())))
        self.assertIn("ARGUMENT_COUNT", [d.code for d in report.diagnostics])

    def test_function_argument_type(self):
        fn = FunctionDecl(
            "f", (Parameter("x", "bool"),), "int", Block((ReturnStmt(IntLiteral(1)),))
        )
        _, report = self.analyze(fn, ExprStmt(CallExpr("f", (IntLiteral(1),))))
        self.assertIn("ARGUMENT_TYPE", [d.code for d in report.diagnostics])

    def test_return_type_mismatch(self):
        fn = FunctionDecl("f", (), "bool", Block((ReturnStmt(IntLiteral(1)),)))
        _, report = self.analyze(fn)
        self.assertEqual(report.diagnostics[0].code, "RETURN_TYPE_MISMATCH")

    def test_forward_function_call_is_resolved(self):
        first = FunctionDecl(
            "first", (), "int", Block((ReturnStmt(CallExpr("second", ())),))
        )
        second = FunctionDecl(
            "second", (), "int", Block((ReturnStmt(IntLiteral(2)),))
        )
        _, report = self.analyze(first, second)
        self.assertTrue(report.valid, report.diagnostics)

    def test_unknown_type_is_reported(self):
        _, report = self.analyze(VarDecl("x", "mystery"))
        self.assertEqual(report.diagnostics[0].code, "UNKNOWN_TYPE")

    def test_symbol_table_preserves_scope_snapshots(self):
        analyzer, report = self.analyze(
            VarDecl("global_x", "int"),
            Block((VarDecl("local_x", "int"),)),
        )
        self.assertTrue(report.valid)
        snapshots = analyzer.symbols.snapshots()
        self.assertEqual(snapshots[0].name, "global")
        self.assertTrue(any(s.name.startswith("block:") for s in snapshots))

    def test_multiple_errors_are_collected(self):
        _, report = self.analyze(
            Assign("missing", IntLiteral(1)),
            VarDecl("flag", "bool", IntLiteral(1)),
        )
        self.assertEqual(report.error_count, 2)

    def test_binary_expression_type_check(self):
        _, report = self.analyze(
            VarDecl("x", "int", BinaryExpr("+", IntLiteral(1), BoolLiteral(True)))
        )
        self.assertIn("INVALID_OPERANDS", [d.code for d in report.diagnostics])


if __name__ == "__main__":
    unittest.main()
