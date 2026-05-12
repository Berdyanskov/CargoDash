import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Handle, Position } from "reactflow";
import { NodeShell } from "./NodeShell";
import { useGraphStore } from "../store/graphStore";
export function LLMCallNode({ id, data, selected }) {
    const refId = data.client.mode === "modelRef" ? data.client.modelNodeId : "";
    const refName = useGraphStore((s) => {
        if (!refId)
            return null;
        const n = s.nodes.find((x) => x.id === refId);
        return n ? n.data.varName : "(missing ref)";
    });
    const summary = data.client.mode === "inline"
        ? `model: ${data.client.model}`
        : `→ ${refName ?? "(missing ref)"}`;
    return (_jsxs(NodeShell, { id: id, title: "LLMCall", subtitle: data.varName, accent: "bg-indigo-600", selected: selected, children: [_jsx(Handle, { type: "target", position: Position.Left }), _jsx("div", { className: "truncate", children: summary }), _jsxs("div", { className: "text-[10px] text-slate-400", children: ["\u2192 ", data.outputField, " \u00B7 workers=", data.intraBatchWorkers] }), _jsx(Handle, { type: "source", position: Position.Right })] }));
}
