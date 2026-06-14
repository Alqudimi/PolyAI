# Coding Standards

> **Repository:** https://github.com/Alqudimi/PolyAI

This document defines the coding standards for all PolyAI contributors.

---

## Tools

| Tool | Purpose | Config |
|---|---|---|
| **Ruff** | Linter + formatter (replaces flake8, isort, black, pyupgrade) | `[tool.ruff]` in `pyproject.toml` |
| **MyPy** | Static type checker | `[tool.mypy]` in `pyproject.toml` |
| **pytest** | Test runner | `[tool.pytest.ini_options]` in `pyproject.toml` |
| **pre-commit** | Git hooks | `.pre-commit-config.yaml` |

---

## Python Style

### Line Length

100 characters maximum.

### String Quotes

Double quotes preferred (enforced by Ruff).

```python
# Good ✅
message = "Hello, world!"

# Avoid ❌
message = 'Hello, world!'
```

### Import Order

Ruff handles import sorting automatically. Manual order:
1. Standard library (`import os`, `import json`)
2. Third-party (`import httpx`)
3. Local (`from polyai import Client`)

Always use `from __future__ import annotations` at the top of every module:

```python
from __future__ import annotations

import json
import os
from typing import Any

import httpx

from polyai.config import ClientConfig
```

---

## Type Annotations

**All** public functions and methods must be fully type-annotated.

```python
# Good ✅
def chat(
    self,
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ChatResponse:
    ...

# Bad ❌
def chat(self, provider, model, messages, temperature=None, max_tokens=None):
    ...
```

### Type Alias Rules

- Use `X | Y` (Python 3.10+ union syntax) — works because of `from __future__ import annotations`
- Use `list[str]` not `List[str]` (lowercase generics)
- Use `dict[str, Any]` not `Dict[str, Any]`

```python
# Good ✅
def foo(x: str | None = None) -> list[dict[str, Any]]:
    ...

# Bad ❌
from typing import Optional, List, Dict
def foo(x: Optional[str] = None) -> List[Dict[str, Any]]:
    ...
```

---

## Docstrings

All **public** classes, methods, and functions must have docstrings in Google style.

```python
def embed(
    self,
    provider: str,
    input: str | list[str],
    model: str,
    timeout: float | None = None,
) -> EmbeddingResponse:
    """Generate text embeddings.

    Args:
        provider: Provider name. Only "ovhcloud" and "pollinations" support embeddings.
        input: Text or list of texts to embed.
        model: Embedding model ID (e.g. "bge-m3" for OVHcloud).
        timeout: Per-request timeout override in seconds.

    Returns:
        EmbeddingResponse containing a list of Embedding objects.

    Raises:
        FeatureNotSupportedError: If provider does not support embeddings.
        AuthenticationError: If the API key is invalid.
        UniversalAIError: For any other provider error.

    Example:
        >>> client = Client()
        >>> result = client.embed(
        ...     provider="ovhcloud",
        ...     input=["Hello", "World"],
        ...     model="bge-m3",
        ... )
        >>> print(result.embeddings[0].dimensions)
        1024
    """
```

Internal/private methods (prefixed with `_`) do not require docstrings, but complex ones should have comments.

---

## Error Handling

### Always raise PolyAI exceptions

```python
# Good ✅
from polyai.exceptions import FeatureNotSupportedError, InvalidRequestError

if not messages:
    raise InvalidRequestError("messages cannot be empty", provider=self.name)

# Bad ❌
raise ValueError("messages cannot be empty")
```

### HTTP errors → typed exceptions

In transport/provider code, always map HTTP status codes to the appropriate exception:

```python
STATUS_CODE_MAP = {
    400: InvalidRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: ModelNotFoundError,
    422: InvalidRequestError,
    429: RateLimitError,
    500: ProviderError,
    502: ProviderError,
    503: ProviderUnavailableError,
    504: ProviderError,
}
```

---

## Security Practices

### Never log secrets

```python
# Good ✅
logger.debug("Request sent to %s", provider_name)

# Bad ❌
logger.debug("Request with key %s", api_key)
```

### Mask secrets in repr

All classes that hold secrets must override `__repr__`:

```python
class BearerCredentials:
    def __init__(self, token: str) -> None:
        self._token = token

    @property
    def _masked(self) -> str:
        if len(self._token) <= 8:
            return "***"
        return self._token[:4] + "..." + self._token[-4:]

    def __repr__(self) -> str:
        return f"BearerCredentials(token='{self._masked}')"

    def __str__(self) -> str:
        return self.__repr__()
```

---

## Naming Conventions

| Type | Convention | Example |
|---|---|---|
| Classes | `PascalCase` | `OVHcloudProvider` |
| Functions/methods | `snake_case` | `chat_stream()` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT = 60.0` |
| Private attributes | `_leading_underscore` | `self._transport` |
| Module names | `lowercase` | `transport.py` |
| Type aliases | `PascalCase` | `MessageList = list[dict]` |

---

## File Structure

Each module should have this structure:

```python
"""Module docstring — one sentence describing what this module does."""

from __future__ import annotations

# Standard library imports
import json
import os
from typing import Any

# Third-party imports
import httpx

# Internal imports
from polyai.config import ClientConfig
from polyai.exceptions import UniversalAIError

# Module-level constants
DEFAULT_TIMEOUT: float = 60.0
BASE_URL: str = "https://api.example.com/v1"


# Classes and functions
class MyClass:
    """Class docstring."""

    def __init__(self, config: ClientConfig) -> None:
        ...
```

---

## Testing Standards

- All new features require unit tests
- All unit tests must pass offline (no network calls)
- Aim for >90% line coverage on new code
- Use `pytest.mark.parametrize` for multiple similar test cases

See [Testing Guide](testing.md) for details.

---

## Running Checks

```bash
# All checks — run before every PR
ruff check polyai tests        # lint
ruff format polyai tests       # format
mypy polyai                    # type check
pytest tests/unit -q           # tests
```

Or all at once:
```bash
pre-commit run --all-files
```
