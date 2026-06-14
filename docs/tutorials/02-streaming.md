# Tutorial 2: Real-Time Streaming

> **Level:** Beginner-Intermediate | **Time:** 10 minutes
> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Goals

- Stream AI responses token-by-token
- Build a live typing effect
- Accumulate a stream into a complete response
- Use async streaming

---

## Prerequisites

- Completed [Tutorial 1](01-first-chat.md)
- PolyAI installed

---

## What is Streaming?

Without streaming, you wait for the entire response before seeing anything — like waiting for a web page to fully load before any content appears.

With streaming, tokens appear as they're generated — like a typewriter.

```
Without streaming: [5 seconds of waiting...] → "Artificial intelligence is the simulation of..."
With streaming:    Artif → icial → intel → ligence → is → the...   (0.5s to first word)
```

---

## Step 1: Basic Streaming

```python
from polyai import Client

client = Client()

print("AI: ", end="", flush=True)

for chunk in client.chat_stream(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Tell me a short story about a robot."}],
    max_tokens=150,
):
    print(chunk.delta, end="", flush=True)

print()  # final newline
```

### Key Points

- `chat_stream()` returns an **iterator** — you loop over it
- `chunk.delta` is the new text in this chunk (usually 1-5 tokens)
- `end=""` prevents Python from adding newlines between chunks
- `flush=True` forces immediate output — critical for the live effect

---

## Step 2: Detecting Completion

Each chunk has a `finish_reason` that's `None` until the final chunk:

```python
from polyai import Client

client = Client()

full_text = ""
finish_reason = None

for chunk in client.chat_stream(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Name 5 planets."}],
    max_tokens=100,
):
    print(chunk.delta, end="", flush=True)
    full_text += chunk.delta
    if chunk.finish_reason:
        finish_reason = chunk.finish_reason

print(f"\n\n--- Done ---")
print(f"Finish reason: {finish_reason}")  # "stop" or "length"
print(f"Total characters: {len(full_text)}")
```

---

## Step 3: Accumulate Stream → Complete Response

If you need both the live streaming effect AND the final `ChatResponse` with token counts:

```python
from polyai import Client

client = Client()

# Streams and accumulates in one call
response = client.chat_accumulate(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Explain photosynthesis simply."}],
    max_tokens=200,
    on_chunk=lambda chunk: print(chunk.delta, end="", flush=True),  # callback
)

print(f"\n\n--- Stream complete ---")
print(f"Full text length: {len(response.text)} chars")
print(f"Total tokens: {response.usage.total_tokens}")
```

---

## Step 4: Streaming Across Providers

```python
from polyai import Client
from polyai.exceptions import FeatureNotSupportedError, UniversalAIError

client = Client()

providers_with_streaming = [
    ("ovhcloud",     "llama-3.1-8b-instruct"),
    ("pollinations", "openai"),
    ("mlvoca",       "tinyllama"),
    # devtoolbox does NOT support streaming
]

question = [{"role": "user", "content": "Say 'hello' three times."}]

for provider, model in providers_with_streaming:
    print(f"\n--- {provider} ---")
    try:
        for chunk in client.chat_stream(provider=provider, model=model,
                                        messages=question, max_tokens=30):
            print(chunk.delta, end="", flush=True)
        print()
    except FeatureNotSupportedError:
        print(f"(streaming not supported)")
    except UniversalAIError as e:
        print(f"Error: {e}")
```

---

## Step 5: Async Streaming

For server applications (FastAPI, etc.), use `AsyncClient`:

```python
import asyncio
from polyai import AsyncClient

async def stream_to_console():
    async with AsyncClient() as client:
        async for chunk in await client.chat_stream(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": "Count from 1 to 10 slowly."}],
            max_tokens=50,
        ):
            print(chunk.delta, end="", flush=True)
    print()

asyncio.run(stream_to_console())
```

### FastAPI Streaming Endpoint

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from polyai import AsyncClient

app = FastAPI()
client = AsyncClient()

@app.get("/stream")
async def stream_chat(prompt: str):
    async def generate():
        async for chunk in await client.chat_stream(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        ):
            yield f"data: {chunk.delta}\n\n"  # SSE format
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## Step 6: Error Handling in Streams

```python
from polyai.exceptions import StreamingError, UniversalAIError

try:
    for chunk in client.chat_stream(
        provider="ovhcloud",
        model="llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": "Tell me a long story."}],
    ):
        print(chunk.delta, end="", flush=True)
except StreamingError as e:
    print(f"\nStream error: {e}")
except UniversalAIError as e:
    print(f"\nProvider error: {e}")
```

---

## Expected Results

After this tutorial, you can:

1. Print tokens as they arrive (live typing effect)
2. Know when the stream ends and why
3. Get full `ChatResponse` after streaming with `chat_accumulate()`
4. Stream in async contexts

---

## Next Steps

- [Tutorial 3: Function Calling](03-function-calling.md) — make AI call your functions
- [Tutorial 4: Vision](04-vision.md) — send images to AI
