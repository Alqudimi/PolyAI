# mlvoca Provider

> **Repository:** https://github.com/Alqudimi/PolyAI

```python
client.chat(provider="mlvoca", ...)
```

---

## Overview

| Property | Value |
|---|---|
| Provider name | `"mlvoca"` |
| Base URL | `https://mlvoca.com` |
| Endpoint | `POST /api/generate` |
| Protocol | Ollama-compatible REST + SSE |
| Auth | **None — completely free** |
| Rate limits | None (hardware limited) |
| Commercial use | ❌ **Non-commercial only** |

> ⚠️ **Important:** mlvoca is for **non-commercial use only**. Do not use it in commercial products. See [LICENSE_GUIDE.md](../../../LICENSE_GUIDE.md) for details.

---

## Authentication

No API key is required or accepted:

```python
client = Client()  # no mlvoca key needed
response = client.chat(provider="mlvoca", model="tinyllama", messages=[...])
```

---

## Models

| Model ID | Parameters | Speed | Use Case |
|---|---|---|---|
| `tinyllama` | 1.1B | Very fast | Quick responses, testing |
| `deepseek-r1:1.5b` | 1.5B | Moderate | Step-by-step reasoning |

### TinyLlama

- Based on LLaMA architecture
- Very lightweight — suitable for simple tasks
- Best for: quick answers, classification, simple generation

### DeepSeek-R1 1.5B

- Outputs `<think>...</think>` reasoning tokens followed by the answer
- The `<think>` tags are preserved in `response.text`
- Best for: problems requiring step-by-step reasoning

```python
response = client.chat(
    provider="mlvoca",
    model="deepseek-r1:1.5b",
    messages=[{"role": "user", "content": "What is 17 × 24?"}],
)
# response.text may include:
# <think>17 × 24 = 17 × 20 + 17 × 4 = 340 + 68 = 408</think>
# 17 × 24 = 408
```

---

## Supported Features

| Feature | Supported | Notes |
|---|:---:|---|
| Chat completions | ✅ | |
| Streaming | ✅ | SSE |
| Function calling | ❌ | Not supported |
| Structured output | ❌ | No JSON mode |
| Vision | ❌ | Not supported |
| Embeddings | ❌ | Not supported |
| Image generation | ❌ | Not supported |
| Text-to-speech | ❌ | Not supported |

---

## Usage Examples

### Basic Chat

```python
response = client.chat(
    provider="mlvoca",
    model="tinyllama",
    messages=[{"role": "user", "content": "What is the capital of Japan?"}],
)
print(response.text)
```

### Multi-Turn Conversation

```python
messages = [
    {"role": "user",      "content": "My name is Alice."},
    {"role": "assistant", "content": "Nice to meet you, Alice!"},
    {"role": "user",      "content": "What is my name?"},
]
response = client.chat(provider="mlvoca", model="tinyllama", messages=messages)
# response.text should contain "Alice"
```

### Streaming

```python
for chunk in client.chat_stream(
    provider="mlvoca",
    model="tinyllama",
    messages=[{"role": "user", "content": "Tell me a short joke."}],
):
    print(chunk.delta, end="", flush=True)
print()
```

### With Higher Timeout

mlvoca can be slow. Always set a generous timeout:

```python
from polyai import ClientConfig
from polyai.config import ProviderConfig

config = ClientConfig(
    providers={"mlvoca": ProviderConfig(timeout=300.0)}  # 5 minutes
)
client = Client(config=config)
```

---

## How mlvoca Integration Works

mlvoca uses the **Ollama API format**, which is different from OpenAI. PolyAI converts OpenAI-style messages automatically:

```python
# You write (OpenAI format)
messages = [
    {"role": "system",    "content": "You are helpful."},
    {"role": "user",      "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user",      "content": "What's 2+2?"},
]

# PolyAI converts to (Ollama format internally)
prompt = "SYSTEM: You are helpful.\n\nUSER: Hello!\nASSISTANT: Hi there!\nUSER: What's 2+2?\nASSISTANT:"
```

This conversion is transparent — you always use the standard PolyAI message format.

---

## Performance Expectations

| Condition | Speed |
|---|---|
| Low traffic | 2–5 seconds |
| High traffic | 10–60+ seconds |
| Very high traffic | May time out |

mlvoca runs on donated hardware with no SLA. For production workloads, use OVHcloud or Pollinations.

---

## Error Handling

```python
from polyai.exceptions import ProviderUnavailableError, TimeoutError, UniversalAIError

try:
    response = client.chat(provider="mlvoca", model="tinyllama", messages=[...])
except TimeoutError:
    print("mlvoca timed out — try a higher timeout or use a different provider")
except ProviderUnavailableError:
    print("mlvoca is temporarily down")
    # Failover to another provider
    response = client.chat(provider="pollinations", model="openai", messages=[...])
except UniversalAIError as e:
    print(f"Error: {e}")
```
