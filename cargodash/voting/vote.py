"""Vote: majority/threshold across multiple predicate models.

A `Vote` instance is itself a callable, so it can be used directly as
the predicate of a Judge. Each "model" is just a callable that takes a
sample and returns a truthy/falsy verdict — Phase 1 stays
provider-agnostic on purpose.
"""
from __future__ import annotations
from typing import Callable, Optional, Sequence


PredictModel = Callable[[dict], bool]


class Vote:
    def __init__(
        self,
        model_list: Sequence[PredictModel],
        true_num: int,
        prompt_list: Optional[Sequence[str]] = None,
    ):
        if not model_list:
            raise ValueError("Vote requires at least one model")
        if not (1 <= true_num <= len(model_list)):
            raise ValueError(
                f"true_num must be in [1, {len(model_list)}], got {true_num}"
            )
        self.models = list(model_list)
        self.true_num = true_num
        self.prompts = list(prompt_list) if prompt_list is not None else [None] * len(model_list)

    def __call__(self, sample: dict) -> bool:
        # Sequential calls. For real LLM models the parallelism should
        # come from the surrounding Judge's intra_batch_workers, which
        # parallelizes across samples within a batch.
        votes = 0
        for model, prompt in zip(self.models, self.prompts):
            if model(sample) if prompt is None else model(sample, prompt):
                votes += 1
                if votes >= self.true_num:
                    return True
        return False
