"""DataOutput: write batches to a jsonl file."""
from __future__ import annotations
import json
import threading
from pathlib import Path
from typing import Iterator, Optional, Tuple

from ..core.module import Module
from ..data_utils.batch import Batch
from ..data_utils.schema import Schema


class DataOutput(Module):
    def __init__(
        self,
        path: str | Path,
        schema: Optional[Schema] = None,
        preserve_order: bool = False,
        name: Optional[str] = None,
    ):
        super().__init__(input_schema=schema, output_schema=None, name=name)
        self.path = Path(path)
        if preserve_order:
            # Preserving original source order across branches needs an
            # ordering key (e.g. an `_id` field assigned by the source) and
            # a reorder buffer at the sink. Phase 1 supports the simple
            # at-arrival-order mode; flag this for a follow-up.
            raise NotImplementedError("preserve_order=True not yet implemented")
        self.preserve_order = preserve_order
        self._lock = threading.Lock()
        self._fh = None  # opened lazily on first batch by the executor thread

    # The executor calls open()/close() around the run.
    def open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w", encoding="utf-8")

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def process(self, batch: Batch) -> Iterator[Tuple[str, Batch]]:
        # Sinks consume but produce nothing.
        with self._lock:
            assert self._fh is not None, "DataOutput.open() not called"
            for row in batch.rows:
                self._fh.write(json.dumps(row, ensure_ascii=False))
                self._fh.write("\n")
        return iter(())  # no downstream output
