"""Judge: split a batch into true/false branches."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterator, Optional, Tuple, Union

from ..core.module import Module, Port
from ..data_utils.batch import Batch
from ..data_utils.schema import Schema


# A predicate is anything callable that returns a truthy/falsy value.
# At granularity="sample" it's called with a single row dict.
# At granularity="batch" it's called with a Batch.
Predicate = Callable[[Union[dict, Batch]], bool]


class Judge(Module):
    TRUE_PORT = "true"
    FALSE_PORT = "false"

    def __init__(
        self,
        fn: Predicate,
        granularity: str = "sample",
        input_schema: Optional[Schema] = None,
        intra_batch_workers: int = 1,
        name: Optional[str] = None,
    ):
        if granularity not in ("sample", "batch"):
            raise ValueError(f"granularity must be 'sample' or 'batch', got {granularity!r}")
        # Judge is a router: it doesn't transform rows, so output schema
        # equals input schema on both ports.
        super().__init__(
            input_schema=input_schema,
            output_schema=input_schema,
            intra_batch_workers=intra_batch_workers,
            name=name,
        )
        self.fn = fn
        self.granularity = granularity
        self._downstreams = {self.TRUE_PORT: [], self.FALSE_PORT: []}
        self.on_true = Port(self, self.TRUE_PORT)
        self.on_false = Port(self, self.FALSE_PORT)

    # `judge >> next` is ambiguous: which branch? Force users to be explicit.
    def __rshift__(self, other):
        raise TypeError(
            f"{self.name}: connect via `.on_true` or `.on_false`, not directly via `>>`"
        )

    def process(self, batch: Batch) -> Iterator[Tuple[str, Batch]]:
        if self.granularity == "batch":
            verdict = bool(self.fn(batch))
            yield (self.TRUE_PORT if verdict else self.FALSE_PORT, batch)
            return

        # granularity == "sample"
        if self.intra_batch_workers > 1 and len(batch) > 1:
            with ThreadPoolExecutor(max_workers=self.intra_batch_workers) as pool:
                verdicts = list(pool.map(self.fn, batch.rows))
        else:
            verdicts = [bool(self.fn(r)) for r in batch.rows]

        true_rows = [r for r, v in zip(batch.rows, verdicts) if v]
        false_rows = [r for r, v in zip(batch.rows, verdicts) if not v]
        if true_rows:
            yield (self.TRUE_PORT, Batch(rows=true_rows, schema=batch.schema))
        if false_rows:
            yield (self.FALSE_PORT, Batch(rows=false_rows, schema=batch.schema))
