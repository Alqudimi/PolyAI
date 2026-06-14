# Troubleshooting Guide

> **Repository:** https://github.com/Alqudimi/PolyAI

This guide covers the most common issues and how to diagnose and fix them.

---

## Quick Diagnostics

Run this snippet to check your environment:

```python
import sys
import polyai
import httpx

print(f"Python:  {sys.version}")
print(f"PolyAI:  {polyai.__version__}")
print(f"httpx:   {httpx.__version__}")
print(f"Platform: {sys.platform}")
```

---

## Installation Issues

### `ModuleNotFoundError: No module named 'polyai'`

**Cause:** PolyAI is not installed in the active Python environment.

**Fix:**
```bash
pip install polyai

# If using a virtual environment, activate it first:
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# If using conda:
conda activate myenv
pip install polyai
```

**Verify:**
```bash
python -c "import polyai; print(polyai.__version__)"
```

---

### `pip install polyai` fails with SSL errors

**Cause:** Corporate network or self-signed certificates.

**Fix:**
```bash
pip install polyai --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

---

### `pip install polyai` fails with `ERROR: Could not find a version that satisfies the requirement`

**Cause:** Python version is below 3.9.

**Fix:** Upgrade Python to 3.9 or higher.

```bash
python --version  # must be 3.9+
```

---

## Authentication Errors

### `AuthenticationError: 401 Unauthorized`

**Cause:** Invalid, expired, or missing API key.

**Diagnosis:**
```bash
# Check if environment variable is set
echo $OVHCLOUD_API_KEY     # Linux/macOS
echo %OVHCLOUD_API_KEY%    # Windows CMD
```

**Fix:**
1. Verify the key is correct — no extra spaces or newlines
2. Try setting it explicitly:
   ```python
   client = Client(ovhcloud_api_key="your-key-here")
   ```
3. Regenerate the key in your provider dashboard

---

### `AuthenticationError` even though I set the environment variable

**Cause:** Variable set in a different shell session or not exported.

**Fix:**
```bash
# Linux/macOS — must use 'export'
export OVHCLOUD_API_KEY="your-key"
python myscript.py

# Or load from .env file
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()

from polyai import Client
client = Client()
```

---

## Network Errors

### `ConnectionError: All connection attempts failed`

**Cause:** Network unreachable, provider down, or firewall blocking.

**Diagnosis:**
```bash
# Test connectivity to OVHcloud
curl -I https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/models

# Test connectivity to Pollinations
curl -I https://gen.pollinations.ai/v1/models
```

**Fix:**
1. Check your internet connection
2. Check provider status pages
3. If behind a corporate proxy:
   ```python
   import httpx
   from polyai import ClientConfig

   config = ClientConfig()
   # PolyAI uses httpx — set proxy via environment variables:
   # HTTPS_PROXY=http://proxy.company.com:8080
   ```

---

### `TimeoutError: Request timed out`

**Cause:** Request took longer than the configured timeout (default: 60s).

**Fix:** Increase the timeout:
```python
config = ClientConfig(timeout=120.0)  # 2 minutes
client = Client(config=config)

# Or per-request
response = client.chat(..., timeout=120.0)
```

**Note:** mlvoca can be slow. Use `timeout=300.0` for mlvoca.

---

## Rate Limiting

### `RateLimitError: 429 Too Many Requests`

**Cause:** Exceeded provider rate limits.

**PolyAI handles this automatically** — it retries with exponential backoff.

**Manual fix if still failing:**
```python
import time
from polyai.exceptions import RateLimitError

try:
    response = client.chat(...)
except RateLimitError as e:
    print(f"Rate limited. Waiting {e.retry_after}s...")
    time.sleep(e.retry_after or 60)
    response = client.chat(...)  # retry
```

**Long-term fix:**
- Get an API key for a higher tier
- Add delays between requests
- Use multiple providers with failover

---

## Provider-Specific Issues

### OVHcloud: `ModelNotFoundError`

**Cause:** The model ID is incorrect or the model is no longer available.

**Fix:** List available models:
```python
models = client.list_models("ovhcloud")
for m in models:
    print(m["id"])
```

---

### mlvoca: Very slow responses

**Cause:** mlvoca is community hardware with limited capacity.

**Fix:**
- Use `timeout=300.0`
- Switch to TinyLlama (faster than DeepSeek-R1)
- For production, use OVHcloud or Pollinations instead

---

### mlvoca: `ConnectionError`

**Cause:** mlvoca servers may be temporarily down.

**Fix:** Implement failover to another provider:
```python
from polyai.exceptions import UniversalAIError

for provider, model in [("mlvoca", "tinyllama"), ("pollinations", "openai")]:
    try:
        resp = client.chat(provider=provider, model=model, messages=[...])
        break
    except UniversalAIError:
        continue
```

---

### Pollinations: Image generation returns error

**Cause:** Model name incorrect or prompt too long.

**Fix:**
```python
# List available image models
from polyai.providers.pollinations import IMAGE_MODELS
print(IMAGE_MODELS)

# Use a known working model
img = client.generate_image(
    provider="pollinations",
    prompt="a red apple",  # keep prompt concise
    model="flux",          # most reliable model
)
```

---

### DevToolbox: Empty response or generic error

**Cause:** DevToolbox API may have rate-limited anonymous requests.

**Fix:**
```python
# Use an API key for more reliable access
import os
client = Client(devtoolbox_api_key=os.environ["DEVTOOLBOX_API_KEY"])
```

---

## Streaming Issues

### Streaming stops mid-response

**Cause:** Network interruption or server-side timeout.

**Fix:** Implement retry around the stream:
```python
from polyai.exceptions import StreamingError
import time

for attempt in range(3):
    try:
        for chunk in client.chat_stream(...):
            print(chunk.delta, end="", flush=True)
        break
    except StreamingError:
        if attempt < 2:
            time.sleep(2 ** attempt)
        else:
            raise
```

---

### `StreamingError: Invalid SSE frame`

**Cause:** Provider returned malformed SSE data.

**Fix:** This is a provider-side issue. Report it as a bug in PolyAI's issue tracker with the raw response.

---

## Async Issues

### `RuntimeError: This event loop is already running`

**Cause:** Running async code in Jupyter or an environment that already has an event loop.

**Fix:** Use `nest_asyncio`:
```bash
pip install nest_asyncio
```

```python
import nest_asyncio
nest_asyncio.apply()

import asyncio
from polyai import AsyncClient

async def main():
    async with AsyncClient() as client:
        resp = await client.chat(...)
        print(resp.text)

asyncio.run(main())
```

---

### `RuntimeError: no running event loop`

**Cause:** Calling async methods from sync context.

**Fix:** Use `asyncio.run()`:
```python
# Wrong ❌
response = client.chat_async(...)

# Right ✅
import asyncio
response = asyncio.run(async_client.chat(...))
```

Or use the sync `Client` instead of `AsyncClient`.

---

## Type Errors

### `TypeError: chat() got an unexpected keyword argument`

**Cause:** Typo in parameter name or using a parameter that doesn't exist.

**Fix:** Check the [API Reference](docs/api/client.md) for the correct parameter names.

Common mistakes:
```python
# Wrong ❌
client.chat(..., max_token=500)     # missing 's'
client.chat(..., temp=0.7)          # wrong name
client.chat(..., json=True)         # wrong name

# Right ✅
client.chat(..., max_tokens=500)
client.chat(..., temperature=0.7)
client.chat(..., json_mode=True)
```

---

## Getting More Help

If your issue isn't covered here:

1. **Search issues:** https://github.com/Alqudimi/PolyAI/issues
2. **Open an issue:** Use the [bug report template](https://github.com/Alqudimi/PolyAI/issues/new?template=bug_report.yml)
3. **Include in your report:**
   - PolyAI version (`python -c "import polyai; print(polyai.__version__)"`)
   - Python version (`python --version`)
   - Operating system
   - Complete error traceback
   - Minimal code to reproduce (with API keys removed)
