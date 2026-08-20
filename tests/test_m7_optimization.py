import unittest

from compiler_mind.intermediate_code.model import IRProgram, Quadruple
from compiler_mind.optimization import (
    Optimizer,
    common_subexpression_elimination,
    constant_folding,
    constant_propagation,
    control_flow_cleanup,
    copy_propagation,
    dead_temporary_elimination,
    peephole_optimization,
)


def q(op, arg1=None, arg2=None, result=None):
    return Quadruple(op, arg1, arg2, result)


class M7OptimizationTests(unittest.TestCase):
    def test_constant_folding_arithmetic(self):
        program, changes = constant_folding(IRProgram((q("+", "2", "3", "%t1"),)))
        self.assertEqual(program.instructions, (q("assign", "5", result="%t1"),))
        self.assertEqual(changes, 1)

    def test_constant_folding_comparison_and_boolean(self):
        program, changes = constant_folding(IRProgram((
            q("<", "2", "3", "%t1"),
            q("&&", "true", "false", "%t2"),
        )))
        self.assertEqual(program.instructions[0].arg1, "true")
        self.assertEqual(program.instructions[1].arg1, "false")
        self.assertEqual(changes, 2)

    def test_divide_by_zero_is_not_folded(self):
        original = IRProgram((q("/", "1", "0", "%t1"),))
        program, changes = constant_folding(original)
        self.assertEqual(program, original)
        self.assertEqual(changes, 0)

    def test_constant_propagation_stays_inside_control_flow_region(self):
        original = IRProgram((
            q("assign", "1", result="x"),
            q("if_false", "cond", result="L1"),
            q("+", "x", "2", "%t1"),
            q("label", result="L1"),
            q("+", "x", "3", "%t2"),
        ))
        program, _ = constant_propagation(original)
        self.assertEqual(program.instructions[2].arg1, "x")
        self.assertEqual(program.instructions[4].arg1, "x")

    def test_copy_propagation(self):
        program, changes = copy_propagation(IRProgram((
            q("assign", "a", result="b"),
            q("+", "b", "1", "%t1"),
        )))
        self.assertEqual(program.instructions[1].arg1, "a")
        self.assertEqual(changes, 1)

    def test_copy_propagation_invalidates_reassigned_source(self):
        program, _ = copy_propagation(IRProgram((
            q("assign", "a", result="b"),
            q("assign", "7", result="a"),
            q("+", "b", "1", "%t1"),
        )))
        self.assertEqual(program.instructions[2].arg1, "b")

    def test_local_common_subexpression_elimination(self):
        program, changes = common_subexpression_elimination(IRProgram((
            q("+", "a", "b", "%t1"),
            q("+", "b", "a", "%t2"),
        )))
        self.assertEqual(program.instructions[1], q("assign", "%t1", result="%t2"))
        self.assertEqual(changes, 1)

    def test_cse_resets_after_user_assignment(self):
        program, changes = common_subexpression_elimination(IRProgram((
            q("+", "a", "b", "%t1"),
            q("assign", "4", result="a"),
            q("+", "a", "b", "%t2"),
        )))
        self.assertEqual(program.instructions[2].op, "+")
        self.assertEqual(changes, 0)

    def test_peephole_algebraic_identities(self):
        program, changes = peephole_optimization(IRProgram((
            q("+", "x", "0", "%t1"),
            q("*", "%t1", "1", "%t2"),
            q("assign", "y", result="y"),
        )))
        self.assertEqual(program.instructions, (
            q("assign", "x", result="%t1"),
            q("assign", "%t1", result="%t2"),
        ))
        self.assertEqual(changes, 3)

    def test_redundant_goto_to_next_label_removed(self):
        program, changes = peephole_optimization(IRProgram((
            q("goto", result="L1"),
            q("label", result="L1"),
        )))
        self.assertEqual(program.instructions, (q("label", result="L1"),))
        self.assertEqual(changes, 1)

    def test_constant_condition_cleanup(self):
        program, changes = control_flow_cleanup(IRProgram((
            q("if_false", "false", result="L1"),
            q("assign", "1", result="x"),
            q("label", result="L1"),
        )))
        self.assertNotIn(q("assign", "1", result="x"), program.instructions)
        self.assertGreaterEqual(changes, 2)

    def test_dead_temporary_elimination_is_iterative(self):
        program, changes = dead_temporary_elimination(IRProgram((
            q("+", "a", "b", "%t1"),
            q("*", "%t1", "2", "%t2"),
        )))
        self.assertEqual(program.instructions, ())
        self.assertEqual(changes, 2)

    def test_unused_call_result_does_not_remove_call(self):
        program, changes = dead_temporary_elimination(IRProgram((
            q("call", "foo", "0", "%t1"),
        )))
        self.assertEqual(program.instructions, (q("call", "foo", "0"),))
        self.assertEqual(changes, 1)

    def test_pipeline_reaches_fixed_point(self):
        original = IRProgram((
            q("assign", "2", result="x"),
            q("+", "x", "3", "%t1"),
            q("*", "%t1", "1", "%t2"),
            q("assign", "%t2", result="y"),
        ))
        result = Optimizer().optimize(original)
        self.assertIn(q("assign", "5", result="y"), result.program.instructions)
        self.assertLess(len(result.program.instructions), len(original.instructions))
        self.assertGreater(result.report.total_changes, 0)

    def test_optimizer_is_deterministic(self):
        original = IRProgram((
            q("+", "2", "3", "%t1"),
            q("assign", "%t1", result="x"),
        ))
        optimizer = Optimizer()
        first = optimizer.optimize(original)
        second = optimizer.optimize(original)
        self.assertEqual(first.program, second.program)
        self.assertEqual(first.report, second.report)

    def test_invalid_iteration_limit_rejected(self):
        with self.assertRaises(ValueError):
            Optimizer(max_iterations=0)


if __name__ == "__main__":
    unittest.main()
