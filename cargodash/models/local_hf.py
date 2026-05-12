"""LocalHFChatClient: load a Hugging Face causal-LM in-process and serve
``chat()`` calls directly via ``model.generate``.

Positioning: this is the **small-model / debugging** path. There is no
continuous batching; concurrent ``chat()`` calls are serialized through
a single lock because the underlying ``model.generate`` mutates shared
state on the GPU. For real throughput on bigger models, use
``LocalVLLMChatClient`` (or a remote vLLM/SGLang endpoint via
``OpenAICompatChatClient``).

The model accepts either a HF repo id or a local directory path —
``transformers`` resolves both, downloading to ``cache_dir`` on demand.
"""
from __future__ import annotations
import threading
from typing import Any, Optional

from .client import ChatClient, Messages


class LocalHFChatClient(ChatClient):
    def __init__(
        self,
        model: str,
        *,
        device: str = "cuda",
        dtype: Optional[str] = None,
        cache_dir: Optional[str] = None,
        trust_remote_code: bool = False,
        max_new_tokens: int = 512,
    ):
        """``dtype``: e.g. ``"float16"`` / ``"bfloat16"`` / ``"float32"``;
        ``None`` lets transformers pick (typically float32, which is rarely
        what you want for a 7B+ model — set it explicitly).
        """
        self.model_id = model
        self.device = device
        self.dtype = dtype
        self.cache_dir = cache_dir
        self.trust_remote_code = bool(trust_remote_code)
        self.max_new_tokens = int(max_new_tokens)

        self._tokenizer = None  # type: ignore[var-annotated]
        self._model = None  # type: ignore[var-annotated]
        # model.generate isn't safe to call concurrently on the same module
        # — the GPU state and any caches inside are shared. We serialize.
        self._lock = threading.Lock()

    # -- lifecycle -----------------------------------------------------------

    def open(self) -> None:
        if self._model is not None:
            return  # idempotent

        try:
            import torch  # noqa: F401  (used below)
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "LocalHFChatClient requires `transformers` and `torch`. "
                "Install with `pip install cargodash[local-hf]`."
            ) from e

        load_kwargs: dict[str, Any] = {"trust_remote_code": self.trust_remote_code}
        if self.cache_dir:
            load_kwargs["cache_dir"] = self.cache_dir
        if self.dtype:
            import torch
            torch_dtype = getattr(torch, self.dtype, None)
            if torch_dtype is None:
                raise ValueError(
                    f"LocalHFChatClient: unknown dtype {self.dtype!r}; expected "
                    "one of 'float16' / 'bfloat16' / 'float32'"
                )
            load_kwargs["torch_dtype"] = torch_dtype

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id, **load_kwargs)
        model = AutoModelForCausalLM.from_pretrained(self.model_id, **load_kwargs)
        model.to(self.device)
        model.eval()
        self._model = model

    def close(self) -> None:
        self._model = None
        self._tokenizer = None
        try:
            import gc
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    # -- chat ----------------------------------------------------------------

    def chat(self, messages: Messages, **gen_kwargs: Any) -> str:
        if self._model is None or self._tokenizer is None:
            raise RuntimeError(
                "LocalHFChatClient.chat() called before open(); did "
                "Pipeline.run() skip lifecycle?"
            )

        import torch

        gen_kwargs.setdefault("max_new_tokens", self.max_new_tokens)
        gen_kwargs.setdefault("do_sample", False)

        with self._lock:
            prompt = self._tokenizer.apply_chat_template(
                list(messages),
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self._model.generate(**inputs, **gen_kwargs)
            new_tokens = outputs[0, inputs["input_ids"].shape[1]:]
            return self._tokenizer.decode(new_tokens, skip_special_tokens=True)
