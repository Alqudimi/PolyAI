# Configuration Guide

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Overview

PolyAI can be configured through:
1. **Environment variables** — recommended for production
2. **Constructor arguments** — for programmatic configuration
3. **`ClientConfig` object** — for advanced per-provider overrides

---

## Environment Variables

Set before running your Python script:

```bash
# API Keys
export OVHCLOUD_API_KEY="your-ovhcloud-api-key"
export POLLINATIONS_API_KEY="sk_your_pollinations_key"
export DEVTOOLBOX_API_KEY="dtb_your_devtoolbox_key"

# Global settings
export UNIVERSAL_AI_TIMEOUT="60"        # request timeout in seconds
export UNIVERSAL_AI_MAX_RETRIES="3"     # number of retry attempts
```

| Variable | Default | Description |
|---|---|---|
| `OVHCLOUD_API_KEY` | `""` | OVHcloud AI Endpoints API key |
| `POLLINATIONS_API_KEY` | `""` | Pollinations.AI API key (`sk_*` or `pk_*`) |
| `DEVTOOLBOX_API_KEY` | `""` | DevToolbox API key (`dtb_*`) |
| `UNIVERSAL_AI_TIMEOUT` | `60.0` | Default request timeout (seconds) |
| `UNIVERSAL_AI_MAX_RETRIES` | `3` | Maximum retry attempts |

mlvoca requires no key.

---

## Constructor Arguments

```python
from polyai import Client

client = Client(
    ovhcloud_api_key="your-key",        # overrides env var
    pollinations_api_key="sk_...",
    devtoolbox_api_key="dtb_...",
    timeout=60.0,
    max_retries=3,
)
```

---

## `ClientConfig` Object

For fine-grained control:

```python
from polyai import Client, ClientConfig
from polyai.config import ProviderConfig

config = ClientConfig(
    # API keys
    ovhcloud_api_key="your-key",
    pollinations_api_key="sk_...",
    devtoolbox_api_key="dtb_...",

    # Global settings
    timeout=60.0,
    max_retries=3,

    # Per-provider overrides
    providers={
        "ovhcloud": ProviderConfig(
            timeout=30.0,        # OVHcloud-specific timeout
            max_retries=5,       # OVHcloud-specific retries
        ),
        "mlvoca": ProviderConfig(
            timeout=300.0,       # mlvoca is slow — give it 5 minutes
            max_retries=1,       # mlvoca doesn't need many retries
            base_url="http://custom-mlvoca-host:11434",  # custom base URL
        ),
    },
)

client = Client(config=config)
```

---

## `ProviderConfig` Options

```python
from polyai.config import ProviderConfig

ProviderConfig(
    timeout=60.0,            # request timeout in seconds
    max_retries=3,           # max retry attempts
    base_url=None,           # custom provider URL (advanced)
)
```

| Field | Type | Default | Description |
|---|---|---|---|
| `timeout` | `float \| None` | From `ClientConfig` | Per-provider timeout |
| `max_retries` | `int \| None` | From `ClientConfig` | Per-provider retries |
| `base_url` | `str \| None` | Provider default | Override provider URL |

---

## Loading from `.env` File

Use `python-dotenv` to load from a `.env` file:

```bash
pip install python-dotenv
```

```python
# main.py
from dotenv import load_dotenv
load_dotenv()  # loads .env before Client() reads env vars

from polyai import Client
client = Client()
```

`.env` file:
```
OVHCLOUD_API_KEY=your-key-here
POLLINATIONS_API_KEY=sk_...
DEVTOOLBOX_API_KEY=dtb_...
UNIVERSAL_AI_TIMEOUT=60
```

---

## Configuration Priority

When multiple sources are set, the priority is (highest → lowest):

1. Constructor argument
2. `ClientConfig` explicit field
3. Environment variable
4. Default value

Example:
```python
os.environ["OVHCLOUD_API_KEY"] = "key-from-env"

# This uses "key-from-constructor" (higher priority)
client = Client(ovhcloud_api_key="key-from-constructor")
```

---

## Timeout Configuration

```python
# Global timeout for all requests
config = ClientConfig(timeout=120.0)

# Per-provider timeout
config = ClientConfig(
    providers={
        "mlvoca": ProviderConfig(timeout=300.0),  # mlvoca can be slow
        "ovhcloud": ProviderConfig(timeout=30.0),
    }
)

# Per-request timeout
response = client.chat(..., timeout=10.0)
```

Timeout values:
- Too low → frequent `TimeoutError`
- Too high → threads/connections hang for too long
- Recommended: 30–60s for most providers, 120–300s for mlvoca

---

## Retry Configuration

```python
config = ClientConfig(max_retries=5)
```

The retry policy uses **exponential backoff with full jitter**:
- Attempt 1: wait 0–1s
- Attempt 2: wait 0–2s
- Attempt 3: wait 0–4s
- Attempt 4: wait 0–8s
- Attempt 5: wait 0–16s (capped at `max_wait_seconds=60`)

Retries happen on:
- HTTP 429 (Rate Limit) — using `Retry-After` header if available
- HTTP 500, 502, 503, 504 (Server errors)
- Network errors (`ConnectionError`)
- Timeouts

Retries do NOT happen on:
- HTTP 400, 401, 403, 404, 422 (client errors — retrying won't help)

---

## Context Manager (Resource Cleanup)

Always close the client when done, or use a context manager:

```python
# Option 1: context manager (recommended)
with Client() as client:
    response = client.chat(...)

# Option 2: explicit close
client = Client()
try:
    response = client.chat(...)
finally:
    client.close()
```

For async:
```python
async with AsyncClient() as client:
    response = await client.chat(...)
```

---

## Multiple Clients

You can create multiple clients with different configurations:

```python
# High-timeout client for mlvoca
slow_client = Client(config=ClientConfig(
    providers={"mlvoca": ProviderConfig(timeout=300.0)}
))

# Fast client for production
fast_client = Client(config=ClientConfig(timeout=10.0, max_retries=1))
```
