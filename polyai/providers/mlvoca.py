"""
mlvoca provider adapter.

Base URL:   https://mlvoca.com
Endpoint:   POST /api/generate
Protocol:   Ollama-compatible API
Auth:       None required
Rate limit: None (hardware limited)
License:    Non-commercial use only

Available models:
  - tinyllama        — TinyLlama 1.1B, lightweight and fast
  - deepseek-r1:1.5b — DeepSeek R1 1.5B, reasoning model with <think> tokens

Request format:
  { "model": "tinyllama", "prompt": "Hello", "stream": false }

Response (stream=false):
  { "response": "...", "done": true, "model": "...", "context": [...], ... }

Response (stream=true):
  Line-delimited JSON objects: { "response": "token", "done": false }
  Final: { "response": "", "done": true, "total_duration": ..., ... }

Notes:
- The API wraps Ollama — it does NOT support OpenAI /chat/completions format.
- There is no multi-turn native support; callers must concatenate history into
  the prompt themselves.  The SDK does this transparently.
- The <think>...</think> tokens in deepseek-r1:1.5b responses are preserved
  in the text output.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from polyai.auth.credentials import NoAuthCredentials
from polyai.config import ClientConfig
from polyai.http.async_transport import AsyncTransport
from polyai.http.retry import RetryPolicy
from polyai.http.transport import SyncTransport
from polyai.providers.base import BaseProvider, ProviderCapabilities
from polyai.types import ChatChunk, ChatResponse, Usage

logger = logging.getLogger(__name__)

_BASE_URL = "https://mlvoca.com"
AVAILABLE_MODELS = ["tinyllama", "deepseek-r1:1.5b"]


def _messages_to_prompt(messages: List[Dict[str, Any]]) -> str:
    """Convert an OpenAI-style messages list to a single prompt string."""
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"
            )
        if role == "system":
            parts.append(f"[System]: {content}")
        elif role == "user":
            parts.append(f"[User]: {content}")
        elif role == "assistant":
            parts.append(f"[Assistant]: {content}")
        elif role == "tool":
            parts.append(f"[Tool]: {content}")
    parts.append("[Assistant]:")
    return "\n".join(parts)


class MlvocaCapabilities(ProviderCapabilities):
    chat = True
    streaming = True
    vision = False
    function_calling = False
    structured_output = False
    embeddings = False
    image_generation = False
    tts = False
    stt = False
    models_endpoint = False
    batch = False


class MlvocaProvider(BaseProvider):
    """mlvoca Free LLM API provider adapter (Ollama-compatible).

    Non-commercial use only. Wraps the /api/generate Ollama endpoint.
    """

    name = "mlvoca"
    capabilities = MlvocaCapabilities()

    def __init__(self, config: ClientConfig) -> None:
        super().__init__(config)
        self._credentials = NoAuthCredentials()

        pc = config.provider_config("mlvoca")
        base_url = pc.base_url or _BASE_URL

        retry_policy = RetryPolicy(
            max_retries=config.get_max_retries("mlvoca"),
            retry_on_status=(429, 500, 502, 503, 504),
        )

        self._transport = SyncTransport(
            base_url=base_url,
            timeout=config.get_timeout("mlvoca"),
            retry_policy=retry_policy,
        )
        self._async_transport = AsyncTransport(
            base_url=base_url,
            timeout=config.get_timeout("mlvoca"),
            retry_policy=retry_policy,
        )

    # ------------------------------------------------------------------
    # Sync chat
    # ------------------------------------------------------------------

    def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        if system:
            messages = [{"role": "system", "content": system}, *messages]

        prompt = _messages_to_prompt(messages)
        options: Dict[str, Any] = {}
        if temperature is not None:
            options["temperature"] = temperature
        if top_p is not None:
            options["top_p"] = top_p
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        body: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        if options:
            body["options"] = options
        if extra:
            body.update(extra)

        data = self._transport.request("POST", "/api/generate", json_body=body, timeout=timeout, provider=self.name)
        return self._parse_response(data, model)

    def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Generator[ChatChunk, None, None]:
        if system:
            messages = [{"role": "system", "content": system}, *messages]

        prompt = _messages_to_prompt(messages)
        options: Dict[str, Any] = {}
        if temperature is not None:
            options["temperature"] = temperature
        if top_p is not None:
            options["top_p"] = top_p
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        body: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": True}
        if options:
            body["options"] = options
        if extra:
            body.update(extra)

        for raw in self._transport.stream("POST", "/api/generate", json_body=body, timeout=timeout, provider=self.name):
            try:
                data = json.loads(raw)
                token = data.get("response", "")
                done = data.get("done", False)
                yield ChatChunk(
                    delta=token,
                    model=data.get("model", model),
                    provider=self.name,
                    finish_reason="stop" if done else None,
                    raw=data,
                )
                if done:
                    return
            except json.JSONDecodeError:
                logger.debug("mlvoca SSE parse error: %r", raw)

    # ------------------------------------------------------------------
    # Async chat
    # ------------------------------------------------------------------

    async def async_chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        if system:
            messages = [{"role": "system", "content": system}, *messages]

        prompt = _messages_to_prompt(messages)
        options: Dict[str, Any] = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        body: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        if options:
            body["options"] = options
        if extra:
            body.update(extra)

        data = await self._async_transport.request("POST", "/api/generate", json_body=body, timeout=timeout, provider=self.name)
        return self._parse_response(data, model)

    async def async_chat_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[ChatChunk, None]:
        if system:
            messages = [{"role": "system", "content": system}, *messages]

        prompt = _messages_to_prompt(messages)
        options: Dict[str, Any] = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        body: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": True}
        if options:
            body["options"] = options
        if extra:
            body.update(extra)

        async for raw in self._async_transport.stream("POST", "/api/generate", json_body=body, timeout=timeout, provider=self.name):
            try:
                data = json.loads(raw)
                token = data.get("response", "")
                done = data.get("done", False)
                yield ChatChunk(
                    delta=token,
                    model=data.get("model", model),
                    provider=self.name,
                    finish_reason="stop" if done else None,
                    raw=data,
                )
                if done:
                    return
            except json.JSONDecodeError:
                logger.debug("mlvoca async SSE parse error: %r", raw)

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------

    def list_models(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        return [{"id": m, "object": "model"} for m in AVAILABLE_MODELS]

    async def async_list_models(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        return [{"id": m, "object": "model"} for m in AVAILABLE_MODELS]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _parse_response(self, data: Dict[str, Any], model: str) -> ChatResponse:
        text = data.get("response", "")
        done = data.get("done", True)
        usage = Usage(
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
        )
        return ChatResponse(
            text=text,
            model=data.get("model", model),
            provider=self.name,
            finish_reason="stop" if done else "length",
            usage=usage,
            raw=data,
        )
