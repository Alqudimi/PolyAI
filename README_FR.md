<div align="center">

# PolyAI

**SDK Python de qualité production pour plusieurs fournisseurs d'IA.**

*Une interface. Quatre fournisseurs. Zéro compromis.*

[![CI](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml)
[![PyPI](https://badge.fury.io/py/polyai.svg)](https://badge.fury.io/py/polyai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Lire dans d'autres langues : [English](README.md) · [العربية](README_AR.md) · [Español](README_ES.md) · [Deutsch](README_DE.md) · [中文](README_ZH.md)*

</div>

---

## Qu'est-ce que PolyAI ?

**PolyAI** est un SDK Python de niveau production qui fournit une interface unique et unifiée pour interagir avec quatre fournisseurs d'IA. Au lieu d'apprendre quatre API différentes, vous n'en apprenez qu'une seule.

---

## Installation

```bash
pip install polyai
```

**Prérequis :** Python 3.9+ · Aucune clé API obligatoire

---

## Démarrage Rapide

```python
from polyai import Client

client = Client()

response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Quelle est la capitale de la France ?"}],
)
print(response.text)  # Paris
```

---

## Fournisseurs Supportés

| Fournisseur | Accès Gratuit | Authentification | Points forts |
|---|:---:|:---:|---|
| **OVHcloud AI Endpoints** | ✅ Anonyme (2 req/min) | Optionnel | 40+ modèles, hébergé en Europe |
| **Pollinations.AI** | ✅ Sans inscription | Optionnel | Images, TTS, 20+ LLMs |
| **mlvoca** | ✅ Toujours gratuit | ❌ Aucune | Non commercial, compatible Ollama |
| **DevToolbox API** | ✅ 100k req/jour | Optionnel | Outils IA développeur |

---

## Fonctionnalités

### Streaming

```python
for chunk in client.chat_stream(
    provider="pollinations",
    model="openai",
    messages=[{"role": "user", "content": "Raconte-moi une histoire."}],
):
    print(chunk.delta, end="", flush=True)
```

### Utilisation Asynchrone

```python
import asyncio
from polyai import AsyncClient

async def main():
    async with AsyncClient() as client:
        response = await client.chat(
            provider="ovhcloud",
            model="meta-llama-3_3-70b-instruct",
            messages=[{"role": "user", "content": "Bonjour !"}],
        )
        print(response.text)

asyncio.run(main())
```

### Gestion des Erreurs

```python
from polyai.exceptions import RateLimitError, UniversalAIError

try:
    response = client.chat(...)
except RateLimitError as e:
    print(f"Limite atteinte. Réessayez dans {e.retry_after}s")
except UniversalAIError as e:
    print(f"Erreur ({e.provider}, HTTP {e.status_code}): {e}")
```

---

## Licence

[MIT](LICENSE) — Copyright © 2026 [Abdulaziz Alqudimi](https://github.com/Alqudimi)
