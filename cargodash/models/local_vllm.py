"""LocalVLLMChatClient: launches a `vllm serve` subprocess in ``open()``
and talks to it over the OpenAI-compatible HTTP API.

Why subprocess (not in-process ``vllm.LLM``):
- ``vllm serve`` is vLLM's recommended deployment path; it uses
  ``AsyncLLMEngine`` internally, so concurrent client requests get
  proper continuous batching for free. The in-process ``LLM`` API is an
  offline batch tool — concurrent ``generate([single])`` calls from
  threads end up locked.
- Re-uses the existing ``OpenAICompatChatClient`` plumbing on the client
  side; the chat path is dead simple.
- The trade-off is process-lifecycle management (port, readiness probe,
  shutdown), which we own carefully here.

GPU OOM, ``vllm`` not installed, port-in-use, or readiness timeout all
surface from ``open()`` so ``Pipeline.run()`` fails *before* the
executor starts.
"""
from __future__ import annotations
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Optional, Sequence

from .client import ChatClient, Messages


class LocalVLLMChatClient(ChatClient):
    def __init__(
        self,
        model: str,
        *,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        served_model_name: Optional[str] = None,
        dtype: Optional[str] = None,
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.9,
        max_model_len: Optional[int] = None,
        trust_remote_code: bool = False,
        download_dir: Optional[str] = None,
        extra_args: Optional[Sequence[str]] = None,
        startup_timeout: float = 600.0,
        log_path: Optional[str] = None,
    ):
        """``model`` is either a local directory or a HF repo id; vLLM
        resolves both. ``port=None`` picks a free port at ``open()`` time.

        ``extra_args`` is passed through to ``vllm serve`` unmodified —
        the escape hatch for flags this wrapper doesn't surface.

        ``log_path``: if set, the vllm subprocess stdout+stderr is teed
        to this file; otherwise it inherits the parent's streams so the
        user can see startup errors directly.
        """
        self.model = model
        self.host = host
        self._configured_port = port
        self.port: Optional[int] = port
        self.served_model_name = served_model_name or _basename_id(model)
        self.dtype = dtype
        self.tensor_parallel_size = int(tensor_parallel_size)
        self.gpu_memory_utilization = float(gpu_memory_utilization)
        self.max_model_len = max_model_len
        self.trust_remote_code = bool(trust_remote_code)
        self.download_dir = download_dir
        self.extra_args = list(extra_args or ())
        self.startup_timeout = float(startup_timeout)
        self.log_path = log_path

        self._proc: Optional[subprocess.Popen] = None
        self._log_fh = None
        self._client = None  # type: ignore[var-annotated]  # openai.OpenAI

    # -- lifecycle -----------------------------------------------------------

    def open(self) -> None:
        if self._proc is not None:
            return  # idempotent

        if self._configured_port is None:
            self.port = _find_free_port(self.host)
        else:
            self.port = self._configured_port

        cmd = [
            sys.executable, "-m", "vllm.entrypoints.openai.api_server",
            "--model", self.model,
            "--host", self.host,
            "--port", str(self.port),
            "--served-model-name", self.served_model_name,
            "--tensor-parallel-size", str(self.tensor_parallel_size),
            "--gpu-memory-utilization", str(self.gpu_memory_utilization),
        ]
        if self.dtype:
            cmd += ["--dtype", self.dtype]
        if self.max_model_len:
            cmd += ["--max-model-len", str(self.max_model_len)]
        if self.trust_remote_code:
            cmd += ["--trust-remote-code"]
        if self.download_dir:
            cmd += ["--download-dir", self.download_dir]
        cmd += self.extra_args

        if self.log_path:
            self._log_fh = open(self.log_path, "ab", buffering=0)
            stdout = self._log_fh
            stderr = subprocess.STDOUT
        else:
            stdout = None
            stderr = None

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=stdout,
                stderr=stderr,
                # New process group so a SIGINT to the parent doesn't kill
                # vllm before we get a chance to drain it.
                start_new_session=True,
            )
        except FileNotFoundError as e:
            self._close_log()
            raise RuntimeError(
                f"failed to spawn vllm: {e}. Install with "
                "`pip install cargodash[local-vllm]` (or `pip install vllm`)."
            ) from e

        try:
            self._wait_ready()
        except BaseException:
            self.close()
            raise

        try:
            from openai import OpenAI
        except ImportError as e:
            self.close()
            raise ImportError(
                "LocalVLLMChatClient requires the `openai` package on the "
                "client side. Install it with `pip install openai`."
            ) from e
        self._client = OpenAI(
            api_key="EMPTY",
            base_url=f"http://{self.host}:{self.port}/v1",
        )

    def close(self) -> None:
        proc = self._proc
        self._proc = None
        if proc is not None and proc.poll() is None:
            # Polite then forceful. vLLM cleans up GPU on SIGTERM.
            try:
                proc.terminate()
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
        self._close_log()
        self._client = None

    def _close_log(self) -> None:
        if self._log_fh is not None:
            try:
                self._log_fh.close()
            except OSError:
                pass
            self._log_fh = None

    # -- readiness probe -----------------------------------------------------

    def _wait_ready(self) -> None:
        assert self._proc is not None
        url = f"http://{self.host}:{self.port}/v1/models"
        deadline = time.time() + self.startup_timeout
        while time.time() < deadline:
            ret = self._proc.poll()
            if ret is not None:
                hint = f" (check log at {self.log_path})" if self.log_path else ""
                raise RuntimeError(
                    f"vllm serve for model={self.model!r} exited early "
                    f"with code {ret}{hint}"
                )
            try:
                with urllib.request.urlopen(url, timeout=3) as resp:
                    if 200 <= resp.status < 300:
                        return
            except (urllib.error.URLError, ConnectionResetError, OSError):
                pass
            time.sleep(2.0)
        raise TimeoutError(
            f"vllm serve for model={self.model!r} not ready within "
            f"{self.startup_timeout:.0f}s on {self.host}:{self.port}"
        )

    # -- chat ----------------------------------------------------------------

    def chat(self, messages: Messages, **gen_kwargs: Any) -> str:
        if self._client is None:
            raise RuntimeError(
                "LocalVLLMChatClient.chat() called before open(); did "
                "Pipeline.run() skip lifecycle?"
            )
        resp = self._client.chat.completions.create(
            model=self.served_model_name,
            messages=list(messages),
            **gen_kwargs,
        )
        return resp.choices[0].message.content or ""


def _find_free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def _basename_id(model: str) -> str:
    """For a HF repo id ``org/name`` return ``name``; for a local path
    return the directory basename. Used as the default ``--served-model-name``
    so callers' ``model=`` field in the chat request stays short."""
    if os.sep in model or "/" in model:
        return os.path.basename(model.rstrip("/" + os.sep)) or model
    return model
