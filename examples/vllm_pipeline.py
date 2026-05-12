"""End-to-end demo: rewrite text with a locally-served vLLM model.

This is the minimal "linear" pipeline:

    source -> rewrite (LLMCall backed by local vLLM) -> target

Pipeline.run() spawns `vllm serve` as a subprocess before the executor
starts, opens the OpenAI-compatible HTTP client, streams batches through,
and tears the subprocess back down on exit — even if the run fails.

Requires:
    pip install cargodash[local-vllm]
    # plus a GPU and either an HF repo id or a local model directory.

Override the default small model via env vars, e.g. to point at the
397B-A17B model on shared storage:

    CARGODASH_VLLM_MODEL=/share/models/Qwen3.5-397B-A17B \\
    CARGODASH_VLLM_TP=8 \\
    python examples/vllm_pipeline.py
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

# Make the example runnable without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cargodash import (
    Schema, RawDataSource, DataOutput,
    Processor, LLMCall, LocalVLLMChatClient,
    Pipeline,
)

HERE = Path(__file__).resolve().parent
IN_PATH = HERE / "_demo_in.jsonl"
OUT_PATH = HERE / "_vllm_demo_out.jsonl"

MODEL = os.environ.get("CARGODASH_VLLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
TP = int(os.environ.get("CARGODASH_VLLM_TP", "1"))


def main() -> None:
    schema = Schema.of(id=int, text=str, quality=float)

    # The model is declared once and referenced by ``LLMCall(client=...)``.
    # If multiple LLMCall / Vote nodes referenced the same object, the
    # framework would still open it exactly once for the whole run.
    qwen = LocalVLLMChatClient(
        MODEL,
        tensor_parallel_size=TP,
        gpu_memory_utilization=0.85,
        dtype="bfloat16",
        log_path=str(HERE / "_vllm.log"),
    )

    source = RawDataSource(IN_PATH, schema=schema, batch_size=4)
    target = DataOutput(OUT_PATH, schema=schema)

    rewrite = Processor(
        LLMCall(
            prompt="Rewrite this sentence to make it more vivid, in one sentence: {text}",
            output_field="text",
            client=qwen,
            max_tokens=128,
        ),
        input_schema=schema,
        output_schema=schema,
        # 4 concurrent HTTP requests per batch; vLLM's continuous batching
        # on the server side does the rest.
        intra_batch_workers=4,
    )

    source >> rewrite >> target

    Pipeline(source).run()

    print(f"\noutput written to {OUT_PATH}:")
    with OUT_PATH.open(encoding="utf-8") as f:
        for line in f:
            print("  " + line.rstrip())


if __name__ == "__main__":
    main()
