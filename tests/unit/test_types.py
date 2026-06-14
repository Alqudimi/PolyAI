"""Unit tests for polyai type classes."""

from __future__ import annotations

import json
import math

import pytest

from polyai.types import (
    ChatChunk,
    ChatResponse,
    Embedding,
    EmbeddingResponse,
    ImageData,
    ImageResponse,
    Tool,
    ToolCall,
    Usage,
)
from polyai.types.chat import (
    AssistantMessage,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from polyai.types.common import FunctionDefinition


class TestUsage:
    def test_from_dict(self):
        data = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        u = Usage.from_dict(data)
        assert u.prompt_tokens == 10
        assert u.completion_tokens == 20
        assert u.total_tokens == 30

    def test_from_dict_defaults(self):
        u = Usage.from_dict({})
        assert u.prompt_tokens == 0
        assert u.completion_tokens == 0
        assert u.total_tokens == 0

    def test_addition(self):
        a = Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15)
        b = Usage(prompt_tokens=3, completion_tokens=7, total_tokens=10)
        c = a + b
        assert c.prompt_tokens == 8
        assert c.completion_tokens == 17
        assert c.total_tokens == 25

    def test_extra_fields_preserved(self):
        data = {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10, "cache_read_tokens": 3}
        u = Usage.from_dict(data)
        assert u.extra.get("cache_read_tokens") == 3


class TestToolCall:
    def test_from_dict(self):
        data = {
            "id": "call_abc",
            "type": "function",
            "function": {"name": "get_weather", "arguments": '{"location": "Paris"}'},
        }
        tc = ToolCall.from_dict(data)
        assert tc.id == "call_abc"
        assert tc.name == "get_weather"
        assert tc.arguments == '{"location": "Paris"}'

    def test_parse_arguments(self):
        tc = ToolCall(id="x", type="function", name="fn", arguments='{"a": 1, "b": "hello"}')
        parsed = tc.parse_arguments()
        assert parsed == {"a": 1, "b": "hello"}

    def test_parse_arguments_invalid_json(self):
        tc = ToolCall(id="x", type="function", name="fn", arguments="not json")
        assert tc.parse_arguments() == {}

    def test_to_dict_roundtrip(self):
        tc = ToolCall(id="c1", type="function", name="foo", arguments='{"x": 1}')
        d = tc.to_dict()
        tc2 = ToolCall.from_dict(d)
        assert tc2.name == "foo"
        assert tc2.id == "c1"


class TestChatResponse:
    def test_from_openai_dict(self):
        data = {
            "id": "chatcmpl-abc",
            "model": "meta-llama-3_3-70b-instruct",
            "choices": [
                {"message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        }
        resp = ChatResponse.from_openai_dict(data, "ovhcloud")
        assert resp.text == "Hello!"
        assert resp.model == "meta-llama-3_3-70b-instruct"
        assert resp.provider == "ovhcloud"
        assert resp.finish_reason == "stop"
        assert resp.usage.total_tokens == 8

    def test_str(self):
        resp = ChatResponse(text="Hi there", model="m", provider="p")
        assert str(resp) == "Hi there"

    def test_empty_choices(self):
        data = {"id": "x", "model": "m", "choices": [], "usage": {}}
        resp = ChatResponse.from_openai_dict(data, "test")
        assert resp.text == ""

    def test_tool_calls_parsed(self):
        data = {
            "id": "x",
            "model": "m",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "tc1",
                        "type": "function",
                        "function": {"name": "search", "arguments": '{"q": "python"}'},
                    }],
                },
                "finish_reason": "tool_calls",
            }],
            "usage": {},
        }
        resp = ChatResponse.from_openai_dict(data, "ovhcloud")
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "search"


class TestChatChunk:
    def test_from_openai_dict(self):
        data = {
            "id": "chunk1",
            "model": "llama",
            "choices": [{"delta": {"content": " world"}, "finish_reason": None}],
        }
        chunk = ChatChunk.from_openai_dict(data, "ovhcloud")
        assert chunk.delta == " world"
        assert chunk.finish_reason is None

    def test_str(self):
        chunk = ChatChunk(delta="hello", model="m", provider="p")
        assert str(chunk) == "hello"


class TestEmbedding:
    def test_dimensions(self):
        emb = Embedding(index=0, vector=[0.1, 0.2, 0.3])
        assert emb.dimensions == 3

    def test_cosine_similarity_same(self):
        emb = Embedding(index=0, vector=[1.0, 0.0, 0.0])
        assert math.isclose(emb.cosine_similarity(emb), 1.0, abs_tol=1e-6)

    def test_cosine_similarity_orthogonal(self):
        a = Embedding(index=0, vector=[1.0, 0.0])
        b = Embedding(index=1, vector=[0.0, 1.0])
        assert math.isclose(a.cosine_similarity(b), 0.0, abs_tol=1e-6)

    def test_cosine_similarity_zero_vector(self):
        a = Embedding(index=0, vector=[0.0, 0.0])
        b = Embedding(index=1, vector=[1.0, 0.0])
        assert a.cosine_similarity(b) == 0.0


class TestEmbeddingResponse:
    def test_from_openai_dict(self):
        data = {
            "model": "bge-m3",
            "data": [
                {"object": "embedding", "index": 0, "embedding": [0.1, 0.2]},
                {"object": "embedding", "index": 1, "embedding": [0.3, 0.4]},
            ],
            "usage": {"prompt_tokens": 6, "total_tokens": 6},
        }
        resp = EmbeddingResponse.from_openai_dict(data, "ovhcloud")
        assert len(resp.embeddings) == 2
        assert resp.embeddings[0].vector == [0.1, 0.2]
        assert resp.vectors == [[0.1, 0.2], [0.3, 0.4]]
        assert resp.first is not None

    def test_similarity_matrix(self):
        data = {
            "model": "bge-m3",
            "data": [
                {"object": "embedding", "index": 0, "embedding": [1.0, 0.0]},
                {"object": "embedding", "index": 1, "embedding": [1.0, 0.0]},
            ],
            "usage": {},
        }
        resp = EmbeddingResponse.from_openai_dict(data, "ovhcloud")
        matrix = resp.similarity_matrix()
        assert math.isclose(matrix[0][0], 1.0, abs_tol=1e-6)
        assert math.isclose(matrix[0][1], 1.0, abs_tol=1e-6)


class TestImageData:
    def test_save_base64(self, tmp_path):
        import base64
        b64 = base64.b64encode(b"fake-png-bytes").decode()
        img = ImageData(b64_json=b64)
        path = str(tmp_path / "out.png")
        img.save(path)
        with open(path, "rb") as f:
            assert f.read() == b"fake-png-bytes"

    def test_save_no_data(self):
        img = ImageData()
        with pytest.raises(ValueError):
            img.save("/tmp/test.png")


class TestTool:
    def test_to_dict(self):
        fn = FunctionDefinition(
            name="get_time",
            description="Returns current time",
            parameters={"type": "object", "properties": {"timezone": {"type": "string"}}, "required": ["timezone"]},
        )
        tool = Tool(function=fn)
        d = tool.to_dict()
        assert d["type"] == "function"
        assert d["function"]["name"] == "get_time"
        assert d["function"]["parameters"]["properties"]["timezone"]["type"] == "string"

    def test_from_dict_roundtrip(self):
        d = {
            "type": "function",
            "function": {
                "name": "search",
                "description": "Search the web",
                "parameters": {"type": "object", "properties": {}},
            },
        }
        tool = Tool.from_dict(d)
        assert tool.function.name == "search"
        assert tool.to_dict() == d


class TestMessageHelpers:
    def test_system_message(self):
        msg = SystemMessage("You are a helpful assistant.")
        assert msg == {"role": "system", "content": "You are a helpful assistant."}

    def test_user_message_text(self):
        msg = UserMessage("Hello!")
        assert msg == {"role": "user", "content": "Hello!"}

    def test_assistant_message(self):
        msg = AssistantMessage("Hi there!")
        assert msg["role"] == "assistant"
        assert msg["content"] == "Hi there!"

    def test_tool_message(self):
        msg = ToolMessage('{"result": 42}', tool_call_id="call_x")
        assert msg["role"] == "tool"
        assert msg["tool_call_id"] == "call_x"
