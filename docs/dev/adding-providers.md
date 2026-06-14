# Adding a New Provider

> **Repository:** https://github.com/Alqudimi/PolyAI

This guide walks through adding a new AI provider to PolyAI from start to finish.

---

## Overview

Adding a provider requires:

1. Create `polyai/providers/myprovider.py` implementing `BaseProvider`
2. Register the provider in `polyai/providers/__init__.py`
3. Add auth config in `polyai/config.py`
4. Add unit tests in `tests/unit/test_providers.py`
5. Add integration tests in `tests/integration/test_myprovider.py`
6. Update `FEATURES.md` capability matrix
7. Create API docs in `docs/api/providers/myprovider.md`
8. Update `CHANGELOG.md`

---

## Step 1: Create the Provider Module

Create `polyai/providers/myprovider.py`:

```python
"""MyProvider adapter for PolyAI.

MyProvider is a hypothetical AI provider offering:
- Chat completions (OpenAI-compatible)
- Streaming

Not supported: embeddings, images, TTS.

Docs: https://myprovider.com/docs
"""

from __future__ import annotations

import json
from typing import Any, Iterator

from polyai.auth.credentials import BearerCredentials, NoAuthCredentials
from polyai.config import ClientConfig
from polyai.exceptions import FeatureNotSupportedError
from polyai.http.transport import SyncTransport
from polyai.providers.base import BaseProvider
from polyai.types import (
    AudioResponse,
    ChatChunk,
    ChatResponse,
    EmbeddingResponse,
    ImageResponse,
    Usage,
)

# Base URL for MyProvider
MYPROVIDER_BASE_URL = "https://api.myprovider.com/v1"

# Supported models
CHAT_MODELS = [
    "myprovider-fast",
    "myprovider-balanced",
    "myprovider-large",
]


class MyProvider(BaseProvider):
    """PolyAI adapter for MyProvider."""

    name = "myprovider"  # must match the registry key

    def __init__(
        self,
        config: ClientConfig,
        transport: SyncTransport | None = None,
    ) -> None:
        super().__init__(config)

        # Resolve API key: explicit config → env var → empty (anonymous)
        api_key = config.myprovider_api_key or ""

        # Choose credential type
        credentials = (
            BearerCredentials(api_key) if api_key else NoAuthCredentials()
        )

        self._transport = transport or SyncTransport(
            config=config,
            credentials=credentials,
            base_url=MYPROVIDER_BASE_URL,
        )

    # ──────────────────────────────────────────────────────────────
    # Chat
    # ──────────────────────────────────────────────────────────────

    def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        system: str | None = None,
        json_mode: bool = False,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a chat completion request."""
        if system:
            messages = [{"role": "system", "content": system}, *messages]

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        raw = self._transport.post(
            url="/chat/completions",
            json=payload,
            timeout=timeout,
        )
        return self._parse_chat_response(raw)

    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> Iterator[ChatChunk]:
        """Stream a chat completion response."""
        if kwargs.get("system"):
            messages = [{"role": "system", "content": kwargs.pop("system")}, *messages]

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            **{k: v for k, v in kwargs.items() if v is not None},
        }

        for line in self._transport.stream(url="/chat/completions", json=payload):
            chunk = self._parse_stream_line(line)
            if chunk is not None:
                yield chunk

    # ──────────────────────────────────────────────────────────────
    # Unsupported features
    # ──────────────────────────────────────────────────────────────

    def embed(self, *args: Any, **kwargs: Any) -> EmbeddingResponse:
        raise FeatureNotSupportedError("embeddings", provider=self.name)

    def generate_image(self, *args: Any, **kwargs: Any) -> ImageResponse:
        raise FeatureNotSupportedError("image generation", provider=self.name)

    def text_to_speech(self, *args: Any, **kwargs: Any) -> AudioResponse:
        raise FeatureNotSupportedError("text-to-speech", provider=self.name)

    def list_models(self) -> list[dict[str, Any]]:
        """List available models."""
        raw = self._transport.get("/models")
        return raw.get("data", [])

    # ──────────────────────────────────────────────────────────────
    # Response parsers
    # ──────────────────────────────────────────────────────────────

    def _parse_chat_response(self, raw: dict[str, Any]) -> ChatResponse:
        """Convert raw API response into a normalised ChatResponse."""
        choice = raw["choices"][0]
        message = choice["message"]

        usage_raw = raw.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_raw.get("prompt_tokens", 0),
            completion_tokens=usage_raw.get("completion_tokens", 0),
            total_tokens=usage_raw.get("total_tokens", 0),
        )

        return ChatResponse(
            text=message.get("content") or "",
            finish_reason=choice.get("finish_reason", "stop"),
            usage=usage,
            model=raw.get("model", ""),
            provider=self.name,
            raw=raw,
        )

    def _parse_stream_line(self, line: str) -> ChatChunk | None:
        """Parse a single SSE line into a ChatChunk."""
        if not line.startswith("data: "):
            return None
        data = line[6:].strip()
        if data == "[DONE]":
            return None
        try:
            obj = json.loads(data)
        except json.JSONDecodeError:
            return None

        choice = obj.get("choices", [{}])[0]
        delta = choice.get("delta", {})
        content = delta.get("content", "")
        return ChatChunk(
            delta=content or "",
            finish_reason=choice.get("finish_reason"),
            raw=obj,
        )
```

---

## Step 2: Register the Provider

In `polyai/providers/__init__.py`:

```python
from polyai.providers.ovhcloud import OVHcloudProvider
from polyai.providers.pollinations import PollinationsProvider
from polyai.providers.mlvoca import MlvocaProvider
from polyai.providers.devtoolbox import DevToolboxProvider
from polyai.providers.myprovider import MyProvider      # ← ADD THIS

_PROVIDERS: dict[str, type[BaseProvider]] = {
    "ovhcloud":     OVHcloudProvider,
    "pollinations": PollinationsProvider,
    "mlvoca":       MlvocaProvider,
    "devtoolbox":   DevToolboxProvider,
    "myprovider":   MyProvider,                          # ← ADD THIS
}
```

---

## Step 3: Add Config Support

In `polyai/config.py`:

```python
@dataclass
class ClientConfig:
    ovhcloud_api_key: str = field(default_factory=lambda: os.getenv("OVHCLOUD_API_KEY", ""))
    pollinations_api_key: str = field(default_factory=lambda: os.getenv("POLLINATIONS_API_KEY", ""))
    devtoolbox_api_key: str = field(default_factory=lambda: os.getenv("DEVTOOLBOX_API_KEY", ""))
    myprovider_api_key: str = field(default_factory=lambda: os.getenv("MYPROVIDER_API_KEY", ""))  # ← ADD
    # ... rest of config
```

---

## Step 4: Unit Tests

In `tests/unit/test_providers.py`, add a test class:

```python
class TestMyProvider:
    """Unit tests for MyProvider."""

    @pytest.fixture
    def provider(self):
        config = ClientConfig(max_retries=0)
        mock_transport = MagicMock()
        return MyProvider(config=config, transport=mock_transport)

    def test_chat_basic(self, provider):
        provider._transport.post.return_value = {
            "id": "chatcmpl-123",
            "choices": [{
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
            "model": "myprovider-fast",
        }
        response = provider.chat(
            model="myprovider-fast",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        assert response.text == "Hello!"
        assert response.finish_reason == "stop"
        assert response.usage.total_tokens == 7
        assert response.provider == "myprovider"

    def test_chat_stream(self, provider):
        lines = [
            'data: {"choices": [{"delta": {"content": "Hello"}, "finish_reason": null}]}',
            'data: {"choices": [{"delta": {"content": " world"}, "finish_reason": "stop"}]}',
            "data: [DONE]",
        ]
        provider._transport.stream.return_value = iter(lines)
        chunks = list(provider.chat_stream(
            model="myprovider-fast",
            messages=[{"role": "user", "content": "Hi"}],
        ))
        assert len(chunks) == 2
        assert "".join(c.delta for c in chunks) == "Hello world"

    def test_embed_raises_not_supported(self, provider):
        from polyai.exceptions import FeatureNotSupportedError
        with pytest.raises(FeatureNotSupportedError):
            provider.embed(input=["hello"], model="any")

    def test_auth_error(self, provider):
        from polyai.exceptions import AuthenticationError
        provider._transport.post.side_effect = AuthenticationError("401", provider="myprovider")
        with pytest.raises(AuthenticationError):
            provider.chat(model="myprovider-fast", messages=[{"role": "user", "content": "hi"}])
```

---

## Step 5: Integration Tests

In `tests/integration/test_myprovider.py`:

```python
"""Integration tests for MyProvider — require MYPROVIDER_API_KEY."""
import os
import pytest

pytestmark = pytest.mark.integration

SKIP = not os.getenv("UNIVERSAL_AI_INTEGRATION_TESTS")

@pytest.mark.skipif(SKIP, reason="Set UNIVERSAL_AI_INTEGRATION_TESTS=1 to run")
class TestMyProviderIntegration:
    @pytest.fixture
    def client(self):
        from polyai import Client
        return Client()

    def test_chat(self, client):
        resp = client.chat(
            provider="myprovider",
            model="myprovider-fast",
            messages=[{"role": "user", "content": "Say 'hello' only."}],
            max_tokens=10,
        )
        assert isinstance(resp.text, str)
        assert len(resp.text) > 0
        assert resp.usage.total_tokens > 0

    def test_stream(self, client):
        chunks = list(client.chat_stream(
            provider="myprovider",
            model="myprovider-fast",
            messages=[{"role": "user", "content": "Say 'ok' only."}],
            max_tokens=10,
        ))
        assert len(chunks) > 0
        assert all(isinstance(c.delta, str) for c in chunks)
```

---

## Checklist Before PR

- [ ] `polyai/providers/myprovider.py` — all `BaseProvider` methods implemented
- [ ] Provider registered in `polyai/providers/__init__.py`
- [ ] `ClientConfig` has `myprovider_api_key` field
- [ ] Unit tests — happy path + error paths
- [ ] Integration test stub
- [ ] `pytest tests/unit -v` — all pass
- [ ] `mypy polyai` — no new type errors
- [ ] `ruff check polyai` — no lint errors
- [ ] `FEATURES.md` capability matrix updated
- [ ] `docs/api/providers/myprovider.md` created
- [ ] `CHANGELOG.md` updated
