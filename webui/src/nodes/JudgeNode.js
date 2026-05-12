import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Handle, Position } from "reactflow";
import { NodeShell } from "./NodeShell";
export function JudgeNode({ id, data, selected }) {
    const predicateLabel = data.predicate.mode === "code"
        ? `code: ${data.predicate.fnName}`
        : `vote → ${data.predicate.voteNodeId || "(unset)"}`;
    return (_jsxs(NodeShell, { id: id, title: "Judge", subtitle: data.varName, accent: "bg-amber-600", selected: selected, children: [_jsx(Handle, { type: "target", position: Position.Left }), _jsxs("div", { children: ["granularity=", data.granularity] }), _jsx("div", { className: "text-[10px] text-slate-400", children: predicateLabel }), _jsxs("div", { className: "relative mt-2 h-8", children: [_jsx("div", { className: "absolute right-0 top-0 text-[10px] text-emerald-700", children: "on_true" }), _jsx("div", { className: "absolute right-0 bottom-0 text-[10px] text-rose-700", children: "on_false" }), _jsx(Handle, { id: "true", type: "source", position: Position.Right, style: { top: "20%", background: "#059669" } }), _jsx(Handle, { id: "false", type: "source", position: Position.Right, style: { top: "80%", background: "#e11d48" } })] })] }));
}
