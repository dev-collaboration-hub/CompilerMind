from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExperienceRecord:
    hypothesis_id: str
    status: str
    discovery_passed: int
    discovery_total: int
    verification_passed: int
    verification_total: int
    note: str


class ExperienceMemory:
    """Small JSON-backed store for verified and rejected lexical hypotheses."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._records: list[ExperienceRecord] = []

        if self.path is not None and self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._records = [ExperienceRecord(**item) for item in raw]

    @property
    def records(self) -> tuple[ExperienceRecord, ...]:
        return tuple(self._records)

    @property
    def verified(self) -> tuple[ExperienceRecord, ...]:
        return tuple(
            record for record in self._records if record.status == "verified"
        )

    def record(self, record: ExperienceRecord) -> None:
        self._records.append(record)
        self._persist()

    def _persist(self) -> None:
        if self.path is None:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(record) for record in self._records]
        self.path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
