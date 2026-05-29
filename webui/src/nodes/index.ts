import type { NodeTypes } from "reactflow";
import { RawDataSourceNode } from "./RawDataSourceNode";
import { DataOutputNode } from "./DataOutputNode";
import { ProcessorNode } from "./ProcessorNode";
import { JudgeNode } from "./JudgeNode";
import { JoinByIdNode } from "./JoinByIdNode";
import { VoteNode } from "./VoteNode";
import { ModelSpecNode } from "./ModelSpecNode";
import type { NodeKind } from "../types/graph";

export const nodeTypes: NodeTypes = {
  RawDataSource: RawDataSourceNode,
  DataOutput: DataOutputNode,
  Processor: ProcessorNode,
  Judge: JudgeNode,
  JoinById: JoinByIdNode,
  Vote: VoteNode,
  ModelSpec: ModelSpecNode,
};

export const nodeKinds: NodeKind[] = [
  "RawDataSource",
  "DataOutput",
  "Processor",
  "Judge",
  "JoinById",
  "Vote",
  "ModelSpec",
];

export const nodeAccent: Record<NodeKind, string> = {
  RawDataSource: "bg-emerald-600",
  DataOutput: "bg-rose-600",
  Processor: "bg-sky-600",
  Judge: "bg-amber-600",
  JoinById: "bg-teal-600",
  Vote: "bg-violet-600",
  ModelSpec: "bg-fuchsia-600",
};
