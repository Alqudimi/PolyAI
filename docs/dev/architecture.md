# Architecture Guide

> **Repository:** https://github.com/Alqudimi/PolyAI

This document describes PolyAI's internal architecture for developers who want to understand, extend, or contribute to the codebase.

---

## System Overview

PolyAI is structured as a **layered SDK** with clear separation between the public API, provider adapters, and transport layer.

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Application                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │  Client / AsyncClient           │
              │  (Public API — stable contract) │
              └────────────────┬────────────────┘
                               │
         ┌─────────────────────▼─────────────────────┐
         │          Provider Registry                │
         │  {"ovhcloud": OVHcloudProvider, ...}     │
         └──────┬──────────┬──────────┬─────────────┘
                │          │          │
    ┌───────────▼──┐ ┌─────▼─────┐ ┌─▼──────────────┐
    │  OVHcloud    │ │Pollinations│ │ mlvoca/Devtools │
    │  Provider    │ │  Provider  │ │    Provider     │
    └───────┬──────┘ └─────┬─────┘ └────────┬────────┘
            │              │                 │
            └──────────────┼─────────────────┘
                           │
               ┌───────────▼───────────┐
               │  SyncTransport /      │
               │  AsyncTransport       │
               │  (httpx sessions)     │
               └───────────┬───────────┘
                           │
               ┌───────────▼───────────┐
               │  RetryPolicy          │
               │  (exp. backoff)       │
               └───────────┬───────────┘
                           │
               ┌───────────▼───────────┐
               │  Auth Credentials     │
               │  Bearer/ApiKey/NoAuth │
               └───────────────────────┘
```

---

## Layer Descriptions

### Layer 1: Public API (`client.py`, `async_client.py`)

The `Client` and `AsyncClient` classes are the **only** entry points users interact with. They:

- Accept provider-agnostic parameters (`provider`, `model`, `messages`, etc.)
- Delegate to the provider registry to find the right `BaseProvider`
- Return normalised response types (`ChatResponse`, `EmbeddingResponse`, etc.)
- Never expose HTTP primitives or provider-specific details

**Key invariant:** `client.chat(provider="ovhcloud", ...)` and `client.chat(provider="pollinations", ...)` must return the same `ChatResponse` type.

### Layer 2: Provider Registry (`providers/__init__.py`)

A simple dict mapping provider name strings to provider instances:

```python
_PROVIDERS: dict[str, type[BaseProvider]] = {
    "ovhcloud":     OVHcloudProvider,
    "pollinations": PollinationsProvider,
    "mlvoca":       MlvocaProvider,
    "devtoolbox":   DevToolboxProvider,
}
```

Providers are instantiated lazily per `Client` instance and cached.

### Layer 3: Provider Adapters (`providers/*.py`)

Each provider implements `BaseProvider` (five abstract methods):

```python
class BaseProvider(ABC):
    @abstractmethod
    def chat(self, ...) -> ChatResponse: ...

    @abstractmethod
    def chat_stream(self, ...) -> Iterator[ChatChunk]: ...

    @abstractmethod
    def embed(self, ...) -> EmbeddingResponse: ...

    @abstractmethod
    def generate_image(self, ...) -> ImageResponse: ...

    @abstractmethod
    def list_models(self) -> list[dict]: ...
```

Providers are responsible for:
- Constructing the correct HTTP request for their API
- Parsing the response into the normalised type
- Mapping HTTP errors to the correct `UniversalAIError` subclass
- Raising `FeatureNotSupportedError` for unsupported features

### Layer 4: Transport (`http/transport.py`, `http/async_transport.py`)

The transport layer manages HTTP sessions:

```python
class SyncTransport:
    def __init__(self, config: ClientConfig, credentials: BaseCredentials):
        self._session = httpx.Client(
            timeout=config.timeout,
            follow_redirects=True,
        )

    def post(self, url: str, json: dict) -> dict: ...
    def stream(self, url: str, json: dict) -> Iterator[str]: ...
    def get(self, url: str) -> dict: ...
    def close(self): ...
```

**Key properties:**
- Uses `httpx.Client` for connection pooling (sync)
- Uses `httpx.AsyncClient` for async
- All errors from httpx are mapped to PolyAI exceptions here
- Transport is injected into providers — this makes testing easy

### Layer 5: Retry Policy (`http/retry.py`)

```python
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True    # full jitter prevents thundering herd

    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
```

The retry policy wraps the transport. On retryable errors:
1. Calculate wait = `random.uniform(0, min(max_delay, base_delay * 2^attempt))`
2. For 429 with `Retry-After` header: use that value instead
3. Wait and retry

### Layer 6: Auth (`auth/credentials.py`)

```python
class BearerCredentials:
    def apply(self, headers: dict) -> dict:
        headers["Authorization"] = f"Bearer {self._token}"
        return headers
    def __repr__(self): return f"BearerCredentials(token='{self._masked}')"

class ApiKeyHeaderCredentials:
    def apply(self, headers: dict) -> dict:
        headers[self._header_name] = self._key
        return headers

class NoAuthCredentials:
    def apply(self, headers: dict) -> dict:
        return headers  # pass-through
```

**Security principle:** All credential objects mask the secret in `__repr__`. This is tested in unit tests.

---

## Request Lifecycle

```
client.chat(provider="ovhcloud", model="llama-3.1-8b-instruct", messages=[...])
  │
  ├── Validate provider name → ProviderNotSupportedError if unknown
  ├── Get OVHcloudProvider from registry (create if first use)
  │
  ▼
OVHcloudProvider.chat(model, messages, temperature, ...)
  │
  ├── Build request payload (OpenAI format for OVHcloud)
  ├── Add system message if `system` parameter given
  ├── Build URL: https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions
  │
  ▼
SyncTransport.post(url, json=payload)
  │
  ├── Apply credentials (add Authorization header)
  │
  ▼
RetryPolicy.execute(lambda: httpx_post(...))
  │
  ├── httpx sends request
  ├── On 429 → sleep(retry_after or backoff) → retry
  ├── On 5xx → sleep(backoff) → retry
  ├── On 401, 403, 404 → raise immediately (no retry)
  │
  ▼
OVHcloudProvider._parse_chat_response(raw_json) → ChatResponse
  │
  ├── Extract text from choices[0].message.content
  ├── Extract usage.prompt_tokens, completion_tokens, total_tokens
  ├── Extract finish_reason
  ├── Extract tool_calls if present
  │
  ▼
client.chat() returns ChatResponse to user
```

---

## Streaming Lifecycle

```
client.chat_stream(provider="ovhcloud", ...)
  │
  ▼
OVHcloudProvider.chat_stream(...) → Iterator[ChatChunk]
  │
  ▼
SyncTransport.stream(url, json=payload)
  │
  ├── httpx opens SSE connection
  ├── Yields raw SSE line strings
  │
  ▼
OVHcloudProvider._parse_stream_line(line) → ChatChunk | None
  │
  ├── Skip empty lines and "[DONE]" sentinel
  ├── Parse JSON from "data: {...}" prefix
  ├── Extract delta.content from choices[0].delta.content
  │
  ▼
client.chat_stream() yields ChatChunk to user
```

---

## Response Type Hierarchy

```
ChatResponse
├── text: str                    # full content (or empty if tool_call)
├── usage: Usage
│   ├── prompt_tokens: int
│   ├── completion_tokens: int
│   └── total_tokens: int
├── finish_reason: str           # "stop", "length", "tool_calls"
├── tool_calls: list[ToolCall]
│   └── ToolCall
│       ├── id: str
│       ├── name: str
│       ├── arguments: str       # raw JSON string
│       └── parse_arguments() -> dict
├── model: str                   # model used
├── provider: str                # provider used
└── raw: dict                    # original provider response

ChatChunk
├── delta: str                   # this chunk's text
├── finish_reason: str | None
└── raw: dict
```

---

## Design Patterns

### Adapter Pattern

Each provider is an Adapter that converts provider-specific HTTP APIs into PolyAI's unified interface. This is the core pattern of the SDK.

### Template Method Pattern

`BaseProvider` defines the algorithm skeleton, with abstract methods that subclasses fill in. For example, `_build_chat_payload()` is overridden by each provider.

### Strategy Pattern

The `RetryPolicy` is a strategy — it can be configured independently of the transport.

### Dependency Injection

`SyncTransport` is injected into providers rather than created internally. In tests, a mock transport can be injected:

```python
mock_transport = MagicMock()
mock_transport.post.return_value = MOCK_CHAT_RESPONSE
provider = OVHcloudProvider(config, transport=mock_transport)
```

---

## Key Design Decisions

### Why httpx over requests?

httpx provides sync and async in one package (via `httpx.Client` and `httpx.AsyncClient`). This eliminates the need for `aiohttp` as a separate async dependency. httpx also has native HTTP/2 and streaming support.

### Why one production dependency?

Keeping dependencies minimal:
- Reduces install time
- Reduces transitive vulnerability surface
- Makes embedding in restricted environments easier

### Why exponential backoff with full jitter?

The ["full jitter" strategy](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) randomises the wait interval within `[0, cap]` rather than using a fixed exponential delay. This prevents the "thundering herd" problem where all clients retry simultaneously after a 429 wave.

### Why masked credentials in `__repr__`?

AI API keys are high-value secrets. In Python, any object can accidentally be logged via `print(config)`, `logger.debug(f"{config}")`, or error tracebacks. By making all credential objects mask their values in `__repr__`, we make accidental leakage impossible.

---

## Testing Architecture

```
tests/
├── unit/
│   ├── conftest.py              # shared fixtures
│   ├── test_client.py          # Client integration tests (mocked HTTP)
│   ├── test_providers.py       # per-provider unit tests
│   ├── test_streaming.py       # streaming + accumulator tests
│   ├── test_auth.py            # credential masking, token application
│   ├── test_retry.py           # retry policy backoff, jitter
│   ├── test_exceptions.py      # exception hierarchy tests
│   └── test_types.py           # response type methods (cosine_similarity, etc.)
├── integration/
│   ├── test_ovhcloud.py        # live OVHcloud tests
│   ├── test_pollinations.py    # live Pollinations tests
│   ├── test_mlvoca.py          # live mlvoca tests
│   └── test_devtoolbox.py      # live DevToolbox tests
└── mocks/
    └── responses.py            # shared mock response dicts
```

All unit tests run fully offline using `respx` (httpx mock library). No real HTTP calls are made in unit tests.
