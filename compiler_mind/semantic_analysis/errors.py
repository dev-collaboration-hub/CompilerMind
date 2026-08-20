from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SemanticDiagnostic:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class SemanticReport:
    diagnostics: tuple[SemanticDiagnostic, ...]

    @property
    def valid(self) -> bool:
        return not self.diagnostics

    @property
    def error_count(self) -> int:
        return len(self.diagnostics)
