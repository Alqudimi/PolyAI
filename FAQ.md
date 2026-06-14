# Frequently Asked Questions

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## General

### What is PolyAI?

PolyAI is a Python SDK that gives you a single, consistent interface for four AI providers: OVHcloud AI Endpoints, Pollinations.AI, mlvoca, and DevToolbox API. Instead of learning four different APIs, you learn one.

### Is PolyAI free to use?

PolyAI itself is MIT-licensed and completely free. The underlying AI providers have their own pricing:
- **OVHcloud:** Free anonymous tier (2 req/min), paid tiers available
- **Pollinations.AI:** Free for anonymous use, paid plans for higher limits
- **mlvoca:** Always free, non-commercial only
- **DevToolbox:** Free 100k requests/day, unlimited with API key

### Do I need API keys?

No. All four providers have free anonymous tiers. You can start immediately:

```python
from polyai import Client
client = Client()  # no keys needed
response = client.chat(provider="ovhcloud", model="llama-3.1-8b-instruct", messages=[...])
```

API keys unlock higher rate limits and more models.

### Which Python versions are supported?

Python **3.9, 3.10, 3.11, 3.12**. PolyAI is tested on all four versions in CI.

### What are PolyAI's dependencies?

**One production dependency:** `httpx>=0.25.0`

That's it. PolyAI intentionally minimises dependencies to reduce installation size and security surface.

### Is PolyAI production-ready?

Yes. v1.0.0 is production-ready with:
- 138 unit tests, fully offline
- Full type annotations
- Automatic retries with exponential backoff
- Connection pooling and session reuse
- Comprehensive error handling

---

## Installation

### `pip install polyai` fails — what do I do?

1. Check Python version: `python --version` (must be 3.9+)
2. Upgrade pip: `pip install --upgrade pip`
3. Try with explicit Python: `python3 -m pip install polyai`
4. Check network/firewall — `pip` needs internet access

### Can I install without internet access (air-gapped)?

Download the wheel from [PyPI](https://pypi.org/project/polyai/#files) and install locally:

```bash
pip install polyai-1.0.0-py3-none-any.whl
```

### Can I use PolyAI with conda?

Yes:

```bash
conda create -n myenv python=3.11
conda activate myenv
pip install polyai
```

---

## Authentication

### Where do I set my API keys?

Recommended: environment variables.

```bash
export OVHCLOUD_API_KEY="your-key"
export POLLINATIONS_API_KEY="sk_..."
export DEVTOOLBOX_API_KEY="dtb_..."
```

Alternative: pass directly to the client constructor.

```python
client = Client(ovhcloud_api_key="your-key")
```

### Are my API keys safe with PolyAI?

Yes. PolyAI:
- Masks secrets in all `repr` and log output
- Never writes keys to disk
- Sends keys only to the configured provider endpoint
- Has no telemetry or analytics

### I don't have an API key. Can I still use PolyAI?

Yes! All four providers work without API keys (anonymous mode). Rate limits apply.

---

## Usage

### How do I switch between providers?

Change the `provider` parameter:

```python
# Same code, different provider
response = client.chat(provider="ovhcloud",     model="llama-3.1-8b-instruct", messages=[...])
response = client.chat(provider="pollinations", model="openai",                 messages=[...])
response = client.chat(provider="mlvoca",       model="tinyllama",              messages=[...])
response = client.chat(provider="devtoolbox",   model="devtoolbox-ai",          messages=[...])
```

### How do I implement provider failover?

```python
from polyai.exceptions import UniversalAIError

providers = [
    ("ovhcloud", "llama-3.1-8b-instruct"),
    ("pollinations", "openai"),
    ("mlvoca", "tinyllama"),
]

for provider, model in providers:
    try:
        resp = client.chat(provider=provider, model=model, messages=[...])
        break  # success — stop trying
    except UniversalAIError:
        continue  # try next provider
```

### How do I use streaming?

```python
for chunk in client.chat_stream(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
):
    print(chunk.delta, end="", flush=True)
```

### How do I use async?

```python
import asyncio
from polyai import AsyncClient

async def main():
    async with AsyncClient() as client:
        response = await client.chat(provider="ovhcloud", model="...", messages=[...])

asyncio.run(main())
```

### How do I send a system prompt?

Two equivalent ways:

```python
# Option 1: system parameter (shorthand)
client.chat(
    ...,
    system="You are a helpful assistant.",
)

# Option 2: include in messages list
client.chat(
    ...,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)
```

### How do I get JSON output?

```python
import json

response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{"role": "user", "content": "Extract name and age as JSON."}],
    json_mode=True,
    temperature=0.0,
)
data = json.loads(response.text)
```

Note: `json_mode` is only supported by OVHcloud and Pollinations.

### Why am I getting `FeatureNotSupportedError`?

The provider doesn't support that feature. Check the [Capability Matrix](FEATURES.md#capability-matrix).

Example: mlvoca doesn't support embeddings.

```python
# This raises FeatureNotSupportedError
client.embed(provider="mlvoca", input=["hello"], model="tinyllama")
```

Solution: switch to a provider that supports embeddings (OVHcloud or Pollinations).

---

## Errors

### I'm getting `AuthenticationError`. What's wrong?

Your API key is invalid, expired, or missing. Check:
1. Is the environment variable set? `echo $OVHCLOUD_API_KEY`
2. Is the key format correct? (OVHcloud keys don't have a prefix; Pollinations keys start with `sk_`)
3. Has the key expired? Regenerate in the provider dashboard.

### I'm getting `RateLimitError`. What should I do?

You've exceeded the provider's rate limit. Options:
1. Wait for `e.retry_after` seconds (PolyAI does this automatically with retries)
2. Reduce request frequency
3. Get an API key for a higher rate limit tier
4. Switch to a different provider

PolyAI's retry policy handles 429 errors automatically:
```python
config = ClientConfig(max_retries=5)  # retries up to 5 times
```

### I'm getting `ConnectionError`. What's wrong?

The provider's server is unreachable. Check:
1. Your internet connection
2. Provider status page
3. Firewall rules (are outbound HTTPS requests allowed?)

### The response is empty or `None`. Why?

If `response.text` is empty, the model may have:
- Hit the `max_tokens` limit — increase it
- Stopped due to content filtering
- Generated a tool call instead of text (check `response.tool_calls`)

```python
response = client.chat(...)
if response.tool_calls:
    print("Model wants to call a tool, not generate text")
elif not response.text:
    print(f"Empty response. Finish reason: {response.finish_reason}")
```

---

## mlvoca-Specific

### Can I use mlvoca commercially?

**No.** mlvoca's terms of service restrict use to non-commercial purposes. For commercial use, switch to OVHcloud, Pollinations, or DevToolbox.

### Why is mlvoca slow?

mlvoca is hosted on limited hardware and has no rate limits, which means it can be slow during high usage periods. For production workloads, use OVHcloud or Pollinations.

---

## Contributing

### How do I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version:

1. Fork the repo
2. `pip install -e ".[dev]"`
3. Make changes with tests
4. `pytest tests/unit -v` must pass
5. Open a PR

### How do I add a new provider?

See [docs/dev/adding-providers.md](docs/dev/adding-providers.md).

### I found a security vulnerability. How do I report it?

See [SECURITY.md](SECURITY.md). **Do not use public GitHub Issues** for security vulnerabilities.

---

## Still have a question?

- [Open a Discussion](https://github.com/Alqudimi/PolyAI/discussions)
- [Open an Issue](https://github.com/Alqudimi/PolyAI/issues/new?template=question.yml)
