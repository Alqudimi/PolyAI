# OVHcloud AI Endpoints Provider

> **Repository:** https://github.com/Alqudimi/PolyAI

```python
client.chat(provider="ovhcloud", ...)
```

---

## Overview

| Property | Value |
|---|---|
| Provider name | `"ovhcloud"` |
| Base URL | `https://oai.endpoints.kepler.ai.cloud.ovh.net/v1` |
| Protocol | OpenAI-compatible REST + SSE |
| Auth | Bearer token (`OVHCLOUD_API_KEY` env var) |
| Free tier | 2 req/min per IP per model (anonymous) |
| Data residency | European Union |
| Commercial use | ✅ Yes |

---

## Authentication

### Anonymous (Free Tier)

```python
client = Client()  # no key set
# Rate limited to 2 requests/minute per model
```

### With API Key (Higher Limits)

```bash
export OVHCLOUD_API_KEY="your-ovhcloud-key"
```

Generate a key: **OVHcloud Manager → Public Cloud → AI & Machine Learning → AI Endpoints → API Keys**

```python
client = Client(ovhcloud_api_key="your-key")
```

---

## Models

### Large Language Models

| Model ID | Context | Best For |
|---|---|---|
| `meta-llama-3_3-70b-instruct` | 128k | High-quality chat, reasoning |
| `llama-3.1-8b-instruct` | 128k | Fast, affordable |
| `llama-3.2-3b-instruct` | 128k | Very fast, lightweight |
| `mistral-7b-instruct-v0.3` | 32k | General purpose |
| `codestral-22b-v0.1` | 32k | Code generation |
| `deepseek-r1-distill-llama-70b` | 64k | Reasoning |
| `llama-3.1-70b-instruct` | 128k | Balanced quality/speed |

### Vision Models

| Model ID | Description |
|---|---|
| `Qwen/Qwen3-VL-8B-Instruct` | Vision + language model |
| `meta-llama/Llama-3.2-11B-Vision-Instruct` | Vision model |

### Embedding Models

| Model ID | Dimensions | Languages |
|---|---|---|
| `bge-m3` | 1024 | 100+ languages |
| `bge-large-en-v1.5` | 1024 | English |
| `nomic-embed-text-v1.5` | 768 | English |
| `multilingual-e5-large-instruct` | 1024 | Multilingual |

### Reranking Models

| Model ID | Description |
|---|---|
| `bge-reranker-v2-m3` | Cross-encoder reranker |
| `bge-reranker-large` | Larger reranker |

### Image Generation

| Model ID | Description |
|---|---|
| `stable-diffusion-xl-base-1.0` | SDXL image generation |
| `flux-1-dev` | Flux image generation |

### Audio Models

| Model ID | Description |
|---|---|
| `whisper-large-v3-turbo` | Speech-to-text (fast) |

---

## Supported Features

| Feature | Supported | Notes |
|---|:---:|---|
| Chat completions | ✅ | Full OpenAI-compatible |
| Streaming | ✅ | SSE |
| Function calling | ✅ | `tools` + `tool_choice` |
| Structured output | ✅ | `json_mode=True` |
| Vision | ✅ | Qwen3-VL, LLaMA 3.2 Vision |
| Embeddings | ✅ | BGE-M3 recommended |
| Reranking | ✅ | BGE-reranker |
| Image generation | ✅ | SDXL, Flux |
| Speech-to-text | ✅ | Whisper large v3 turbo |
| Text-to-speech | ❌ | Not supported |
| Model listing | ✅ | `/v1/models` |

---

## Usage Examples

### Basic Chat

```python
response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "What is quantum computing?"}],
    temperature=0.7,
    max_tokens=300,
)
print(response.text)
```

### Multi-Turn Conversation

```python
messages = [
    {"role": "system",    "content": "You are a helpful coding assistant."},
    {"role": "user",      "content": "Write a Python function to reverse a string."},
    {"role": "assistant", "content": "def reverse(s):\n    return s[::-1]"},
    {"role": "user",      "content": "Now make it handle None input."},
]
response = client.chat(provider="ovhcloud", model="llama-3.1-8b-instruct", messages=messages)
```

### Function Calling

```python
from polyai.types import Tool, FunctionDefinition

tools = [Tool(function=FunctionDefinition(
    name="search_database",
    description="Search a database for information",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
))]

response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{"role": "user", "content": "Find me info about Python"}],
    tools=tools,
    tool_choice="auto",
)

if response.tool_calls:
    tc = response.tool_calls[0]
    print(f"Function: {tc.name}")
    print(f"Args: {tc.parse_arguments()}")
```

### Embeddings

```python
result = client.embed(
    provider="ovhcloud",
    input=["The quick brown fox", "A lazy dog"],
    model="bge-m3",
)
sim = result.embeddings[0].cosine_similarity(result.embeddings[1])
print(f"Similarity: {sim:.4f}")
```

### Vision

```python
from polyai.utils import build_vision_message

msg = build_vision_message(
    "Describe this image in detail.",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/640px-Camponotus_flavomarginatus_ant.jpg",
)
response = client.chat(
    provider="ovhcloud",
    model="Qwen/Qwen3-VL-8B-Instruct",
    messages=[msg],
    max_tokens=200,
)
print(response.text)
```

---

## Rate Limits

| Tier | Rate Limit |
|---|---|
| Anonymous | 2 requests/minute per model per IP |
| Registered (free) | Higher limits |
| Paid | 400 req/min per project per model |

The anonymous tier is sufficient for development and testing.

---

## Error Codes

| HTTP Status | Exception | Common Cause |
|---|---|---|
| 401 | `AuthenticationError` | Invalid or missing API key |
| 403 | `PermissionDeniedError` | Key lacks permission for this model |
| 404 | `ModelNotFoundError` | Model ID is wrong |
| 422 | `InvalidRequestError` | Bad parameters |
| 429 | `RateLimitError` | Rate limit hit (auto-retried) |
| 500 | `ProviderError` | OVHcloud server error |
| 503 | `ProviderUnavailableError` | OVHcloud maintenance |
