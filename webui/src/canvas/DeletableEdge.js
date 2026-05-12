import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { BaseEdge, EdgeLabelRenderer, getSmoothStepPath, useReactFlow, } from "reactflow";
// Smooth-step edge with a small × button shown on hover or when selected.
// React Flow's default Backspace/Delete shortcut still works; this is just
// the discoverable affordance.
export function DeletableEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, style, markerEnd, selected, }) {
    const { setEdges } = useReactFlow();
    const [hover, setHover] = useState(false);
    const [path, labelX, labelY] = getSmoothStepPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
    });
    const visible = hover || selected;
    return (_jsxs(_Fragment, { children: [_jsx(BaseEdge, { id: id, path: path, markerEnd: markerEnd, style: {
                    ...style,
                    stroke: selected ? "#0284c7" : style?.stroke ?? "#94a3b8",
                    strokeWidth: selected ? 2 : 1.5,
                } }), _jsx("path", { d: path, fill: "none", stroke: "transparent", strokeWidth: 20, onMouseEnter: () => setHover(true), onMouseLeave: () => setHover(false), style: { pointerEvents: "stroke" } }), _jsx(EdgeLabelRenderer, { children: _jsx("div", { onMouseEnter: () => setHover(true), onMouseLeave: () => setHover(false), style: {
                        position: "absolute",
                        transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                        pointerEvents: "all",
                        opacity: visible ? 1 : 0,
                        transition: "opacity 120ms",
                    }, className: "nodrag nopan", children: _jsx("button", { onClick: (e) => {
                            e.stopPropagation();
                            setEdges((eds) => eds.filter((edge) => edge.id !== id));
                        }, title: "Delete edge", className: "w-5 h-5 rounded-full bg-white border border-slate-300 shadow text-slate-600 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-300 text-xs leading-none flex items-center justify-center", children: "\u00D7" }) }) })] }));
}
