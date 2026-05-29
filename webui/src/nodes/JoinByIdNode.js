import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Handle, Position } from "reactflow";
import { NodeShell } from "./NodeShell";
export function JoinByIdNode({ id, data, selected, }) {
    // Single target handle on the left accepts multiple incoming edges
    // (React Flow allows many connections into one target) — that's the
    // fan-in: several upstream branches converge here.
    const merge = data.fields.trim()
        ? `merge: ${data.fields}`
        : "merge: all non-empty fields";
    return (_jsxs(NodeShell, { id: id, title: "JoinById", subtitle: data.varName, accent: "bg-teal-600", selected: selected, children: [_jsx(Handle, { type: "target", position: Position.Left }), _jsxs("div", { className: "truncate", children: ["key=", data.key, " \u00B7 expected=", data.expected] }), _jsx("div", { className: "text-[10px] text-slate-400 truncate", children: merge }), _jsx(Handle, { type: "source", position: Position.Right })] }));
}
