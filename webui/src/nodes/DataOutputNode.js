import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Handle, Position } from "reactflow";
import { NodeShell } from "./NodeShell";
export function DataOutputNode({ id, data, selected, }) {
    return (_jsxs(NodeShell, { id: id, title: "DataOutput", subtitle: data.varName, accent: "bg-rose-600", selected: selected, children: [_jsx(Handle, { type: "target", position: Position.Left }), _jsx("div", { className: "truncate", children: data.path }), _jsxs("div", { className: "text-[10px] text-slate-400", children: ["preserve_order=", String(data.preserveOrder)] })] }));
}
