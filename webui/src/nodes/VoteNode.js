import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { NodeShell } from "./NodeShell";
// Vote is referenced by Judge, not connected on the canvas. We render it
// without handles so users see it floating, and Judge's properties panel
// picks it up by id.
export function VoteNode({ id, data, selected }) {
    return (_jsxs(NodeShell, { id: id, title: "Vote", subtitle: data.varName, accent: "bg-violet-600", selected: selected, children: [_jsxs("div", { children: ["true_num=", data.trueNum] }), _jsxs("div", { className: "text-[10px] text-slate-400", children: [data.models.length, " model fn(s)"] }), _jsx("div", { className: "text-[10px] text-slate-400 italic", children: "referenced by a Judge" })] }));
}
