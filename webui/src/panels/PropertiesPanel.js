import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useGraphStore } from "../store/graphStore";
import { SchemaEditor } from "./SchemaEditor";
import { CodeField } from "./CodeField";
import { Checkbox, Field, NumberInput, Select, TextArea, TextInput, } from "./fields";
export function PropertiesPanel() {
    const selectedId = useGraphStore((s) => s.selectedId);
    const node = useGraphStore((s) => selectedId ? s.nodes.find((n) => n.id === selectedId) : null);
    const updateNodeData = useGraphStore((s) => s.updateNodeData);
    const deleteNode = useGraphStore((s) => s.deleteNode);
    if (!node) {
        return (_jsx("div", { className: "p-4 text-xs text-slate-400", children: "Select a node to edit its properties." }));
    }
    const data = node.data;
    const patch = (p) => updateNodeData(node.id, p);
    return (_jsxs("div", { className: "h-full overflow-y-auto p-3 space-y-3", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("div", { className: "text-xs text-slate-400", children: data.kind }), _jsx("div", { className: "text-sm font-semibold", children: data.varName })] }), _jsx("button", { onClick: () => deleteNode(node.id), className: "text-[11px] text-rose-600 hover:underline", children: "delete" })] }), _jsx(Field, { label: "variable name", children: _jsx(TextInput, { value: data.varName, onChange: (v) => patch({ varName: v }) }) }), data.kind === "RawDataSource" && (_jsx(RawDataSourceForm, { data: data, onPatch: patch })), data.kind === "DataOutput" && (_jsx(DataOutputForm, { data: data, onPatch: patch })), data.kind === "Processor" && (_jsx(ProcessorForm, { data: data, onPatch: patch })), data.kind === "Judge" && _jsx(JudgeForm, { data: data, onPatch: patch }), data.kind === "Vote" && _jsx(VoteForm, { data: data, onPatch: patch }), data.kind === "LLMCall" && _jsx(LLMCallForm, { data: data, onPatch: patch }), data.kind === "ModelSpec" && (_jsx(ModelSpecForm, { data: data, onPatch: patch }))] }));
}
function RawDataSourceForm({ data, onPatch, }) {
    return (_jsxs(_Fragment, { children: [_jsx(Field, { label: "path", children: _jsx(TextInput, { value: data.path, onChange: (v) => onPatch({ path: v }) }) }), _jsx(Field, { label: "batch_size", children: _jsx(NumberInput, { value: data.batchSize, min: 1, onChange: (v) => onPatch({ batchSize: v }) }) }), _jsx(SchemaEditor, { label: "schema", value: data.schema, onChange: (v) => onPatch({ schema: v }) })] }));
}
function DataOutputForm({ data, onPatch, }) {
    return (_jsxs(_Fragment, { children: [_jsx(Field, { label: "path", children: _jsx(TextInput, { value: data.path, onChange: (v) => onPatch({ path: v }) }) }), _jsx(Checkbox, { label: "preserve_order", value: data.preserveOrder, onChange: (v) => onPatch({ preserveOrder: v }) }), _jsx(SchemaEditor, { label: "schema", value: data.schema, onChange: (v) => onPatch({ schema: v }) })] }));
}
function ProcessorForm({ data, onPatch, }) {
    return (_jsxs(_Fragment, { children: [_jsx(Field, { label: "mode", children: _jsx(Select, { value: data.mode, options: ["sample", "batch"], onChange: (v) => onPatch({ mode: v }) }) }), _jsx(Field, { label: "intra_batch_workers", children: _jsx(NumberInput, { value: data.intraBatchWorkers, min: 1, onChange: (v) => onPatch({ intraBatchWorkers: v }) }) }), _jsx(Field, { label: "fn name (must match def in code below)", children: _jsx(TextInput, { value: data.fnName, onChange: (v) => onPatch({ fnName: v }) }) }), _jsx(CodeField, { label: "fn source", value: data.fnSource, onChange: (v) => onPatch({ fnSource: v }), height: 200 }), _jsx(SchemaEditor, { label: "input_schema", value: data.inputSchema, onChange: (v) => onPatch({ inputSchema: v }) }), _jsx(SchemaEditor, { label: "output_schema", value: data.outputSchema, onChange: (v) => onPatch({ outputSchema: v }) })] }));
}
function JudgeForm({ data, onPatch }) {
    const voteNodes = useGraphStore((s) => s.nodes.filter((n) => n.data.kind === "Vote"));
    return (_jsxs(_Fragment, { children: [_jsx(Field, { label: "granularity", children: _jsx(Select, { value: data.granularity, options: ["sample", "batch"], onChange: (v) => onPatch({ granularity: v }) }) }), _jsx(Field, { label: "intra_batch_workers", children: _jsx(NumberInput, { value: data.intraBatchWorkers, min: 1, onChange: (v) => onPatch({ intraBatchWorkers: v }) }) }), _jsx(Field, { label: "predicate source", children: _jsx(Select, { value: data.predicate.mode, options: ["code", "voteRef"], onChange: (mode) => {
                        if (mode === "code") {
                            onPatch({
                                predicate: {
                                    mode: "code",
                                    fnSource: "def predicate(row):\n    return True\n",
                                    fnName: "predicate",
                                },
                            });
                        }
                        else {
                            onPatch({
                                predicate: { mode: "voteRef", voteNodeId: voteNodes[0]?.id ?? "" },
                            });
                        }
                    } }) }), data.predicate.mode === "code" ? (_jsxs(_Fragment, { children: [_jsx(Field, { label: "fn name", children: _jsx(TextInput, { value: data.predicate.fnName, onChange: (v) => onPatch({
                                predicate: { ...data.predicate, fnName: v },
                            }) }) }), _jsx(CodeField, { label: "predicate source", value: data.predicate.fnSource, onChange: (v) => onPatch({
                            predicate: { ...data.predicate, fnSource: v },
                        }), height: 200 })] })) : (_jsx(Field, { label: "vote node", children: _jsxs("select", { value: data.predicate.voteNodeId, onChange: (e) => onPatch({
                        predicate: { mode: "voteRef", voteNodeId: e.target.value },
                    }), className: "w-full text-xs px-2 py-1 border rounded", children: [_jsx("option", { value: "", children: "\u2014 pick a Vote node \u2014" }), voteNodes.map((n) => (_jsxs("option", { value: n.id, children: [n.data.varName, " (", n.id, ")"] }, n.id)))] }) })), _jsx(SchemaEditor, { label: "input_schema", value: data.inputSchema, onChange: (v) => onPatch({ inputSchema: v }) })] }));
}
function VoteForm({ data, onPatch }) {
    const updateModel = (i, patch) => {
        const next = data.models.slice();
        next[i] = { ...next[i], ...patch };
        onPatch({ models: next });
    };
    const addModel = () => onPatch({
        models: [
            ...data.models,
            {
                fnName: `model_${data.models.length + 1}`,
                fnSource: `def model_${data.models.length + 1}(sample):\n    return True\n`,
            },
        ],
    });
    const removeModel = (i) => onPatch({
        models: data.models.filter((_, j) => j !== i),
    });
    return (_jsxs(_Fragment, { children: [_jsx(Field, { label: "true_num", children: _jsx(NumberInput, { value: data.trueNum, min: 1, onChange: (v) => onPatch({ trueNum: v }) }) }), _jsxs("div", { className: "space-y-3", children: [_jsx("div", { className: "text-[11px] uppercase tracking-wide text-slate-400", children: "model_list" }), data.models.map((m, i) => (_jsxs("div", { className: "border rounded p-2 space-y-2 bg-slate-50", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx("input", { value: m.fnName, onChange: (e) => updateModel(i, { fnName: e.target.value }), className: "flex-1 text-xs px-2 py-1 border rounded", placeholder: "fn name" }), _jsx("button", { onClick: () => removeModel(i), className: "text-[11px] text-rose-600", children: "remove" })] }), _jsx(CodeField, { label: `model #${i + 1} source`, value: m.fnSource, onChange: (v) => updateModel(i, { fnSource: v }), height: 120 })] }, i))), _jsx("button", { onClick: addModel, className: "text-[11px] text-sky-600 hover:underline", children: "+ add model fn" })] })] }));
}
function LLMCallForm({ data, onPatch, }) {
    const modelSpecs = useGraphStore((s) => s.nodes.filter((n) => n.data.kind === "ModelSpec"));
    return (_jsxs(_Fragment, { children: [_jsx(Field, { label: "client source", children: _jsx(Select, { value: data.client.mode, options: ["inline", "modelRef"], onChange: (mode) => {
                        if (mode === "inline") {
                            onPatch({
                                client: {
                                    mode: "inline",
                                    model: "gpt-4.1-mini",
                                    apiKey: "",
                                    baseUrl: "",
                                },
                            });
                        }
                        else {
                            onPatch({
                                client: {
                                    mode: "modelRef",
                                    modelNodeId: modelSpecs[0]?.id ?? "",
                                },
                            });
                        }
                    } }) }), data.client.mode === "inline" ? (_jsxs(_Fragment, { children: [_jsx(Field, { label: "model", children: _jsx(TextInput, { value: data.client.model, onChange: (v) => onPatch({
                                client: { ...data.client, model: v },
                            }) }) }), _jsx(Field, { label: "api_key", children: _jsx(TextInput, { value: data.client.apiKey, onChange: (v) => onPatch({
                                client: { ...data.client, apiKey: v },
                            }), placeholder: "sk-..." }) }), _jsx(Field, { label: "base_url (optional)", children: _jsx(TextInput, { value: data.client.baseUrl, onChange: (v) => onPatch({
                                client: { ...data.client, baseUrl: v },
                            }), placeholder: "https://api.deepseek.com/v1" }) })] })) : (_jsx(Field, { label: "model spec", children: _jsxs("select", { value: data.client.modelNodeId, onChange: (e) => onPatch({
                        client: { mode: "modelRef", modelNodeId: e.target.value },
                    }), className: "w-full text-xs px-2 py-1 border rounded", children: [_jsx("option", { value: "", children: "\u2014 pick a ModelSpec node \u2014" }), modelSpecs.map((n) => (_jsxs("option", { value: n.id, children: [n.data.varName, " (", n.data.modelKind, ")"] }, n.id)))] }) })), _jsx(Field, { label: "output_field", children: _jsx(TextInput, { value: data.outputField, onChange: (v) => onPatch({ outputField: v }) }) }), _jsx(Field, { label: "prompt template", children: _jsx(TextArea, { value: data.prompt, rows: 4, onChange: (v) => onPatch({ prompt: v }) }) }), _jsx(Field, { label: "gen_kwargs (JSON)", children: _jsx(TextArea, { value: data.genKwargs, rows: 3, onChange: (v) => onPatch({ genKwargs: v }) }) }), _jsx(Field, { label: "intra_batch_workers", children: _jsx(NumberInput, { value: data.intraBatchWorkers, min: 1, onChange: (v) => onPatch({ intraBatchWorkers: v }) }) }), _jsx(SchemaEditor, { label: "input_schema", value: data.inputSchema, onChange: (v) => onPatch({ inputSchema: v }) }), _jsx(SchemaEditor, { label: "output_schema", value: data.outputSchema, onChange: (v) => onPatch({ outputSchema: v }) })] }));
}
function ModelSpecForm({ data, onPatch, }) {
    const setKind = (k) => onPatch({ modelKind: k });
    return (_jsxs(_Fragment, { children: [_jsx(Field, { label: "kind", children: _jsx(Select, { value: data.modelKind, options: ["remote", "local_hf", "local_vllm"], onChange: (v) => setKind(v) }) }), _jsx(Field, { label: "model (HF repo id, local path, or remote model name)", children: _jsx(TextInput, { value: data.model, onChange: (v) => onPatch({ model: v }), placeholder: data.modelKind === "remote"
                        ? "gpt-4.1-mini"
                        : "Qwen/Qwen2.5-7B-Instruct or /share/models/..." }) }), data.modelKind === "remote" && (_jsxs(_Fragment, { children: [_jsx(Field, { label: "api_key", children: _jsx(TextInput, { value: data.apiKey, onChange: (v) => onPatch({ apiKey: v }), placeholder: "sk-..." }) }), _jsx(Field, { label: "base_url (optional)", children: _jsx(TextInput, { value: data.baseUrl, onChange: (v) => onPatch({ baseUrl: v }), placeholder: "https://api.deepseek.com/v1" }) })] })), (data.modelKind === "local_hf" || data.modelKind === "local_vllm") && (_jsxs(_Fragment, { children: [_jsx(Field, { label: "cache_dir (optional, for HF downloads)", children: _jsx(TextInput, { value: data.cacheDir, onChange: (v) => onPatch({ cacheDir: v }), placeholder: "/path/to/hf_cache" }) }), _jsx(Field, { label: "dtype", children: _jsx(Select, { value: data.dtype || "", options: ["", "float16", "bfloat16", "float32"], onChange: (v) => onPatch({ dtype: v }) }) }), _jsx(Checkbox, { label: "trust_remote_code", value: data.trustRemoteCode, onChange: (v) => onPatch({ trustRemoteCode: v }) })] })), data.modelKind === "local_hf" && (_jsxs(_Fragment, { children: [_jsx(Field, { label: "device", children: _jsx(TextInput, { value: data.device, onChange: (v) => onPatch({ device: v }), placeholder: "cuda / cpu / cuda:0" }) }), _jsx(Field, { label: "max_new_tokens (default)", children: _jsx(NumberInput, { value: data.maxNewTokens, min: 1, onChange: (v) => onPatch({ maxNewTokens: v }) }) })] })), data.modelKind === "local_vllm" && (_jsxs(_Fragment, { children: [_jsx(Field, { label: "served_model_name (optional)", children: _jsx(TextInput, { value: data.servedModelName, onChange: (v) => onPatch({ servedModelName: v }), placeholder: "(defaults to basename of model)" }) }), _jsx(Field, { label: "tensor_parallel_size", children: _jsx(NumberInput, { value: data.tensorParallelSize, min: 1, onChange: (v) => onPatch({ tensorParallelSize: v }) }) }), _jsx(Field, { label: "gpu_memory_utilization", children: _jsx(NumberInput, { value: data.gpuMemoryUtilization, min: 0, step: 0.05, onChange: (v) => onPatch({ gpuMemoryUtilization: v }) }) }), _jsx(Field, { label: "max_model_len (0 = unset)", children: _jsx(NumberInput, { value: data.maxModelLen, min: 0, onChange: (v) => onPatch({ maxModelLen: v }) }) }), _jsx(Field, { label: "startup_timeout (s)", children: _jsx(NumberInput, { value: data.startupTimeout, min: 1, onChange: (v) => onPatch({ startupTimeout: v }) }) }), _jsx(Field, { label: "log_path (optional)", children: _jsx(TextInput, { value: data.logPath, onChange: (v) => onPatch({ logPath: v }), placeholder: "vllm.log" }) }), _jsx(Field, { label: "extra_args (space-separated)", children: _jsx(TextInput, { value: data.extraArgs, onChange: (v) => onPatch({ extraArgs: v }), placeholder: "--enable-prefix-caching" }) })] }))] }));
}
