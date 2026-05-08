"""RawDataSource: stream rows from a jsonl file as Batches."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterator, Optional

from ..core.module import Module
from ..data_utils.batch import Batch
from ..data_utils.schema import Schema


class RawDataSource(Module):
    def __init__(
        self,
        path: str | Path,
        schema: Optional[Schema] = None,
        batch_size: int = 32,
        name: Optional[str] = None,
    ):
        super().__init__(input_schema=None, output_schema=schema, name=name)
        self.path = Path(path)
        self.batch_size = batch_size

    def iter_batches(self) -> Iterator[Batch]:
        rows: list[dict] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
                if len(rows) >= self.batch_size:
                    yield Batch(rows=rows, schema=self.output_schema)
                    rows = []
        if rows:
            yield Batch(rows=rows, schema=self.output_schema)
