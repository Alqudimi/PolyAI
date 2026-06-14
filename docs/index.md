# PolyAI Documentation

**Production-grade unified Python SDK for multiple AI providers.**

*One interface. Four providers. Zero compromise.*

---

## Quick Install

```bash
pip install polyai
```

## Quick Start

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

## Navigation

- **[Installation Guide](user/installation.md)** — Get up and running
- **[Configuration](user/configuration.md)** — API keys and settings
- **[Tutorials](tutorials/01-first-chat.md)** — Step-by-step guides
- **[API Reference](api/overview.md)** — Complete API docs
- **[Provider Docs](api/providers/ovhcloud.md)** — Per-provider guides
- **[Architecture](dev/architecture.md)** — Internal design
- **[Contributing](../CONTRIBUTING.md)** — How to contribute

---

*Repository: [https://github.com/Alqudimi/PolyAI](https://github.com/Alqudimi/PolyAI)*
*Author: Abdulaziz Alqudimi*
