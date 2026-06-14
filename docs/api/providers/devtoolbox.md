# DevToolbox API Provider

> **Repository:** https://github.com/Alqudimi/PolyAI

```python
client.chat(provider="devtoolbox", ...)
```

---

## Overview

| Property | Value |
|---|---|
| Provider name | `"devtoolbox"` |
| Base URL | `https://devtoolbox-api.devtoolbox-api.workers.dev` |
| Platform | Cloudflare Workers (global edge) |
| Auth | None (100k req/day) or `dtb_*` key (unlimited) |
| Commercial use | ✅ Yes |
| Latency | Very low (edge-hosted) |

---

## Authentication

### Free Tier (No Key)

```python
client = Client()  # 100k requests/day
```

### Premium (API Key)

```bash
export DEVTOOLBOX_API_KEY="dtb_your_key_here"
```

```python
client = Client(devtoolbox_api_key="dtb_...")
```

---

## Supported Features

| Feature | Supported | Notes |
|---|:---:|---|
| Chat completions | ✅ | `/ai/generate` |
| Streaming | ❌ | No SSE support |
| Function calling | ❌ | Not supported |
| Vision | ❌ | Not supported |
| Embeddings | ❌ | Not supported |
| Image generation | ❌ | Not supported |
| Text summarization | ✅ | `/ai/summarize` |
| Translation | ✅ | `/ai/translate` |
| Code explanation | ✅ | `/ai/explain-code` |
| Regex generation | ✅ | `/ai/generate-regex` |
| UUID generation | ✅ | Utility |
| Password generation | ✅ | Utility |
| Hashing | ✅ | Utility |
| Lorem ipsum | ✅ | Utility |
| QR code | ✅ | Utility |

---

## AI Endpoints

### Chat (Standard Interface)

```python
response = client.chat(
    provider="devtoolbox",
    model="devtoolbox-ai",
    messages=[{"role": "user", "content": "Write a haiku about the ocean."}],
)
print(response.text)
```

### DevTools Resource

Access DevToolbox-specific AI features through the namespaced resource:

```python
devtools = client.with_provider("devtoolbox").devtools
```

---

## DevTools Methods

### `devtools.summarize(text, max_length=None)`

Summarize long text.

```python
article = """
Python is a high-level, general-purpose programming language. Its design philosophy 
emphasizes code readability through the use of significant indentation. Python is 
dynamically typed and garbage-collected. It supports multiple programming paradigms, 
including structured (particularly procedural), object-oriented and functional programming.
"""
summary = devtools.summarize(article, max_length=50)
print(summary)
# "Python is a high-level language emphasizing code readability with dynamic typing."
```

---

### `devtools.translate(text, target_language)`

Translate text to another language.

```python
# Translate to French
result = devtools.translate("Good morning, how are you?", "fr")
print(result)  # "Bonjour, comment allez-vous ?"

# Translate to Arabic
result = devtools.translate("Hello world", "ar")
print(result)  # "مرحباً بالعالم"

# Supported language codes: ISO 639-1 codes (en, fr, es, de, ar, zh, ja, ko, ...)
```

---

### `devtools.explain_code(code, language=None)`

Explain what code does in plain English.

```python
code = """
const fibonacci = (n) => n <= 1 ? n : fibonacci(n-1) + fibonacci(n-2);
"""
explanation = devtools.explain_code(code)
print(explanation)
# "This is a recursive JavaScript function that calculates the nth Fibonacci number..."
```

---

### `devtools.generate_regex(description)`

Generate a regex pattern from a natural language description.

```python
patterns = [
    devtools.generate_regex("match valid email addresses"),
    devtools.generate_regex("match US phone numbers in format (xxx) xxx-xxxx"),
    devtools.generate_regex("match IPv4 addresses"),
    devtools.generate_regex("match dates in YYYY-MM-DD format"),
]
for p in patterns:
    print(p)
```

---

## Developer Utility Methods

### `devtools.generate_uuid(version=4)`

Generate a UUID.

```python
uuid = devtools.generate_uuid()
print(uuid)  # "550e8400-e29b-41d4-a716-446655440000"
```

---

### `devtools.generate_password(length=16, symbols=True, numbers=True, uppercase=True)`

Generate a cryptographically secure password.

```python
pwd = devtools.generate_password(length=20, symbols=True)
print(pwd)  # "K#9mP$2vL!xQ@8nR^5yW"

# Simple alphanumeric
pwd2 = devtools.generate_password(length=12, symbols=False)
```

---

### `devtools.hash(algorithm, input)`

Compute a cryptographic hash.

```python
# SHA-256
result = devtools.hash("sha256", "hello world")
print(result)  # {"hash": "b94d27b9934d3e0...", "algorithm": "sha256"}

# MD5
result = devtools.hash("md5", "hello")

# Supported: sha256, sha512, sha1, md5
```

---

### `devtools.lorem_ipsum(paragraphs=1, sentences_per_paragraph=5)`

Generate placeholder text.

```python
text = devtools.lorem_ipsum(paragraphs=3)
print(text[:100] + "...")
# "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor..."
```

---

### `devtools.qr_code(data, size=300)`

Generate a QR code PNG.

```python
qr_bytes = devtools.qr_code("https://github.com/Alqudimi/PolyAI", size=300)
with open("qr.png", "wb") as f:
    f.write(qr_bytes)
print(f"QR code: {len(qr_bytes):,} bytes")
```

---

## Error Handling

```python
from polyai.exceptions import UniversalAIError, RateLimitError

devtools = client.with_provider("devtoolbox").devtools

try:
    summary = devtools.summarize("Very long text...")
except RateLimitError:
    print("Free tier limit reached. Use a dtb_* API key for unlimited access.")
except UniversalAIError as e:
    print(f"DevToolbox error: {e}")
```

---

## Async Usage

```python
from polyai import AsyncClient

async with AsyncClient() as client:
    # Standard chat
    response = await client.chat(provider="devtoolbox", model="devtoolbox-ai", messages=[...])

    # DevTools (async resource)
    devtools = client.with_provider("devtoolbox").devtools  # uses async under the hood
```
