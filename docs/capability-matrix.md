# Provider Capability Matrix

| Feature | OVHcloud | Pollinations | mlvoca | DevToolbox |
|---|:---:|:---:|:---:|:---:|
| **Chat completions** | ✅ | ✅ | ✅ | ✅ |
| **Streaming (SSE)** | ✅ | ✅ | ✅ | ❌ |
| **Function / tool calling** | ✅ | ✅ | ❌ | ❌ |
| **Structured output (JSON mode)** | ✅ | ✅ | ❌ | ❌ |
| **Vision (multimodal image input)** | ✅ | ✅ | ❌ | ❌ |
| **Embeddings** | ✅ | ✅ | ❌ | ❌ |
| **Reranking** | ✅ | ❌ | ❌ | ❌ |
| **Image generation** | ✅ | ✅ | ❌ | ❌ |
| **Image editing** | ❌ | ✅ | ❌ | ❌ |
| **Text-to-speech (TTS)** | ❌ | ✅ | ❌ | ❌ |
| **Speech-to-text (STT)** | ✅ | ❌ | ❌ | ❌ |
| **Models endpoint** | ✅ | ✅ | ❌¹ | ❌¹ |
| **Batch jobs** | ❌ | ❌ | ❌ | ❌ |
| **Async support** | ✅ | ✅ | ✅ | ✅ |
| **Auth required** | ❌² | ❌² | ❌ | ❌² |
| **Rate limits** | 2/min (free) | Varies | None | 100k/day |
| **Commercial use** | ✅ | ✅ | ❌ | ✅ |

**Notes:**
1. mlvoca and DevToolbox return a static built-in model list
2. Anonymous / keyless access available with some limitations

## Authentication Summary

| Provider | Env Variable | Notes |
|---|---|---|
| OVHcloud | `OVHCLOUD_API_KEY` | Empty string = anonymous (2 req/min) |
| Pollinations | `POLLINATIONS_API_KEY` | `sk_*` (backend) or `pk_*` (frontend); omit for anonymous |
| mlvoca | *(none)* | Always free, non-commercial only |
| DevToolbox | `DEVTOOLBOX_API_KEY` | `dtb_*` prefix; omit for free 100k/day tier |

## Model Count

| Provider | LLMs | Vision | Embeddings | Images | Audio |
|---|:---:|:---:|:---:|:---:|:---:|
| OVHcloud | 15+ | 3 | 4 | 4 | 1 |
| Pollinations | 20+ | via OpenAI | via endpoint | 20+ | 4+ voices |
| mlvoca | 2 | — | — | — | — |
| DevToolbox | 1 (AI gen) | — | — | — | — |

## Performance Characteristics

| Provider | Latency | Throughput | Streaming | Notes |
|---|---|---|---|---|
| OVHcloud | Low–Medium | High (paid) | ✅ SSE | EU data sovereignty |
| Pollinations | Medium | Medium | ✅ SSE | Free, global CDN |
| mlvoca | High | Low | ✅ SSE | Hardware limited |
| DevToolbox | Low | Medium | ❌ | Cloudflare edge |
