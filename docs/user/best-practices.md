# Best Practices

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Client Lifecycle

### ✅ Reuse the Client

```python
# Good — one client per application lifetime
client = Client()

def handle_request(user_input):
    return client.chat(provider="ovhcloud", model="...", messages=[...])

# Bad — creating a new client per request wastes connections
def handle_request(user_input):
    client = Client()  # ❌ new connection pool every call
    return client.chat(...)
```

### ✅ Use Context Managers

```python
# Good
with Client() as client:
    response = client.chat(...)

# Or keep the client alive for the app lifetime
client = Client()
app.on_shutdown(client.close)
```

---

## Provider Selection

### Match Provider to Task

| Task | Best Provider | Reason |
|---|---|---|
| High-quality chat | OVHcloud 70B | Best model quality |
| Fast cheap chat | Pollinations | Good free tier |
| No-signup quick test | mlvoca | Zero auth required |
| Summarise text | DevToolbox | Purpose-built endpoint |
| Semantic search | OVHcloud BGE-M3 | Best embedding model |
| Generate images | Pollinations Flux | Most image models |
| EU GDPR compliance | OVHcloud | EU-hosted |

### Implement Failover

```python
from polyai.exceptions import UniversalAIError

PROVIDERS = [
    ("ovhcloud",     "llama-3.1-8b-instruct"),
    ("pollinations", "openai"),
    ("mlvoca",       "tinyllama"),
]

def chat_with_failover(messages):
    last_error = None
    for provider, model in PROVIDERS:
        try:
            return client.chat(provider=provider, model=model, messages=messages)
        except UniversalAIError as e:
            last_error = e
            continue
    raise last_error
```

---

## Message Construction

### ✅ Clear, Specific Prompts

```python
# Good — specific, structured prompt
messages = [
    {"role": "system", "content": "You are a JSON data extractor. Always return valid JSON."},
    {"role": "user", "content": "Extract: name, age, city from: 'Alice Smith, 28, London'"},
]

# Bad — vague
messages = [{"role": "user", "content": "Extract info"}]
```

### ✅ Use System Prompts

```python
response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{"role": "user", "content": "..."}],
    system="You are a concise assistant. Respond in 1-2 sentences maximum.",
)
```

### ✅ Manage Context Length

For long conversations, truncate old messages:

```python
from polyai.utils import truncate_messages

# Keep only the most recent messages within a token budget
messages = truncate_messages(
    messages,
    max_tokens=3000,       # leave room for response
    chars_per_token=4,
)
```

---

## Temperature and Sampling

| Use Case | Temperature | Reasoning |
|---|---|---|
| Data extraction / JSON | 0.0 | Deterministic, consistent |
| Code generation | 0.2–0.4 | Mostly deterministic |
| Question answering | 0.3–0.7 | Balanced |
| Creative writing | 0.7–1.2 | More variety |
| Brainstorming | 1.0–1.5 | Maximum creativity |

```python
# Deterministic extraction
response = client.chat(..., temperature=0.0, json_mode=True)

# Creative story
response = client.chat(..., temperature=1.0, max_tokens=1000)
```

---

## Error Handling

### ✅ Catch Specific Exceptions

```python
from polyai.exceptions import (
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    ProviderUnavailableError,
    UniversalAIError,
)
import time

def safe_chat(messages, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return client.chat(provider="ovhcloud", model="...", messages=messages)

        except RateLimitError as e:
            wait = e.retry_after or (2 ** attempt)
            time.sleep(wait)

        except AuthenticationError:
            raise  # no point retrying — fix the key

        except ModelNotFoundError as e:
            raise ValueError(f"Bad model: {e}") from e

        except ProviderUnavailableError:
            time.sleep(5)

        except UniversalAIError:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)
```

---

## Streaming

### ✅ Always Flush

```python
for chunk in client.chat_stream(...):
    print(chunk.delta, end="", flush=True)  # flush=True is important
print()  # final newline
```

### ✅ Accumulate When You Need the Full Response

```python
response = client.chat_accumulate(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[...],
    on_chunk=lambda c: print(c.delta, end="", flush=True),
)
# Now you have the full ChatResponse
print(f"Total tokens: {response.usage.total_tokens}")
```

---

## Async

### ✅ Use AsyncClient in Async Contexts

```python
# In an async context (FastAPI, async script, etc.)
async with AsyncClient() as client:
    response = await client.chat(...)
```

### ✅ Parallelise Independent Requests

```python
# Don't do this sequentially if requests are independent
async def slow():
    r1 = await client.chat(provider="ovhcloud", ...)
    r2 = await client.chat(provider="pollinations", ...)
    return r1, r2

# Do this instead — parallel
async def fast():
    r1, r2 = await asyncio.gather(
        client.chat(provider="ovhcloud", ...),
        client.chat(provider="pollinations", ...),
    )
    return r1, r2
```

Or use the built-in method:
```python
results = await client.chat_many([
    {"provider": "ovhcloud", ...},
    {"provider": "pollinations", ...},
], max_concurrency=5)
```

---

## Production Checklist

- [ ] API keys loaded from environment variables, not hardcoded
- [ ] Client created once and reused (not per-request)
- [ ] Context manager used for proper cleanup
- [ ] Specific exceptions caught (not bare `except Exception`)
- [ ] Retries configured appropriately for your SLA
- [ ] Timeouts set to prevent hanging connections
- [ ] Logging does not include API keys or raw responses
- [ ] Provider failover implemented for critical paths
- [ ] `max_tokens` set to prevent unexpectedly large responses
- [ ] JSON output validated before use (`json.loads` + schema check)

See also: [Production Guide](production-guide.md), [Security Best Practices](security-best-practices.md).
