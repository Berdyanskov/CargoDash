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
import threading
from queue import Queue
from typing import Optional

from ..core.module import Module
from ..core.pipeline import Pipeline
from ..data_utils.queue import make_stream_queue, SENTINEL
from ..modules.source import RawDataSource
from ..modules.output import DataOutput


class Executor:
    DEFAULT_QUEUE_SIZE = 16

    def run(self, pipeline: Pipeline) -> None:
        nodes = pipeline.nodes
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
            threading.Thread(target=self._run_node, args=(node, inbound), name=node.name)
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

        if errors:
            raise errors[0]

    # -- per-node loop --------------------------------------------------------

    def _run_node(self, node: Module, inbound: dict[int, Optional[Queue]]) -> None:
        # On any failure inside this node we must still:
        #   1) propagate SENTINEL to downstreams so they don't hang forever
        #   2) keep draining our own input queue so upstream's blocking puts
        #      eventually return (otherwise the failure cascades into a
        #      deadlock all the way up the DAG)
        # The error is recorded and re-raised; the wrap() in run() collects it.
        try:
            if isinstance(node, RawDataSource):
                for batch in node.iter_batches():
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
                try:
                    for port, out_batch in node.process(msg):
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
