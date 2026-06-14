# Client API Reference

> **Repository:** https://github.com/Alqudimi/PolyAI

```python
from polyai import Client
```

---

## Constructor

```python
Client(
    ovhcloud_api_key: str | None = None,
    pollinations_api_key: str | None = None,
    devtoolbox_api_key: str | None = None,
    timeout: float = 60.0,
    max_retries: int = 3,
    config: ClientConfig | None = None,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ovhcloud_api_key` | `str \| None` | `None` | OVHcloud API key. Falls back to `OVHCLOUD_API_KEY` env var. Empty string = anonymous. |
| `pollinations_api_key` | `str \| None` | `None` | Pollinations key (`sk_*` or `pk_*`). Falls back to `POLLINATIONS_API_KEY` env var. |
| `devtoolbox_api_key` | `str \| None` | `None` | DevToolbox key (`dtb_*`). Falls back to `DEVTOOLBOX_API_KEY` env var. |
| `timeout` | `float` | `60.0` | Default request timeout in seconds. |
| `max_retries` | `int` | `3` | Maximum retry attempts for transient failures. |
| `config` | `ClientConfig \| None` | `None` | Full config object (overrides other parameters if provided). |

**Example:**
```python
# Minimal — reads keys from environment
client = Client()

# With explicit keys
client = Client(ovhcloud_api_key="your-key", timeout=30.0)

# With full config
from polyai import ClientConfig
client = Client(config=ClientConfig(max_retries=5))
```

---

## `client.chat()`

Send a chat completion request.

```python
client.chat(
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    tools: list[Tool] | None = None,
    tool_choice: Any = None,
    response_format: dict | None = None,
    system: str | None = None,
    json_mode: bool = False,
    timeout: float | None = None,
    **extra: Any,
) -> ChatResponse
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `provider` | `str` | required | Provider name: `"ovhcloud"`, `"pollinations"`, `"mlvoca"`, `"devtoolbox"` |
| `model` | `str` | required | Model ID for the chosen provider |
| `messages` | `list[dict]` | required | List of `{"role": str, "content": str}` dicts |
| `temperature` | `float \| None` | `None` | Sampling temperature. 0.0 = deterministic. |
| `max_tokens` | `int \| None` | `None` | Maximum tokens to generate |
| `top_p` | `float \| None` | `None` | Nucleus sampling parameter |
| `tools` | `list[Tool] \| None` | `None` | Tools/functions the model can call |
| `tool_choice` | `Any` | `None` | `"auto"`, `"none"`, or `{"type": "function", ...}` |
| `response_format` | `dict \| None` | `None` | `{"type": "json_object"}` for JSON mode |
| `system` | `str \| None` | `None` | Shorthand system prompt (prepended to messages) |
| `json_mode` | `bool` | `False` | Shorthand for `response_format={"type": "json_object"}` |
| `timeout` | `float \| None` | `None` | Per-request timeout override |
| `**extra` | `Any` | — | Provider-specific passthrough parameters |

**Returns:** [`ChatResponse`](types.md#chatresponse)

**Raises:**
- `ProviderNotSupportedError` — unknown provider name
- `AuthenticationError` — invalid API key
- `RateLimitError` — rate limit exceeded
- `InvalidRequestError` — bad parameters
- `ModelNotFoundError` — model ID not found
- `ProviderUnavailableError` — provider server down
- `TimeoutError` — request timed out
- `ConnectionError` — network unreachable

**Example:**
```python
response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": "What is Python?"},
    ],
    temperature=0.7,
    max_tokens=200,
)
print(response.text)
print(response.usage.total_tokens)
```

---

## `client.chat_stream()`

Stream a chat completion response token-by-token.

```python
client.chat_stream(
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    **kwargs: Any,
) -> Iterator[ChatChunk]
```

Same parameters as `chat()`. Returns an iterator of [`ChatChunk`](types.md#chatchunk).

**Example:**
```python
for chunk in client.chat_stream(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Tell me a story."}],
    max_tokens=300,
):
    print(chunk.delta, end="", flush=True)
print()
```

**Raises:** Same as `chat()`, plus `StreamingError` for SSE parse errors.

---

## `client.chat_accumulate()`

Stream and automatically accumulate into a complete `ChatResponse`.

```python
client.chat_accumulate(
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    on_chunk: Callable[[ChatChunk], None] | None = None,
    **kwargs: Any,
) -> ChatResponse
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `on_chunk` | `Callable \| None` | Optional callback called for each chunk as it arrives |
| `**kwargs` | | Same as `chat()` |

**Example:**
```python
response = client.chat_accumulate(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Count from 1 to 10."}],
    on_chunk=lambda c: print(c.delta, end="", flush=True),
)
print(f"\nTotal tokens: {response.usage.total_tokens}")
```

---

## `client.embed()`

Generate text embeddings.

```python
client.embed(
    provider: str,
    input: str | list[str],
    model: str,
    timeout: float | None = None,
) -> EmbeddingResponse
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `provider` | `str` | `"ovhcloud"` or `"pollinations"` |
| `input` | `str \| list[str]` | Text or list of texts to embed |
| `model` | `str` | Embedding model ID |
| `timeout` | `float \| None` | Per-request timeout |

**Returns:** [`EmbeddingResponse`](types.md#embeddingresponse)

**Raises:** `FeatureNotSupportedError` if provider doesn't support embeddings.

**Example:**
```python
result = client.embed(
    provider="ovhcloud",
    input=["Hello world", "Bonjour monde"],
    model="bge-m3",
)
sim = result.embeddings[0].cosine_similarity(result.embeddings[1])
```

---

## `client.generate_image()`

Generate images from a text prompt.

```python
client.generate_image(
    provider: str,
    prompt: str,
    model: str | None = None,
    n: int = 1,
    size: str | None = None,
    width: int | None = None,
    height: int | None = None,
    response_format: str | None = None,
    timeout: float | None = None,
    **extra: Any,
) -> ImageResponse
```

**Returns:** [`ImageResponse`](types.md#imageresponse)

**Example:**
```python
img = client.generate_image(
    provider="pollinations",
    prompt="a sunset over the ocean",
    model="flux",
    width=1024,
    height=768,
)
img.images[0].save("sunset.png")
```

---

## `client.text_to_speech()`

Convert text to audio.

```python
client.text_to_speech(
    provider: str,
    text: str,
    model: str | None = None,
    voice: str | None = None,
    response_format: str = "mp3",
    speed: float = 1.0,
) -> AudioResponse
```

**Returns:** [`AudioResponse`](types.md#audioresponse)

**Raises:** `FeatureNotSupportedError` if provider doesn't support TTS.

**Example:**
```python
audio = client.text_to_speech(
    provider="pollinations",
    text="Hello world!",
    voice="alloy",
)
audio.save("hello.mp3")
```

---

## `client.list_models()`

List available models for a provider.

```python
client.list_models(provider: str) -> list[dict[str, Any]]
```

**Returns:** List of model dicts with at minimum an `"id"` key.

**Example:**
```python
models = client.list_models("ovhcloud")
for m in models:
    print(m["id"])
```

---

## `client.with_provider()`

Get a namespaced provider client with resource attributes.

```python
client.with_provider(provider: str) -> ProviderClient
```

**Returns:** `ProviderClient` with attributes:
- `.chat` — `ChatResource`
- `.images` — `ImagesResource`
- `.audio` — `AudioResource`
- `.embeddings` — `EmbeddingsResource`
- `.devtools` — `DevToolsResource`
- `.models` — `ModelsResource`

**Example:**
```python
ovh = client.with_provider("ovhcloud")
response = ovh.chat.complete(messages=[...], model="llama-3.1-8b-instruct")
models = ovh.models.list()
```

---

## `client.close()`

Close the underlying HTTP connections.

```python
client.close() -> None
```

Call when done, or use the context manager:
```python
with Client() as client:
    ...  # automatically closed
```

---

## Context Manager Protocol

```python
with Client() as client:
    response = client.chat(...)
# Connection pool is closed here
```
