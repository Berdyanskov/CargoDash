import { Handle, Position, type NodeProps } from "reactflow";
import type { JoinByIdData } from "../types/graph";
import { NodeShell } from "./NodeShell";

export function JoinByIdNode({
  id,
  data,
  selected,
}: NodeProps<JoinByIdData>) {
  // Single target handle on the left accepts multiple incoming edges
  // (React Flow allows many connections into one target) — that's the
  // fan-in: several upstream branches converge here.
  const merge = data.fields.trim()
    ? `merge: ${data.fields}`
    : "merge: all non-empty fields";
  return (
    <NodeShell
      id={id}
      title="JoinById"
      subtitle={data.varName}
      accent="bg-teal-600"
      selected={selected}
    >
      <Handle type="target" position={Position.Left} />
      <div className="truncate">
        key={data.key} · expected={data.expected}
      </div>
      <div className="text-[10px] text-slate-400 truncate">{merge}</div>
      <Handle type="source" position={Position.Right} />
    </NodeShell>
  );
}
