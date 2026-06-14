"""
Integration tests for Pollinations.AI.

Pollinations has a free anonymous tier — these tests can run without any API key.
Still gated behind UNIVERSAL_AI_INTEGRATION_TESTS=1 to avoid CI rate limits.

Run:
    UNIVERSAL_AI_INTEGRATION_TESTS=1 pytest tests/integration/test_pollinations.py -v
"""

from __future__ import annotations

import os

import pytest

from polyai import Client
from polyai.config import ClientConfig

SKIP_REASON = "Set UNIVERSAL_AI_INTEGRATION_TESTS=1 to run integration tests"
INTEGRATION = pytest.mark.skipif(
    os.environ.get("UNIVERSAL_AI_INTEGRATION_TESTS") != "1",
    reason=SKIP_REASON,
)


@pytest.fixture(scope="module")
def client():
    config = ClientConfig(
        pollinations_api_key=os.environ.get("POLLINATIONS_API_KEY", ""),
        timeout=60.0,
        max_retries=2,
    )
    c = Client(config=config)
    yield c
    c.close()


@INTEGRATION
class TestPollinationsChat:
    def test_basic_chat(self, client):
        resp = client.chat(
            provider="pollinations",
            model="openai",
            messages=[{"role": "user", "content": "Say exactly: hello world"}],
            max_tokens=20,
        )
        assert resp.text.strip()
        assert resp.provider == "pollinations"

    def test_streaming(self, client):
        chunks = list(client.chat_stream(
            provider="pollinations",
            model="openai",
            messages=[{"role": "user", "content": "Count 1 to 3."}],
            max_tokens=30,
        ))
        assert len(chunks) > 0
        text = "".join(c.delta for c in chunks)
        assert text.strip()

    def test_list_models(self, client):
        models = client.list_models("pollinations")
        assert isinstance(models, list)
        assert len(models) > 0


@INTEGRATION
class TestPollinationsImages:
    def test_generate_image_url(self, client):
        from polyai.providers.pollinations import PollinationsProvider
        provider = client._get_provider("pollinations")
        assert isinstance(provider, PollinationsProvider)
        url = provider.generate_image_url("a red apple", model="flux", width=256, height=256)
        assert url.startswith("https://image.pollinations.ai")
        assert "flux" in url


@INTEGRATION
class TestPollinationsTTS:
    def test_text_to_speech(self, client):
        audio = client.text_to_speech(
            provider="pollinations",
            text="Hello, world!",
            voice="alloy",
        )
        assert len(audio.content) > 0
        assert "audio" in audio.content_type
