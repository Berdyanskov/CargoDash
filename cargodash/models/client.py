"""Chat-style LLM client abstraction.

A ``ChatClient`` is a thin transport: take an OpenAI-style messages list,
return the assistant's reply text. Concrete implementations:

- ``OpenAICompatChatClient``: covers OpenAI itself plus any vendor that
  speaks the OpenAI-compatible chat-completions API (DeepSeek, Moonshot,
  Zhipu, vLLM, SGLang, Ollama, ...). Just point ``base_url`` at them.
- ``MockChatClient``: for examples and tests; no network.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Mapping, Optional


Messages = List[Mapping[str, str]]   # [{"role": "system"|"user"|"assistant", "content": str}, ...]


class ChatClient(ABC):
    """Single-turn or multi-turn chat transport.

    Concrete implementations must be **thread-safe**: the executor will
    call ``chat`` concurrently from multiple worker threads when a
    Processor sets ``intra_batch_workers > 1``.

    Lifecycle: ``Pipeline.run()`` calls ``open()`` on every client used
    by the graph before any executor thread starts, and ``close()`` after
    the executor finishes (in a ``finally``). Clients that allocate heavy
    resources (loading a model, spawning a vLLM subprocess) should do it
    in ``open()`` so a failure surfaces *before* the pipeline starts —
    not in the middle of a run. Defaults are no-ops; cheap network clients
    do not need to override.
    """

    def open(self) -> None:  # noqa: A003 - mirrors file-like API
        pass

    def close(self) -> None:
        pass

    @abstractmethod
    def chat(self, messages: Messages, **gen_kwargs: Any) -> str:
        ...


class OpenAICompatChatClient(ChatClient):
    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        # Lazy import so cargodash itself doesn't hard-depend on the openai SDK.
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "OpenAICompatChatClient requires the `openai` package. "
                "Install it with `pip install openai`."
            ) from e
        self.model = model
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

    def chat(self, messages: Messages, **gen_kwargs: Any) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=list(messages),
            **gen_kwargs,
        )
        return resp.choices[0].message.content or ""


class MockChatClient(ChatClient):
    """Returns canned responses. Useful for examples, unit tests, and
    cost-free dry runs of a pipeline graph."""

    def __init__(
        self,
        response_fn: Optional[Callable[[Messages], str]] = None,
        fixed_response: str = "[mock-response]",
    ):
        self.response_fn = response_fn
        self.fixed_response = fixed_response

    def chat(self, messages: Messages, **gen_kwargs: Any) -> str:
        if self.response_fn is not None:
            return self.response_fn(messages)
        return self.fixed_response
