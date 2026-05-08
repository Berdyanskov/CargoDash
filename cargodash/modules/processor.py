"""Processor: per-batch transformation. MapProcessor: per-sample with parallelism."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Iterator, Optional, Tuple

from ..core.module import Module
from ..data_utils.batch import Batch
from ..data_utils.schema import Schema


class Processor(Module):
    """User function takes a Batch and yields (or returns) zero or more Batches.

    Use this when transforms are inherently batch-shaped (e.g. dedup,
    in-batch sort). Per-sample parallelism is the user's responsibility.
    """

    def __init__(
        self,
        fn: Callable[[Batch], Iterable[Batch]],
        input_schema: Optional[Schema] = None,
        output_schema: Optional[Schema] = None,
        name: Optional[str] = None,
    ):
        super().__init__(input_schema=input_schema, output_schema=output_schema, name=name)
        self.fn = fn

    def process(self, batch: Batch) -> Iterator[Tuple[str, Batch]]:
        result = self.fn(batch)
        # fn may return a single Batch, an iterable of Batches, or None.
        if result is None:
            return
        if isinstance(result, Batch):
            yield (self.DEFAULT_PORT, result)
            return
        for out in result:
            yield (self.DEFAULT_PORT, out)


class MapProcessor(Module):
    """User function takes one row dict and returns one row dict.

    The framework applies it across the batch with up to
    ``intra_batch_workers`` threads — the typical case for IO-bound
    LLM calls.
    """

    def __init__(
        self,
        fn: Callable[[dict], dict],
        input_schema: Optional[Schema] = None,
        output_schema: Optional[Schema] = None,
        intra_batch_workers: int = 1,
        name: Optional[str] = None,
    ):
        super().__init__(
            input_schema=input_schema,
            output_schema=output_schema,
            intra_batch_workers=intra_batch_workers,
            name=name,
        )
        self.fn = fn

    def process(self, batch: Batch) -> Iterator[Tuple[str, Batch]]:
        if self.intra_batch_workers > 1 and len(batch) > 1:
            with ThreadPoolExecutor(max_workers=self.intra_batch_workers) as pool:
                new_rows = list(pool.map(self.fn, batch.rows))
        else:
            new_rows = [self.fn(r) for r in batch.rows]
        yield (self.DEFAULT_PORT, Batch(rows=new_rows, schema=self.output_schema or batch.schema))
