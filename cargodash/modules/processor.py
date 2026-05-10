"""Processor: the sequential processing node.

Two modes (default ``"sample"``):

- ``mode="sample"``: ``fn`` receives a single row ``dict`` and returns
  one of:
    * a ``dict``         — the transformed row (1 -> 1)
    * an ``Iterable[dict]`` — multiple rows from one input (1 -> N, augment)
    * ``None`` / empty   — drop this row (1 -> 0, filter)
  The framework calls ``fn`` per-row across the batch with up to
  ``intra_batch_workers`` threads — **this is the typical path for
  LLM-call processors** (each row -> one API call, fan out within the
  batch for throughput).

- ``mode="batch"``: ``fn`` receives the whole ``Batch`` and returns one
  of: ``Batch``, ``Iterable[Batch]``, or ``None``. Use this when the
  transform is inherently batch-shaped (in-batch dedup, sort, group).
  ``intra_batch_workers`` is ignored — concurrency is the user's
  responsibility inside ``fn``.

Choosing a mode is a question of "do I want to think in rows, or in
batches?". The sample-mode default fits 90% of LLM data work.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Iterator, Literal, Optional, Tuple, Union

from ..core.module import Module
from ..data_utils.batch import Batch
from ..data_utils.schema import Schema


SampleFn = Callable[[dict], Union[dict, Iterable[dict], None]]
BatchFn = Callable[[Batch], Union[Batch, Iterable[Batch], None]]


class Processor(Module):
    def __init__(
        self,
        fn: Union[SampleFn, BatchFn],
        mode: Literal["sample", "batch"] = "sample",
        input_schema: Optional[Schema] = None,
        output_schema: Optional[Schema] = None,
        intra_batch_workers: int = 1,
        name: Optional[str] = None,
    ):
        if mode not in ("sample", "batch"):
            raise ValueError(f"mode must be 'sample' or 'batch', got {mode!r}")
        super().__init__(
            input_schema=input_schema,
            output_schema=output_schema,
            intra_batch_workers=intra_batch_workers,
            name=name,
        )
        self.fn = fn
        self.mode = mode

    def process(self, batch: Batch) -> Iterator[Tuple[str, Batch]]:
        if self.mode == "sample":
            yield from self._process_sample(batch)
        else:
            yield from self._process_batch(batch)

    # -- sample mode ----------------------------------------------------------

    def _process_sample(self, batch: Batch) -> Iterator[Tuple[str, Batch]]:
        out_schema = self.output_schema or batch.schema

        if self.intra_batch_workers > 1 and len(batch) > 1:
            with ThreadPoolExecutor(max_workers=self.intra_batch_workers) as pool:
                groups = list(pool.map(self._call_one, batch.rows))
        else:
            groups = [self._call_one(row) for row in batch.rows]

        new_rows = [r for group in groups for r in group]
        if new_rows:
            yield (self.DEFAULT_PORT, Batch(rows=new_rows, schema=out_schema))

    def _call_one(self, row: dict) -> tuple:
        result = self.fn(row)
        if result is None:
            return ()
        if isinstance(result, dict):
            return (result,)
        # iterable[dict]
        return tuple(result)

    # -- batch mode -----------------------------------------------------------

    def _process_batch(self, batch: Batch) -> Iterator[Tuple[str, Batch]]:
        result = self.fn(batch)
        if result is None:
            return
        if isinstance(result, Batch):
            yield (self.DEFAULT_PORT, result)
            return
        for out in result:
            yield (self.DEFAULT_PORT, out)
