import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function Field({ label, children, }) {
    return (_jsxs("label", { className: "block space-y-1", children: [_jsx("span", { className: "text-[11px] uppercase tracking-wide text-slate-400", children: label }), children] }));
}
export function TextInput({ value, onChange, placeholder, }) {
    return (_jsx("input", { value: value, placeholder: placeholder, onChange: (e) => onChange(e.target.value), className: "w-full text-xs px-2 py-1 border rounded" }));
}
export function NumberInput({ value, onChange, min, step, }) {
    return (_jsx("input", { type: "number", value: value, min: min, step: step, onChange: (e) => onChange(Number(e.target.value)), className: "w-full text-xs px-2 py-1 border rounded" }));
}
export function Select({ value, onChange, options, }) {
    return (_jsx("select", { value: value, onChange: (e) => onChange(e.target.value), className: "w-full text-xs px-2 py-1 border rounded", children: options.map((o) => (_jsx("option", { value: o, children: o }, o))) }));
}
export function Checkbox({ value, onChange, label, }) {
    return (_jsxs("label", { className: "flex items-center gap-2 text-xs text-slate-600", children: [_jsx("input", { type: "checkbox", checked: value, onChange: (e) => onChange(e.target.checked) }), label] }));
}
export function TextArea({ value, onChange, rows = 3, }) {
    return (_jsx("textarea", { value: value, rows: rows, onChange: (e) => onChange(e.target.value), className: "w-full text-xs px-2 py-1 border rounded font-mono" }));
}
