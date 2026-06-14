# Migration Guide

> **Repository:** https://github.com/Alqudimi/PolyAI

This guide covers migrating between major and minor versions of PolyAI.

---

## Migrating to v1.0.0

v1.0.0 is the initial stable release. If you were using a pre-release version, follow this guide.

### Package Name

The package was renamed from `universal_ai` to `polyai`.

```bash
# Remove old package
pip uninstall universal_ai

# Install new package
pip install polyai
```

### Import Changes

```python
# Old (pre-release)
from universal_ai import Client
from universal_ai.exceptions import UniversalAIError

# New (v1.0.0)
from polyai import Client
from polyai.exceptions import UniversalAIError
```

All other imports follow the same pattern — replace `universal_ai` with `polyai`.

### API Changes

The public API (`client.chat()`, `client.embed()`, etc.) is unchanged.

### Environment Variables

Environment variables are unchanged:
```bash
OVHCLOUD_API_KEY=...
POLLINATIONS_API_KEY=...
DEVTOOLBOX_API_KEY=...
UNIVERSAL_AI_TIMEOUT=...
UNIVERSAL_AI_MAX_RETRIES=...
```

---

## Future Migrations

When v1.1.0 or v2.0.0 are released, migration instructions will be added here.

---

## Migrating FROM Other SDKs

### From the OpenAI Python SDK

```python
# OpenAI SDK
from openai import OpenAI
client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)

# PolyAI equivalent
from polyai import Client
client = Client()  # key from OVHCLOUD_API_KEY or POLLINATIONS_API_KEY
response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",  # or use pollinations/openai for GPT-4o
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.text)  # cleaner access pattern
```

Key differences:
- PolyAI: `response.text` vs OpenAI: `response.choices[0].message.content`
- PolyAI: pass `provider` parameter vs OpenAI: baked into the client
- PolyAI: streaming via `chat_stream()` vs OpenAI: `create(stream=True)`

### From the Anthropic Python SDK

```python
# Anthropic SDK
import anthropic
client = anthropic.Anthropic(api_key="sk-ant-...")
message = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
print(message.content[0].text)

# PolyAI equivalent (using Pollinations which offers Claude)
from polyai import Client
client = Client()
response = client.chat(
    provider="pollinations",
    model="claude",              # Anthropic Claude via Pollinations
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=1024,
)
print(response.text)
```

### From requests/httpx Direct API Calls

```python
# Direct HTTP
import httpx
response = httpx.post(
    "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": "llama-3.1-8b-instruct",
        "messages": [{"role": "user", "content": "Hello!"}],
    },
)
data = response.json()
text = data["choices"][0]["message"]["content"]

# PolyAI equivalent
from polyai import Client
client = Client(ovhcloud_api_key=api_key)
response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
)
text = response.text  # all the HTTP handling done for you
```

Benefits of PolyAI over direct calls:
- Automatic retries (3x by default)
- Connection pooling
- Error mapping to typed exceptions
- Streaming support
- Type annotations
- No HTTP boilerplate
