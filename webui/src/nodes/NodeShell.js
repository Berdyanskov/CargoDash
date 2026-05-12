import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useGraphStore } from "../store/graphStore";
export function NodeShell({ id, title, subtitle, accent, children, selected, }) {
    const selectedId = useGraphStore((s) => s.selectedId);
    const isSelected = selected ?? selectedId === id;
    return (_jsxs("div", { className: `min-w-[180px] rounded-md border bg-white shadow-sm text-xs ${isSelected ? "border-sky-500 ring-2 ring-sky-200" : "border-slate-300"}`, children: [_jsxs("div", { className: `px-3 py-2 rounded-t-md text-white font-medium ${accent}`, children: [_jsx("div", { children: title }), subtitle && _jsx("div", { className: "text-[10px] opacity-90", children: subtitle })] }), children && _jsx("div", { className: "px-3 py-2 text-slate-600", children: children })] }));
}
