# PolyAI — Feature Reference

> **Repository:** https://github.com/Alqudimi/PolyAI

This document is the authoritative list of every feature in PolyAI.

---

## Core Features

### ✅ Unified Chat Completions

Send chat messages to any provider using identical code.

```python
response = client.chat(
    provider="ovhcloud",                # "pollinations", "mlvoca", "devtoolbox"
    model="llama-3.1-8b-instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": "What is Python?"},
    ],
    temperature=0.7,
    max_tokens=500,
    top_p=0.95,
)
print(response.text)
print(response.usage.total_tokens)
print(response.finish_reason)  # "stop", "length", "tool_calls"
```

**Supported by:** OVHcloud ✅ | Pollinations ✅ | mlvoca ✅ | DevToolbox ✅

---

### ✅ Real-Time Streaming (SSE)

Receive tokens as they are generated.

```python
for chunk in client.chat_stream(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{"role": "user", "content": "Write a poem."}],
    max_tokens=200,
):
    print(chunk.delta, end="", flush=True)
print()  # newline after stream
```

**Supported by:** OVHcloud ✅ | Pollinations ✅ | mlvoca ✅ | DevToolbox ❌

---

### ✅ Async Client

Non-blocking I/O for server applications.

```python
from polyai import AsyncClient

async with AsyncClient() as client:
    response = await client.chat(...)
    async for chunk in await client.chat_stream(...):
        print(chunk.delta, end="")
```

**Supported by:** All providers ✅

---

### ✅ Concurrent Multi-Provider Requests

Fan out requests to multiple providers simultaneously.

```python
async with AsyncClient() as client:
    results = await client.chat_many([
        {"provider": "ovhcloud",     "model": "llama-3.1-8b-instruct", "messages": [...]},
        {"provider": "pollinations", "model": "openai",                 "messages": [...]},
        {"provider": "mlvoca",       "model": "tinyllama",              "messages": [...]},
    ], max_concurrency=10)
```

---

### ✅ System Prompt Shorthand

Convenient shorthand instead of prepending to messages list.

```python
response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Who are you?"}],
    system="You are a pirate named Jack. Always speak in pirate.",
)
```

---

### ✅ JSON Mode / Structured Output

Force the model to output valid JSON.

```python
import json

response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{"role": "user", "content": "Extract: name, age, city from: 'John, 30, Paris'"}],
    json_mode=True,   # shorthand for response_format={"type": "json_object"}
    temperature=0.0,
)
data = json.loads(response.text)
print(data)  # {"name": "John", "age": 30, "city": "Paris"}
```

**Supported by:** OVHcloud ✅ | Pollinations ✅ | mlvoca ❌ | DevToolbox ❌

---

### ✅ Function Calling / Tool Use

Enable models to call external functions.

```python
from polyai.types import Tool, FunctionDefinition

weather_tool = Tool(function=FunctionDefinition(
    name="get_weather",
    description="Get current weather",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
        },
        "required": ["location"],
    },
))

response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{"role": "user", "content": "What's the weather in London?"}],
    tools=[weather_tool],
    tool_choice="auto",  # "auto", "none", or {"type": "function", "function": {"name": "..."}}
)

if response.tool_calls:
    for tc in response.tool_calls:
        args = tc.parse_arguments()
        result = call_my_function(tc.name, args)
```

**Supported by:** OVHcloud ✅ | Pollinations ✅ | mlvoca ❌ | DevToolbox ❌

---

### ✅ Vision (Multimodal Input)

Send images alongside text.

```python
from polyai.utils import build_vision_message

# From URL
msg = build_vision_message("What is in this image?", "https://example.com/photo.jpg")

# From local file
msg = build_vision_message("Describe this.", "/path/to/image.png")

# From base64 data URI
msg = build_vision_message("Analyse this.", "data:image/jpeg;base64,/9j/...")

# Multiple images
msg = build_vision_message("Compare these.", ["url1", "url2"])

response = client.chat(
    provider="ovhcloud",
    model="Qwen/Qwen3-VL-8B-Instruct",
    messages=[msg],
)
```

**Supported by:** OVHcloud ✅ | Pollinations ✅ | mlvoca ❌ | DevToolbox ❌

---

### ✅ Embeddings

Generate semantic embeddings for text.

```python
result = client.embed(
    provider="ovhcloud",
    input=["Hello world", "Bonjour monde", "Hola mundo"],
    model="bge-m3",
)

# Access vectors
for emb in result.embeddings:
    print(f"Dimensions: {emb.dimensions}, First 5: {emb.vector[:5]}")

# Cosine similarity between two embeddings
sim = result.embeddings[0].cosine_similarity(result.embeddings[1])

# Full similarity matrix
matrix = result.similarity_matrix()  # list[list[float]]
```

**Supported by:** OVHcloud ✅ | Pollinations ✅ | mlvoca ❌ | DevToolbox ❌

---

### ✅ Image Generation

Generate images from text prompts.

```python
# API-based
img = client.generate_image(
    provider="pollinations",
    prompt="a sunset over the ocean, oil painting",
    model="flux",
    width=1024,
    height=1024,
    n=1,
    seed=42,
)
print(img.url)
img.images[0].save("sunset.png")

# Zero-cost URL (no API call)
from polyai.providers.pollinations import PollinationsProvider
provider = client._get_provider("pollinations")
url = provider.generate_image_url("a sunset", model="flux", width=512, height=512, seed=42)
```

**Supported by:** OVHcloud ✅ | Pollinations ✅ | mlvoca ❌ | DevToolbox ❌

---

### ✅ Text-to-Speech

Convert text to spoken audio.

```python
audio = client.text_to_speech(
    provider="pollinations",
    text="Hello, this is PolyAI speaking.",
    voice="alloy",          # "alloy", "echo", "fable", "onyx", "nova", "shimmer"
    response_format="mp3",  # "mp3", "wav", "ogg"
    speed=1.0,              # 0.25 to 4.0
)
audio.save("output.mp3")
print(f"Audio: {len(audio.content):,} bytes, type: {audio.content_type}")
```

**Supported by:** OVHcloud ❌ | Pollinations ✅ | mlvoca ❌ | DevToolbox ❌

---

### ✅ DevToolbox AI Utilities

AI-powered text tools without managing a model.

```python
devtools = client.with_provider("devtoolbox").devtools

# AI tools
summary    = devtools.summarize("Long text...", max_length=100)
translated = devtools.translate("Hello!", target_language="fr")
explained  = devtools.explain_code("const x = arr.reduce((a,b)=>a+b,0)")
regex      = devtools.generate_regex("match ISO 8601 dates")

# Developer utilities
uuid       = devtools.generate_uuid()
password   = devtools.generate_password(length=20, symbols=True)
hash_val   = devtools.hash("sha256", "hello world")
lorem      = devtools.lorem_ipsum(paragraphs=3)
qr_bytes   = devtools.qr_code("https://github.com/Alqudimi/PolyAI", size=300)
```

---

### ✅ Namespaced Resource API

Alternative API style modelled after the OpenAI SDK.

```python
ovh = client.with_provider("ovhcloud")
pollinations = client.with_provider("pollinations")

# Chat
resp = ovh.chat.complete(messages=[...], model="llama-3.1-8b-instruct")

# Embeddings
emb = ovh.embeddings.create("text to embed", model="bge-m3")

# Images
img = pollinations.images.generate("a sunset", model="flux")

# Audio
audio = pollinations.audio.speech("Hello!", voice="nova")

# Models
models = ovh.models.list()
```

---

### ✅ Stream Accumulation

Accumulate a stream into a single response.

```python
from polyai.streaming import StreamAccumulator

acc = StreamAccumulator()
for chunk in client.chat_stream(...):
    print(chunk.delta, end="", flush=True)
    acc.add(chunk)

response = acc.result()
print(f"\nTotal: {response.usage.total_tokens} tokens")
```

Shorthand:

```python
response = client.chat_accumulate(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[...],
    on_chunk=lambda c: print(c.delta, end="", flush=True),
)
```

---

### ✅ Automatic Retries

Configurable retry policy with exponential backoff.

```python
from polyai import ClientConfig

config = ClientConfig(
    max_retries=5,   # retry up to 5 times
    timeout=60.0,    # 60s request timeout
)
# Retries on: 429, 500, 502, 503, 504, connection errors, timeouts
```

---

### ✅ Error Handling

Rich exception hierarchy.

```python
from polyai.exceptions import (
    UniversalAIError,          # base — catch all
    AuthenticationError,        # 401 Unauthorized
    PermissionDeniedError,      # 403 Forbidden
    RateLimitError,             # 429 — has .retry_after attribute
    InvalidRequestError,        # 400, 422
    ModelNotFoundError,         # 404
    ProviderError,              # 5xx server errors
    ProviderUnavailableError,   # 503 Service Unavailable
    TimeoutError,               # request timeout
    ConnectionError,            # network failure
    StreamingError,             # SSE parse error
    ContentFilterError,         # content policy violation
    ContextLengthExceededError, # prompt too long
    FeatureNotSupportedError,   # provider doesn't support feature
    ProviderNotSupportedError,  # unknown provider name
)
```

---

### ✅ Middleware Hooks (Request / Response Observers)

Plug callbacks into every HTTP request and response for logging, metrics, latency measurement, tracing or testing.

```python
from polyai import Client
from polyai.middleware import MiddlewareRegistry

registry = MiddlewareRegistry()

@registry.on_request
def log_request(payload):
    payload.set_header("x-request-id", "123")  # inject extra headers / params
    print("REQ", payload.method, payload.url, payload.provider)

@registry.on_response
def log_response(payload):
    print("RES", payload.status_code, f"{payload.elapsed_ms:.0f}ms", "OK" if payload.ok else payload.exception)

client = Client(middleware=registry)  # also works via ClientConfig(middleware=...)
```

Request and response hooks are dispatched by both `SyncTransport` and `AsyncTransport`, including streaming requests and failed responses. Hook exceptions are logged and swallowed so observers can never break user requests.

---

### ✅ Model Discovery

List available models from any provider.

```python
models = client.list_models("ovhcloud")
for m in models:
    print(m["id"])
```

---

## Capability Matrix

| Feature | OVHcloud | Pollinations | mlvoca | DevToolbox |
|---|:---:|:---:|:---:|:---:|
| Chat completions | ✅ | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ | ❌ |
| Function calling | ✅ | ✅ | ❌ | ❌ |
| Structured output | ✅ | ✅ | ❌ | ❌ |
| Vision | ✅ | ✅ | ❌ | ❌ |
| Embeddings | ✅ | ✅ | ❌ | ❌ |
| Image generation | ✅ | ✅ | ❌ | ❌ |
| Text-to-speech | ❌ | ✅ | ❌ | ❌ |
| Speech-to-text | ✅ | ❌ | ❌ | ❌ |
| Async support | ✅ | ✅ | ✅ | ✅ |
| Middleware hooks | ✅ | ✅ | ✅ | ✅ |
| Free tier | ✅ | ✅ | ✅ | ✅ |
