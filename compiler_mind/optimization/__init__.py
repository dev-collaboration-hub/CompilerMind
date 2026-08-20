from .pipeline import OptimizationReport, OptimizationResult, Optimizer, PassReport
from .passes import (
    common_subexpression_elimination,
    constant_folding,
    constant_propagation,
    control_flow_cleanup,
    copy_propagation,
    dead_temporary_elimination,
    peephole_optimization,
)

__all__ = [
    "OptimizationReport",
    "OptimizationResult",
    "Optimizer",
    "PassReport",
    "common_subexpression_elimination",
    "constant_folding",
    "constant_propagation",
    "control_flow_cleanup",
    "copy_propagation",
    "dead_temporary_elimination",
    "peephole_optimization",
]
