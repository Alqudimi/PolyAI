# Testing Guide

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Overview

PolyAI has two test suites:

| Suite | Location | Requires Network | Run in CI |
|---|---|:---:|:---:|
| **Unit tests** | `tests/unit/` | ❌ Fully offline | ✅ Always |
| **Integration tests** | `tests/integration/` | ✅ Live providers | ✅ Nightly only |

---

## Running Unit Tests

```bash
# All unit tests
pytest tests/unit -v

# Quick check (no output on pass)
pytest tests/unit -q

# With coverage report
pytest tests/unit --cov=polyai --cov-report=term-missing

# Specific test file
pytest tests/unit/test_providers.py -v

# Specific test
pytest tests/unit/test_providers.py::TestOVHcloudProvider::test_chat -v

# Run tests matching a keyword
pytest tests/unit -k "streaming" -v
```

---

## Running Integration Tests

```bash
# Requires live API credentials
export OVHCLOUD_API_KEY="your-key"
export POLLINATIONS_API_KEY="sk_..."

# Enable integration test mode
export UNIVERSAL_AI_INTEGRATION_TESTS=1

# Run all integration tests
pytest tests/integration -v

# One provider only
pytest tests/integration/test_ovhcloud.py -v
```

---

## Test Infrastructure

### `respx` for HTTP Mocking

PolyAI uses [respx](https://lundberg.github.io/respx/) to mock httpx requests:

```python
import respx
import httpx

@respx.mock
def test_chat():
    respx.post("https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
        })
    )
    client = Client()
    resp = client.chat(provider="ovhcloud", model="llama-3.1-8b-instruct", messages=[...])
    assert resp.text == "Hello!"
```

### Alternative: `MagicMock` on Transport

For unit-testing providers directly without respx:

```python
from unittest.mock import MagicMock
from polyai.providers.ovhcloud import OVHcloudProvider
from polyai.config import ClientConfig

def test_chat_direct():
    config = ClientConfig(max_retries=0)
    mock_transport = MagicMock()
    mock_transport.post.return_value = {
        "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
    }
    provider = OVHcloudProvider(config=config, transport=mock_transport)
    response = provider.chat(model="llama", messages=[{"role": "user", "content": "Hi"}])
    assert response.text == "Hello!"
```

---

## Writing Unit Tests

### Test File Structure

```python
# tests/unit/test_providers.py

import pytest
from unittest.mock import MagicMock
from polyai.config import ClientConfig
from polyai.providers.ovhcloud import OVHcloudProvider
from polyai.exceptions import AuthenticationError, RateLimitError

MOCK_CHAT_RESPONSE = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "choices": [{
        "index": 0,
        "message": {"role": "assistant", "content": "Paris"},
        "finish_reason": "stop",
    }],
    "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
    "model": "llama-3.1-8b-instruct",
}


class TestOVHcloudProvider:

    @pytest.fixture
    def provider(self):
        config = ClientConfig(ovhcloud_api_key="test-key", max_retries=0)
        transport = MagicMock()
        return OVHcloudProvider(config=config, transport=transport)

    # ── Happy path ─────────────────────────────────────────────────

    def test_chat_returns_response(self, provider):
        provider._transport.post.return_value = MOCK_CHAT_RESPONSE
        resp = provider.chat(
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": "Capital of France?"}],
        )
        assert resp.text == "Paris"
        assert resp.finish_reason == "stop"
        assert resp.usage.total_tokens == 11

    def test_system_prompt_prepended(self, provider):
        provider._transport.post.return_value = MOCK_CHAT_RESPONSE
        provider.chat(
            model="llama",
            messages=[{"role": "user", "content": "Hi"}],
            system="You are a pirate.",
        )
        call_args = provider._transport.post.call_args
        messages_sent = call_args[1]["json"]["messages"]
        assert messages_sent[0]["role"] == "system"
        assert messages_sent[0]["content"] == "You are a pirate."

    def test_json_mode_sets_response_format(self, provider):
        provider._transport.post.return_value = MOCK_CHAT_RESPONSE
        provider.chat(model="llama", messages=[...], json_mode=True)
        payload = provider._transport.post.call_args[1]["json"]
        assert payload["response_format"] == {"type": "json_object"}

    # ── Error paths ─────────────────────────────────────────────────

    def test_auth_error_propagates(self, provider):
        provider._transport.post.side_effect = AuthenticationError("401", provider="ovhcloud")
        with pytest.raises(AuthenticationError):
            provider.chat(model="llama", messages=[{"role": "user", "content": "hi"}])

    def test_rate_limit_error_propagates(self, provider):
        provider._transport.post.side_effect = RateLimitError("429", provider="ovhcloud")
        with pytest.raises(RateLimitError):
            provider.chat(model="llama", messages=[{"role": "user", "content": "hi"}])

    # ── Streaming ───────────────────────────────────────────────────

    def test_streaming_yields_chunks(self, provider):
        provider._transport.stream.return_value = iter([
            'data: {"choices": [{"delta": {"content": "Hel"}, "finish_reason": null}]}',
            'data: {"choices": [{"delta": {"content": "lo!"}, "finish_reason": "stop"}]}',
            "data: [DONE]",
        ])
        chunks = list(provider.chat_stream(model="llama", messages=[{"role": "user", "content": "hi"}]))
        assert len(chunks) == 2
        assert "".join(c.delta for c in chunks) == "Hello!"

    def test_streaming_skips_empty_lines(self, provider):
        provider._transport.stream.return_value = iter([
            "",
            ": keep-alive",
            'data: {"choices": [{"delta": {"content": "hi"}, "finish_reason": "stop"}]}',
            "data: [DONE]",
        ])
        chunks = list(provider.chat_stream(model="llama", messages=[...]))
        assert len(chunks) == 1
```

---

## Test Coverage

Target: **>90% line coverage** on `polyai/` package.

```bash
# Generate HTML report
pytest tests/unit --cov=polyai --cov-report=html
open htmlcov/index.html

# Fail if coverage drops below threshold
pytest tests/unit --cov=polyai --cov-fail-under=90
```

Coverage is automatically reported to Codecov on every CI run.

---

## Fixtures

Shared fixtures are in `tests/conftest.py`:

```python
# tests/conftest.py
import pytest
from polyai import Client, AsyncClient
from polyai.config import ClientConfig

@pytest.fixture
def client():
    """Sync client with no retries for tests."""
    return Client(config=ClientConfig(max_retries=0))

@pytest.fixture
async def async_client():
    """Async client for async tests."""
    async with AsyncClient(config=ClientConfig(max_retries=0)) as c:
        yield c

@pytest.fixture
def mock_chat_response():
    return {
        "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
    }
```

---

## Async Tests

pytest-asyncio is configured with `asyncio_mode = "auto"` — no decorator needed:

```python
# tests/unit/test_async.py

async def test_async_chat():
    from polyai import AsyncClient
    from unittest.mock import AsyncMock, MagicMock, patch

    client = AsyncClient(config=ClientConfig(max_retries=0))
    mock_response = MagicMock()
    mock_response.text = "Hello async!"

    with patch.object(client, "chat", new_callable=AsyncMock, return_value=mock_response):
        response = await client.chat(
            provider="ovhcloud",
            model="llama",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert response.text == "Hello async!"
    await client.aclose()
```

---

## Pre-Commit Checks

Run all checks locally before pushing:

```bash
# Lint
ruff check polyai tests

# Format check
ruff format --check polyai tests

# Type check
mypy polyai --ignore-missing-imports

# Tests
pytest tests/unit -q

# Or all at once:
pre-commit run --all-files
```
