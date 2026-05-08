"""Module base class, Port, and the >> connection operator.

Design notes:
- Each module has named output ports. A plain `Module` has one port,
  "default". `Judge` has two, "true"/"false".
- `>>` connects a source port to a downstream module. Source can be
  either a `Module` (uses its default port) or a `Port` (uses the named
  port). Returns the downstream so chains work.
- Convergence is just "two upstreams end up pointing at the same
  downstream object". The Pipeline traversal sees this naturally.
- Edges (queues) are NOT created here. Construction-time we only build
  the graph; the executor materializes queues at run time. This keeps
  graph manipulation cheap and serializable.
"""
from __future__ import annotations
from typing import Iterator, Optional, Tuple

from ..data_utils.batch import Batch
from ..data_utils.schema import Schema


class Module:
    DEFAULT_PORT = "default"

    def __init__(
        self,
        input_schema: Optional[Schema] = None,
        output_schema: Optional[Schema] = None,
        intra_batch_workers: int = 1,
        name: Optional[str] = None,
    ):
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.intra_batch_workers = max(1, int(intra_batch_workers))
        self.name = name or self.__class__.__name__

        # Graph state. Populated by `>>`. Read by Pipeline / Executor.
        self._downstreams: dict[str, list["Module"]] = {self.DEFAULT_PORT: []}
        self._upstreams: list["Module"] = []

    # -- Graph construction --------------------------------------------------

    def __rshift__(self, other: "Module") -> "Module":
        return _connect(self, self.DEFAULT_PORT, other)

    def __repr__(self) -> str:
        return f"<{self.name}>"

    # -- Execution hook (override in subclasses) -----------------------------

    def process(self, batch: Batch) -> Iterator[Tuple[str, Batch]]:
        """Yield ``(port_name, output_batch)`` tuples.

        A plain Processor yields ``("default", out)``; Judge yields
        ``("true", ...)`` and/or ``("false", ...)``. Yielding zero
        tuples is allowed and means "this batch produced no output".
        """
        raise NotImplementedError


class Port:
    """A handle to a named output of a module. Lets us write
    ``judge.on_true >> next_node`` cleanly."""

    __slots__ = ("owner", "name")

    def __init__(self, owner: Module, name: str):
        self.owner = owner
        self.name = name

    def __rshift__(self, other: Module) -> Module:
        return _connect(self.owner, self.name, other)

    def __repr__(self) -> str:
        return f"<Port {self.owner.name}.{self.name}>"


def _connect(src: Module, port: str, dst: Module) -> Module:
    if port not in src._downstreams:
        raise ValueError(
            f"{src.name} has no output port '{port}' (available: "
            f"{list(src._downstreams)})"
        )
    src._downstreams[port].append(dst)
    dst._upstreams.append(src)
    return dst
