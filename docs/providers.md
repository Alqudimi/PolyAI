# Provider Reference

## OVHcloud AI Endpoints

| Property | Value |
|---|---|
| Base URL | `https://oai.endpoints.kepler.ai.cloud.ovh.net/v1` |
| Protocol | OpenAI-compatible REST + SSE |
| Auth | Bearer token (empty = anonymous) |
| Free tier | 2 requests/min per IP per model (no signup) |
| Paid tier | 400 req/min per project per model |
| Models | 40+ (LLMs, vision, embeddings, rerankers, images, audio) |

### Authentication

```bash
export OVHCLOUD_API_KEY="your-key"
```

Generate a key: *OVHcloud Manager → Public Cloud → AI & Machine Learning → AI Endpoints → API Keys*

Anonymous (free, rate-limited):
```python
client = Client()  # OVHCLOUD_API_KEY not set → anonymous
```

### Key Models

| Category | Model ID |
|---|---|
| General LLM | `meta-llama-3_3-70b-instruct` |
| Small LLM | `llama-3.1-8b-instruct` |
| Coding | `codestral-22b-v0.1` |
| Reasoning | `deepseek-r1-distill-llama-70b` |
| Vision | `Qwen/Qwen3-VL-8B-Instruct` |
| Embedding | `bge-m3`, `bge-large-en-v1.5` |
| Reranker | `bge-reranker-v2-m3` |
| Image | `flux-1-dev`, `stable-diffusion-xl-base-1.0` |
| Audio STT | `whisper-large-v3-turbo` |

### Supported Features

✅ Chat completions  ✅ Streaming  ✅ Function calling  ✅ Structured output
✅ Vision  ✅ Embeddings  ✅ Reranking  ✅ Image generation  ✅ Models endpoint
❌ TTS  ❌ Batch jobs

---

## Pollinations.AI

| Property | Value |
|---|---|
| Primary URL | `https://gen.pollinations.ai/v1` |
| Image URL | `https://image.pollinations.ai/prompt/{prompt}` |
| Protocol | OpenAI-compatible REST + SSE |
| Auth | None (anonymous) or `sk_*` / `pk_*` keys |
| Free tier | All core features, anonymous, no signup |

### Authentication

Anonymous (no key required):
```python
client = Client()  # works without any key
```

With key (more models + higher limits):
```bash
export POLLINATIONS_API_KEY="sk_your_key"
```

### Text Models

`openai`, `openai-fast`, `openai-large`, `claude`, `claude-large`, `mistral`,
`mistral-large`, `deepseek`, `deepseek-r1`, `llama`, `phi`, `gemma`, `qwen`,
`qwen-coder`, `grok`, `command-r`, `unity`, and more.

### Image Models

`flux`, `flux-realism`, `flux-anime`, `turbo`, `kontext`, `nanobanana`,
`seedream`, `gptimage`, `gpt-image-2`, `wan-image`, `zimage`, and more.

### Unique Feature: Direct Image URLs

No API call needed — build a URL, embed it anywhere:

```python
from universal_ai.providers.pollinations import PollinationsProvider

provider = client._get_provider("pollinations")
url = provider.generate_image_url(
    "a sunset over the ocean",
    model="flux",
    width=1280,
    height=720,
    seed=42,
)
```

### Supported Features

✅ Chat  ✅ Streaming  ✅ Function calling  ✅ Vision  ✅ Embeddings
✅ Image generation  ✅ TTS  ✅ Image editing  ✅ Models endpoint

---

## mlvoca

| Property | Value |
|---|---|
| Base URL | `https://mlvoca.com` |
| Endpoint | `POST /api/generate` |
| Protocol | Ollama-compatible |
| Auth | None — completely free |
| Rate limits | None (hardware limited) |
| License | Non-commercial use only |

### Available Models

| Model | Description |
|---|---|
| `tinyllama` | TinyLlama 1.1B — fast, lightweight |
| `deepseek-r1:1.5b` | DeepSeek R1 1.5B — reasoning with `<think>` tokens |

### Notes

- No API key, no account, no rate limits
- **Non-commercial use only** (see [mlvoca terms](https://mlvoca.com))
- Responses may be slow during high usage
- The SDK transparently converts OpenAI-style messages to Ollama prompt format
- `deepseek-r1:1.5b` outputs `<think>...</think>` reasoning tokens — these are preserved in `.text`

### Supported Features

✅ Chat  ✅ Streaming
❌ Function calling  ❌ Vision  ❌ Embeddings  ❌ Image generation  ❌ TTS

---

## DevToolbox API

| Property | Value |
|---|---|
| Base URL | `https://devtoolbox-api.devtoolbox-api.workers.dev` |
| Platform | Cloudflare Workers |
| Auth | None (free) or `X-API-Key: dtb_*` (unlimited) |
| Rate limits | 100,000 requests/day (free) |

### Authentication

Free (no key):
```python
client = Client()
```

Premium (unlimited):
```bash
export DEVTOOLBOX_API_KEY="dtb_your_key"
```

### AI Endpoints

| Endpoint | SDK Method | Description |
|---|---|---|
| `POST /ai/generate` | `client.chat(provider="devtoolbox", ...)` | General AI text generation |
| `POST /ai/summarize` | `devtools.summarize(text)` | Text summarization |
| `POST /ai/translate` | `devtools.translate(text, "fr")` | Language translation |
| `POST /ai/explain-code` | `devtools.explain_code(code)` | Code explanation |
| `POST /ai/generate-regex` | `devtools.generate_regex(description)` | Regex from natural language |

### Developer Utility Endpoints

| Method | Description |
|---|---|
| `devtools.generate_uuid()` | UUID v4 |
| `devtools.generate_password(length, symbols)` | Secure password |
| `devtools.hash(algorithm, input)` | Cryptographic hash |
| `devtools.lorem_ipsum(paragraphs)` | Placeholder text |
| `devtools.qr_code(data, size)` | QR code PNG bytes |

### Supported Features

✅ Chat (AI generate)  ✅ Summarization  ✅ Translation  ✅ Code explanation
✅ Regex generation  ✅ Developer utilities
❌ Streaming  ❌ Embeddings  ❌ Vision  ❌ Image generation  ❌ TTS
