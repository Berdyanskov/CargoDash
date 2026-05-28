"""JoinById: stateful per-key fan-in merger.

Pairs with fan-out — one upstream feeds multiple downstream branches, each
branch fills a different field of the same row (keyed by ``key``), and a
single ``JoinById`` recombines them once ``expected`` branches have
reported for that key. The canonical example is "ask N models to solve
the same problem in parallel, then merge their answers row-by-row":

    judge.on_true >> gen_a
    judge.on_true >> gen_b
    judge.on_true >> gen_c
    gen_a >> join
    gen_b >> join
    gen_c >> join
    join >> downstream

Why count contributions rather than gate on "all required fields are
truthy": upstream nodes may legitimately produce an empty value (LLM
exhausted retries, model returned empty content, retry wrapper returned
``""``). Gating on truthiness would deadlock those rows in the buffer
forever; counting contributions lets empty values flow on and lets
downstream verifiers/filters decide what to do with them.
"""
from __future__ import annotations
import threading
from typing import Iterator, Optional, Sequence, Tuple

from ..core.module import Module
from ..data_utils.batch import Batch
from ..data_utils.schema import Schema


class JoinById(Module):
    def __init__(
        self,
        key: str = "id",
        fields: Optional[Sequence[str]] = None,
        *,
        expected: int = 2,
        input_schema: Optional[Schema] = None,
        output_schema: Optional[Schema] = None,
        name: Optional[str] = None,
    ):
        """
        Args:
            key: row field that identifies which partial rows belong
                together. Must be present in every input row (typically a
                stable source ID).
            fields: field names to merge from each contributing upstream.
                Each upstream's row contributes its truthy values for
                these fields into the buffered slot; falsy values
                (``""``, ``None``, ``0``) are skipped so they don't
                overwrite an earlier contribution. If ``None``, every
                truthy field in the incoming row is merged.
            expected: how many upstreams must report for the same ``key``
                before the merged row is emitted. With three fan-out gens
                feeding one JoinById, set ``expected=3``.
            input_schema/output_schema: JoinById doesn't transform
                shape, so output equals input by default. If both given
                they must match.

        Thread-safety: the executor schedules one worker per node, so
        ``process`` is called serially on this instance. The internal
        lock is defensive — it costs ~nothing uncontended and protects
        against future executor changes that may parallelize within a
        node.
        """
        if expected < 1:
            raise ValueError(f"expected must be >= 1, got {expected}")
        if (input_schema is not None and output_schema is not None
                and input_schema != output_schema):
            raise ValueError(
                "JoinById output_schema must equal input_schema "
                "(or omit output_schema to inherit)"
            )
        super().__init__(
            input_schema=input_schema,
            output_schema=output_schema if output_schema is not None else input_schema,
            intra_batch_workers=1,
            name=name,
        )
        self.key = key
        self.fields = list(fields) if fields is not None else None
        self.expected = expected
        # key -> {"slot": dict, "count": int}
        self._buf: dict = {}
        self._lock = threading.Lock()

    def process(self, batch: Batch) -> Iterator[Tuple[str, Batch]]:
        ready: list[dict] = []
        with self._lock:
            for row in batch.rows:
                if self.key not in row:
                    raise KeyError(
                        f"{self.name}: input row missing key field "
                        f"{self.key!r} (available: {sorted(row)})"
                    )
                k = row[self.key]
                entry = self._buf.setdefault(k, {"slot": dict(row), "count": 0})
                slot = entry["slot"]
                merge_fields = (
                    self.fields if self.fields is not None
                    else [f for f in row if row.get(f)]
                )
                for f in merge_fields:
                    if row.get(f):
                        slot[f] = row[f]
                entry["count"] += 1
                if entry["count"] >= self.expected:
                    ready.append(slot)
                    del self._buf[k]
        if ready:
            yield (self.DEFAULT_PORT, Batch(rows=ready, schema=batch.schema))

    @property
    def pending(self) -> int:
        """Number of keys still in the buffer (waiting for more
        contributions). Useful for end-of-run sanity checks: a non-zero
        ``pending`` after Pipeline.run() returns means some rows never
        got all their expected upstream contributions."""
        with self._lock:
            return len(self._buf)
