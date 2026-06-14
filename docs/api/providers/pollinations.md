# Pollinations.AI Provider

> **Repository:** https://github.com/Alqudimi/PolyAI

```python
client.chat(provider="pollinations", ...)
```

---

## Overview

| Property | Value |
|---|---|
| Provider name | `"pollinations"` |
| Chat URL | `https://gen.pollinations.ai/v1` |
| Image URL | `https://image.pollinations.ai/prompt/{prompt}` |
| Protocol | OpenAI-compatible REST + SSE |
| Auth | None (anonymous) or `sk_*` / `pk_*` keys |
| Free tier | ✅ All features, no signup |
| Commercial use | ✅ Yes |

---

## Authentication

### Anonymous (No Key)

All features work without an API key:

```python
client = Client()  # POLLINATIONS_API_KEY not set
```

### With API Key

Get a key at [pollinations.ai](https://pollinations.ai):

```bash
export POLLINATIONS_API_KEY="sk_your_key"  # backend key (server-side)
# or
export POLLINATIONS_API_KEY="pk_your_key"  # frontend key (client-side)
```

Key types:
- `sk_*` — server-side key, higher limits, full features
- `pk_*` — client-side key, safe to expose in browser JS

---

## Chat Models

| Model ID | Description |
|---|---|
| `openai` | OpenAI GPT-4o |
| `openai-fast` | OpenAI GPT-4o-mini |
| `openai-large` | OpenAI GPT-4o (high capacity) |
| `claude` | Anthropic Claude Sonnet |
| `claude-large` | Anthropic Claude Opus |
| `mistral` | Mistral 7B |
| `mistral-large` | Mistral Large |
| `deepseek` | DeepSeek V3 |
| `deepseek-r1` | DeepSeek R1 (reasoning) |
| `llama` | Meta LLaMA |
| `phi` | Microsoft Phi |
| `gemma` | Google Gemma |
| `qwen` | Alibaba Qwen |
| `qwen-coder` | Qwen for coding |
| `grok` | xAI Grok |
| `command-r` | Cohere Command R |
| `unity` | Unity AI |

---

## Image Models

```python
from polyai.providers.pollinations import IMAGE_MODELS
print(IMAGE_MODELS)
```

Key models:

| Model ID | Style |
|---|---|
| `flux` | High quality, versatile |
| `flux-realism` | Photorealistic |
| `flux-anime` | Anime style |
| `turbo` | Fast generation |
| `kontext` | Image editing |
| `nanobanana` | Experimental |
| `gptimage` | GPT-Image-1 |
| `gpt-image-2` | GPT-Image-2 |

---

## Supported Features

| Feature | Supported | Notes |
|---|:---:|---|
| Chat completions | ✅ | |
| Streaming | ✅ | SSE |
| Function calling | ✅ | |
| Structured output | ✅ | `json_mode=True` |
| Vision | ✅ | Via `openai` model |
| Embeddings | ✅ | |
| Image generation | ✅ | 20+ models |
| Image editing | ✅ | Via `kontext` model |
| Text-to-speech | ✅ | 6+ voices |
| Model listing | ✅ | |

---

## Usage Examples

### Basic Chat

```python
response = client.chat(
    provider="pollinations",
    model="openai",
    messages=[{"role": "user", "content": "What is the Eiffel Tower?"}],
    max_tokens=200,
)
print(response.text)
```

### Image Generation (API)

```python
img = client.generate_image(
    provider="pollinations",
    prompt="a photorealistic mountain lake at sunrise",
    model="flux",
    width=1024,
    height=768,
    seed=42,
)
print(img.url)
img.images[0].save("lake.png")
```

### Image Generation (Zero-Cost URL)

No API call needed — construct a URL directly:

```python
from polyai.providers.pollinations import PollinationsProvider

provider = client._get_provider("pollinations")
url = provider.generate_image_url(
    "a red apple on a white table",
    model="flux",
    width=512,
    height=512,
    seed=42,
    enhance=True,   # enhance prompt automatically
    nologo=True,    # remove Pollinations watermark
)
print(url)
# https://image.pollinations.ai/prompt/a%20red%20apple%20on%20a%20white%20table?model=flux&width=512&height=512&seed=42&enhance=true&nologo=true
```

Use in HTML:
```html
<img src="{{ url }}" alt="Generated image" />
```

### Text-to-Speech

```python
audio = client.text_to_speech(
    provider="pollinations",
    text="Hello! Welcome to PolyAI.",
    voice="alloy",         # alloy, echo, fable, onyx, nova, shimmer
    response_format="mp3",
    speed=1.0,             # 0.25 to 4.0
)
audio.save("welcome.mp3")
print(f"Size: {len(audio.content):,} bytes")
```

### Namespaced API

```python
pollinations = client.with_provider("pollinations")

# Chat
resp = pollinations.chat.complete(messages=[...], model="openai")

# Images
img = pollinations.images.generate("a sunset", model="flux")

# Audio
audio = pollinations.audio.speech("Hello!", voice="nova")

# Models
models = pollinations.models.list()
```

---

## Rate Limits

Pollinations is generous with anonymous access. For production:
- Use an `sk_*` API key for higher limits
- The image URL approach has no API rate limits

---

## Special: Direct Image URLs

Pollinations exposes images at stable URLs that work like CDN resources:

```
https://image.pollinations.ai/prompt/{encoded_prompt}?model={model}&width={w}&height={h}&seed={seed}
```

These URLs:
- Work anywhere an `<img>` tag is accepted
- Are cacheable by CDNs
- Require no API call from your server
- Change only if the prompt or parameters change
