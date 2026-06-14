# PolyAI — Project Overview

> **Repository:** https://github.com/Alqudimi/PolyAI
> **Author:** Abdulaziz Alqudimi
> **License:** MIT
> **Status:** Production-ready (v1.0.0)

---

## Executive Summary

PolyAI is an open-source Python SDK that solves a common pain point for AI developers: **the fragmentation of AI provider APIs**. Each provider — OVHcloud, Pollinations, mlvoca, DevToolbox — has its own authentication scheme, HTTP format, response structure, error codes, and streaming protocol.

PolyAI abstracts all of this into a single, consistent, production-hardened interface.

---

## Problem Statement

Modern AI applications frequently need to:

- **Switch providers** based on cost, capability, or availability
- **Fall back** when a provider is down or rate-limited
- **Compare** outputs across providers for quality evaluation
- **Route** different request types to specialized providers

Without a unification layer, each of these scenarios requires significant boilerplate code that must be maintained across every provider integration.

---

## Solution

PolyAI provides:

1. **One unified `Client`** — `client.chat(provider="...", ...)` works identically across all providers
2. **Normalised response types** — `response.text`, `response.usage`, `response.tool_calls` are always the same shape
3. **Built-in reliability** — automatic retries with exponential backoff and jitter
4. **Full async support** — `AsyncClient` for non-blocking I/O in server contexts
5. **Type safety** — complete Python type annotations throughout

---

## Design Principles

| Principle | Implementation |
|---|---|
| **Consistency** | Every provider returns the same `ChatResponse` type |
| **Transparency** | Raw provider responses always available via `.raw` |
| **Safety** | Secrets are masked in all repr/log output |
| **Reliability** | Retries, timeouts, connection pooling built-in |
| **Extensibility** | Add a provider by implementing `BaseProvider` (5 methods) |
| **Testability** | All HTTP calls go through an injectable transport layer |

---

## Supported Providers

### OVHcloud AI Endpoints
- **Type:** OpenAI-compatible REST + SSE
- **Models:** 40+ (LLMs, vision, embeddings, rerankers, image gen, audio)
- **Auth:** Bearer token (anonymous free tier available)
- **Base URL:** `https://oai.endpoints.kepler.ai.cloud.ovh.net/v1`
- **Use case:** EU-hosted open-source models, GDPR compliance

### Pollinations.AI
- **Type:** OpenAI-compatible REST + SSE
- **Models:** 20+ LLMs, 20+ image models, TTS
- **Auth:** None (or optional `sk_*` / `pk_*` keys)
- **Use case:** Free image generation, TTS, broad model selection

### mlvoca
- **Type:** Ollama-compatible REST + SSE
- **Models:** TinyLlama 1.1B, DeepSeek-R1 1.5B
- **Auth:** None — always free
- **License:** Non-commercial use only
- **Use case:** Lightweight LLM calls, no signup required

### DevToolbox API
- **Type:** Custom REST (Cloudflare Workers)
- **Models:** 1 AI generation model + developer utilities
- **Auth:** None (or optional `dtb_*` key for unlimited)
- **Use case:** Summarization, translation, code explanation, developer tools

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Application                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                ┌──────────▼──────────┐
                │   Client / AsyncClient  │
                │   (unified public API)  │
                └──────────┬──────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌─────▼───────┐
    │  OVHcloud   │ │Pollinations │ │   mlvoca    │  ...
    │  Provider   │ │  Provider   │ │  Provider   │
    └──────┬──────┘ └──────┬──────┘ └─────┬───────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                ┌──────────▼──────────┐
                │   SyncTransport /   │
                │   AsyncTransport    │
                │   (httpx, retry)    │
                └─────────────────────┘
```

---

## Key Technical Decisions

### httpx over requests
`httpx` provides both sync and async HTTP in the same package, eliminating the need for `aiohttp` as a separate async dependency. It also has native streaming and HTTP/2 support.

### Exponential backoff with full jitter
Rather than fixed retry delays, PolyAI uses exponential backoff with full jitter (random delay within `[0, 2^attempt * base]`). This prevents the "thundering herd" problem when many clients retry simultaneously.

### Provider adapter pattern
Each provider is an implementation of `BaseProvider`, a five-method abstract class. This enforces a consistent contract and makes adding new providers straightforward.

### Secrets masking
All credential objects implement `__repr__` to mask the actual value. This prevents accidental secret leakage in logs and debug output.

---

## Project Stats

| Metric | Value |
|---|---|
| Lines of code (SDK) | ~4,000 |
| Unit tests | 138 |
| Test coverage | >95% |
| Type coverage | 100% |
| Python support | 3.9, 3.10, 3.11, 3.12 |
| OS support | Linux, macOS, Windows |
| Dependencies | 1 (httpx) |
| Dev dependencies | 8 |

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for upcoming features and milestones.

---

## Links

- **Repository:** https://github.com/Alqudimi/PolyAI
- **PyPI:** https://pypi.org/p/polyai
- **Issues:** https://github.com/Alqudimi/PolyAI/issues
- **Author:** [Abdulaziz Alqudimi](https://github.com/Alqudimi)
