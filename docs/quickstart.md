# Quick Start

Get up and running with **PolyAI** in under 5 minutes.

## Installation

```bash
pip install polyai
```

Or with optional development extras:

```bash
pip install "polyai[dev]"
```

## Minimal Example

No API keys are required for OVHcloud (anonymous free tier), Pollinations.AI,
mlvoca, or DevToolbox. Install and run:

```python
from polyai import Client

client = Client()

response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Hello, who are you?"}],
)
print(response.text)
```

## Setting Up Credentials

For higher rate limits and access to more models, set API keys as environment variables:

```bash
export OVHCLOUD_API_KEY="your-ovhcloud-key"
export POLLINATIONS_API_KEY="sk_your_pollinations_key"
export DEVTOOLBOX_API_KEY="dtb_your_devtoolbox_key"
```

Or pass them directly:

```python
client = Client(
    ovhcloud_api_key="your-key",
    pollinations_api_key="sk_...",
)
```

## Streaming

```python
for chunk in client.chat_stream(
    provider="pollinations",
    model="openai",
    messages=[{"role": "user", "content": "Tell me a short story."}],
):
    print(chunk.delta, end="", flush=True)
```

## Async

```python
import asyncio
from polyai import AsyncClient

async def main():
    async with AsyncClient() as client:
        response = await client.chat(
            provider="ovhcloud",
            model="meta-llama-3_3-70b-instruct",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response.text)

asyncio.run(main())
```

## Image Generation

```python
img = client.generate_image(
    provider="pollinations",
    prompt="a futuristic cityscape at night, digital art",
    model="flux",
)
print(img.url)
```

## Embeddings

```python
result = client.embed(
    provider="ovhcloud",
    input=["Hello world", "Bonjour monde"],
    model="bge-m3",
)
similarity = result.embeddings[0].cosine_similarity(result.embeddings[1])
print(f"Cosine similarity: {similarity:.4f}")
```

## Next Steps

- [Providers Reference](providers.md) — capabilities, models, and authentication for each provider
- [API Reference](api-reference.md) — complete method and type documentation
- [Capability Matrix](capability-matrix.md) — side-by-side provider feature comparison
