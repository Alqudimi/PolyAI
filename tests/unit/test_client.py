"""Unit tests for the top-level Client and AsyncClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from polyai import AsyncClient, Client
from polyai.config import ClientConfig
from polyai.exceptions import ProviderNotSupportedError
from polyai.types import ChatResponse
from tests.mocks.mock_responses import (
    CHAT_RESPONSE_OPENAI,
    EMBEDDING_RESPONSE,
    IMAGE_RESPONSE,
    OLLAMA_RESPONSE,
    DEVTOOLBOX_GENERATE_RESPONSE,
)


@pytest.fixture
def config():
    return ClientConfig(
        ovhcloud_api_key="test-key",
        pollinations_api_key="sk_test",
        devtoolbox_api_key="dtb_test",
        timeout=5.0,
        max_retries=0,
    )


class TestClientProviderRouting:
    def test_unknown_provider_raises(self, config):
        client = Client(config=config)
        with pytest.raises(ProviderNotSupportedError):
            client.chat(provider="nonexistent", model="m", messages=[])

    def test_with_provider_returns_correct_type(self, config):
        from polyai.client import ProviderClient
        client = Client(config=config)
        pc = client.with_provider("ovhcloud")
        assert isinstance(pc, ProviderClient)
        assert pc.name == "ovhcloud"

    def test_provider_cached(self, config):
        client = Client(config=config)
        p1 = client._get_provider("ovhcloud")
        p2 = client._get_provider("ovhcloud")
        assert p1 is p2

    def test_all_four_providers_instantiate(self, config):
        client = Client(config=config)
        for name in ["ovhcloud", "pollinations", "mlvoca", "devtoolbox"]:
            provider = client._get_provider(name)
            assert provider.name == name

    def test_context_manager(self, config):
        with Client(config=config) as client:
            assert isinstance(client, Client)

    def test_repr(self, config):
        client = Client(config=config)
        r = repr(client)
        assert "Client" in r


class TestClientChatUnified:
    def test_chat_ovhcloud(self, config):
        client = Client(config=config)
        with patch.object(client._get_provider("ovhcloud")._transport, "request", return_value=CHAT_RESPONSE_OPENAI):
            resp = client.chat("ovhcloud", "meta-llama-3_3-70b-instruct", [{"role": "user", "content": "Hi"}])
        assert isinstance(resp, ChatResponse)
        assert resp.provider == "ovhcloud"

    def test_chat_mlvoca(self, config):
        client = Client(config=config)
        with patch.object(client._get_provider("mlvoca")._transport, "request", return_value=OLLAMA_RESPONSE):
            resp = client.chat("mlvoca", "tinyllama", [{"role": "user", "content": "Hi"}])
        assert resp.provider == "mlvoca"

    def test_chat_devtoolbox(self, config):
        client = Client(config=config)
        with patch.object(client._get_provider("devtoolbox")._transport, "request", return_value=DEVTOOLBOX_GENERATE_RESPONSE):
            resp = client.chat("devtoolbox", "devtoolbox-ai", [{"role": "user", "content": "Hi"}])
        assert resp.provider == "devtoolbox"

    def test_chat_stream(self, config):
        import json
        client = Client(config=config)
        chunks_data = [
            json.dumps({
                "id": "s1", "model": "test",
                "choices": [{"index": 0, "delta": {"content": "Hi"}, "finish_reason": None}],
            }),
            json.dumps({
                "id": "s1", "model": "test",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }),
        ]
        with patch.object(client._get_provider("ovhcloud")._transport, "stream", return_value=iter(chunks_data)):
            chunks = list(client.chat_stream("ovhcloud", "model", [{"role": "user", "content": "hi"}]))
        text = "".join(c.delta for c in chunks)
        assert "Hi" in text

    def test_chat_accumulate(self, config):
        import json
        client = Client(config=config)
        chunks_data = [
            json.dumps({
                "id": "s1", "model": "llama",
                "choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": None}],
            }),
            json.dumps({
                "id": "s1", "model": "llama",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }),
        ]
        received = []
        with patch.object(client._get_provider("ovhcloud")._transport, "stream", return_value=iter(chunks_data)):
            resp = client.chat_accumulate(
                "ovhcloud", "model", [{"role": "user", "content": "hi"}],
                on_chunk=lambda c: received.append(c.delta),
            )
        assert resp.text == "Hello"
        assert "Hello" in received

    def test_generate_image(self, config):
        client = Client(config=config)
        with patch.object(client._get_provider("ovhcloud")._transport, "request", return_value=IMAGE_RESPONSE):
            resp = client.generate_image("ovhcloud", "a sunset")
        assert resp.url is not None

    def test_embed(self, config):
        client = Client(config=config)
        with patch.object(client._get_provider("ovhcloud")._transport, "request", return_value=EMBEDDING_RESPONSE):
            resp = client.embed("ovhcloud", ["hello", "world"], "bge-m3")
        assert len(resp.embeddings) == 2

    def test_list_models(self, config):
        client = Client(config=config)
        with patch.object(client._get_provider("ovhcloud")._transport, "request", return_value={"data": [{"id": "m1"}]}):
            models = client.list_models("ovhcloud")
        assert len(models) == 1


@pytest.mark.asyncio
class TestAsyncClient:
    async def test_async_chat(self, config):
        from polyai import AsyncClient
        client = AsyncClient(config=config)
        mock = AsyncMock(return_value=CHAT_RESPONSE_OPENAI)
        with patch.object(client._get_provider("ovhcloud")._async_transport, "request", mock):
            resp = await client.chat("ovhcloud", "model", [{"role": "user", "content": "hi"}])
        assert isinstance(resp, ChatResponse)
        await client.aclose()

    async def test_async_context_manager(self, config):
        async with AsyncClient(config=config) as client:
            assert isinstance(client, AsyncClient)

    async def test_chat_many_concurrent(self, config):
        from unittest.mock import AsyncMock
        client = AsyncClient(config=config)

        mock_fn = AsyncMock(return_value=CHAT_RESPONSE_OPENAI)

        with patch.object(client._get_provider("ovhcloud")._async_transport, "request", mock_fn):
            requests = [
                {"provider": "ovhcloud", "model": "m", "messages": [{"role": "user", "content": f"Q{i}"}]}
                for i in range(3)
            ]
            responses = await client.chat_many(requests)

        assert len(responses) == 3
        for r in responses:
            assert isinstance(r, ChatResponse)
        await client.aclose()

    async def test_repr(self, config):
        client = AsyncClient(config=config)
        assert "AsyncClient" in repr(client)
        await client.aclose()
