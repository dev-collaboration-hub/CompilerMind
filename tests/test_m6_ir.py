import unittest

from compiler_mind.intermediate_code import (
    IRGenerationError,
    IRGenerator,
    build_cfg,
)
from compiler_mind.semantic_analysis import (
    Assign,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    CharLiteral,
    ExprStmt,
    FloatLiteral,
    FunctionDecl,
    Identifier,
    IfStmt,
    IntLiteral,
    Parameter,
    Program,
    ReturnStmt,
    UnaryExpr,
    VarDecl,
    WhileStmt,
)


class M6IntermediateCodeTests(unittest.TestCase):
    def test_generates_arithmetic_three_address_code(self) -> None:
        program = Program(
            (
                VarDecl(
                    "x",
                    "int",
                    BinaryExpr(
                        "+",
                        IntLiteral(2),
                        BinaryExpr("*", IntLiteral(3), IntLiteral(4)),
                    ),
                ),
            )
        )

        ir = IRGenerator().generate(program)

        self.assertEqual(
            ir.tac(),
            (
                "declare int x",
                "%t1 = 3 * 4",
                "%t2 = 2 + %t1",
                "x = %t2",
            ),
        )

    def test_generates_assignment_and_unary_expression(self) -> None:
        program = Program(
            (
                VarDecl("y", "int", IntLiteral(4)),
                VarDecl("x", "int"),
                Assign("x", UnaryExpr("-", Identifier("y"))),
            )
        )

        tac = IRGenerator().generate(program).tac()

        self.assertIn("%t1 = -y", tac)
        self.assertEqual(tac[-1], "x = %t1")

    def test_invalid_semantic_program_is_rejected(self) -> None:
        program = Program((Assign("missing", IntLiteral(1)),))

        with self.assertRaises(IRGenerationError):
            IRGenerator().generate(program)

    def test_generates_if_else_control_flow(self) -> None:
        program = Program(
            (
                VarDecl("ok", "bool", BoolLiteral(True)),
                VarDecl("x", "int", IntLiteral(0)),
                IfStmt(
                    Identifier("ok"),
                    Block((Assign("x", IntLiteral(1)),)),
                    Block((Assign("x", IntLiteral(2)),)),
                ),
            )
        )

        tac = IRGenerator().generate(program).tac()

        self.assertTrue(any(line.startswith("ifFalse ok goto else_") for line in tac))
        self.assertTrue(any(line.startswith("goto if_end_") for line in tac))
        self.assertTrue(any(line.startswith("else_") and line.endswith(":") for line in tac))
        self.assertTrue(any(line.startswith("if_end_") and line.endswith(":") for line in tac))

    def test_generates_if_without_else(self) -> None:
        program = Program(
            (
                VarDecl("ok", "bool", BoolLiteral(True)),
                IfStmt(Identifier("ok"), Block(())),
            )
        )

        tac = IRGenerator().generate(program).tac()

        self.assertTrue(any(line.startswith("ifFalse ok goto if_end_") for line in tac))
        self.assertTrue(tac[-1].startswith("if_end_"))

    def test_generates_while_loop_and_back_jump(self) -> None:
        program = Program(
            (
                VarDecl("x", "int", IntLiteral(0)),
                WhileStmt(
                    BinaryExpr("<", Identifier("x"), IntLiteral(3)),
                    Block(
                        (
                            Assign(
                                "x",
                                BinaryExpr("+", Identifier("x"), IntLiteral(1)),
                            ),
                        )
                    ),
                ),
            )
        )

        tac = IRGenerator().generate(program).tac()

        self.assertTrue(any(line.startswith("while_start_") for line in tac))
        self.assertTrue(any(line.startswith("goto while_start_") for line in tac))
        self.assertTrue(tac[-1].startswith("while_end_"))

    def test_generates_functions_parameters_calls_and_returns(self) -> None:
        add = FunctionDecl(
            "add",
            (Parameter("a", "int"), Parameter("b", "int")),
            "int",
            Block((ReturnStmt(BinaryExpr("+", Identifier("a"), Identifier("b"))),)),
        )
        program = Program(
            (
                add,
                VarDecl("x", "int", CallExpr("add", (IntLiteral(2), IntLiteral(3)))),
            )
        )

        tac = IRGenerator().generate(program).tac()

        self.assertIn("function add:", tac)
        self.assertIn("param int a", tac)
        self.assertIn("param int b", tac)
        self.assertIn("param 2", tac)
        self.assertIn("param 3", tac)
        self.assertTrue(any("call add, 2" in line for line in tac))
        self.assertTrue(any(line.startswith("return %t") for line in tac))

    def test_void_call_statement_does_not_create_unused_temporary(self) -> None:
        log = FunctionDecl(
            "log",
            (),
            "void",
            Block((ReturnStmt(),)),
        )
        program = Program((log, ExprStmt(CallExpr("log"))))

        tac = IRGenerator().generate(program).tac()

        self.assertIn("call log, 0", tac)
        self.assertFalse(any("= call log, 0" in line for line in tac))

    def test_preserves_primitive_literals(self) -> None:
        program = Program(
            (
                VarDecl("b", "bool", BoolLiteral(True)),
                VarDecl("c", "char", CharLiteral("z")),
                VarDecl("f", "float", FloatLiteral(1.5)),
            )
        )

        tac = IRGenerator().generate(program).tac()

        self.assertIn("b = true", tac)
        self.assertIn("c = 'z'", tac)
        self.assertIn("f = 1.5", tac)

    def test_triples_reference_producing_instruction(self) -> None:
        program = Program(
            (
                VarDecl("x", "int", BinaryExpr("+", IntLiteral(1), IntLiteral(2))),
            )
        )
        triples = IRGenerator().generate(program).triples()

        operation = next(triple for triple in triples if triple.op == "+")
        assignment = triples[-1]
        self.assertEqual(assignment.op, "=")
        self.assertEqual(assignment.arg1, f"({operation.index})")
        self.assertEqual(assignment.arg2, "x")

    def test_cfg_if_has_two_successors(self) -> None:
        program = Program(
            (
                VarDecl("ok", "bool", BoolLiteral(True)),
                IfStmt(Identifier("ok"), Block(()), Block(())),
            )
        )
        cfg = build_cfg(IRGenerator().generate(program))

        self.assertTrue(any(len(successors) == 2 for successors in cfg.edges.values()))

    def test_cfg_while_contains_back_edge(self) -> None:
        program = Program(
            (
                VarDecl("ok", "bool", BoolLiteral(True)),
                WhileStmt(Identifier("ok"), Block(())),
            )
        )
        cfg = build_cfg(IRGenerator().generate(program))

        self.assertTrue(
            any(
                target <= source
                for source, successors in cfg.edges.items()
                for target in successors
            )
        )

    def test_cfg_does_not_fall_through_into_function_definition(self) -> None:
        function = FunctionDecl("f", (), "void", Block((ReturnStmt(),)))
        program = Program((VarDecl("x", "int", IntLiteral(1)), function))
        cfg = build_cfg(IRGenerator().generate(program))

        function_block = next(
            block
            for block in cfg.blocks
            if block.instructions[0].op == "func_begin"
        )
        predecessors = {
            source
            for source, successors in cfg.edges.items()
            if function_block.block_id in successors
        }
        self.assertEqual(predecessors, set())

    def test_empty_program_has_empty_cfg(self) -> None:
        cfg = build_cfg(IRGenerator().generate(Program()))
        self.assertEqual(cfg.blocks, ())
        self.assertEqual(dict(cfg.edges), {})

    def test_generation_is_deterministic_and_resets_counters(self) -> None:
        generator = IRGenerator()
        program = Program(
            (
                VarDecl("x", "int", BinaryExpr("+", IntLiteral(1), IntLiteral(2))),
            )
        )

        first = generator.generate(program).tac()
        second = generator.generate(program).tac()

        self.assertEqual(first, second)
        self.assertIn("%t1 = 1 + 2", first)


if __name__ == "__main__":
    unittest.main()
