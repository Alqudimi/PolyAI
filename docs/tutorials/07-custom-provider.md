# Tutorial 7: Adding a Custom Provider

> **Level:** Expert | **Time:** 45 minutes
> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Goals

- Understand `BaseProvider` contract
- Implement a minimal custom provider
- Add authentication
- Handle streaming
- Write tests for your provider

---

## Prerequisites

- Completed all previous tutorials
- Python type annotation knowledge
- Basic HTTP knowledge

---

## What You'll Build

We'll build a provider for a hypothetical AI API called **"MyAI"** that:
- Has an OpenAI-compatible chat endpoint
- Requires a Bearer token
- Supports streaming

---

## Step 1: Study BaseProvider

```python
# polyai/providers/base.py
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    name: str  # provider identifier string
    
    @abstractmethod
    def chat(self, model, messages, **kwargs) -> ChatResponse:
        """Synchronous chat completion."""
    
    @abstractmethod
    def chat_stream(self, model, messages, **kwargs) -> Iterator[ChatChunk]:
        """Streaming chat completion."""
    
    @abstractmethod
    def embed(self, input, model, **kwargs) -> EmbeddingResponse:
        """Text embeddings. Raise FeatureNotSupportedError if unsupported."""
    
    @abstractmethod
    def generate_image(self, prompt, **kwargs) -> ImageResponse:
        """Image generation. Raise FeatureNotSupportedError if unsupported."""
    
    @abstractmethod
    def list_models(self) -> list[dict]:
        """Return list of available models."""
```

You must implement all five abstract methods. For unsupported features, raise `FeatureNotSupportedError`.

---

## Step 2: Create the Provider Module

Create `polyai/providers/myai.py`:

```python
"""MyAI provider adapter for PolyAI.

MyAI offers chat completions and streaming via an OpenAI-compatible API.
Embeddings and images are not supported.

API docs: https://myai.example.com/docs
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

MYAI_BASE_URL = "https://api.myai.example.com/v1"


class MyAIProvider(BaseProvider):
    """PolyAI adapter for the MyAI provider."""

    name = "myai"

    def __init__(
        self,
        config: ClientConfig,
        transport: SyncTransport | None = None,
    ) -> None:
        super().__init__(config)
        api_key = config.myai_api_key or ""
        credentials = BearerCredentials(api_key) if api_key else NoAuthCredentials()
        self._transport = transport or SyncTransport(
            config=config,
            credentials=credentials,
            base_url=MYAI_BASE_URL,
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
        """Send a chat completion request to MyAI."""
        if system:
            messages = [{"role": "system", "content": system}, *messages]

        payload: dict[str, Any] = {"model": model, "messages": messages}
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        raw = self._transport.post("/chat/completions", json=payload, timeout=timeout)
        return self._build_chat_response(raw)

    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        system: str | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatChunk]:
        """Stream a chat completion from MyAI."""
        if system:
            messages = [{"role": "system", "content": system}, *messages]

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            **{k: v for k, v in kwargs.items() if v is not None},
        }

        for line in self._transport.stream("/chat/completions", json=payload, timeout=timeout):
            chunk = self._parse_sse_line(line)
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
        """List available models from MyAI."""
        raw = self._transport.get("/models")
        return raw.get("data", [])

    # ──────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────

    def _build_chat_response(self, raw: dict[str, Any]) -> ChatResponse:
        choice = raw["choices"][0]
        usage_raw = raw.get("usage", {})
        return ChatResponse(
            text=choice["message"].get("content") or "",
            finish_reason=choice.get("finish_reason", "stop"),
            usage=Usage(
                prompt_tokens=usage_raw.get("prompt_tokens", 0),
                completion_tokens=usage_raw.get("completion_tokens", 0),
                total_tokens=usage_raw.get("total_tokens", 0),
            ),
            model=raw.get("model", model),
            provider=self.name,
            raw=raw,
        )

    def _parse_sse_line(self, line: str) -> ChatChunk | None:
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
        delta_content = choice.get("delta", {}).get("content", "")
        return ChatChunk(
            delta=delta_content or "",
            finish_reason=choice.get("finish_reason"),
            raw=obj,
        )
```

---

## Step 3: Register It

In `polyai/providers/__init__.py`:

```python
from polyai.providers.myai import MyAIProvider

_PROVIDERS: dict[str, type[BaseProvider]] = {
    # existing...
    "myai": MyAIProvider,     # ADD THIS
}
```

In `polyai/config.py`, add the API key field:

```python
@dataclass
class ClientConfig:
    # existing fields...
    myai_api_key: str = field(
        default_factory=lambda: os.getenv("MYAI_API_KEY", "")
    )
```

---

## Step 4: Use Your Provider

```python
from polyai import Client

client = Client(myai_api_key="your-key")

response = client.chat(
    provider="myai",
    model="myai-fast",
    messages=[{"role": "user", "content": "Hello from my custom provider!"}],
)
print(response.text)

# Streaming
for chunk in client.chat_stream(
    provider="myai",
    model="myai-fast",
    messages=[{"role": "user", "content": "Tell me a story."}],
):
    print(chunk.delta, end="", flush=True)
```

---

## Step 5: Write Tests

```python
# tests/unit/test_myai.py
import pytest
from unittest.mock import MagicMock
from polyai.providers.myai import MyAIProvider
from polyai.config import ClientConfig
from polyai.exceptions import FeatureNotSupportedError


@pytest.fixture
def provider():
    config = ClientConfig(max_retries=0)
    transport = MagicMock()
    return MyAIProvider(config=config, transport=transport)


class TestMyAIProvider:
    def test_chat_basic(self, provider):
        provider._transport.post.return_value = {
            "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
            "model": "myai-fast",
        }
        resp = provider.chat(
            model="myai-fast",
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert resp.text == "Hello!"
        assert resp.provider == "myai"
        assert resp.usage.total_tokens == 7

    def test_chat_with_system(self, provider):
        provider._transport.post.return_value = {
            "choices": [{"message": {"content": "Ahoy!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
        }
        provider.chat(
            model="myai-fast",
            messages=[{"role": "user", "content": "Hello"}],
            system="You are a pirate.",
        )
        payload = provider._transport.post.call_args[1]["json"]
        assert payload["messages"][0]["role"] == "system"

    def test_streaming(self, provider):
        provider._transport.stream.return_value = iter([
            'data: {"choices": [{"delta": {"content": "Hi"}, "finish_reason": null}]}',
            'data: {"choices": [{"delta": {"content": "!"}, "finish_reason": "stop"}]}',
            "data: [DONE]",
        ])
        chunks = list(provider.chat_stream(
            model="myai-fast",
            messages=[{"role": "user", "content": "Hi"}],
        ))
        assert "".join(c.delta for c in chunks) == "Hi!"
        assert chunks[-1].finish_reason == "stop"

    def test_embed_raises(self, provider):
        with pytest.raises(FeatureNotSupportedError):
            provider.embed(input=["hello"], model="any")

    def test_image_raises(self, provider):
        with pytest.raises(FeatureNotSupportedError):
            provider.generate_image(prompt="test")
```

Run:
```bash
pytest tests/unit/test_myai.py -v
```

---

## Step 6: Submitting as a PR

Before opening a PR, ensure:

```bash
pytest tests/unit -v                  # all 138+ tests pass
ruff check polyai tests               # no lint errors
mypy polyai --ignore-missing-imports  # no type errors
```

Add to `FEATURES.md` capability matrix and `CHANGELOG.md`. See [Contributing Guide](../../CONTRIBUTING.md).

---

## Expected Results

After this tutorial:
- You have a working custom provider `"myai"`
- `client.chat(provider="myai", ...)` works
- Tests pass
- You understand the PolyAI provider contract

---

## Next Steps

- [Contributing Guide](../../CONTRIBUTING.md) — open a PR to add your provider
- [Architecture Guide](../dev/architecture.md) — understand deeper internals
