import { RawDataSourceNode } from "./RawDataSourceNode";
import { DataOutputNode } from "./DataOutputNode";
import { ProcessorNode } from "./ProcessorNode";
import { JudgeNode } from "./JudgeNode";
import { JoinByIdNode } from "./JoinByIdNode";
import { VoteNode } from "./VoteNode";
import { ModelSpecNode } from "./ModelSpecNode";
export const nodeTypes = {
    RawDataSource: RawDataSourceNode,
    DataOutput: DataOutputNode,
    Processor: ProcessorNode,
    Judge: JudgeNode,
    JoinById: JoinByIdNode,
    Vote: VoteNode,
    ModelSpec: ModelSpecNode,
};
export const nodeKinds = [
    "RawDataSource",
    "DataOutput",
    "Processor",
    "Judge",
    "JoinById",
    "Vote",
    "ModelSpec",
];
export const nodeAccent = {
    RawDataSource: "bg-emerald-600",
    DataOutput: "bg-rose-600",
    Processor: "bg-sky-600",
    Judge: "bg-amber-600",
    JoinById: "bg-teal-600",
    Vote: "bg-violet-600",
    ModelSpec: "bg-fuchsia-600",
};
