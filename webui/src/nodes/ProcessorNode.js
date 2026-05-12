import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Handle, Position } from "reactflow";
import { NodeShell } from "./NodeShell";
export function ProcessorNode({ id, data, selected, }) {
    return (_jsxs(NodeShell, { id: id, title: "Processor", subtitle: data.varName, accent: "bg-sky-600", selected: selected, children: [_jsx(Handle, { type: "target", position: Position.Left }), _jsxs("div", { children: ["mode=", data.mode, " \u00B7 workers=", data.intraBatchWorkers] }), _jsxs("div", { className: "text-[10px] text-slate-400", children: ["fn: ", data.fnName] }), _jsx(Handle, { type: "source", position: Position.Right })] }));
}
