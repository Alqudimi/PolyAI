# Changelog

All notable changes to **PolyAI** are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

## [1.0.0] — 2026-05-31

### Added

#### Core Architecture
- `Client` and `AsyncClient` top-level clients with a unified interface
- Provider adapter system (`BaseProvider`) for clean extensibility
- `ClientConfig` with full environment variable support and per-provider overrides
- Four-layer architecture: transport → auth → provider → resource
- Per-provider configuration via `ProviderConfig`

#### Providers
- **OVHcloud AI Endpoints** — full OpenAI-compatible adapter
  - Chat completions, streaming, function calling, structured output (JSON mode)
  - Vision (Qwen3-VL, LLaMA 3.2 Vision)
  - Embeddings (BGE-M3, BGE-large, nomic-embed, multilingual-e5)
  - Reranking (BGE-reranker family)
  - Image generation (Stable Diffusion XL, Flux)
  - Speech-to-text (Whisper large v3 turbo)
  - Model discovery via `/v1/models`
- **Pollinations.AI** — free, no-auth generative AI platform
  - Chat completions, streaming, function calling, vision, embeddings
  - 20+ image generation models (Flux, Kontext, NanoBanana, GPT-Image, etc.)
  - Text-to-speech (OpenAI TTS API compatible)
  - `generate_image_url()` — instant URL without any API call
- **mlvoca** — free Ollama-compatible LLM API
  - Chat completions and streaming for TinyLlama 1.1B and DeepSeek-R1 1.5B
  - Automatic OpenAI-to-Ollama message format conversion
- **DevToolbox API** — free Cloudflare Workers developer API
  - AI text generation, summarization, translation, code explanation, regex generation
  - Developer utilities: UUID, password, hash, lorem ipsum, QR code

#### HTTP Transport
- `SyncTransport` — thread-safe httpx-based sync client with connection pooling
- `AsyncTransport` — httpx.AsyncClient-based async client
- SSE streaming support (sync + async), binary response support

#### Reliability
- `RetryPolicy` with exponential backoff and full jitter
- Retry-After header parsing, configurable retry status codes

#### Authentication
- `BearerCredentials`, `ApiKeyHeaderCredentials`, `NoAuthCredentials`
- Secrets masked in all `__repr__` and log output

#### Type System
- `ChatResponse`, `ChatChunk`, `ChatDelta` — normalised chat types
- `EmbeddingResponse`, `Embedding` — with built-in cosine similarity and similarity matrix
- `ImageResponse`, `ImageData` — with `.save()` helper
- `AudioResponse`, `AudioTranscription`
- `Usage`, `Tool`, `ToolCall`, `FunctionDefinition`
- `SystemMessage`, `UserMessage`, `AssistantMessage`, `ToolMessage` convenience helpers

#### Streaming
- `StreamAccumulator` — sync chunk accumulation → `ChatResponse`
- `AsyncStreamAccumulator` — async variant

#### Resources (Namespaced API)
- `ChatResource`, `ImagesResource`, `AudioResource`, `EmbeddingsResource`,
  `DevToolsResource`, `ModelsResource` — sync + async variants

#### Utilities
- `build_vision_message()` — multimodal message construction (URL, base64, local path)
- `cosine_similarity()`, `truncate_messages()`, `count_tokens_approx()`,
  `merge_tool_call_chunks()`

#### Tests
- 138 unit tests across types, config, exceptions, retry, streaming, providers, client
- Tests run fully offline with mocked HTTP
- 4 integration test files for live provider testing

#### CI/CD
- GitHub Actions: multi-stage CI (lint → test matrix → security → integration → docs)
- GitHub Actions: automated release pipeline (build → PyPI → GitHub release)
- Dependabot: automated dependency updates
- Pre-commit hook configuration

#### Documentation
- Quickstart guide, provider reference, API reference, capability matrix

[Unreleased]: https://github.com/polyai-sdk/polyai-python/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/polyai-sdk/polyai-python/releases/tag/v1.0.0
