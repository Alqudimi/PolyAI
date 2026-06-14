"""
Integration tests for OVHcloud AI Endpoints.

These tests make real HTTP calls and require a valid (or empty-string anonymous)
API key.  They are skipped automatically unless UNIVERSAL_AI_INTEGRATION_TESTS=1
is set in the environment.

Run:
    UNIVERSAL_AI_INTEGRATION_TESTS=1 pytest tests/integration/test_ovhcloud.py -v
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
        ovhcloud_api_key=os.environ.get("OVHCLOUD_API_KEY", ""),
        timeout=60.0,
        max_retries=2,
    )
    c = Client(config=config)
    yield c
    c.close()


@INTEGRATION
class TestOVHcloudChat:
    def test_basic_chat(self, client):
        resp = client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": "Say 'hello world' and nothing else."}],
            max_tokens=20,
        )
        assert resp.text.strip()
        assert resp.model
        assert resp.provider == "ovhcloud"
        assert resp.usage.total_tokens > 0

    def test_streaming_chat(self, client):
        chunks = list(client.chat_stream(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": "Count from 1 to 5."}],
            max_tokens=50,
        ))
        assert len(chunks) > 0
        text = "".join(c.delta for c in chunks)
        assert text.strip()

    def test_system_prompt(self, client):
        resp = client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": "Who are you?"}],
            system="You are a pirate named Jack. Always respond in pirate speak.",
            max_tokens=50,
        )
        assert resp.text.strip()

    def test_json_mode(self, client):
        import json
        resp = client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": 'Return a JSON object with keys "name" and "age".'}],
            json_mode=True,
            max_tokens=100,
        )
        try:
            data = json.loads(resp.text)
            assert "name" in data or "age" in data
        except json.JSONDecodeError:
            pass

    def test_temperature_zero(self, client):
        resp1 = client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": "What is 2+2? Just the number."}],
            temperature=0.0,
            max_tokens=10,
        )
        resp2 = client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": "What is 2+2? Just the number."}],
            temperature=0.0,
            max_tokens=10,
        )
        assert "4" in resp1.text
        assert "4" in resp2.text


@INTEGRATION
class TestOVHcloudEmbeddings:
    def test_basic_embed(self, client):
        resp = client.embed(
            provider="ovhcloud",
            input=["The quick brown fox"],
            model="bge-m3",
        )
        assert len(resp.embeddings) == 1
        assert len(resp.embeddings[0].vector) > 0

    def test_batch_embed(self, client):
        texts = ["Hello world", "Bonjour monde", "Hola mundo"]
        resp = client.embed(provider="ovhcloud", input=texts, model="bge-m3")
        assert len(resp.embeddings) == 3

    def test_cosine_similarity(self, client):
        resp = client.embed(
            provider="ovhcloud",
            input=["king", "queen"],
            model="bge-m3",
        )
        sim = resp.embeddings[0].cosine_similarity(resp.embeddings[1])
        assert -1.0 <= sim <= 1.0


@INTEGRATION
class TestOVHcloudModels:
    def test_list_models(self, client):
        models = client.list_models("ovhcloud")
        assert isinstance(models, list)
        assert len(models) > 0
        assert all("id" in m for m in models)
