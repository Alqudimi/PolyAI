# PolyAI Wiki

> **Repository:** https://github.com/Alqudimi/PolyAI
> **Author:** Abdulaziz Alqudimi

Welcome to the PolyAI documentation wiki. This is the central hub for all documentation.

---

## Getting Started

| Resource | Description |
|---|---|
| [Installation](Installation) | Install PolyAI in any environment |
| [Quick Start](Quick-Start) | Working code in 2 minutes |
| [Configuration](Configuration) | API keys, timeouts, retries |
| [First Project Tutorial](Tutorials/01-First-Chat) | Step-by-step beginner guide |

---

## User Guide

| Resource | Description |
|---|---|
| [Best Practices](Best-Practices) | Patterns for reliable AI apps |
| [Security Best Practices](Security-Best-Practices) | Keep your keys and data safe |
| [Performance Guide](Performance) | Faster responses, lower latency |
| [Production Guide](Production-Guide) | Deploy to production |
| [Migration Guide](Migration-Guide) | Upgrade between versions |

---

## Tutorials

| Tutorial | Level | Time |
|---|---|---|
| [01 — Your First Chat](Tutorials/01-First-Chat) | Beginner | 5 min |
| [02 — Streaming](Tutorials/02-Streaming) | Beginner | 10 min |
| [03 — Function Calling](Tutorials/03-Function-Calling) | Intermediate | 20 min |
| [04 — Vision (Multimodal)](Tutorials/04-Vision) | Intermediate | 15 min |
| [05 — Embeddings & Semantic Search](Tutorials/05-Embeddings) | Intermediate | 20 min |
| [06 — Production Deployment](Tutorials/06-Production) | Advanced | 30 min |
| [07 — Adding a Custom Provider](Tutorials/07-Custom-Provider) | Expert | 45 min |

---

## API Reference

| Reference | Description |
|---|---|
| [Client API](API-Reference/Client) | All `Client` methods |
| [AsyncClient API](API-Reference/AsyncClient) | All `AsyncClient` methods |
| [Exceptions](API-Reference/Exceptions) | Complete exception hierarchy |
| [Types](API-Reference/Types) | Response types and data models |
| [OVHcloud Provider](API-Reference/Providers/OVHcloud) | OVHcloud-specific docs |
| [Pollinations Provider](API-Reference/Providers/Pollinations) | Pollinations-specific docs |
| [mlvoca Provider](API-Reference/Providers/mlvoca) | mlvoca-specific docs |
| [DevToolbox Provider](API-Reference/Providers/DevToolbox) | DevToolbox-specific docs |

---

## Developer Guide

| Resource | Description |
|---|---|
| [Architecture](Developer/Architecture) | Internal design and data flow |
| [Adding a Provider](Developer/Adding-Providers) | Step-by-step provider guide |
| [Testing Guide](Developer/Testing) | Unit + integration tests |
| [Coding Standards](Developer/Coding-Standards) | Style, types, docstrings |

---

## Project

| Document | Description |
|---|---|
| [Features](Features) | Complete feature list with examples |
| [Roadmap](Roadmap) | Planned features and milestones |
| [Changelog](Changelog) | Version history |
| [FAQ](FAQ) | Frequently asked questions |
| [Troubleshooting](Troubleshooting) | Common issues and fixes |
| [Security Policy](Security-Policy) | Vulnerability reporting |
| [Contributing](Contributing) | How to contribute |
| [Governance](Governance) | Project structure and decisions |
| [Glossary](Glossary) | Definitions of terms |

---

## Quick Code Samples

### Install
```bash
pip install polyai
```

### Basic Chat
```python
from polyai import Client
client = Client()
response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.text)
```

### Streaming
```python
for chunk in client.chat_stream(provider="ovhcloud", model="llama-3.1-8b-instruct", messages=[...]):
    print(chunk.delta, end="", flush=True)
```

### Async
```python
import asyncio
from polyai import AsyncClient

async def main():
    async with AsyncClient() as client:
        r = await client.chat(provider="ovhcloud", model="llama-3.1-8b-instruct", messages=[...])
        print(r.text)

asyncio.run(main())
```

---

## Support

- **Questions:** [GitHub Discussions](https://github.com/Alqudimi/PolyAI/discussions)
- **Bugs:** [GitHub Issues](https://github.com/Alqudimi/PolyAI/issues)
- **Security:** [SECURITY.md](https://github.com/Alqudimi/PolyAI/blob/main/SECURITY.md) (private)
