# Exceptions Reference

> **Repository:** https://github.com/Alqudimi/PolyAI

```python
from polyai.exceptions import UniversalAIError, AuthenticationError, ...
```

---

## Exception Hierarchy

```
UniversalAIError (base)
├── AuthenticationError         # 401
├── PermissionDeniedError       # 403
├── RateLimitError              # 429
├── InvalidRequestError         # 400, 422
│   └── ContextLengthExceededError
├── ModelNotFoundError          # 404
├── ProviderError               # 5xx
│   └── ProviderUnavailableError  # 503
├── TimeoutError
├── ConnectionError
├── StreamingError
├── ContentFilterError
├── RetryExhaustedError
├── FeatureNotSupportedError
└── ProviderNotSupportedError
```

---

## Base Class: `UniversalAIError`

All PolyAI exceptions inherit from this.

```python
class UniversalAIError(Exception):
    message: str          # human-readable error message
    provider: str | None  # which provider raised the error
    status_code: int | None  # HTTP status code (if applicable)
    request_id: str | None   # provider request ID (if returned)
    response: dict | None    # raw provider response body
```

**Usage:**
```python
from polyai.exceptions import UniversalAIError

try:
    response = client.chat(...)
except UniversalAIError as e:
    print(f"Error: {e}")
    print(f"Provider: {e.provider}")
    print(f"HTTP Status: {e.status_code}")
```

---

## `AuthenticationError`

**HTTP Status:** 401

Raised when the API key is missing, invalid, or expired.

```python
from polyai.exceptions import AuthenticationError

try:
    client.chat(...)
except AuthenticationError as e:
    print(f"Auth failed: {e}")
    # Fix: check your API key, regenerate if expired
```

**Common causes:**
- Empty `OVHCLOUD_API_KEY` when the provider requires one
- Expired API key
- Typo in the key

---

## `PermissionDeniedError`

**HTTP Status:** 403

Raised when the API key is valid but lacks permission for the requested operation.

```python
from polyai.exceptions import PermissionDeniedError

try:
    client.chat(...)
except PermissionDeniedError as e:
    print(f"Permission denied: {e}")
    # Fix: check API key scopes, upgrade account tier
```

---

## `RateLimitError`

**HTTP Status:** 429

Raised when the provider's rate limit is exceeded.

```python
class RateLimitError(UniversalAIError):
    retry_after: float | None  # seconds to wait before retrying
```

**Usage:**
```python
import time
from polyai.exceptions import RateLimitError

try:
    response = client.chat(...)
except RateLimitError as e:
    wait = e.retry_after or 60
    print(f"Rate limited. Waiting {wait}s...")
    time.sleep(wait)
    # retry...
```

**Note:** PolyAI automatically retries on 429 by default (up to `max_retries` times). You'll only see this exception if retries are exhausted.

---

## `InvalidRequestError`

**HTTP Status:** 400, 422

Raised when the request parameters are invalid.

```python
from polyai.exceptions import InvalidRequestError

try:
    client.chat(provider="ovhcloud", model="...", messages=[])  # empty messages
except InvalidRequestError as e:
    print(f"Bad request: {e}")
```

**Common causes:**
- Empty `messages` list
- `max_tokens` below 1
- Invalid `temperature` value
- Unsupported parameter for the provider

### `ContextLengthExceededError`

Subclass of `InvalidRequestError`. Raised when the prompt is too long.

```python
from polyai.exceptions import ContextLengthExceededError

try:
    client.chat(...)  # prompt with 200k tokens
except ContextLengthExceededError:
    # Truncate the messages and retry
    messages = truncate_messages(messages, max_tokens=3000)
    response = client.chat(messages=messages, ...)
```

---

## `ModelNotFoundError`

**HTTP Status:** 404

Raised when the requested model ID doesn't exist.

```python
from polyai.exceptions import ModelNotFoundError

try:
    client.chat(provider="ovhcloud", model="nonexistent-model", ...)
except ModelNotFoundError as e:
    print(f"Model not found: {e}")
    models = client.list_models("ovhcloud")
    print(f"Available: {[m['id'] for m in models]}")
```

---

## `ProviderError`

**HTTP Status:** 500, 502, 504

Raised on server-side errors from the provider.

```python
from polyai.exceptions import ProviderError

try:
    client.chat(...)
except ProviderError as e:
    print(f"Provider error (HTTP {e.status_code}): {e}")
    # Usually transient — PolyAI retries automatically
```

### `ProviderUnavailableError`

**HTTP Status:** 503

The provider is temporarily unavailable (maintenance, overload).

```python
from polyai.exceptions import ProviderUnavailableError

try:
    client.chat(...)
except ProviderUnavailableError:
    # Switch to backup provider
    response = client.chat(provider="pollinations", ...)
```

---

## `TimeoutError`

Raised when the request exceeds the configured timeout.

```python
from polyai.exceptions import TimeoutError

try:
    client.chat(..., timeout=5.0)
except TimeoutError:
    print("Request timed out — try a higher timeout or a faster provider")
```

---

## `ConnectionError`

Raised when the network is unreachable or DNS fails.

```python
from polyai.exceptions import ConnectionError

try:
    client.chat(...)
except ConnectionError:
    print("Network unreachable")
```

---

## `StreamingError`

Raised when the SSE stream contains malformed data.

```python
from polyai.exceptions import StreamingError

try:
    for chunk in client.chat_stream(...):
        print(chunk.delta, end="")
except StreamingError as e:
    print(f"Streaming error: {e}")
```

---

## `ContentFilterError`

Raised when the provider's content filter blocks the request or response.

```python
from polyai.exceptions import ContentFilterError

try:
    client.chat(...)
except ContentFilterError:
    print("Content was filtered by the provider's safety system")
```

---

## `FeatureNotSupportedError`

Raised when you request a feature the provider doesn't implement.

```python
from polyai.exceptions import FeatureNotSupportedError

try:
    client.embed(provider="mlvoca", input=["hello"], model="tinyllama")
except FeatureNotSupportedError as e:
    print(f"Feature not supported: {e}")
    # mlvoca doesn't support embeddings — use ovhcloud instead
```

---

## `ProviderNotSupportedError`

Raised when you pass an unknown provider name.

```python
from polyai.exceptions import ProviderNotSupportedError

try:
    client.chat(provider="openai", ...)  # openai is not a polyai provider
except ProviderNotSupportedError as e:
    print(f"Unknown provider: {e}")
    # Valid providers: ovhcloud, pollinations, mlvoca, devtoolbox
```

---

## `RetryExhaustedError`

Raised when all retry attempts are exhausted.

```python
class RetryExhaustedError(UniversalAIError):
    attempts: int          # number of attempts made
    last_error: Exception  # the final error that caused retry exhaustion
```

---

## Error Handling Patterns

### Catch Everything
```python
from polyai.exceptions import UniversalAIError

try:
    response = client.chat(...)
except UniversalAIError as e:
    handle_ai_error(e)
```

### Tiered Handling
```python
from polyai.exceptions import (
    AuthenticationError, RateLimitError, ProviderUnavailableError, UniversalAIError
)

try:
    response = client.chat(...)
except AuthenticationError:
    alert_ops("API key invalid")
    raise
except RateLimitError as e:
    time.sleep(e.retry_after or 60)
    response = client.chat(...)  # one manual retry
except ProviderUnavailableError:
    response = client.chat(provider="pollinations", ...)  # failover
except UniversalAIError as e:
    log_error(e)
    raise
```
