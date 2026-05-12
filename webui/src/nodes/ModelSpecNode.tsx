import type { NodeProps } from "reactflow";
import type { ModelSpecData } from "../types/graph";
import { NodeShell } from "./NodeShell";

const KIND_LABEL: Record<ModelSpecData["modelKind"], string> = {
  remote: "remote (OpenAI-compat)",
  local_hf: "local HF (in-process)",
  local_vllm: "local vLLM (subprocess)",
};

// ModelSpec is referenced by LLMCall (and can be cited in user code), not
// connected on the canvas. Rendered without handles, like Vote.
export function ModelSpecNode({ id, data, selected }: NodeProps<ModelSpecData>) {
  return (
    <NodeShell
      id={id}
      title="ModelSpec"
      subtitle={data.varName}
      accent="bg-fuchsia-600"
      selected={selected}
    >
      <div className="truncate">{KIND_LABEL[data.modelKind]}</div>
      <div className="text-[10px] text-slate-400 truncate">
        {data.model || "(model unset)"}
      </div>
      <div className="text-[10px] text-slate-400 italic">
        referenced by LLMCall
      </div>
    </NodeShell>
  );
}
