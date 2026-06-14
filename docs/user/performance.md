# Performance Best Practices

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Client Reuse

The single most impactful performance improvement is reusing the `Client` instance:

```python
# ❌ Slow — new connection pool every request (100ms+ overhead)
def handle_request(text):
    client = Client()
    return client.chat(...)

# ✅ Fast — reuses existing connections
client = Client()  # create once

def handle_request(text):
    return client.chat(...)
```

The `Client` internally uses an `httpx.Client` with connection pooling. Reusing the client means:
- No TCP handshake overhead after the first request
- No TLS negotiation overhead after the first request
- HTTP/1.1 keep-alive connections reused

---

## Async for I/O-Bound Workloads

If your application handles multiple concurrent AI requests, use `AsyncClient`:

```python
import asyncio
from polyai import AsyncClient

async with AsyncClient() as client:
    # These run concurrently — not sequentially
    results = await asyncio.gather(
        client.chat(provider="ovhcloud", ...),
        client.chat(provider="pollinations", ...),
        client.chat(provider="mlvoca", ...),
    )
```

### Concurrency Limits

Avoid overwhelming a provider's rate limits:

```python
# Control concurrency with Semaphore
async def limited_chat(semaphore, messages):
    async with semaphore:
        return await client.chat(...)

semaphore = asyncio.Semaphore(5)  # max 5 concurrent requests
tasks = [limited_chat(semaphore, msg) for msg in messages_list]
results = await asyncio.gather(*tasks)
```

Or use the built-in `chat_many`:

```python
results = await client.chat_many(
    requests_list,
    max_concurrency=5,
)
```

---

## Streaming for Long Responses

For long responses (>200 tokens), streaming returns the first token much faster:

```python
# Without streaming: user waits 5-10s for entire response
response = client.chat(provider="ovhcloud", model="meta-llama-3_3-70b-instruct",
                       messages=[...], max_tokens=500)
print(response.text)  # user sees output after 5-10s

# With streaming: user sees first words in 0.5-1s
for chunk in client.chat_stream(provider="ovhcloud", model="meta-llama-3_3-70b-instruct",
                                 messages=[...], max_tokens=500):
    print(chunk.delta, end="", flush=True)
```

Time to first token (TTFT) is typically 5–10× faster with streaming.

---

## Model Selection

Choosing the right model dramatically affects latency:

| Model | Quality | Speed | Best For |
|---|---|---|---|
| `llama-3.2-3b-instruct` | Good | Very fast | Classification, quick answers |
| `llama-3.1-8b-instruct` | Better | Fast | Most use cases |
| `meta-llama-3_3-70b-instruct` | Best | Slow | Complex reasoning, quality-critical |
| `tinyllama` (mlvoca) | Basic | Variable | Zero-cost testing |

**Rule of thumb:** Use the smallest model that produces acceptable quality for your task.

---

## Token Efficiency

Fewer tokens = faster responses + lower cost.

### Minimise System Prompts

```python
# ❌ Verbose system prompt
system = """
You are a helpful assistant. Your job is to help users with their questions.
Please be polite and professional at all times. Always provide clear and
concise answers. If you don't know something, say so.
"""

# ✅ Concise system prompt
system = "You are a helpful, concise assistant."
```

### Set `max_tokens` Appropriately

```python
# For classification (yes/no, category names)
response = client.chat(..., max_tokens=10)

# For summaries
response = client.chat(..., max_tokens=150)

# For detailed explanations
response = client.chat(..., max_tokens=500)
```

### Truncate Long Conversation History

For multi-turn chats, old messages accumulate and slow down requests:

```python
def truncate_messages(
    messages: list[dict],
    max_tokens: int = 3000,
    chars_per_token: int = 4,
) -> list[dict]:
    """Keep the most recent messages within a token budget."""
    max_chars = max_tokens * chars_per_token
    total_chars = 0
    kept = []
    # Always keep system message
    system_msgs = [m for m in messages if m["role"] == "system"]
    other_msgs = [m for m in messages if m["role"] != "system"]

    # Add from most recent
    for msg in reversed(other_msgs):
        msg_chars = len(str(msg.get("content", "")))
        if total_chars + msg_chars > max_chars:
            break
        kept.append(msg)
        total_chars += msg_chars

    return system_msgs + list(reversed(kept))
```

---

## Caching

Cache responses for identical or semantically similar queries:

### Simple In-Memory Cache

```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_chat(prompt: str, model: str) -> str:
    response = client.chat(
        provider="ovhcloud",
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,  # deterministic — safe to cache
    )
    return response.text

# Subsequent calls with same prompt return instantly
result1 = cached_chat("What is Python?", "llama-3.1-8b-instruct")
result2 = cached_chat("What is Python?", "llama-3.1-8b-instruct")  # from cache
```

### Redis Cache for Distributed Systems

```python
import redis
import hashlib
import json

r = redis.Redis()

def cached_chat(messages: list[dict], model: str, ttl: int = 3600) -> str:
    # Create cache key from messages hash
    key = hashlib.sha256(json.dumps(messages + [model], sort_keys=True).encode()).hexdigest()

    # Check cache
    cached = r.get(key)
    if cached:
        return cached.decode()

    # Cache miss — call API
    response = client.chat(provider="ovhcloud", model=model, messages=messages, temperature=0.0)
    r.setex(key, ttl, response.text)
    return response.text
```

---

## Connection Settings

```python
from polyai import ClientConfig

config = ClientConfig(
    timeout=30.0,      # don't set too high — hanging connections waste resources
    max_retries=3,     # 3 retries is usually enough; more wastes time on failing providers
)
```

### For High-Throughput Applications

```python
# AsyncClient maintains a persistent connection pool
# All requests in the same context manager share connections
async with AsyncClient(config=config) as client:
    # Connection pool is alive for the entire duration
    results = await asyncio.gather(*[client.chat(...) for _ in range(1000)])
```

---

## Benchmarking

Run the built-in benchmark:

```bash
python examples/benchmark.py
```

Or measure yourself:

```python
import time

start = time.perf_counter()
response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Hi"}],
    max_tokens=50,
)
elapsed = time.perf_counter() - start

print(f"Latency: {elapsed:.2f}s")
print(f"Tokens/sec: {response.usage.total_tokens / elapsed:.1f}")
```
