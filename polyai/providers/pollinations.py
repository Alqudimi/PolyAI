"""
Pollinations.AI provider adapter.

Primary URL:  https://gen.pollinations.ai/v1  (OpenAI-compatible)
Legacy image: https://image.pollinations.ai/prompt/{prompt}
Legacy text:  https://text.pollinations.ai

Auth:
  - No auth (anonymous, rate-limited)
  - sk_* secret key (backend usage, full account access)
  - pk_* publishable key (browser / mobile safe)

Free tier features (no key required):
  - Text generation (limited models)
  - Image generation (Flux, etc.)
  - Referrer attribution

Paid / key features:
  - All models (Claude, GPT-4, Mistral, DeepSeek, etc.)
  - Audio TTS
  - Embeddings
  - Higher rate limits
  - Private outputs (no-log)

Image models: flux, flux-realism, flux-anime, flux-3d, flux-pro, turbo,
              kontext, nanobanana, seedream, gptimage, gpt-image-2,
              wan-image, zimage, stable-diffusion-3, etc.

Text models: openai, openai-fast, openai-large, openai-audio,
             claude, claude-fast, claude-large, mistral, mistral-large,
             deepseek, deepseek-r1, llama, phi, gemma, qwen, etc.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from polyai.auth.credentials import BearerCredentials, NoAuthCredentials
from polyai.config import ClientConfig
from polyai.http.async_transport import AsyncTransport
from polyai.http.retry import RetryPolicy
from polyai.http.transport import SyncTransport
from polyai.providers.base import BaseProvider, ProviderCapabilities
from polyai.types import (
    AudioResponse,
    ChatChunk,
    ChatResponse,
    EmbeddingResponse,
    ImageData,
    ImageResponse,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://gen.pollinations.ai/v1"
_IMAGE_BASE = "https://image.pollinations.ai"
_GEN_IMAGE_BASE = "https://gen.pollinations.ai"

TEXT_MODELS = [
    "openai", "openai-fast", "openai-large", "openai-audio",
    "claude", "claude-fast", "claude-large",
    "mistral", "mistral-large",
    "deepseek", "deepseek-r1",
    "llama", "llama-fast",
    "phi", "gemma",
    "qwen", "qwen-coder",
    "grok",
    "command-r",
    "hormoz",
    "searchgpt",
    "rtist",
    "midijourney",
    "unity",
    "magi",
    "bidara",
]

IMAGE_MODELS = [
    "flux", "flux-realism", "flux-anime", "flux-3d", "flux-pro",
    "turbo", "kontext", "nanobanana", "nanobanana-2", "nanobanana-pro",
    "seedream", "seedream5", "seedream-pro",
    "gptimage", "gptimage-large", "gpt-image-2",
    "wan-image", "zimage",
    "stable-diffusion-3",
]


class PollinationsCapabilities(ProviderCapabilities):
    chat = True
    streaming = True
    vision = True
    function_calling = True
    structured_output = True
    embeddings = True
    image_generation = True
    image_editing = True
    tts = True
    stt = False
    models_endpoint = True
    batch = False


class PollinationsProvider(BaseProvider):
    """Pollinations.AI provider adapter.

    Works without any API key (anonymous), or with ``sk_*`` / ``pk_*`` keys
    for full model access and higher limits.
    """

    name = "pollinations"
    capabilities = PollinationsCapabilities()

    def __init__(self, config: ClientConfig) -> None:
        super().__init__(config)
        api_key = config.get_api_key("pollinations")
        self._credentials = BearerCredentials(api_key) if api_key else NoAuthCredentials()

        retry_policy = RetryPolicy(max_retries=config.get_max_retries("pollinations"))
        pc = config.provider_config("pollinations")
        base_url = pc.base_url or _BASE_URL

        auth_headers: Dict[str, str] = {}
        self._credentials.apply(auth_headers)

        middleware = getattr(config, "middleware", None)
        self._transport = SyncTransport(
            base_url=base_url,
            headers=auth_headers,
            timeout=config.get_timeout("pollinations"),
            retry_policy=retry_policy,
            middleware=middleware,
        )
        self._async_transport = AsyncTransport(
            base_url=base_url,
            headers=auth_headers,
            timeout=config.get_timeout("pollinations"),
            retry_policy=retry_policy,
            middleware=middleware,
        )
        # Separate transport for image API (different base)
        self._image_transport = SyncTransport(
            base_url=_GEN_IMAGE_BASE,
            headers=auth_headers,
            timeout=config.get_timeout("pollinations"),
            retry_policy=retry_policy,
            middleware=middleware,
        )
        self._async_image_transport = AsyncTransport(
            base_url=_GEN_IMAGE_BASE,
            headers=auth_headers,
            timeout=config.get_timeout("pollinations"),
            retry_policy=retry_policy,
            middleware=middleware,
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
                logger.debug("Pollinations SSE parse error: %r", raw)

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
                logger.debug("Pollinations async SSE parse error: %r", raw)

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
        response_format: Optional[str] = None,
        seed: Optional[int] = None,
        enhance: bool = False,
        nologo: bool = False,
        private: bool = False,
        safe: bool = False,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ImageResponse:
        """Generate an image via the OpenAI-compatible endpoint.

        For a direct URL-based approach (no API key required), use
        ``generate_image_url()`` instead.
        """
        body: Dict[str, Any] = {
            "prompt": prompt,
            "model": model or "flux",
            "n": n,
        }
        if width:
            body["width"] = width
        if height:
            body["height"] = height
        if size:
            w, h = self._parse_size(size)
            body["width"] = w
            body["height"] = h
        if seed is not None:
            body["seed"] = seed
        if response_format:
            body["response_format"] = response_format
        if extra:
            body.update(extra)

        data = self._image_transport.request(
            "POST", "/v1/images/generations",
            json_body=body, timeout=timeout, provider=self.name,
        )
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
        response_format: Optional[str] = None,
        seed: Optional[int] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ImageResponse:
        body: Dict[str, Any] = {
            "prompt": prompt,
            "model": model or "flux",
            "n": n,
        }
        if width:
            body["width"] = width
        if height:
            body["height"] = height
        if size:
            w, h = self._parse_size(size)
            body["width"] = w
            body["height"] = h
        if seed is not None:
            body["seed"] = seed
        if response_format:
            body["response_format"] = response_format
        if extra:
            body.update(extra)

        data = await self._async_image_transport.request(
            "POST", "/v1/images/generations",
            json_body=body, timeout=timeout, provider=self.name,
        )
        return ImageResponse.from_openai_dict(data, self.name)

    def generate_image_url(
        self,
        prompt: str,
        *,
        model: str = "flux",
        width: int = 1024,
        height: int = 1024,
        seed: int = 0,
        enhance: bool = False,
        nologo: bool = False,
        private: bool = False,
        safe: bool = False,
    ) -> str:
        """Build a direct image URL (no HTTP request made).

        The image is generated when the URL is fetched (e.g., in a browser
        or with ``requests.get``).
        """
        encoded = urllib.parse.quote(prompt)
        params = f"width={width}&height={height}&seed={seed}&model={model}"
        if enhance:
            params += "&enhance=true"
        if nologo:
            params += "&nologo=true"
        if private:
            params += "&private=true"
        if safe:
            params += "&safe=true"
        return f"{_IMAGE_BASE}/prompt/{encoded}?{params}"

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
    # Text-to-speech
    # ------------------------------------------------------------------

    def text_to_speech(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> AudioResponse:
        body: Dict[str, Any] = {
            "model": model or "openai-audio",
            "input": text,
            "voice": voice or "alloy",
            "response_format": response_format,
            "speed": speed,
        }
        if extra:
            body.update(extra)
        content, content_type = self._transport.post_bytes(
            "/audio/speech", json_body=body, timeout=timeout, provider=self.name,
        )
        return AudioResponse(content=content, content_type=content_type, provider=self.name, model=body["model"])

    async def async_text_to_speech(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> AudioResponse:
        body: Dict[str, Any] = {
            "model": model or "openai-audio",
            "input": text,
            "voice": voice or "alloy",
            "response_format": response_format,
            "speed": speed,
        }
        if extra:
            body.update(extra)
        content, content_type = await self._async_transport.post_bytes(
            "/audio/speech", json_body=body, timeout=timeout, provider=self.name,
        )
        return AudioResponse(content=content, content_type=content_type, provider=self.name, model=body["model"])

    # ------------------------------------------------------------------
    # Models list
    # ------------------------------------------------------------------

    def list_models(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        try:
            data = self._image_transport.request("GET", "/v1/models", timeout=timeout, provider=self.name)
            return data.get("data", [])
        except Exception:
            return [{"id": m, "type": "text"} for m in TEXT_MODELS] + [{"id": m, "type": "image"} for m in IMAGE_MODELS]

    async def async_list_models(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        try:
            data = await self._async_image_transport.request("GET", "/v1/models", timeout=timeout, provider=self.name)
            return data.get("data", [])
        except Exception:
            return [{"id": m, "type": "text"} for m in TEXT_MODELS] + [{"id": m, "type": "image"} for m in IMAGE_MODELS]

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

    @staticmethod
    def _parse_size(size: str):
        parts = size.lower().replace("x", "×").split("×")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        return 1024, 1024
