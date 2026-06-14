"""
DevToolbox API provider adapter.

Base URL:   https://devtoolbox-api.devtoolbox-api.workers.dev
Auth:       None (free tier) | X-API-Key: dtb_<key> (premium, unlimited)
Rate limit: 100,000 requests/day (free), unlimited (premium)
Platform:   Cloudflare Workers

AI Endpoints (all POST):
  /ai/generate        — General AI text generation
  /ai/summarize       — Text summarisation
  /ai/translate       — Language translation
  /ai/explain-code    — Code explanation
  /ai/generate-regex  — Regex generation from natural language

Developer Utility Endpoints (GET/POST, non-AI):
  /hash/{algorithm}/{input}   — Hash generation (md5, sha1, sha256, …)
  /uuid                       — UUID v4 generation
  /qr?data=&size=             — QR code generation (returns PNG)
  /ip                         — Client IP information
  /color/random               — Random colour
  /password?length=&symbols=  — Secure password generation
  /base64/encode / /decode    — Base64 encode/decode
  /lorem-ipsum?paragraphs=    — Lorem Ipsum generation

This adapter maps AI endpoints to the unified SDK chat interface and also
exposes provider-specific helper methods for the utility endpoints.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from polyai.auth.credentials import ApiKeyHeaderCredentials, NoAuthCredentials
from polyai.config import ClientConfig
from polyai.http.async_transport import AsyncTransport
from polyai.http.retry import RetryPolicy
from polyai.http.transport import SyncTransport
from polyai.providers.base import BaseProvider, ProviderCapabilities
from polyai.types import ChatChunk, ChatResponse, Usage

logger = logging.getLogger(__name__)

_BASE_URL = "https://devtoolbox-api.devtoolbox-api.workers.dev"


def _messages_to_prompt(messages: List[Dict[str, Any]]) -> str:
    """Flatten messages into a single prompt string for DevToolbox /ai/generate."""
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"
            )
        parts.append(content)
    return "\n".join(parts).strip()


class DevToolboxCapabilities(ProviderCapabilities):
    chat = True
    streaming = False
    vision = False
    function_calling = False
    structured_output = False
    embeddings = False
    image_generation = False
    tts = False
    stt = False
    models_endpoint = False
    batch = False


class DevToolboxProvider(BaseProvider):
    """DevToolbox API provider adapter.

    Exposes AI generation, summarisation, translation, code explanation,
    and regex generation through the unified SDK interface, plus provider-
    specific developer utility methods.
    """

    name = "devtoolbox"
    capabilities = DevToolboxCapabilities()

    def __init__(self, config: ClientConfig) -> None:
        super().__init__(config)
        api_key = config.get_api_key("devtoolbox")
        self._credentials = (
            ApiKeyHeaderCredentials(api_key, "X-API-Key") if api_key else NoAuthCredentials()
        )

        pc = config.provider_config("devtoolbox")
        base_url = pc.base_url or _BASE_URL

        retry_policy = RetryPolicy(max_retries=config.get_max_retries("devtoolbox"))

        extra_headers: Dict[str, str] = {}
        self._credentials.apply(extra_headers)

        self._transport = SyncTransport(
            base_url=base_url,
            headers=extra_headers,
            timeout=config.get_timeout("devtoolbox"),
            retry_policy=retry_policy,
        )
        self._async_transport = AsyncTransport(
            base_url=base_url,
            headers=extra_headers,
            timeout=config.get_timeout("devtoolbox"),
            retry_policy=retry_policy,
        )

    # ------------------------------------------------------------------
    # Sync chat — routes to /ai/generate
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
        body: Dict[str, Any] = {"prompt": prompt}
        if max_tokens:
            body["max_tokens"] = max_tokens
        if extra:
            body.update(extra)

        data = self._transport.request("POST", "/ai/generate", json_body=body, timeout=timeout, provider=self.name)
        return self._wrap_response(data, model)

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
        response = self.chat(
            model, messages, max_tokens=max_tokens, system=system, timeout=timeout, extra=extra,
        )
        yield ChatChunk(delta=response.text, model=response.model, provider=self.name, finish_reason="stop", raw=response.raw)

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
        body: Dict[str, Any] = {"prompt": prompt}
        if max_tokens:
            body["max_tokens"] = max_tokens
        if extra:
            body.update(extra)

        data = await self._async_transport.request("POST", "/ai/generate", json_body=body, timeout=timeout, provider=self.name)
        return self._wrap_response(data, model)

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
        response = await self.async_chat(
            model, messages, max_tokens=max_tokens, system=system, timeout=timeout, extra=extra,
        )
        yield ChatChunk(delta=response.text, model=response.model, provider=self.name, finish_reason="stop", raw=response.raw)

    # ------------------------------------------------------------------
    # Provider-specific AI helpers
    # ------------------------------------------------------------------

    def summarize(self, text: str, *, max_length: Optional[int] = None, timeout: Optional[float] = None) -> str:
        """Summarize a block of text using the DevToolbox AI.

        Args:
            text:       The text to summarize.
            max_length: Maximum summary length in characters.
            timeout:    Request timeout override.

        Returns:
            Summary string.
        """
        body: Dict[str, Any] = {"text": text}
        if max_length:
            body["max_length"] = max_length
        data = self._transport.request("POST", "/ai/summarize", json_body=body, timeout=timeout, provider=self.name)
        return data.get("summary", data.get("result", str(data)))

    async def async_summarize(self, text: str, *, max_length: Optional[int] = None, timeout: Optional[float] = None) -> str:
        body: Dict[str, Any] = {"text": text}
        if max_length:
            body["max_length"] = max_length
        data = await self._async_transport.request("POST", "/ai/summarize", json_body=body, timeout=timeout, provider=self.name)
        return data.get("summary", data.get("result", str(data)))

    def translate(self, text: str, target_lang: str, *, timeout: Optional[float] = None) -> str:
        """Translate text to a target language.

        Args:
            text:        Source text.
            target_lang: Target language code (e.g. ``"fr"``, ``"es"``, ``"de"``).
            timeout:     Request timeout override.

        Returns:
            Translated string.
        """
        data = self._transport.request(
            "POST", "/ai/translate",
            json_body={"text": text, "target_lang": target_lang},
            timeout=timeout, provider=self.name,
        )
        return data.get("translation", data.get("result", str(data)))

    async def async_translate(self, text: str, target_lang: str, *, timeout: Optional[float] = None) -> str:
        data = await self._async_transport.request(
            "POST", "/ai/translate",
            json_body={"text": text, "target_lang": target_lang},
            timeout=timeout, provider=self.name,
        )
        return data.get("translation", data.get("result", str(data)))

    def explain_code(self, code: str, *, timeout: Optional[float] = None) -> str:
        """Explain what a code snippet does.

        Args:
            code:    The code snippet to explain.
            timeout: Request timeout override.

        Returns:
            Plain-English explanation string.
        """
        data = self._transport.request(
            "POST", "/ai/explain-code",
            json_body={"code": code},
            timeout=timeout, provider=self.name,
        )
        return data.get("explanation", data.get("result", str(data)))

    async def async_explain_code(self, code: str, *, timeout: Optional[float] = None) -> str:
        data = await self._async_transport.request(
            "POST", "/ai/explain-code",
            json_body={"code": code},
            timeout=timeout, provider=self.name,
        )
        return data.get("explanation", data.get("result", str(data)))

    def generate_regex(self, description: str, *, timeout: Optional[float] = None) -> str:
        """Generate a regex pattern from a natural language description.

        Args:
            description: Natural language description (e.g. ``"match email addresses"``).
            timeout:     Request timeout override.

        Returns:
            Regex pattern string.
        """
        data = self._transport.request(
            "POST", "/ai/generate-regex",
            json_body={"description": description},
            timeout=timeout, provider=self.name,
        )
        return data.get("regex", data.get("pattern", data.get("result", str(data))))

    async def async_generate_regex(self, description: str, *, timeout: Optional[float] = None) -> str:
        data = await self._async_transport.request(
            "POST", "/ai/generate-regex",
            json_body={"description": description},
            timeout=timeout, provider=self.name,
        )
        return data.get("regex", data.get("pattern", data.get("result", str(data))))

    # ------------------------------------------------------------------
    # Developer utility helpers (non-AI)
    # ------------------------------------------------------------------

    def hash(self, algorithm: str, input: str, *, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Generate a cryptographic hash.

        Args:
            algorithm: Hash algorithm (``"md5"``, ``"sha1"``, ``"sha256"``, etc.).
            input:     String to hash.
        """
        return self._transport.request("GET", f"/hash/{algorithm}/{input}", timeout=timeout, provider=self.name)

    def generate_uuid(self, *, timeout: Optional[float] = None) -> str:
        """Generate a UUID v4."""
        data = self._transport.request("GET", "/uuid", timeout=timeout, provider=self.name)
        return data.get("uuid", str(data))

    def generate_password(self, length: int = 16, symbols: bool = True, *, timeout: Optional[float] = None) -> str:
        """Generate a cryptographically secure random password."""
        data = self._transport.request(
            "GET", "/password",
            params={"length": length, "symbols": str(symbols).lower()},
            timeout=timeout, provider=self.name,
        )
        return data.get("password", str(data))

    def lorem_ipsum(self, paragraphs: int = 1, *, timeout: Optional[float] = None) -> str:
        """Generate Lorem Ipsum placeholder text."""
        data = self._transport.request(
            "GET", "/lorem-ipsum",
            params={"paragraphs": paragraphs},
            timeout=timeout, provider=self.name,
        )
        return data.get("text", str(data))

    def qr_code(self, data: str, size: int = 300, *, timeout: Optional[float] = None) -> bytes:
        """Generate a QR code PNG image for the given data string.

        Returns the raw PNG bytes.
        """
        content, _ = self._transport.get_bytes(
            "/qr",
            params={"data": data, "size": size},
            timeout=timeout, provider=self.name,
        )
        return content

    # ------------------------------------------------------------------
    # Models list — static since DevToolbox has no /models endpoint
    # ------------------------------------------------------------------

    def list_models(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        return [
            {"id": "devtoolbox-ai", "object": "model", "capabilities": ["generate", "summarize", "translate", "explain-code", "generate-regex"]},
        ]

    async def async_list_models(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        return self.list_models()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap_response(data: Dict[str, Any], model: str) -> ChatResponse:
        text = (
            data.get("response")
            or data.get("result")
            or data.get("text")
            or data.get("output")
            or json.dumps(data)
        )
        return ChatResponse(
            text=str(text),
            model=model or "devtoolbox-ai",
            provider="devtoolbox",
            finish_reason="stop",
            usage=Usage(),
            raw=data,
        )
