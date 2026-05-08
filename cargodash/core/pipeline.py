"""Pipeline: walks the DAG from a source, validates schema, runs it."""
from __future__ import annotations
from typing import List

from .module import Module


class Pipeline:
    def __init__(self, source: Module):
        self.source = source
        self.nodes: List[Module] = self._collect_nodes(source)
        self._validate_schemas()

    @staticmethod
    def _collect_nodes(source: Module) -> List[Module]:
        seen: list[Module] = []
        seen_ids: set[int] = set()
        stack = [source]
        while stack:
            node = stack.pop()
            if id(node) in seen_ids:
                continue
            seen_ids.add(id(node))
            seen.append(node)
            for downstreams in node._downstreams.values():
                stack.extend(downstreams)
        return seen

    def _validate_schemas(self) -> None:
        # For every edge, src.output_schema must be compatible with
        # dst.input_schema (when both are declared).
        # For convergence (multiple upstreams -> one downstream), all
        # upstreams must declare equivalent output_schema.
        upstream_out_by_dst: dict[int, list] = {}
        for src in self.nodes:
            for port, dsts in src._downstreams.items():
                for dst in dsts:
                    if (src.output_schema is not None
                            and dst.input_schema is not None
                            and not src.output_schema.is_compatible_with(dst.input_schema)):
                        raise TypeError(
                            f"schema mismatch: {src.name}.{port} -> {dst.name}\n"
                            f"  src.output_schema = {src.output_schema}\n"
                            f"  dst.input_schema  = {dst.input_schema}"
                        )
                    upstream_out_by_dst.setdefault(id(dst), []).append(
                        (src, src.output_schema)
                    )
        for dst_id, srcs in upstream_out_by_dst.items():
            schemas = [s for _, s in srcs if s is not None]
            if len(schemas) > 1 and any(s != schemas[0] for s in schemas[1:]):
                names = ", ".join(src.name for src, _ in srcs)
                raise TypeError(
                    f"convergence schema mismatch into a single downstream "
                    f"from upstreams: [{names}]"
                )

    def run(self) -> None:
        # Lazy import so `core` doesn't depend on `runtime`.
        from ..runtime.executor import Executor
        Executor().run(self)
