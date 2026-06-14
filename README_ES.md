<div align="center">

# PolyAI

**SDK de Python de producción para múltiples proveedores de IA.**

*Una interfaz. Cuatro proveedores. Sin compromisos.*

[![CI](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml)
[![PyPI](https://badge.fury.io/py/polyai.svg)](https://badge.fury.io/py/polyai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Leer en otros idiomas: [English](README.md) · [العربية](README_AR.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [中文](README_ZH.md)*

</div>

---

## ¿Qué es PolyAI?

**PolyAI** es un SDK de Python de nivel productivo que proporciona una interfaz única y unificada para interactuar con cuatro proveedores de IA. En lugar de aprender cuatro APIs diferentes, aprendes solo una.

---

## Instalación

```bash
pip install polyai
```

**Requisitos:** Python 3.9+ · No se requieren claves API obligatorias

---

## Inicio Rápido

```python
from polyai import Client

client = Client()

response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "¿Cuál es la capital de Francia?"}],
)
print(response.text)  # París
```

---

## Proveedores Soportados

| Proveedor | Capa Gratuita | Autenticación | Destacados |
|---|:---:|:---:|---|
| **OVHcloud AI Endpoints** | ✅ Anónimo (2 req/min) | Opcional | 40+ modelos, alojado en Europa |
| **Pollinations.AI** | ✅ Sin registro | Opcional | Imágenes, TTS, 20+ LLMs |
| **mlvoca** | ✅ Siempre gratuito | ❌ Ninguna | No comercial, compatible con Ollama |
| **DevToolbox API** | ✅ 100k req/día | Opcional | Herramientas de IA para desarrolladores |

---

## Características

### Streaming

```python
for chunk in client.chat_stream(
    provider="pollinations",
    model="openai",
    messages=[{"role": "user", "content": "Cuéntame una historia."}],
):
    print(chunk.delta, end="", flush=True)
```

### Uso Asíncrono

```python
import asyncio
from polyai import AsyncClient

async def main():
    async with AsyncClient() as client:
        response = await client.chat(
            provider="ovhcloud",
            model="meta-llama-3_3-70b-instruct",
            messages=[{"role": "user", "content": "¡Hola!"}],
        )
        print(response.text)

asyncio.run(main())
```

### Generación de Imágenes

```python
img = client.generate_image(
    provider="pollinations",
    prompt="ciudad futurista de noche, arte digital",
    model="flux",
)
img.images[0].save("output.png")
```

### Manejo de Errores

```python
from polyai.exceptions import RateLimitError, UniversalAIError

try:
    response = client.chat(...)
except RateLimitError as e:
    print(f"Límite de tasa. Reintentar en {e.retry_after}s")
except UniversalAIError as e:
    print(f"Error ({e.provider}, HTTP {e.status_code}): {e}")
```

---

## Licencia

[MIT](LICENSE) — Copyright © 2026 [Abdulaziz Alqudimi](https://github.com/Alqudimi)
