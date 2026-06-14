# Compatibility Matrix

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Python Version Compatibility

| Python Version | PolyAI 1.x | Notes |
|---|:---:|---|
| 3.12 | ✅ | Fully supported |
| 3.11 | ✅ | Primary development version |
| 3.10 | ✅ | Fully supported |
| 3.9 | ✅ | Minimum supported version |
| 3.8 | ❌ | Not supported (uses 3.9+ syntax) |
| 3.7 and below | ❌ | Not supported |

---

## Operating System Compatibility

| OS | Status | Notes |
|---|:---:|---|
| Ubuntu 22.04+ | ✅ | Primary CI environment |
| Ubuntu 20.04 | ✅ | Tested in CI |
| macOS 13+ | ✅ | Tested in CI |
| macOS 12 | ✅ | Should work |
| Windows 11 | ✅ | Tested in CI |
| Windows 10 | ✅ | Should work |
| Alpine Linux | ✅ | Tested (Docker) |
| Other Linux | ✅ | Should work if Python 3.9+ available |

---

## Dependency Compatibility

### httpx

| httpx version | PolyAI 1.x |
|---|:---:|
| 0.28.x | ✅ Tested |
| 0.27.x | ✅ Compatible |
| 0.26.x | ✅ Compatible |
| 0.25.x | ✅ Minimum version |
| < 0.25 | ❌ Not supported |

---

## Provider API Compatibility

PolyAI follows provider APIs as they are. When providers update their APIs, PolyAI will be updated accordingly.

| Provider | API Version Tracked | Last Verified |
|---|---|---|
| OVHcloud AI Endpoints | OpenAI-compatible v1 | 2026-05 |
| Pollinations.AI | `/v1` (OpenAI-compat) | 2026-05 |
| mlvoca | Ollama `/api/generate` | 2026-05 |
| DevToolbox API | Cloudflare Workers v1 | 2026-05 |

---

## Runtime Environment Compatibility

| Environment | Status | Notes |
|---|:---:|---|
| Standard Python scripts | ✅ | Fully supported |
| Jupyter Notebooks | ✅ | Use `nest_asyncio` for async |
| FastAPI | ✅ | Use `AsyncClient` |
| Django | ✅ | Use sync `Client` |
| Flask | ✅ | Use sync `Client` |
| AWS Lambda | ✅ | Cold start: ~50ms |
| Google Cloud Functions | ✅ | Tested |
| Docker containers | ✅ | Tested on Alpine + Ubuntu |
| GitHub Actions | ✅ | Used in own CI |
| Kubernetes pods | ✅ | No special config needed |

---

## Async Framework Compatibility

| Framework | Status | Notes |
|---|:---:|---|
| asyncio (stdlib) | ✅ | Primary async framework |
| anyio | ✅ | httpx uses anyio internally |
| uvicorn + FastAPI | ✅ | Tested |
| Gunicorn (sync workers) | ✅ | Use sync `Client` |
| Celery | ✅ | Use sync `Client` in tasks |
| trio | ⚠️ | Not explicitly tested |

---

## Breaking Change History

| Version | Breaking Changes |
|---|---|
| 1.0.0 | Initial release — no breaking changes |

Future breaking changes will be documented here with migration instructions.
