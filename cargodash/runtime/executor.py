"""Threaded execution engine.

Model:
- One worker thread per module.
- Each module gets a single inbound queue. All upstreams write into it,
  including a SENTINEL marker each upstream emits when finished.
- Source modules have no inbound queue; they iterate batches directly
  and push to their downstreams' inbound queues.
- Sinks (no downstreams) just consume.
- Backpressure: bounded queues + blocking put/get.

Why threads (not asyncio): the workload is dominated by IO-bound LLM
calls and disk reads. Threads keep the user-facing API plain Python (no
`async def` required in user fns) and the GIL is fine here. Swap in
asyncio or multiprocessing later behind the same Pipeline / Module
contract.
"""
from __future__ import annotations
import sys
import threading
from pathlib import Path
from queue import Queue
from typing import Iterator, Optional

from ..core.module import Module
from ..core.pipeline import Pipeline
from ..data_utils.batch import Batch
from ..data_utils.queue import make_stream_queue, SENTINEL
from ..modules.source import RawDataSource
from ..modules.output import DataOutput


def _dryrun_path(p: Path) -> Path:
    """``out.jsonl`` -> ``out.dryrun.jsonl`` (preserves the original
    extension and parent directory)."""
    return p.parent / f"{p.stem}.dryrun{p.suffix}"


class Executor:
    DEFAULT_QUEUE_SIZE = 16

    def run(
        self,
        pipeline: Pipeline,
        dry_run_rows: Optional[int] = None,
    ) -> None:
        nodes = pipeline.nodes
        dry_run = dry_run_rows is not None

        # In dry-run mode we redirect every DataOutput to a sibling
        # `.dryrun` file so production artifacts are never overwritten.
        # Originals are restored in a `finally` so a partial-failure
        # mid-run leaves DataOutput.path identical to how we found it.
        saved_paths: dict[int, Path] = {}
        if dry_run:
            for node in nodes:
                if isinstance(node, DataOutput):
                    saved_paths[id(node)] = node.path
                    node.path = _dryrun_path(node.path)
            print(
                f"[cargodash] DRY-RUN: capping each source to "
                f"{dry_run_rows} rows; DataOutputs redirected to "
                f"`<stem>.dryrun<suffix>`",
                file=sys.stderr,
            )

        # Per-node row counters. `in_rows` tracks rows received via the
        # inbound queue; `out_rows` tracks rows fanned out to downstreams
        # (summed across all output ports). Each node writes only its
        # own slot, so no locking needed.
        row_counts: dict[int, dict[str, int]] = {
            id(node): {"in": 0, "out": 0} for node in nodes
        }

        try:
            inbound: dict[int, Optional[Queue]] = {}
            for node in nodes:
                inbound[id(node)] = (
                    None if isinstance(node, RawDataSource)
                    else make_stream_queue(self.DEFAULT_QUEUE_SIZE)
                )

            # Open sinks before any worker starts writing.
            for node in nodes:
                if isinstance(node, DataOutput):
                    node.open()

            threads = [
                threading.Thread(
                    target=self._run_node,
                    args=(node, inbound, row_counts, dry_run_rows),
                    name=node.name,
                )
                for node in nodes
            ]
            errors: list[BaseException] = []

            # Wrap targets so an exception in any worker propagates after join.
            def wrap(t: threading.Thread):
                orig = t._target  # type: ignore[attr-defined]

                def safe_run(*args, **kwargs):
                    try:
                        orig(*args, **kwargs)
                    except BaseException as e:  # noqa: BLE001
                        errors.append(e)
                t._target = safe_run  # type: ignore[attr-defined]

            for t in threads:
                wrap(t)
                t.start()
            for t in threads:
                t.join()

            for node in nodes:
                if isinstance(node, DataOutput):
                    node.close()

            if dry_run:
                self._print_dryrun_summary(nodes, row_counts)

            if errors:
                raise errors[0]
        finally:
            # Restore DataOutput paths even if the run blew up partway —
            # leaving them pointing at `.dryrun.jsonl` would silently
            # corrupt the next real run.
            for node in nodes:
                if id(node) in saved_paths:
                    node.path = saved_paths[id(node)]

    # -- per-node loop --------------------------------------------------------

    def _run_node(
        self,
        node: Module,
        inbound: dict[int, Optional[Queue]],
        row_counts: dict[int, dict[str, int]],
        dry_run_rows: Optional[int],
    ) -> None:
        # On any failure inside this node we must still:
        #   1) propagate SENTINEL to downstreams so they don't hang forever
        #   2) keep draining our own input queue so upstream's blocking puts
        #      eventually return (otherwise the failure cascades into a
        #      deadlock all the way up the DAG)
        # The error is recorded and re-raised; the wrap() in run() collects it.
        counts = row_counts[id(node)]
        try:
            if isinstance(node, RawDataSource):
                source_iter: Iterator[Batch] = (
                    self._capped_source_iter(node, dry_run_rows)
                    if dry_run_rows is not None
                    else node.iter_batches()
                )
                for batch in source_iter:
                    counts["out"] += len(batch)
                    self._fanout(node, node.DEFAULT_PORT, batch, inbound)
                return

            in_q = inbound[id(node)]
            assert in_q is not None
            upstream_count = len(node._upstreams)
            sentinels_seen = 0
            error: Optional[BaseException] = None
            while True:
                msg = in_q.get()
                if msg is SENTINEL:
                    sentinels_seen += 1
                    if sentinels_seen >= upstream_count:
                        break
                    continue
                if error is not None:
                    continue  # drain mode: don't process, just unblock upstream
                counts["in"] += len(msg)
                try:
                    for port, out_batch in node.process(msg):
                        counts["out"] += len(out_batch)
                        self._fanout(node, port, out_batch, inbound)
                except BaseException as e:  # noqa: BLE001
                    error = e
            if error is not None:
                raise error
        finally:
            self._close_all_ports(node, inbound)

    def _fanout(self, node: Module, port: str, batch, inbound) -> None:
        for downstream in node._downstreams.get(port, []):
            inbound[id(downstream)].put(batch)

    def _close_all_ports(self, node: Module, inbound) -> None:
        # One SENTINEL per outgoing edge; each downstream will count to
        # know when *all* its upstreams are done.
        for downstreams in node._downstreams.values():
            for downstream in downstreams:
                inbound[id(downstream)].put(SENTINEL)

    # -- dry-run helpers ------------------------------------------------------

    @staticmethod
    def _capped_source_iter(
        node: RawDataSource, max_rows: int
    ) -> Iterator[Batch]:
        """Yield from ``node.iter_batches()``, truncating so at most
        ``max_rows`` rows ever leave this source. The last yielded batch
        is sliced in place rather than dropped, so dry-runs against
        small files still see *some* data when ``batch_size > max_rows``.
        """
        seen = 0
        for batch in node.iter_batches():
            if seen >= max_rows:
                break
            remaining = max_rows - seen
            if len(batch) > remaining:
                batch = Batch(rows=batch.rows[:remaining], schema=batch.schema)
            seen += len(batch)
            yield batch
            if seen >= max_rows:
                break

    @staticmethod
    def _print_dryrun_summary(
        nodes: list[Module],
        row_counts: dict[int, dict[str, int]],
    ) -> None:
        print("[cargodash] DRY-RUN summary (rows in -> rows out):", file=sys.stderr)
        # Field widths chosen for the typical case (single-digit / few-digit
        # row counts); over-long names just push the column right.
        for node in nodes:
            c = row_counts[id(node)]
            if isinstance(node, RawDataSource):
                line = f"  {node.name:<24} (source) ->  {c['out']:>6}"
            elif isinstance(node, DataOutput):
                line = (
                    f"  {node.name:<24} {c['in']:>6}  ->  (sink)"
                    f"   wrote {node.path}"
                )
            else:
                line = f"  {node.name:<24} {c['in']:>6}  ->  {c['out']:>6}"
            print(line, file=sys.stderr)
