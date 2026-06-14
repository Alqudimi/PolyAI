# API Reference

## Client

```python
from universal_ai import Client

client = Client(
    ovhcloud_api_key="...",       # or OVHCLOUD_API_KEY env var
    pollinations_api_key="...",   # or POLLINATIONS_API_KEY env var
    devtoolbox_api_key="...",     # or DEVTOOLBOX_API_KEY env var
    timeout=60.0,                 # default request timeout
    max_retries=3,                # automatic retry count
)
```

### `client.chat()`

```python
response = client.chat(
    provider: str,                       # "ovhcloud" | "pollinations" | "mlvoca" | "devtoolbox"
    model: str,                          # provider-specific model ID
    messages: list[dict],                # [{"role": "user", "content": "..."}]
    temperature: float | None = None,    # 0.0 – 2.0
    max_tokens: int | None = None,
    top_p: float | None = None,
    tools: list | None = None,
    tool_choice: any = None,
    response_format: dict | None = None,
    system: str | None = None,           # shorthand system prompt
    json_mode: bool = False,             # shorthand for {"type": "json_object"}
    timeout: float | None = None,
    **extra,                             # provider-specific passthrough
) -> ChatResponse
```

### `client.chat_stream()`

```python
for chunk in client.chat_stream(provider, model, messages, ...):
    print(chunk.delta, end="")
```

### `client.chat_accumulate()`

```python
response = client.chat_accumulate(
    provider, model, messages,
    on_chunk=lambda c: print(c.delta, end=""),  # optional callback
    **kwargs,
) -> ChatResponse
```

### `client.generate_image()`

```python
img = client.generate_image(
    provider: str,
    prompt: str,
    model: str | None = None,
    n: int = 1,
    size: str | None = None,     # "1024x1024"
    width: int | None = None,
    height: int | None = None,
    response_format: str | None = None,
    timeout: float | None = None,
) -> ImageResponse
```

### `client.embed()`

```python
result = client.embed(
    provider: str,
    input: str | list[str],
    model: str,
    timeout: float | None = None,
) -> EmbeddingResponse
```

### `client.text_to_speech()`

```python
audio = client.text_to_speech(
    provider: str,
    text: str,
    model: str | None = None,
    voice: str | None = None,
    response_format: str = "mp3",
    speed: float = 1.0,
) -> AudioResponse
```

### `client.list_models()`

```python
models = client.list_models(provider: str) -> list[dict]
```

### `client.with_provider()`

Returns a `ProviderClient` with namespaced resources:

```python
ovh = client.with_provider("ovhcloud")
ovh.chat.complete(messages=[...], model="...")
ovh.images.generate(prompt="...")
ovh.embeddings.create("text", model="bge-m3")
ovh.models.list()
```

---

## AsyncClient

Identical API to `Client` but all methods are `async`:

```python
from universal_ai import AsyncClient

async with AsyncClient() as client:
    response = await client.chat(...)
    
    async for chunk in await client.chat_stream(...):
        print(chunk.delta, end="")
    
    responses = await client.chat_many([...], max_concurrency=10)
```

---

## Response Types

### ChatResponse

```python
response.text           # str — generated text
response.model          # str — model ID
response.provider       # str — provider name
response.finish_reason  # str — "stop" | "length" | "tool_calls"
response.tool_calls     # list[ToolCall]
response.usage          # Usage
response.id             # str
response.raw            # dict — raw provider response
```

### ChatChunk (streaming)

```python
chunk.delta        # str — incremental token text
chunk.model        # str
chunk.provider     # str
chunk.finish_reason  # str | None
```

### ImageResponse

```python
response.url        # str | None — first image URL
response.urls       # list[str] — all image URLs
response.images     # list[ImageData]
response.images[0].save("output.png")  # save to file
```

### EmbeddingResponse

```python
result.embeddings      # list[Embedding]
result.vectors         # list[list[float]]
result.first           # Embedding | None
result.similarity_matrix()  # list[list[float]]
result.embeddings[0].cosine_similarity(result.embeddings[1])  # float
result.embeddings[0].dimensions  # int
```

### AudioResponse

```python
audio.content       # bytes — raw audio
audio.content_type  # str — "audio/mpeg"
audio.save("file.mp3")
```

### Usage

```python
usage.prompt_tokens     # int
usage.completion_tokens # int
usage.total_tokens      # int
```

---

## Types & Helpers

### Message helpers

```python
from universal_ai.types.chat import SystemMessage, UserMessage, AssistantMessage, ToolMessage

messages = [
    SystemMessage("You are a helpful assistant."),
    UserMessage("Hello!"),
]
```

### Vision message helper

```python
from universal_ai.utils import build_vision_message

msg = build_vision_message(
    "What is in this image?",
    "https://example.com/photo.jpg",  # or local path or base64 URI
)
```

### Tool definition

```python
from universal_ai.types import Tool, FunctionDefinition

tool = Tool(function=FunctionDefinition(
    name="get_weather",
    description="Get current weather",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string"},
        },
        "required": ["location"],
    },
))
```

### StreamAccumulator

```python
from universal_ai.streaming import StreamAccumulator

acc = StreamAccumulator()
for chunk in client.chat_stream(...):
    print(chunk.delta, end="", flush=True)
    acc.add(chunk)
response = acc.result()
```

---

## Exceptions

```python
from universal_ai.exceptions import (
    UniversalAIError,       # base — catch all
    AuthenticationError,    # 401
    RateLimitError,         # 429 — has .retry_after attribute
    InvalidRequestError,    # 400, 422
    ModelNotFoundError,     # 404
    ProviderError,          # 500, 502
    ProviderUnavailableError, # 503
    TimeoutError,
    ConnectionError,
    StreamingError,
    FeatureNotSupportedError,
    ProviderNotSupportedError,
)

try:
    response = client.chat(...)
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except AuthenticationError:
    print("Check your API key")
except UniversalAIError as e:
    print(f"Provider error: {e} (status={e.status_code})")
```
