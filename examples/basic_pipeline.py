"""End-to-end demo:

  source --> clean (MapProcessor) --> judge_quality (Judge, sample-level)
                                          |
                                  on_true: judge_lang (Judge, batch-level)
                                          |
                              on_true: augment (MapProcessor) ----+
                              on_false: ------------------------> +--> target
                                          |
                                  on_false: log_drop (Processor)

Run from the repo root:
    python examples/basic_pipeline.py
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

# Make the example runnable without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cargodash import (
    Batch, Schema,
    RawDataSource, DataOutput, Processor, Judge, Vote,
    LLMCall, MockChatClient,
    Pipeline,
)

HERE = Path(__file__).resolve().parent
IN_PATH = HERE / "_demo_in.jsonl"
OUT_PATH = HERE / "_demo_out.jsonl"


# def make_demo_input() -> None:
#     samples = [
#         {"id": 1, "text": "你好，世界",            "quality": 0.9},
#         {"id": 2, "text": "low quality garbage",  "quality": 0.1},
#         {"id": 3, "text": "Hello world",          "quality": 0.8},
#         {"id": 4, "text": "也是中文示例",         "quality": 0.7},
#         {"id": 5, "text": "noisy noisy noisy",    "quality": 0.2},
#         {"id": 6, "text": "another english one",  "quality": 0.95},
#     ]
#     with IN_PATH.open("w", encoding="utf-8") as f:
#         for s in samples:
#             f.write(json.dumps(s, ensure_ascii=False) + "\n")


# --- user-defined per-row functions ----------------------------------------

def clean_row(row: dict) -> dict:
    return {**row, "text": row["text"].strip()}


def quality_model_a(sample: dict) -> bool:
    return sample["quality"] >= 0.5


def quality_model_b(sample: dict) -> bool:
    return sample["quality"] >= 0.6


def quality_model_c(sample: dict) -> bool:
    return len(sample["text"]) >= 5


def is_chinese_batch(batch: Batch) -> bool:
    # Batch-level predicate: vote within the batch.
    chinese = sum(any("一" <= ch <= "鿿" for ch in r["text"]) for r in batch.rows)
    return chinese * 2 >= len(batch)

# LLM-call node: built from the LLMCall helper. The demo defaults to a
# mock client so it runs anywhere; flip USE_REAL_OPENAI to hit gpt-4.1-mini.
USE_REAL_OPENAI = bool(os.environ.get("OPENAI_API_KEY"))


def make_augment_call() -> LLMCall:
    prompt = "Please add an argument after the following sentence: {text}"
    if USE_REAL_OPENAI:
        return LLMCall(
            prompt=prompt,
            output_field="text",
            model="gpt-4.1-mini",
            api_key=os.environ["OPENAI_API_KEY"],
            # Anything else (temperature, max_tokens, ...) is forwarded to chat().
            # base_url="https://api.deepseek.com/v1",   # for OpenAI-compat gateways
        )
    return LLMCall(
        prompt=prompt,
        output_field="text",
        client=MockChatClient(
            response_fn=lambda msgs: msgs[-1]["content"].split(": ", 1)[-1] + " [AUG]"
        ),
    )


def log_drop(row: dict):
    print(f"  [dropped] id={row['id']}  quality={row['quality']}")
    # Returning None drops the row (sample-mode N->0).


# --- build & run -----------------------------------------------------------

def main() -> None:
    # make_demo_input()

    schema = Schema.of(id=int, text=str, quality=float)

    source = RawDataSource(IN_PATH, schema=schema, batch_size=4)
    target = DataOutput(OUT_PATH, schema=schema)

    clean = Processor(clean_row, input_schema=schema, output_schema=schema)

    quality_vote = Vote(
        model_list=[quality_model_a, quality_model_b, quality_model_c],
        true_num=2,
    )
    judge_quality = Judge(quality_vote, granularity="sample",
                          input_schema=schema, intra_batch_workers=4)
    judge_lang = Judge(is_chinese_batch, granularity="batch", input_schema=schema)

    # Per-sample function + intra_batch_workers = the canonical LLM-call
    # processor: each row triggers one model call, batches fan out for throughput.
    augment = Processor(make_augment_call(),
                        input_schema=schema, output_schema=schema,
                        intra_batch_workers=4)
    drop_logger = Processor(log_drop, input_schema=schema, output_schema=schema)

    # Wire the DAG.
    source >> clean >> judge_quality
    judge_quality.on_true >> judge_lang
    judge_lang.on_true >> augment >> target
    judge_lang.on_false >> target
    judge_quality.on_false >> drop_logger

    Pipeline(source).run()

    print(f"\noutput written to {OUT_PATH}:")
    with OUT_PATH.open(encoding="utf-8") as f:
        for line in f:
            print("  " + line.rstrip())


if __name__ == "__main__":
    main()
