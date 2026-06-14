"""
Shared pytest fixtures and configuration for the polyai test suite.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator
from unittest.mock import MagicMock, patch

import pytest

from polyai import Client, AsyncClient
from polyai.config import ClientConfig


# ---------------------------------------------------------------------------
# Config fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def config() -> ClientConfig:
    """A ClientConfig with dummy credentials for testing."""
    return ClientConfig(
        ovhcloud_api_key="test-ovhcloud-key",
        pollinations_api_key="sk_test_pollinations",
        devtoolbox_api_key="dtb_test_key",
        timeout=5.0,
        max_retries=0,
    )


@pytest.fixture
def client(config: ClientConfig) -> Iterator[Client]:
    """A sync Client with test credentials."""
    c = Client(config=config)
    yield c
    c.close()


@pytest.fixture
def async_client(config: ClientConfig) -> AsyncClient:
    """An AsyncClient with test credentials (caller must close)."""
    return AsyncClient(config=config)


# ---------------------------------------------------------------------------
# Mock HTTP response helpers
# ---------------------------------------------------------------------------

def make_chat_response(
    content: str = "Hello, world!",
    model: str = "test-model",
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
) -> Dict[str, Any]:
    """Build a minimal OpenAI-format chat completion response dict."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1700000000,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def make_embedding_response(
    vectors: list = None,
    model: str = "bge-m3",
) -> Dict[str, Any]:
    """Build a minimal OpenAI-format embeddings response dict."""
    if vectors is None:
        vectors = [[0.1, 0.2, 0.3]]
    return {
        "object": "list",
        "model": model,
        "data": [
            {"object": "embedding", "index": i, "embedding": v}
            for i, v in enumerate(vectors)
        ],
        "usage": {"prompt_tokens": len(vectors) * 5, "total_tokens": len(vectors) * 5},
    }


def make_image_response(
    url: str = "https://example.com/image.png",
    model: str = "flux",
) -> Dict[str, Any]:
    """Build a minimal OpenAI-format image generation response dict."""
    return {
        "created": 1700000000,
        "model": model,
        "data": [{"url": url}],
    }


def make_sse_chunks(tokens: list) -> list:
    """Build a list of SSE data strings simulating a streaming response."""
    chunks = []
    for i, token in enumerate(tokens):
        is_last = i == len(tokens) - 1
        chunk = {
            "id": "chatcmpl-stream-test",
            "object": "chat.completion.chunk",
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": token} if not is_last else {},
                    "finish_reason": "stop" if is_last else None,
                }
            ],
        }
        chunks.append(json.dumps(chunk))
    return chunks


def make_ollama_response(text: str = "Hello", model: str = "tinyllama") -> Dict[str, Any]:
    """Build a minimal Ollama-format response dict (mlvoca)."""
    return {
        "model": model,
        "created_at": "2024-01-01T00:00:00Z",
        "response": text,
        "done": True,
        "context": [1, 2, 3],
        "total_duration": 1000000000,
        "prompt_eval_count": 5,
        "eval_count": 10,
    }


def make_devtoolbox_response(result: str = "Generated text") -> Dict[str, Any]:
    """Build a minimal DevToolbox AI response dict."""
    return {"response": result, "status": "success"}


@pytest.fixture
def mock_http_request():
    """Patch ``SyncTransport.request`` to return a controllable response."""
    with patch("polyai.http.transport.SyncTransport.request") as mock:
        yield mock


@pytest.fixture
def mock_http_stream():
    """Patch ``SyncTransport.stream`` to return a controllable SSE sequence."""
    with patch("polyai.http.transport.SyncTransport.stream") as mock:
        yield mock


@pytest.fixture
def mock_async_request():
    """Patch ``AsyncTransport.request`` for async tests."""
    with patch("polyai.http.async_transport.AsyncTransport.request") as mock:
        yield mock
