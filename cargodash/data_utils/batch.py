"""Batch: rows + an optional bound schema. Rows are plain dicts for now."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .schema import Schema


@dataclass
class Batch:
    rows: list[dict] = field(default_factory=list)
    schema: Optional[Schema] = None

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    @classmethod
    def from_rows(cls, rows: Iterable[dict], schema: Optional[Schema] = None) -> "Batch":
        return cls(rows=list(rows), schema=schema)
