import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Handle, Position } from "reactflow";
import { NodeShell } from "./NodeShell";
export function RawDataSourceNode({ id, data, selected, }) {
    return (_jsxs(NodeShell, { id: id, title: "RawDataSource", subtitle: data.varName, accent: "bg-emerald-600", selected: selected, children: [_jsx("div", { className: "truncate", children: data.path }), _jsxs("div", { className: "text-[10px] text-slate-400", children: ["batch=", data.batchSize, " \u00B7 ", data.schema.length, " fields"] }), _jsx(Handle, { type: "source", position: Position.Right })] }));
}
