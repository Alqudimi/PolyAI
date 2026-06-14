# API Reference Overview

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Module Structure

```
polyai
├── Client                    # Synchronous client
├── AsyncClient               # Asynchronous client
├── ClientConfig              # Global configuration
├── ProviderConfig            # Per-provider configuration
├── exceptions                # Exception hierarchy
│   ├── UniversalAIError
│   ├── AuthenticationError
│   ├── RateLimitError
│   └── ... (14 total)
└── types
    ├── ChatResponse
    ├── ChatChunk
    ├── EmbeddingResponse
    ├── ImageResponse
    ├── AudioResponse
    ├── Usage
    ├── Tool
    ├── ToolCall
    └── ... (more)
```

---

## Public API Surface

Everything exported from `polyai.__init__` is part of the public API and follows [Semantic Versioning](../../VERSIONING_POLICY.md).

### Clients

| Class | Description |
|---|---|
| [`Client`](client.md) | Synchronous client — use in scripts, Django, Flask |
| [`AsyncClient`](async-client.md) | Asynchronous client — use in FastAPI, async scripts |
| `ProviderClient` | Namespaced provider client (returned by `client.with_provider()`) |

### Configuration

| Class | Description |
|---|---|
| `ClientConfig` | Global configuration object |
| `ProviderConfig` | Per-provider timeout, retries, base URL overrides |

### Response Types

| Class | Returned by |
|---|---|
| `ChatResponse` | `client.chat()`, `client.chat_accumulate()` |
| `ChatChunk` | `client.chat_stream()` (each iteration) |
| `EmbeddingResponse` | `client.embed()` |
| `ImageResponse` | `client.generate_image()` |
| `AudioResponse` | `client.text_to_speech()` |
| `Usage` | `response.usage` |
| `ToolCall` | `response.tool_calls[i]` |

### Exceptions

| Exception | HTTP Status | Description |
|---|---|---|
| `UniversalAIError` | any | Base class — catch all provider errors |
| `AuthenticationError` | 401 | Invalid or missing API key |
| `PermissionDeniedError` | 403 | Key lacks permission |
| `RateLimitError` | 429 | Rate limit exceeded |
| `InvalidRequestError` | 400, 422 | Bad request parameters |
| `ModelNotFoundError` | 404 | Model ID not found |
| `ProviderError` | 5xx | Server-side error |
| `ProviderUnavailableError` | 503 | Provider temporarily down |
| `TimeoutError` | — | Request timed out |
| `ConnectionError` | — | Network unreachable |
| `StreamingError` | — | SSE parse error |
| `ContentFilterError` | — | Content policy violation |
| `ContextLengthExceededError` | — | Prompt too long |
| `FeatureNotSupportedError` | — | Provider doesn't support feature |
| `ProviderNotSupportedError` | — | Unknown provider name |

---

## Quick Reference

```python
from polyai import (
    # Clients
    Client, AsyncClient,

    # Config
    ClientConfig,

    # Exceptions
    UniversalAIError, AuthenticationError, RateLimitError,
    InvalidRequestError, ModelNotFoundError, ProviderError,
    FeatureNotSupportedError, ProviderNotSupportedError,

    # Types
    ChatResponse, ChatChunk, EmbeddingResponse,
    ImageResponse, AudioResponse, Usage,
    Tool, ToolCall, FunctionDefinition,

    # Message helpers
    SystemMessage, UserMessage, AssistantMessage, ToolMessage,

    # Streaming
    StreamAccumulator, AsyncStreamAccumulator,
)
```

---

## Detailed References

- [Client](client.md) — all `Client` methods documented
- [AsyncClient](async-client.md) — all `AsyncClient` methods documented
- [Exceptions](exceptions.md) — complete exception hierarchy
- [Types](types.md) — all response and request types
- **Providers:**
  - [OVHcloud](providers/ovhcloud.md)
  - [Pollinations](providers/pollinations.md)
  - [mlvoca](providers/mlvoca.md)
  - [DevToolbox](providers/devtoolbox.md)
