# Types Reference

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## ChatResponse

The return type of `client.chat()` and `client.chat_accumulate()`.

```python
from polyai.types import ChatResponse
```

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `text` | `str` | Full assistant response text. Empty string if finish_reason is "tool_calls". |
| `usage` | `Usage` | Token usage statistics |
| `finish_reason` | `str` | Why generation stopped: `"stop"`, `"length"`, `"tool_calls"`, `"content_filter"` |
| `tool_calls` | `list[ToolCall]` | Function calls requested by the model (empty list if none) |
| `model` | `str` | Model ID that generated the response |
| `provider` | `str` | Provider name that handled the request |
| `raw` | `dict` | Raw provider API response (for debugging) |

### Example

```python
response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
)

print(response.text)           # "Hello! How can I help you today?"
print(response.finish_reason)  # "stop"
print(response.usage.total_tokens)  # 15
print(response.model)          # "llama-3.1-8b-instruct"
print(response.provider)       # "ovhcloud"
print(response.tool_calls)     # []
print(type(response.raw))      # dict
```

---

## ChatChunk

One token/chunk yielded by `client.chat_stream()`.

```python
from polyai.types import ChatChunk
```

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `delta` | `str` | Text content of this chunk (may be empty for the final chunk) |
| `finish_reason` | `str \| None` | `None` until the last chunk, then `"stop"`, `"length"`, etc. |
| `raw` | `dict` | Raw SSE frame data |

### Example

```python
full_text = ""
for chunk in client.chat_stream(...):
    full_text += chunk.delta
    print(chunk.delta, end="", flush=True)
    if chunk.finish_reason:
        print(f"\n[Done: {chunk.finish_reason}]")
```

---

## Usage

Token usage statistics.

```python
from polyai.types import Usage
```

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `prompt_tokens` | `int` | Tokens in the input (messages + system prompt) |
| `completion_tokens` | `int` | Tokens in the generated response |
| `total_tokens` | `int` | `prompt_tokens + completion_tokens` |

### Example

```python
print(f"Prompt: {response.usage.prompt_tokens}")
print(f"Completion: {response.usage.completion_tokens}")
print(f"Total: {response.usage.total_tokens}")
```

---

## EmbeddingResponse

Return type of `client.embed()`.

```python
from polyai.types import EmbeddingResponse
```

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `embeddings` | `list[Embedding]` | List of embedding objects, one per input text |
| `model` | `str` | Embedding model used |
| `provider` | `str` | Provider that generated the embeddings |
| `usage` | `Usage` | Token usage |

### Methods

```python
# Get pairwise similarity matrix
matrix: list[list[float]] = result.similarity_matrix()
# matrix[i][j] = cosine_similarity(embeddings[i], embeddings[j])
```

### Example

```python
result = client.embed(
    provider="ovhcloud",
    input=["Hello", "Bonjour", "Hola"],
    model="bge-m3",
)
print(f"Embeddings: {len(result.embeddings)}")
print(f"Dimensions: {result.embeddings[0].dimensions}")
matrix = result.similarity_matrix()
print(f"EN-FR similarity: {matrix[0][1]:.4f}")
```

---

## Embedding

A single embedding vector.

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `index` | `int` | Position in the input list |
| `vector` | `list[float]` | The embedding vector |
| `dimensions` | `int` | Length of the vector |

### Methods

```python
# Cosine similarity to another embedding
sim: float = emb1.cosine_similarity(emb2)
# Returns value in [-1.0, 1.0]; higher = more similar
```

### Example

```python
emb1 = result.embeddings[0]
emb2 = result.embeddings[1]
print(f"Vector length: {emb1.dimensions}")     # e.g., 1024 for bge-m3
print(f"First 5 values: {emb1.vector[:5]}")
print(f"Similarity: {emb1.cosine_similarity(emb2):.4f}")
```

---

## ImageResponse

Return type of `client.generate_image()`.

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `images` | `list[ImageData]` | Generated images |
| `url` | `str` | URL of the first image (if URL-based) |
| `provider` | `str` | Provider used |
| `model` | `str` | Image model used |

### ImageData

| Attribute | Type | Description |
|---|---|---|
| `b64_json` | `str \| None` | Base64-encoded image data |
| `url` | `str \| None` | URL of the image |

### Methods

```python
# Save image to file (works for both b64 and URL)
img_data.save("output.png")
```

### Example

```python
result = client.generate_image(
    provider="pollinations",
    prompt="a sunset",
    model="flux",
)
print(result.url)            # image URL
result.images[0].save("sunset.png")  # save to disk
```

---

## AudioResponse

Return type of `client.text_to_speech()`.

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `content` | `bytes` | Raw audio bytes |
| `content_type` | `str` | MIME type (`"audio/mpeg"`, `"audio/wav"`, etc.) |
| `duration` | `float \| None` | Duration in seconds if available |

### Methods

```python
audio.save("output.mp3")   # save bytes to file
len(audio.content)         # file size in bytes
```

---

## Tool

Defines a function the model can call.

```python
from polyai.types import Tool, FunctionDefinition
```

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `type` | `str` | Always `"function"` |
| `function` | `FunctionDefinition` | The function definition |

### FunctionDefinition

| Attribute | Type | Description |
|---|---|---|
| `name` | `str` | Function name (no spaces, alphanumeric + underscores) |
| `description` | `str` | What the function does |
| `parameters` | `dict` | JSON Schema describing the parameters |

### Example

```python
from polyai.types import Tool, FunctionDefinition

get_weather = Tool(function=FunctionDefinition(
    name="get_weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name, e.g. 'Paris, France'",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "default": "celsius",
            },
        },
        "required": ["location"],
    },
))
```

---

## ToolCall

A function call requested by the model. Found in `response.tool_calls`.

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `id` | `str` | Unique call identifier |
| `name` | `str` | Function name to call |
| `arguments` | `str` | Raw JSON string of arguments |

### Methods

```python
# Parse arguments to dict
args: dict = tc.parse_arguments()
```

### Example

```python
if response.tool_calls:
    for tc in response.tool_calls:
        print(f"Call: {tc.name}")
        args = tc.parse_arguments()
        print(f"Args: {args}")
        # result = your_function(tc.name, args)
```

---

## Message Helpers

Convenience constructors for message dicts.

```python
from polyai.types import SystemMessage, UserMessage, AssistantMessage, ToolMessage

messages = [
    SystemMessage("You are a helpful assistant."),
    UserMessage("Hello!"),
    AssistantMessage("Hi there!"),
    UserMessage("What's the weather?"),
]
# Equivalent to:
messages = [
    {"role": "system",    "content": "You are a helpful assistant."},
    {"role": "user",      "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user",      "content": "What's the weather?"},
]
```
