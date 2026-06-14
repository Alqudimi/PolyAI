"""
Integration tests for mlvoca Free LLM API.

No API key required — tests make real HTTP calls to mlvoca.com.
Gated behind UNIVERSAL_AI_INTEGRATION_TESTS=1.

Note: mlvoca is for non-commercial use only.

Run:
    UNIVERSAL_AI_INTEGRATION_TESTS=1 pytest tests/integration/test_mlvoca.py -v
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
    config = ClientConfig(timeout=120.0, max_retries=1)
    c = Client(config=config)
    yield c
    c.close()


@INTEGRATION
class TestMlvocaChat:
    def test_basic_chat_tinyllama(self, client):
        resp = client.chat(
            provider="mlvoca",
            model="tinyllama",
            messages=[{"role": "user", "content": "What is 2+2? Reply with just the number."}],
        )
        assert resp.text.strip()
        assert resp.provider == "mlvoca"
        assert resp.model == "tinyllama"

    def test_basic_chat_deepseek(self, client):
        resp = client.chat(
            provider="mlvoca",
            model="deepseek-r1:1.5b",
            messages=[{"role": "user", "content": "What is 1+1? Reply with just the number."}],
        )
        assert resp.text.strip()

    def test_streaming(self, client):
        chunks = list(client.chat_stream(
            provider="mlvoca",
            model="tinyllama",
            messages=[{"role": "user", "content": "Say 'hello' only."}],
        ))
        assert len(chunks) > 0
        text = "".join(c.delta for c in chunks)
        assert text.strip()

    def test_multi_turn_conversation(self, client):
        messages = [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
            {"role": "user", "content": "What is my name?"},
        ]
        resp = client.chat(provider="mlvoca", model="tinyllama", messages=messages)
        assert resp.text.strip()

    def test_list_models(self, client):
        models = client.list_models("mlvoca")
        assert len(models) == 2
        ids = [m["id"] for m in models]
        assert "tinyllama" in ids


@INTEGRATION
class TestMlvocaUnsupported:
    def test_embeddings_not_supported(self, client):
        from polyai.exceptions import FeatureNotSupportedError
        with pytest.raises(FeatureNotSupportedError):
            client.embed("mlvoca", ["hello"], "some-model")

    def test_image_generation_not_supported(self, client):
        from polyai.exceptions import FeatureNotSupportedError
        with pytest.raises(FeatureNotSupportedError):
            client.generate_image("mlvoca", "a sunset")
