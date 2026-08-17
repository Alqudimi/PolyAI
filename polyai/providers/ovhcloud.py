"""
OVHcloud AI Endpoints provider adapter.

Endpoint:   https://oai.endpoints.kepler.ai.cloud.ovh.net/v1
Protocol:   OpenAI-compatible REST + SSE streaming
Auth:       Bearer token (empty string = anonymous free tier)
Free tier:  2 requests/min per IP per model
Paid tier:  400 requests/min per project per model

Supported features:
- Chat completions (all OpenAI parameters)
- SSE streaming
- Function / tool calling
- Structured output (JSON mode)
- Vision (multimodal models, e.g. Qwen3-VL)
- Embeddings (BGE family + others)
- Reranking
- Image generation (Stable Diffusion variants)
- Audio analysis
- Model discovery via /v1/models

See: https://endpoints.ai.cloud.ovh.net/catalog
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from polyai.auth.credentials import BearerCredentials, NoAuthCredentials
from polyai.config import ClientConfig
from polyai.http.async_transport import AsyncTransport
from polyai.http.retry import RetryPolicy
from polyai.http.transport import SyncTransport
from polyai.providers.base import BaseProvider, ProviderCapabilities
from polyai.types import (
    ChatChunk,
    ChatResponse,
    EmbeddingResponse,
    ImageResponse,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"

MODELS = {
    "llm": [
        "meta-llama-3_3-70b-instruct",
        "meta-llama-3_1-70b-instruct",
        "llama-3.1-8b-instruct",
        "mixtral-8x7b-instruct-v0.1",
        "mistral-nemo-instruct-2407",
        "mistral-small-3.2-24b-instruct-2506",
        "deepseek-r1-distill-llama-70b",
        "deepseek-r1",
        "qwen2.5-72b-instruct",
        "qwen3-14b",
        "qwen3-32b",
        "qwen3-30b-a3b",
        "qwen3-235b-a22b",
        "gpt-oss-120b",
        "codestral-mamba-7b-v0.1",
        "codestral-22b-v0.1",
    ],
    "vision": [
        "Qwen/Qwen3-VL-8B-Instruct",
        "llama-3.2-11b-vision-instruct",
        "llama-3.2-90b-vision-instruct",
    ],
    "embedding": [
        "bge-m3",
        "bge-large-en-v1.5",
        "multilingual-e5-large-instruct",
        "nomic-embed-text-v1.5",
    ],
    "reranker": [
        "bge-reranker-v2-m3",
        "bge-reranker-large",
    ],
    "image": [
        "stable-diffusion-xl-base-1.0",
        "stable-diffusion-3-medium",
        "flux-1-dev",
        "flux-1-schnell",
    ],
    "audio": [
        "whisper-large-v3-turbo",
    ],
}


class OVHcloudCapabilities(ProviderCapabilities):
    chat = True
    streaming = True
    vision = True
    function_calling = True
    structured_output = True
    embeddings = True
    reranking = True
    image_generation = True
    tts = False
    stt = True
    models_endpoint = True
    batch = False


class OVHcloudProvider(BaseProvider):
    """OVHcloud AI Endpoints provider adapter.

    Uses an OpenAI-compatible API. Requires either an empty string
    (anonymous, rate-limited) or a valid OVHcloud API key.
    """

    name = "ovhcloud"
    capabilities = OVHcloudCapabilities()

    def __init__(self, config: ClientConfig) -> None:
        super().__init__(config)
        api_key = config.get_api_key("ovhcloud")
        self._credentials = BearerCredentials(api_key) if api_key else NoAuthCredentials()

        retry_policy = RetryPolicy(max_retries=config.get_max_retries("ovhcloud"))
        base_url = config.provider_config("ovhcloud").base_url or _BASE_URL

        auth_headers: Dict[str, str] = {}
        self._credentials.apply(auth_headers)

        middleware = getattr(config, "middleware", None)
        self._transport = SyncTransport(
            base_url=base_url,
            headers=auth_headers,
            timeout=config.get_timeout("ovhcloud"),
            retry_policy=retry_policy,
            proxy=config.proxy,
            verify_ssl=config.verify_ssl,
            middleware=middleware,
        )
        self._async_transport = AsyncTransport(
            base_url=base_url,
            headers=auth_headers,
            timeout=config.get_timeout("ovhcloud"),
            retry_policy=retry_policy,
            proxy=config.proxy,
            verify_ssl=config.verify_ssl,
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
        body = self._build_chat_body(
            model, messages, temperature=temperature, max_tokens=max_tokens,
            top_p=top_p, stream=False, tools=tools, tool_choice=tool_choice,
            response_format=response_format, system=system, extra=extra,
        )
        data = self._transport.request("POST", "/chat/completions", json_body=body, timeout=timeout, provider=self.name)
        return ChatResponse.from_openai_dict(data, self.name)

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
        body = self._build_chat_body(
            model, messages, temperature=temperature, max_tokens=max_tokens,
            top_p=top_p, stream=True, tools=tools, tool_choice=tool_choice,
            system=system, extra=extra,
        )
        for raw in self._transport.stream("POST", "/chat/completions", json_body=body, timeout=timeout, provider=self.name):
            try:
                data = json.loads(raw)
                chunk = ChatChunk.from_openai_dict(data, self.name)
                if chunk.delta or chunk.finish_reason:
                    yield chunk
            except json.JSONDecodeError:
                logger.debug("Could not parse SSE chunk: %r", raw)

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
        body = self._build_chat_body(
            model, messages, temperature=temperature, max_tokens=max_tokens,
            top_p=top_p, stream=False, tools=tools, tool_choice=tool_choice,
            response_format=response_format, system=system, extra=extra,
        )
        data = await self._async_transport.request("POST", "/chat/completions", json_body=body, timeout=timeout, provider=self.name)
        return ChatResponse.from_openai_dict(data, self.name)

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
        body = self._build_chat_body(
            model, messages, temperature=temperature, max_tokens=max_tokens,
            top_p=top_p, stream=True, tools=tools, tool_choice=tool_choice,
            system=system, extra=extra,
        )
        async for raw in self._async_transport.stream("POST", "/chat/completions", json_body=body, timeout=timeout, provider=self.name):
            try:
                data = json.loads(raw)
                chunk = ChatChunk.from_openai_dict(data, self.name)
                if chunk.delta or chunk.finish_reason:
                    yield chunk
            except json.JSONDecodeError:
                logger.debug("Could not parse async SSE chunk: %r", raw)

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def embed(
        self,
        model: str,
        input: List[str],
        *,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> EmbeddingResponse:
        body: Dict[str, Any] = {"model": model, "input": input}
        if extra:
            body.update(extra)
        data = self._transport.request("POST", "/embeddings", json_body=body, timeout=timeout, provider=self.name)
        return EmbeddingResponse.from_openai_dict(data, self.name)

    async def async_embed(
        self,
        model: str,
        input: List[str],
        *,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> EmbeddingResponse:
        body: Dict[str, Any] = {"model": model, "input": input}
        if extra:
            body.update(extra)
        data = await self._async_transport.request("POST", "/embeddings", json_body=body, timeout=timeout, provider=self.name)
        return EmbeddingResponse.from_openai_dict(data, self.name)

    # ------------------------------------------------------------------
    # Image generation
    # ------------------------------------------------------------------

    def generate_image(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        n: int = 1,
        size: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        response_format: Optional[str] = "url",
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ImageResponse:
        body: Dict[str, Any] = {
            "prompt": prompt,
            "model": model or "stable-diffusion-xl-base-1.0",
            "n": n,
            "response_format": response_format or "url",
        }
        if size:
            body["size"] = size
        if extra:
            body.update(extra)
        data = self._transport.request("POST", "/images/generations", json_body=body, timeout=timeout, provider=self.name)
        return ImageResponse.from_openai_dict(data, self.name)

    async def async_generate_image(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        n: int = 1,
        size: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        response_format: Optional[str] = "url",
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ImageResponse:
        body: Dict[str, Any] = {
            "prompt": prompt,
            "model": model or "stable-diffusion-xl-base-1.0",
            "n": n,
            "response_format": response_format or "url",
        }
        if size:
            body["size"] = size
        if extra:
            body.update(extra)
        data = await self._async_transport.request("POST", "/images/generations", json_body=body, timeout=timeout, provider=self.name)
        return ImageResponse.from_openai_dict(data, self.name)

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------

    def list_models(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        data = self._transport.request("GET", "/models", timeout=timeout, provider=self.name)
        return data.get("data", [])

    async def async_list_models(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        data = await self._async_transport.request("GET", "/models", timeout=timeout, provider=self.name)
        return data.get("data", [])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_chat_body(
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: Optional[float],
        max_tokens: Optional[int],
        top_p: Optional[float],
        stream: bool,
        tools: Optional[List[Dict[str, Any]]],
        tool_choice: Optional[Any],
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if system:
            messages = [{"role": "system", "content": system}, *messages]

        body: Dict[str, Any] = {"model": model, "messages": messages, "stream": stream}

        if temperature is not None:
            body["temperature"] = temperature
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if top_p is not None:
            body["top_p"] = top_p
        if tools:
            body["tools"] = tools
        if tool_choice is not None:
            body["tool_choice"] = tool_choice
        if response_format:
            body["response_format"] = response_format
        if extra:
            body.update(extra)

        return body
