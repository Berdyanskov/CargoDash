// Smoke test for the dry-run codegen option.
//
// Builds a minimal graph and asserts that:
//   - generatePython(project)            → ends with `Pipeline(src).run()`
//   - generatePython(project, {dryRunRows: 25}) → `Pipeline(src).run(dry_run_rows=25)`
//   - generatePython(project, {dryRunRows: 0})  → plain `.run()` (treated as off)
//
// Run from webui/:
//   npx tsx scripts/smoke_dry_run.ts

import { generatePython } from "../src/codegen/generate";
import type { GraphProject, SchemaField } from "../src/types/graph";

const schema: SchemaField[] = [{ name: "v", type: "int" }];

const project: GraphProject = {
  version: 1,
  nodes: [
    {
      id: "src",
      position: { x: 0, y: 0 },
      data: {
        kind: "RawDataSource",
        varName: "source",
        path: "in.jsonl",
        schema,
        batchSize: 4,
      },
    },
    {
      id: "tgt",
      position: { x: 400, y: 0 },
      data: {
        kind: "DataOutput",
        varName: "target",
        path: "out.jsonl",
        schema,
        preserveOrder: false,
      },
    },
  ],
  edges: [
    { id: "e1", source: "src", target: "tgt", sourceHandle: "default" },
  ],
};

function tail(s: string): string {
  return s.trimEnd().split("\n").slice(-2).join("\n");
}

const plain = generatePython(project);
const dry25 = generatePython(project, { dryRunRows: 25 });
const dryZero = generatePython(project, { dryRunRows: 0 });
const dryNull = generatePython(project, { dryRunRows: null });

console.log("[plain run]:");
console.log(tail(plain));
console.log("\n[dry-run rows=25]:");
console.log(tail(dry25));
console.log("\n[dry-run rows=0]:");
console.log(tail(dryZero));
console.log("\n[dry-run null]:");
console.log(tail(dryNull));

const fail = (msg: string) => {
  console.error(`\n[FAIL] ${msg}`);
  process.exit(1);
};

if (!plain.includes("Pipeline(source).run()"))
  fail("plain output should emit `Pipeline(source).run()`");
if (!dry25.includes("Pipeline(source).run(dry_run_rows=25)"))
  fail("dry-run rows=25 should emit `Pipeline(source).run(dry_run_rows=25)`");
if (!dryZero.includes("Pipeline(source).run()"))
  fail("dry-run rows=0 should be treated as off (plain `.run()`)");
if (!dryNull.includes("Pipeline(source).run()"))
  fail("dry-run rows=null should be treated as off (plain `.run()`)");

console.error("\n[OK] dry-run codegen behaves as expected");
