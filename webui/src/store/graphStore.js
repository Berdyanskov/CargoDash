import { create } from "zustand";
import { applyEdgeChanges, applyNodeChanges, addEdge, } from "reactflow";
import { defaultNodeData } from "../nodes/defaults";
let nodeCounter = 0;
const nextNodeId = (kind) => `${kind}_${++nodeCounter}`;
export const useGraphStore = create((set, get) => ({
    nodes: [],
    edges: [],
    selectedId: null,
    onNodesChange: (changes) => set((s) => ({ nodes: applyNodeChanges(changes, s.nodes) })),
    onEdgesChange: (changes) => set((s) => ({ edges: applyEdgeChanges(changes, s.edges) })),
    onConnect: (conn) => set((s) => {
        // sourceHandle drives Judge.on_true / on_false. Default is "default".
        const port = conn.sourceHandle === "true" || conn.sourceHandle === "false"
            ? conn.sourceHandle
            : "default";
        return {
            edges: addEdge({ ...conn, sourceHandle: port, type: "smoothstep" }, s.edges),
        };
    }),
    addNode: (kind, position) => set((s) => {
        const id = nextNodeId(kind);
        const data = defaultNodeData(kind, id);
        const node = { id, type: kind, position, data };
        return { nodes: [...s.nodes, node], selectedId: id };
    }),
    updateNodeData: (id, patch) => set((s) => ({
        nodes: s.nodes.map((n) => n.id === id
            ? { ...n, data: { ...n.data, ...patch } }
            : n),
    })),
    deleteNode: (id) => set((s) => ({
        nodes: s.nodes.filter((n) => n.id !== id),
        edges: s.edges.filter((e) => e.source !== id && e.target !== id),
        selectedId: s.selectedId === id ? null : s.selectedId,
    })),
    selectNode: (id) => set({ selectedId: id }),
    loadProject: (project) => {
        if (project.version !== 1) {
            throw new Error(`unsupported project version: ${project.version}`);
        }
        nodeCounter = Math.max(nodeCounter, ...project.nodes.map((n) => parseInt(n.id.split("_").pop() ?? "0", 10)));
        set({
            nodes: project.nodes.map((n) => ({
                id: n.id,
                position: n.position,
                type: n.data.kind,
                data: n.data,
            })),
            edges: project.edges.map((e) => ({
                id: e.id,
                source: e.source,
                target: e.target,
                sourceHandle: e.sourceHandle,
                type: "smoothstep",
            })),
            selectedId: null,
        });
    },
    toProject: () => {
        const { nodes, edges } = get();
        return {
            version: 1,
            nodes: nodes.map((n) => ({
                id: n.id,
                position: n.position,
                data: n.data,
            })),
            edges: edges.map((e) => ({
                id: e.id,
                source: e.source,
                target: e.target,
                sourceHandle: e.sourceHandle ?? "default",
            })),
        };
    },
    reset: () => set({ nodes: [], edges: [], selectedId: null }),
}));
