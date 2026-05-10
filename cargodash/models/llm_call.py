"""LLMCall: drop-in callable that turns a row into a single LLM call.

Designed to be the ``fn`` of a sample-mode ``Processor``. The minimum a
user has to provide is a model name + api key + a prompt template:

    augment = Processor(
        LLMCall(
            prompt="Rewrite this sentence: {text}",
            model="gpt-4.1-mini",
            api_key="sk-...",
            output_field="text",
        ),
        intra_batch_workers=8,
    )

Phase-1 scope: single-turn only — one row in, one row out (with an
extra/overwritten field carrying the LLM reply). Multi-turn dialogs and
chain-of-thought-style multi-call patterns are out of scope here; build
those as separate node types.
"""
from __future__ import annotations
from typing import Any, Optional

from .client import ChatClient, OpenAICompatChatClient


class LLMCall:
    def __init__(
        self,
        prompt: str,
        *,
        output_field: str = "llm_output",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        client: Optional[ChatClient] = None,
        **gen_kwargs: Any,
    ):
        """Either provide ``client`` (any ChatClient) **or** ``model`` (+
        optional ``api_key`` / ``base_url``); not both ways at once.

        Anything else passed via ``**gen_kwargs`` (``temperature``,
        ``max_tokens``, ``top_p``, ``response_format``, ...) is forwarded
        to ``client.chat`` on every call.
        """
        if client is None:
            if model is None:
                raise ValueError("LLMCall: must provide either `client` or `model`")
            client = OpenAICompatChatClient(
                model=model, api_key=api_key, base_url=base_url
            )
        elif model is not None or api_key is not None or base_url is not None:
            raise ValueError(
                "LLMCall: when `client` is given, `model`/`api_key`/`base_url` "
                "must not also be set (they belong to the client)"
            )

        self.client = client
        self.prompt_template = prompt
        self.system_prompt = system_prompt
        self.output_field = output_field
        self.gen_kwargs = gen_kwargs

    def __call__(self, row: dict) -> dict:
        try:
            user_content = self.prompt_template.format(**row)
        except KeyError as e:
            missing = e.args[0]
            raise KeyError(
                f"LLMCall prompt template references field '{missing}' "
                f"which is not in the row (available: {sorted(row)})"
            ) from None

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_content})

        reply = self.client.chat(messages, **self.gen_kwargs)
        return {**row, self.output_field: reply}
