# PolyAI Roadmap

> **Repository:** https://github.com/Alqudimi/PolyAI
> **Maintained by:** Abdulaziz Alqudimi

This document describes the planned direction for PolyAI. Items are grouped by milestone. Priorities may shift based on community feedback — open an issue to influence the roadmap.

---

## ✅ v1.0.0 — Released (2026-05-31)

### Core
- [x] Unified `Client` and `AsyncClient` across all 4 providers
- [x] Provider adapter system (`BaseProvider`)
- [x] `ClientConfig` with environment variable support
- [x] `ProviderConfig` per-provider overrides

### Providers
- [x] OVHcloud AI Endpoints (full OpenAI-compatible)
- [x] Pollinations.AI (chat, images, TTS, embeddings)
- [x] mlvoca (Ollama-format chat + streaming)
- [x] DevToolbox API (AI utilities + developer tools)

### Features
- [x] Chat completions (sync + async)
- [x] Real-time streaming (SSE)
- [x] Function calling / tool use
- [x] Structured output (JSON mode)
- [x] Vision / multimodal input
- [x] Embeddings + cosine similarity
- [x] Image generation
- [x] Text-to-speech
- [x] Speech-to-text (OVHcloud Whisper)
- [x] Namespaced resource API (`client.with_provider(...)`)
- [x] `StreamAccumulator` + `AsyncStreamAccumulator`
- [x] Exponential backoff retry with full jitter
- [x] Full type annotations (Python 3.9+)
- [x] 138 unit tests, fully offline

### Infrastructure
- [x] CI/CD: 7 GitHub Actions workflows
- [x] Security scanning (Bandit, CodeQL, TruffleHog, pip-audit)
- [x] Nightly integration tests
- [x] Dependabot (Python deps + GitHub Actions)
- [x] Pre-commit hooks

---

## 🚧 v1.1.0 — In Progress

### New Features
- [ ] **Reranking resource** — expose OVHcloud reranking endpoint via `client.rerank()`
- [ ] **Batch embedding** — chunked embedding for large document sets
- [ ] **Middleware hooks** — `on_request` / `on_response` callbacks for logging, metrics
- [ ] **Request ID propagation** — pass `X-Request-ID` through to provider and surface on response
- [ ] **Response caching** — optional in-memory + disk cache layer

### Provider Improvements
- [ ] OVHcloud: Audio transcription via `client.transcribe()`
- [ ] Pollinations: Image editing endpoint
- [ ] DevToolbox: QR code generation in `DevToolsResource`

### Developer Experience
- [ ] `polyai` CLI — quick chat from the command line: `polyai chat "hello"`
- [ ] Debug mode — `Client(debug=True)` prints redacted request/response logs

---

## 📅 v1.2.0 — Planned Q3 2026

### New Providers
- [ ] **Groq** — ultra-fast inference (Llama, Mixtral, Whisper)
- [ ] **Together AI** — open-source model hosting
- [ ] **Mistral AI** — Mistral + Codestral

### Features
- [ ] **Structured output with Pydantic** — `client.chat_parsed(response_model=MyModel)`
- [ ] **Conversation history** — built-in message store with sliding window
- [ ] **Token budget management** — auto-truncate messages to fit context window
- [ ] **Async streaming accumulate** — `client.chat_accumulate_async()`

### Infrastructure
- [ ] MkDocs documentation site deployed to GitHub Pages
- [ ] Benchmarks dashboard (GitHub Pages)
- [ ] Plugin system for custom providers without modifying source

---

## 🔮 v2.0.0 — Future

### Major Features
- [ ] **Agents framework** — multi-step agentic loops with tool orchestration
- [ ] **Prompt templates** — Jinja2-based prompt management
- [ ] **Observability** — OpenTelemetry tracing integration
- [ ] **Rate limit budget** — per-provider quota tracking across multiple clients
- [ ] **Webhooks support** — async completion callbacks
- [ ] **Model router** — intelligent provider selection based on capability and cost

### New Providers
- [ ] Google Gemini
- [ ] Anthropic Claude
- [ ] Cohere
- [ ] Replicate
- [ ] Hugging Face Inference API

### Breaking Changes (semver major)
- Provider registry will move to a plugin-based discovery mechanism
- `ClientConfig` fields will be validated with Pydantic v2

---

## 💡 Community Ideas

These are community-requested features under consideration:

- [ ] LangChain integration layer
- [ ] LlamaIndex integration layer
- [ ] FastAPI middleware (`PolyAIMiddleware`)
- [ ] Django app (`django-polyai`)
- [ ] Jupyter notebook helpers

Have an idea? [Open a feature request](https://github.com/Alqudimi/PolyAI/issues/new?template=feature_request.yml).

---

## Version Policy

PolyAI follows [Semantic Versioning](VERSIONING_POLICY.md):
- **Patch** (`1.0.x`) — bug fixes, documentation, CI
- **Minor** (`1.x.0`) — new features, new providers, backward-compatible
- **Major** (`x.0.0`) — breaking API changes

See [VERSIONING_POLICY.md](VERSIONING_POLICY.md) for details.
