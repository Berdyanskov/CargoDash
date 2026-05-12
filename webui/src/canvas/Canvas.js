import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useCallback, useMemo, useRef } from "react";
import ReactFlow, { Background, Controls, MiniMap, } from "reactflow";
import { useGraphStore } from "../store/graphStore";
import { nodeTypes } from "../nodes";
import { DeletableEdge } from "./DeletableEdge";
export function Canvas() {
    const nodes = useGraphStore((s) => s.nodes);
    const edges = useGraphStore((s) => s.edges);
    const onNodesChange = useGraphStore((s) => s.onNodesChange);
    const onEdgesChange = useGraphStore((s) => s.onEdgesChange);
    const onConnect = useGraphStore((s) => s.onConnect);
    const selectNode = useGraphStore((s) => s.selectNode);
    const addNode = useGraphStore((s) => s.addNode);
    const wrapperRef = useRef(null);
    const rfRef = useRef(null);
    const onDragOver = useCallback((e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
    }, []);
    const onDrop = useCallback((e) => {
        e.preventDefault();
        const kind = e.dataTransfer.getData("application/cargodash-node");
        if (!kind || !rfRef.current)
            return;
        const position = rfRef.current.screenToFlowPosition({
            x: e.clientX,
            y: e.clientY,
        });
        addNode(kind, position);
    }, [addNode]);
    const edgeTypes = useMemo(() => ({ smoothstep: DeletableEdge, default: DeletableEdge }), []);
    return (_jsx("div", { ref: wrapperRef, className: "h-full w-full", onDragOver: onDragOver, onDrop: onDrop, children: _jsxs(ReactFlow, { nodes: nodes, edges: edges, nodeTypes: nodeTypes, edgeTypes: edgeTypes, onNodesChange: onNodesChange, onEdgesChange: onEdgesChange, onConnect: onConnect, onInit: (rf) => (rfRef.current = rf), onSelectionChange: ({ nodes }) => selectNode(nodes[0]?.id ?? null), deleteKeyCode: ["Delete", "Backspace"], 
            // React Flow defaults Space to "pan-activation". Disable it so the
            // Space key is never intercepted at the canvas level.
            panActivationKeyCode: null, fitView: true, children: [_jsx(Background, { gap: 16 }), _jsx(Controls, {}), _jsx(MiniMap, { pannable: true, zoomable: true })] }) }));
}
