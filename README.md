<div align="center">

# PolyAI

**Production-grade unified Python SDK for multiple AI providers.**

*One interface. Four providers. Zero compromise.*

[![CI](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml)
[![Release](https://github.com/Alqudimi/PolyAI/actions/workflows/release.yml/badge.svg)](https://github.com/Alqudimi/PolyAI/actions/workflows/release.yml)
[![Security](https://github.com/Alqudimi/PolyAI/actions/workflows/security.yml/badge.svg)](https://github.com/Alqudimi/PolyAI/actions/workflows/security.yml)
[![PyPI version](https://badge.fury.io/py/polyai.svg)](https://badge.fury.io/py/polyai)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://codecov.io/gh/Alqudimi/PolyAI/branch/main/graph/badge.svg)](https://codecov.io/gh/Alqudimi/PolyAI)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[**Documentation**](https://github.com/Alqudimi/PolyAI/wiki) •
[**Quick Start**](#quick-start) •
[**Providers**](#providers) •
[**Examples**](examples/) •
[**Contributing**](CONTRIBUTING.md) •
[**Changelog**](CHANGELOG.md)

*Read in: [العربية](README_AR.md) · [Español](README_ES.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [中文](README_ZH.md)*

</div>

---

## What is PolyAI?

PolyAI is a **production-grade Python SDK** that provides a single, unified interface for interacting with multiple AI providers. Instead of learning four different APIs, authentication schemes, and response formats — you learn one.

```python
from polyai import Client

client = Client()

# Works with any of the four providers — same code, same response format
response = client.chat(
    provider="ovhcloud",      # or "pollinations", "mlvoca", "devtoolbox"
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.text)
```

### Why PolyAI?

| Without PolyAI | With PolyAI |
|---|---|
| Learn 4 different HTTP APIs | One unified `client.chat()` call |
| Handle 4 different auth schemes | `OVHCLOUD_API_KEY` env var, done |
| Parse 4 different response formats | Always get `response.text` |
| Write 4 different streaming loops | `for chunk in client.chat_stream(...)` |
| No automatic retries | Exponential backoff built-in |
| No failover logic | Drop-in provider switching |

---

## Providers

| Provider | Free Tier | Auth Required | Highlights |
|---|:---:|:---:|---|
| **OVHcloud AI Endpoints** | ✅ Anonymous (2 req/min) | Optional | EU-hosted, 40+ models, GDPR-ready |
| **Pollinations.AI** | ✅ No signup | Optional | Images, TTS, 20+ LLMs |
| **mlvoca** | ✅ Always free | ❌ None | Non-commercial, Ollama-compatible |
| **DevToolbox API** | ✅ 100k req/day | Optional | AI utilities + developer tools |

---

## Installation

```bash
pip install polyai
```

**Requirements:** Python 3.9+ · No mandatory API keys

> For development: `pip install "polyai[dev]"`

---

## Quick Start

### Basic Chat

```python
from polyai import Client

client = Client()

response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)
print(response.text)       # Paris
print(response.usage)      # Usage(prompt=12, completion=2, total=14)
```

### Streaming

```python
for chunk in client.chat_stream(
    provider="pollinations",
    model="openai",
    messages=[{"role": "user", "content": "Tell me a story."}],
):
    print(chunk.delta, end="", flush=True)
```

### Async

```python
import asyncio
from polyai import AsyncClient

async def main():
    async with AsyncClient() as client:
        response = await client.chat(
            provider="ovhcloud",
            model="meta-llama-3_3-70b-instruct",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response.text)

asyncio.run(main())
```

### Concurrent Multi-Provider

```python
async def main():
    async with AsyncClient() as client:
        results = await client.chat_many([
            {"provider": "ovhcloud",     "model": "llama-3.1-8b-instruct", "messages": [...]},
            {"provider": "pollinations", "model": "openai",                 "messages": [...]},
            {"provider": "mlvoca",       "model": "tinyllama",              "messages": [...]},
        ], max_concurrency=10)
```

---

## Feature Overview

<details>
<summary><strong>💬 Chat Completions</strong></summary>

```python
response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{"role": "user", "content": "Explain quantum computing."}],
    temperature=0.7,
    max_tokens=500,
    system="You are a physicist.",
    json_mode=False,
)
print(response.text)
print(f"Finish: {response.finish_reason} | Tokens: {response.usage.total_tokens}")
```
</details>

<details>
<summary><strong>🖼️ Image Generation</strong></summary>

```python
img = client.generate_image(
    provider="pollinations",
    prompt="a futuristic city at night, digital art",
    model="flux",
    width=1024,
    height=1024,
)
img.images[0].save("output.png")
print(img.url)
```
</details>

<details>
<summary><strong>📐 Embeddings</strong></summary>

```python
result = client.embed(
    provider="ovhcloud",
    input=["Hello world", "Bonjour monde"],
    model="bge-m3",
)
sim = result.embeddings[0].cosine_similarity(result.embeddings[1])
print(f"Similarity: {sim:.4f}")
matrix = result.similarity_matrix()
```
</details>

<details>
<summary><strong>🔧 Function Calling</strong></summary>

```python
from polyai.types import Tool, FunctionDefinition

tool = Tool(function=FunctionDefinition(
    name="get_weather",
    description="Get current weather for a city",
    parameters={
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"],
    },
))

response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=[tool],
)
if response.tool_calls:
    tc = response.tool_calls[0]
    print(f"Call: {tc.name}({tc.parse_arguments()})")
```
</details>

<details>
<summary><strong>👁️ Vision (Multimodal)</strong></summary>

```python
from polyai.utils import build_vision_message

msg = build_vision_message(
    "What is in this image?",
    "https://example.com/photo.jpg",
)
response = client.chat(
    provider="ovhcloud",
    model="Qwen/Qwen3-VL-8B-Instruct",
    messages=[msg],
)
```
</details>

<details>
<summary><strong>🔊 Text-to-Speech</strong></summary>

```python
audio = client.text_to_speech(
    provider="pollinations",
    text="Hello, world!",
    voice="alloy",
)
audio.save("hello.mp3")
```
</details>

<details>
<summary><strong>🛠️ DevToolbox Utilities</strong></summary>

```python
devtools = client.with_provider("devtoolbox").devtools

summary   = devtools.summarize("Long article...")
translated = devtools.translate("Hello!", "fr")
explained  = devtools.explain_code("const x = arr.reduce((a,b) => a+b, 0)")
regex      = devtools.generate_regex("match email addresses")
uuid       = devtools.generate_uuid()
password   = devtools.generate_password(length=20)
```
</details>

<details>
<summary><strong>🔄 Provider Failover</strong></summary>

```python
from polyai.exceptions import UniversalAIError

for provider, model in [
    ("ovhcloud",     "llama-3.1-8b-instruct"),
    ("pollinations", "openai"),
    ("mlvoca",       "tinyllama"),
]:
    try:
        resp = client.chat(provider=provider, model=model, messages=[...])
        print(resp.text)
        break
    except UniversalAIError:
        continue
```
</details>

---

## Architecture

```
polyai/
├── client.py              # Client (sync)
├── async_client.py        # AsyncClient
├── config.py              # ClientConfig, ProviderConfig
├── exceptions.py          # Full exception hierarchy (14 types)
├── types/                 # ChatResponse, ImageResponse, Embedding, …
├── http/
│   ├── transport.py       # SyncTransport (httpx, connection pooling)
│   ├── async_transport.py # AsyncTransport
│   └── retry.py           # RetryPolicy (exponential backoff + jitter)
├── auth/
│   └── credentials.py     # Bearer, ApiKey, NoAuth (secrets masked)
├── providers/
│   ├── base.py            # BaseProvider (abstract)
│   ├── ovhcloud.py        # OVHcloud OpenAI-compatible adapter
│   ├── pollinations.py    # Pollinations adapter
│   ├── mlvoca.py          # mlvoca Ollama-format adapter
│   └── devtoolbox.py      # DevToolbox adapter
├── resources/             # chat, images, audio, embeddings, devtools, models
├── streaming/engine.py    # StreamAccumulator, AsyncStreamAccumulator
└── utils/helpers.py       # build_vision_message, cosine_similarity, …
```

---

## Configuration

```python
from polyai import Client, ClientConfig
from polyai.config import ProviderConfig

config = ClientConfig(
    ovhcloud_api_key="...",        # or OVHCLOUD_API_KEY env var
    pollinations_api_key="sk_...", # or POLLINATIONS_API_KEY env var
    devtoolbox_api_key="dtb_...", # or DEVTOOLBOX_API_KEY env var
    timeout=60.0,
    max_retries=3,
    providers={
        "ovhcloud": ProviderConfig(timeout=30.0, max_retries=5),
    },
)
client = Client(config=config)
```

**Environment variables:**

```bash
export OVHCLOUD_API_KEY="your-key"
export POLLINATIONS_API_KEY="sk_..."
export DEVTOOLBOX_API_KEY="dtb_..."
export UNIVERSAL_AI_TIMEOUT=60
export UNIVERSAL_AI_MAX_RETRIES=3
```

---

## Error Handling

```python
from polyai.exceptions import (
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    UniversalAIError,
)

try:
    response = client.chat(...)
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except AuthenticationError:
    print("Check your API key")
except ModelNotFoundError as e:
    print(f"Model not found: {e.provider}")
except UniversalAIError as e:
    print(f"Error ({e.provider}, HTTP {e.status_code}): {e}")
```

---

## Examples

| Example | Description |
|---|---|
| [`basic_chat.py`](examples/basic_chat.py) | Minimal chat across all 4 providers |
| [`streaming_chat.py`](examples/streaming_chat.py) | Real-time token streaming |
| [`async_chat.py`](examples/async_chat.py) | Async + concurrent requests |
| [`image_generation.py`](examples/image_generation.py) | Image generation with Pollinations |
| [`embeddings_similarity.py`](examples/embeddings_similarity.py) | Semantic similarity + cosine |
| [`function_calling.py`](examples/function_calling.py) | Tool use agentic loop |
| [`vision_chat.py`](examples/vision_chat.py) | Multimodal vision with Qwen3-VL |
| [`audio_tts.py`](examples/audio_tts.py) | Text-to-speech with Pollinations |
| [`devtools_utilities.py`](examples/devtools_utilities.py) | DevToolbox AI + utilities |
| [`provider_routing.py`](examples/provider_routing.py) | Failover + capability routing |
| [`structured_output.py`](examples/structured_output.py) | JSON mode + entity extraction |

---

## Development

```bash
git clone https://github.com/Alqudimi/PolyAI.git
cd PolyAI
pip install -e ".[dev]"

# Unit tests (fully offline)
pytest tests/unit -v

# With coverage
pytest tests/unit --cov=polyai --cov-report=term-missing

# Integration tests (live providers)
UNIVERSAL_AI_INTEGRATION_TESTS=1 pytest tests/integration -v

# Lint + format
ruff check polyai tests
ruff format polyai tests

# Type check
mypy polyai
```

---

## Documentation

| Document | Description |
|---|---|
| [Wiki Home](https://github.com/Alqudimi/PolyAI/wiki) | Full documentation portal |
| [Installation Guide](docs/user/installation.md) | Detailed installation instructions |
| [Configuration Guide](docs/user/configuration.md) | All config options explained |
| [API Reference](docs/api/overview.md) | Complete API documentation |
| [Provider Reference](docs/api/providers/) | Per-provider documentation |
| [Architecture](docs/dev/architecture.md) | System design and internals |
| [Contributing Guide](CONTRIBUTING.md) | How to contribute |
| [FAQ](FAQ.md) | Frequently asked questions |
| [Troubleshooting](TROUBLESHOOTING.md) | Common issues and fixes |

---

## License

[MIT](LICENSE) — Copyright © 2026 [Abdulaziz Alqudimi](https://github.com/Alqudimi)

> **Note:** mlvoca is for non-commercial use only per its provider terms.
> All other providers permit commercial use.

---

<div align="center">

Made with ❤️ by [Abdulaziz Alqudimi](https://github.com/Alqudimi)

⭐ **Star this repo if PolyAI helps you!**

</div>
