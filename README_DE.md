<div align="center">

# PolyAI

**Produktionsreifes Python SDK für mehrere KI-Anbieter.**

*Eine Schnittstelle. Vier Anbieter. Kein Kompromiss.*

[![CI](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml)
[![PyPI](https://badge.fury.io/py/polyai.svg)](https://badge.fury.io/py/polyai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*In anderen Sprachen lesen: [English](README.md) · [العربية](README_AR.md) · [Español](README_ES.md) · [Français](README_FR.md) · [中文](README_ZH.md)*

</div>

---

## Was ist PolyAI?

**PolyAI** ist ein produktionsreifes Python SDK, das eine einzige, einheitliche Schnittstelle für vier KI-Anbieter bietet. Statt vier verschiedene APIs zu lernen, lernt man nur eine.

---

## Installation

```bash
pip install polyai
```

**Voraussetzungen:** Python 3.9+ · Keine obligatorischen API-Schlüssel

---

## Schnellstart

```python
from polyai import Client

client = Client()

response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Was ist die Hauptstadt von Frankreich?"}],
)
print(response.text)  # Paris
```

---

## Unterstützte Anbieter

| Anbieter | Kostenlose Stufe | Authentifizierung | Highlights |
|---|:---:|:---:|---|
| **OVHcloud AI Endpoints** | ✅ Anonym (2 Req/Min) | Optional | 40+ Modelle, EU-gehostet |
| **Pollinations.AI** | ✅ Ohne Anmeldung | Optional | Bilder, TTS, 20+ LLMs |
| **mlvoca** | ✅ Immer kostenlos | ❌ Keine | Nicht-kommerziell, Ollama-kompatibel |
| **DevToolbox API** | ✅ 100k Req/Tag | Optional | KI-Entwicklerwerkzeuge |

---

## Funktionen

### Streaming

```python
for chunk in client.chat_stream(
    provider="pollinations",
    model="openai",
    messages=[{"role": "user", "content": "Erzähl mir eine Geschichte."}],
):
    print(chunk.delta, end="", flush=True)
```

### Asynchrone Nutzung

```python
import asyncio
from polyai import AsyncClient

async def main():
    async with AsyncClient() as client:
        response = await client.chat(
            provider="ovhcloud",
            model="meta-llama-3_3-70b-instruct",
            messages=[{"role": "user", "content": "Hallo!"}],
        )
        print(response.text)

asyncio.run(main())
```

---

## Lizenz

[MIT](LICENSE) — Copyright © 2026 [Abdulaziz Alqudimi](https://github.com/Alqudimi)
