import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
const TYPES = ["int", "float", "str", "bool"];
export function SchemaEditor({ label, value, onChange }) {
    const update = (i, patch) => {
        const next = value.slice();
        next[i] = { ...next[i], ...patch };
        onChange(next);
    };
    const remove = (i) => onChange(value.filter((_, j) => j !== i));
    const add = () => onChange([...value, { name: `field${value.length + 1}`, type: "str" }]);
    return (_jsxs("div", { className: "space-y-1", children: [_jsx("div", { className: "text-[11px] uppercase tracking-wide text-slate-400", children: label }), _jsx("div", { className: "space-y-1", children: value.map((f, i) => (_jsxs("div", { className: "flex gap-1 items-center", children: [_jsx("input", { value: f.name, onChange: (e) => update(i, { name: e.target.value }), className: "flex-1 text-xs px-2 py-1 border rounded", placeholder: "field name" }), _jsx("select", { value: f.type, onChange: (e) => update(i, { type: e.target.value }), className: "text-xs px-1 py-1 border rounded", children: TYPES.map((t) => (_jsx("option", { value: t, children: t }, t))) }), _jsx("button", { onClick: () => remove(i), className: "text-xs text-slate-400 hover:text-rose-600 px-1", title: "remove", children: "\u00D7" })] }, i))) }), _jsx("button", { onClick: add, className: "text-[11px] text-sky-600 hover:underline", children: "+ add field" })] }));
}
