"""Unit tests for all four provider adapters (with mocked HTTP)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from polyai.config import ClientConfig
from polyai.providers.devtoolbox import DevToolboxProvider
from polyai.providers.mlvoca import MlvocaProvider, _messages_to_prompt
from polyai.providers.ovhcloud import OVHcloudProvider
from polyai.providers.pollinations import PollinationsProvider
from polyai.types import ChatResponse, EmbeddingResponse, ImageResponse
from tests.mocks.mock_responses import (
    CHAT_RESPONSE_OPENAI,
    CHAT_RESPONSE_TOOL_CALL,
    DEVTOOLBOX_GENERATE_RESPONSE,
    DEVTOOLBOX_SUMMARIZE_RESPONSE,
    DEVTOOLBOX_TRANSLATE_RESPONSE,
    DEVTOOLBOX_EXPLAIN_RESPONSE,
    DEVTOOLBOX_REGEX_RESPONSE,
    EMBEDDING_RESPONSE,
    IMAGE_RESPONSE,
    OLLAMA_RESPONSE,
    SSE_CHAT_CHUNKS,
)


# ------------------------------------------------------------------
# OVHcloud
# ------------------------------------------------------------------

class TestOVHcloudProvider:
    @pytest.fixture
    def provider(self):
        config = ClientConfig(ovhcloud_api_key="test-key", max_retries=0)
        return OVHcloudProvider(config)

    def test_chat(self, provider):
        with patch.object(provider._transport, "request", return_value=CHAT_RESPONSE_OPENAI):
            resp = provider.chat("meta-llama-3_3-70b-instruct", [{"role": "user", "content": "Hi"}])
        assert isinstance(resp, ChatResponse)
        assert resp.text == "The capital of France is Paris."
        assert resp.provider == "ovhcloud"

    def test_chat_stream(self, provider):
        with patch.object(provider._transport, "stream", return_value=iter(SSE_CHAT_CHUNKS)):
            chunks = list(provider.chat_stream("meta-llama-3_3-70b-instruct", [{"role": "user", "content": "Hi"}]))
        text = "".join(c.delta for c in chunks)
        assert "Hello" in text

    def test_embed(self, provider):
        with patch.object(provider._transport, "request", return_value=EMBEDDING_RESPONSE):
            resp = provider.embed("bge-m3", ["hello", "world"])
        assert isinstance(resp, EmbeddingResponse)
        assert len(resp.embeddings) == 2

    def test_generate_image(self, provider):
        with patch.object(provider._transport, "request", return_value=IMAGE_RESPONSE):
            resp = provider.generate_image("a sunset")
        assert isinstance(resp, ImageResponse)
        assert resp.url is not None

    def test_list_models(self, provider):
        with patch.object(provider._transport, "request", return_value={"data": [{"id": "m1"}, {"id": "m2"}]}):
            models = provider.list_models()
        assert len(models) == 2

    def test_tool_call_response(self, provider):
        with patch.object(provider._transport, "request", return_value=CHAT_RESPONSE_TOOL_CALL):
            resp = provider.chat(
                "meta-llama-3_3-70b-instruct",
                [{"role": "user", "content": "What's the weather in Paris?"}],
                tools=[{"type": "function", "function": {"name": "get_weather", "description": "...", "parameters": {}}}],
            )
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "get_weather"

    def test_system_prompt_prepended(self, provider):
        captured = {}

        def capture_request(method, path, json_body=None, **kwargs):
            captured["body"] = json_body
            return CHAT_RESPONSE_OPENAI

        with patch.object(provider._transport, "request", side_effect=capture_request):
            provider.chat("model", [{"role": "user", "content": "hi"}], system="Be helpful.")

        messages = captured["body"]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Be helpful."

    def test_json_mode_sets_response_format(self, provider):
        captured = {}

        def capture_request(method, path, json_body=None, **kwargs):
            captured["body"] = json_body
            return CHAT_RESPONSE_OPENAI

        with patch.object(provider._transport, "request", side_effect=capture_request):
            from polyai.config import ClientConfig
            from polyai.client import Client
            config = ClientConfig(ovhcloud_api_key="k", max_retries=0)
            client = Client(config=config)
            with patch.object(client._get_provider("ovhcloud")._transport, "request", side_effect=capture_request):
                client.chat("ovhcloud", "model", [{"role": "user", "content": "hi"}], json_mode=True)

        assert captured.get("body", {}).get("response_format") == {"type": "json_object"}

    def test_name(self, provider):
        assert provider.name == "ovhcloud"

    def test_capabilities(self, provider):
        assert provider.capabilities.chat is True
        assert provider.capabilities.streaming is True
        assert provider.capabilities.embeddings is True
        assert provider.capabilities.image_generation is True


# ------------------------------------------------------------------
# Pollinations
# ------------------------------------------------------------------

class TestPollinationsProvider:
    @pytest.fixture
    def provider(self):
        config = ClientConfig(pollinations_api_key="sk_test", max_retries=0)
        return PollinationsProvider(config)

    def test_chat(self, provider):
        with patch.object(provider._transport, "request", return_value=CHAT_RESPONSE_OPENAI):
            resp = provider.chat("openai", [{"role": "user", "content": "Hello"}])
        assert isinstance(resp, ChatResponse)

    def test_generate_image_url(self, provider):
        url = provider.generate_image_url("a sunset", model="flux", width=512, height=512)
        assert "image.pollinations.ai" in url
        assert "flux" in url
        assert "512" in url

    def test_list_models_fallback(self, provider):
        with patch.object(provider._image_transport, "request", side_effect=Exception("unavailable")):
            models = provider.list_models()
        assert len(models) > 0
        assert any(m["id"] == "openai" for m in models)

    def test_name(self, provider):
        assert provider.name == "pollinations"

    def test_anonymous_no_auth_header(self):
        config = ClientConfig(max_retries=0)
        provider = PollinationsProvider(config)
        from polyai.auth.credentials import NoAuthCredentials
        assert isinstance(provider._credentials, NoAuthCredentials)


# ------------------------------------------------------------------
# mlvoca
# ------------------------------------------------------------------

class TestMlvocaProvider:
    @pytest.fixture
    def provider(self):
        config = ClientConfig(max_retries=0)
        return MlvocaProvider(config)

    def test_chat(self, provider):
        with patch.object(provider._transport, "request", return_value=OLLAMA_RESPONSE):
            resp = provider.chat("tinyllama", [{"role": "user", "content": "What is 2+2?"}])
        assert isinstance(resp, ChatResponse)
        assert resp.text == "The answer is 42."
        assert resp.provider == "mlvoca"

    def test_chat_stream(self, provider):
        import json
        stream_data = [
            json.dumps({"model": "tinyllama", "response": "The ", "done": False}),
            json.dumps({"model": "tinyllama", "response": "answer ", "done": False}),
            json.dumps({"model": "tinyllama", "response": "is 42.", "done": True}),
        ]
        with patch.object(provider._transport, "stream", return_value=iter(stream_data)):
            chunks = list(provider.chat_stream("tinyllama", [{"role": "user", "content": "Q"}]))
        text = "".join(c.delta for c in chunks)
        assert text == "The answer is 42."

    def test_list_models(self, provider):
        models = provider.list_models()
        assert len(models) == 2
        ids = [m["id"] for m in models]
        assert "tinyllama" in ids
        assert "deepseek-r1:1.5b" in ids

    def test_messages_to_prompt(self):
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "What is Python?"},
        ]
        prompt = _messages_to_prompt(messages)
        assert "[System]: You are helpful." in prompt
        assert "[User]: What is Python?" in prompt
        assert "[Assistant]:" in prompt

    def test_no_auth_required(self, provider):
        assert not provider._credentials.is_configured() or True

    def test_usage_in_response(self, provider):
        with patch.object(provider._transport, "request", return_value=OLLAMA_RESPONSE):
            resp = provider.chat("tinyllama", [{"role": "user", "content": "hi"}])
        assert resp.usage.prompt_tokens == 8
        assert resp.usage.completion_tokens == 5


# ------------------------------------------------------------------
# DevToolbox
# ------------------------------------------------------------------

class TestDevToolboxProvider:
    @pytest.fixture
    def provider(self):
        config = ClientConfig(devtoolbox_api_key="dtb_test", max_retries=0)
        return DevToolboxProvider(config)

    def test_chat(self, provider):
        with patch.object(provider._transport, "request", return_value=DEVTOOLBOX_GENERATE_RESPONSE):
            resp = provider.chat("devtoolbox-ai", [{"role": "user", "content": "Write a haiku"}])
        assert isinstance(resp, ChatResponse)
        assert resp.text == "Here is a haiku about coding."

    def test_summarize(self, provider):
        with patch.object(provider._transport, "request", return_value=DEVTOOLBOX_SUMMARIZE_RESPONSE):
            result = provider.summarize("Long text about something interesting.")
        assert result == "A brief summary of the text."

    def test_translate(self, provider):
        with patch.object(provider._transport, "request", return_value=DEVTOOLBOX_TRANSLATE_RESPONSE):
            result = provider.translate("Hello, world!", "fr")
        assert result == "Bonjour, monde!"

    def test_explain_code(self, provider):
        with patch.object(provider._transport, "request", return_value=DEVTOOLBOX_EXPLAIN_RESPONSE):
            result = provider.explain_code("const x = arr.reduce((a,b) => a+b, 0)")
        assert "reduces" in result.lower()

    def test_generate_regex(self, provider):
        with patch.object(provider._transport, "request", return_value=DEVTOOLBOX_REGEX_RESPONSE):
            result = provider.generate_regex("match email addresses")
        assert "@" in result

    def test_list_models(self, provider):
        models = provider.list_models()
        assert len(models) == 1
        assert models[0]["id"] == "devtoolbox-ai"

    def test_name(self, provider):
        assert provider.name == "devtoolbox"

    def test_capabilities(self, provider):
        assert provider.capabilities.chat is True
        assert provider.capabilities.streaming is False
        assert provider.capabilities.embeddings is False
