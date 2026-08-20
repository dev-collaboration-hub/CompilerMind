from __future__ import annotations

from dataclasses import dataclass

from compiler_mind.intermediate_code.model import IRProgram

from .passes import (
    common_subexpression_elimination,
    constant_folding,
    constant_propagation,
    control_flow_cleanup,
    copy_propagation,
    dead_temporary_elimination,
    peephole_optimization,
)


@dataclass(frozen=True, slots=True)
class PassReport:
    name: str
    changes: int


@dataclass(frozen=True, slots=True)
class OptimizationReport:
    original_instructions: int
    optimized_instructions: int
    iterations: int
    passes: tuple[PassReport, ...]

    @property
    def total_changes(self) -> int:
        return sum(item.changes for item in self.passes)


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    program: IRProgram
    report: OptimizationReport


class Optimizer:
    """Deterministic fixed-point optimizer for CompilerMind quadruple IR."""

    DEFAULT_PASSES = (
        ("constant_propagation", constant_propagation),
        ("copy_propagation", copy_propagation),
        ("constant_folding", constant_folding),
        ("common_subexpression_elimination", common_subexpression_elimination),
        ("peephole", peephole_optimization),
        ("control_flow_cleanup", control_flow_cleanup),
        ("dead_temporary_elimination", dead_temporary_elimination),
    )

    def __init__(self, *, max_iterations: int = 8) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1.")
        self.max_iterations = max_iterations

    def optimize(self, program: IRProgram) -> OptimizationResult:
        current = program
        reports: list[PassReport] = []
        iterations = 0

        for iteration in range(1, self.max_iterations + 1):
            iterations = iteration
            changed_this_round = 0
            for name, optimization_pass in self.DEFAULT_PASSES:
                current, changes = optimization_pass(current)
                reports.append(PassReport(name, changes))
                changed_this_round += changes
            if changed_this_round == 0:
                break

        return OptimizationResult(
            current,
            OptimizationReport(
                original_instructions=len(program.instructions),
                optimized_instructions=len(current.instructions),
                iterations=iterations,
                passes=tuple(reports),
            ),
        )
