import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { NodeShell } from "./NodeShell";
const KIND_LABEL = {
    remote: "remote (OpenAI-compat)",
    local_hf: "local HF (in-process)",
    local_vllm: "local vLLM (subprocess)",
};
// ModelSpec is referenced by LLMCall (and can be cited in user code), not
// connected on the canvas. Rendered without handles, like Vote.
export function ModelSpecNode({ id, data, selected }) {
    return (_jsxs(NodeShell, { id: id, title: "ModelSpec", subtitle: data.varName, accent: "bg-fuchsia-600", selected: selected, children: [_jsx("div", { className: "truncate", children: KIND_LABEL[data.modelKind] }), _jsx("div", { className: "text-[10px] text-slate-400 truncate", children: data.model || "(model unset)" }), _jsx("div", { className: "text-[10px] text-slate-400 italic", children: "referenced by LLMCall" })] }));
}
