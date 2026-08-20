from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .model import IRProgram, Quadruple


@dataclass(frozen=True, slots=True)
class BasicBlock:
    block_id: int
    instruction_indices: tuple[int, ...]
    instructions: tuple[Quadruple, ...]


@dataclass(frozen=True, slots=True)
class ControlFlowGraph:
    blocks: tuple[BasicBlock, ...]
    edges: Mapping[int, frozenset[int]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "edges", MappingProxyType(dict(self.edges)))


def build_cfg(program: IRProgram) -> ControlFlowGraph:
    """Create basic blocks and control-flow edges from quadruple IR."""

    instructions = program.instructions
    if not instructions:
        return ControlFlowGraph((), {})

    labels = {
        instruction.result: index
        for index, instruction in enumerate(instructions)
        if instruction.op == "label" and instruction.result is not None
    }

    leaders = {0}
    for index, instruction in enumerate(instructions):
        if instruction.op in {"label", "func_begin"}:
            leaders.add(index)

        if (
            instruction.op in {"goto", "if_false", "return", "func_end"}
            and index + 1 < len(instructions)
        ):
            leaders.add(index + 1)

        if (
            instruction.op in {"goto", "if_false"}
            and instruction.result in labels
        ):
            leaders.add(labels[instruction.result])

    starts = sorted(leaders)
    blocks: list[BasicBlock] = []
    instruction_to_block: dict[int, int] = {}

    for block_id, start in enumerate(starts):
        end = starts[block_id + 1] if block_id + 1 < len(starts) else len(instructions)
        indices = tuple(range(start, end))
        block = BasicBlock(
            block_id,
            indices,
            tuple(instructions[index] for index in indices),
        )
        blocks.append(block)
        for index in indices:
            instruction_to_block[index] = block_id

    edges: dict[int, set[int]] = {block.block_id: set() for block in blocks}

    for block in blocks:
        last_index = block.instruction_indices[-1]
        last = instructions[last_index]

        if last.op == "goto":
            if last.result in labels:
                edges[block.block_id].add(
                    instruction_to_block[labels[last.result]]
                )
            continue

        if last.op == "if_false":
            if last.result in labels:
                edges[block.block_id].add(
                    instruction_to_block[labels[last.result]]
                )
            if last_index + 1 < len(instructions):
                edges[block.block_id].add(
                    instruction_to_block[last_index + 1]
                )
            continue

        if last.op in {"return", "func_end"}:
            continue

        if last_index + 1 < len(instructions):
            next_instruction = instructions[last_index + 1]
            if next_instruction.op != "func_begin":
                edges[block.block_id].add(
                    instruction_to_block[last_index + 1]
                )

    return ControlFlowGraph(
        tuple(blocks),
        {block_id: frozenset(successors) for block_id, successors in edges.items()},
    )
