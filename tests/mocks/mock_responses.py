"""
Reusable mock HTTP responses for testing provider adapters.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Generator, Iterator, List
from unittest.mock import AsyncMock, MagicMock, patch


class MockSyncTransport:
    """Minimal sync transport mock for unit tests."""

    def __init__(self, responses: Dict[str, Any]) -> None:
        self._responses = responses

    def request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        key = f"{method.upper()} {path}"
        if key in self._responses:
            return self._responses[key]
        if path in self._responses:
            return self._responses[path]
        raise ValueError(f"No mock response configured for {key}")

    def stream(self, method: str, path: str, **kwargs: Any) -> Generator[str, None, None]:
        key = f"STREAM {path}"
        chunks = self._responses.get(key, [])
        yield from chunks

    def get_bytes(self, path: str, **kwargs: Any):
        key = f"BYTES {path}"
        return self._responses.get(key, (b"", "application/octet-stream"))

    def post_bytes(self, path: str, **kwargs: Any):
        key = f"POST_BYTES {path}"
        return self._responses.get(key, (b"\xff\xfb\x90\x00", "audio/mpeg"))

    def close(self) -> None:
        pass


CHAT_RESPONSE_OPENAI = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1700000000,
    "model": "meta-llama-3_3-70b-instruct",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "The capital of France is Paris."},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 15, "completion_tokens": 8, "total_tokens": 23},
}

CHAT_RESPONSE_TOOL_CALL = {
    "id": "chatcmpl-tool123",
    "object": "chat.completion",
    "created": 1700000000,
    "model": "meta-llama-3_3-70b-instruct",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_abc",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "Paris", "unit": "celsius"}',
                        },
                    }
                ],
            },
            "finish_reason": "tool_calls",
        }
    ],
    "usage": {"prompt_tokens": 30, "completion_tokens": 20, "total_tokens": 50},
}

EMBEDDING_RESPONSE = {
    "object": "list",
    "model": "bge-m3",
    "data": [
        {"object": "embedding", "index": 0, "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]},
        {"object": "embedding", "index": 1, "embedding": [0.5, 0.4, 0.3, 0.2, 0.1]},
    ],
    "usage": {"prompt_tokens": 8, "total_tokens": 8},
}

IMAGE_RESPONSE = {
    "created": 1700000000,
    "model": "flux",
    "data": [
        {"url": "https://image.pollinations.ai/prompt/a%20sunset?seed=42&model=flux"},
    ],
}

SSE_CHAT_CHUNKS = [
    json.dumps({
        "id": "chatcmpl-stream1",
        "object": "chat.completion.chunk",
        "model": "meta-llama-3_3-70b-instruct",
        "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}],
    }),
    json.dumps({
        "id": "chatcmpl-stream1",
        "object": "chat.completion.chunk",
        "model": "meta-llama-3_3-70b-instruct",
        "choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": None}],
    }),
    json.dumps({
        "id": "chatcmpl-stream1",
        "object": "chat.completion.chunk",
        "model": "meta-llama-3_3-70b-instruct",
        "choices": [{"index": 0, "delta": {"content": " world"}, "finish_reason": None}],
    }),
    json.dumps({
        "id": "chatcmpl-stream1",
        "object": "chat.completion.chunk",
        "model": "meta-llama-3_3-70b-instruct",
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }),
]

OLLAMA_RESPONSE = {
    "model": "tinyllama",
    "response": "The answer is 42.",
    "done": True,
    "context": [1, 2, 3],
    "total_duration": 500000000,
    "prompt_eval_count": 8,
    "eval_count": 5,
}

DEVTOOLBOX_GENERATE_RESPONSE = {"response": "Here is a haiku about coding.", "status": "success"}
DEVTOOLBOX_SUMMARIZE_RESPONSE = {"summary": "A brief summary of the text."}
DEVTOOLBOX_TRANSLATE_RESPONSE = {"translation": "Bonjour, monde!"}
DEVTOOLBOX_EXPLAIN_RESPONSE = {"explanation": "This code reduces an array to a single value."}
DEVTOOLBOX_REGEX_RESPONSE = {"regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}
