"""Unit tests for utility helpers."""

from __future__ import annotations

import math

import pytest

from polyai.utils.helpers import (
    build_vision_message,
    cosine_similarity,
    count_tokens_approx,
    merge_tool_call_chunks,
    truncate_messages,
)


class TestCosigneSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        assert math.isclose(cosine_similarity(v, v), 1.0, abs_tol=1e-6)

    def test_orthogonal_vectors(self):
        assert math.isclose(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0, abs_tol=1e-6)

    def test_opposite_vectors(self):
        assert math.isclose(cosine_similarity([1.0, 0.0], [-1.0, 0.0]), -1.0, abs_tol=1e-6)

    def test_zero_vector(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


class TestBuildVisionMessage:
    def test_url_image(self):
        msg = build_vision_message("What is this?", "https://example.com/photo.jpg")
        assert msg["role"] == "user"
        parts = msg["content"]
        assert parts[0]["type"] == "text"
        assert parts[0]["text"] == "What is this?"
        assert parts[1]["type"] == "image_url"
        assert parts[1]["image_url"]["url"] == "https://example.com/photo.jpg"

    def test_multiple_images(self):
        msg = build_vision_message("Compare these", ["https://a.com/1.jpg", "https://b.com/2.jpg"])
        parts = msg["content"]
        assert len(parts) == 3

    def test_data_uri_passthrough(self):
        uri = "data:image/png;base64,abc123"
        msg = build_vision_message("Check this", uri)
        assert msg["content"][1]["image_url"]["url"] == uri

    def test_custom_role(self):
        msg = build_vision_message("text", "https://x.com/img.png", role="system")
        assert msg["role"] == "system"


class TestTruncateMessages:
    def _make_msgs(self, n: int, chars: int = 100) -> list:
        return [{"role": "user", "content": "x" * chars} for _ in range(n)]

    def test_no_truncation_needed(self):
        msgs = self._make_msgs(3, chars=10)
        result = truncate_messages(msgs, max_tokens=1000)
        assert len(result) == 3

    def test_truncation_preserves_last(self):
        msgs = [
            {"role": "user", "content": "First message " * 20},
            {"role": "assistant", "content": "Response " * 20},
            {"role": "user", "content": "Final question"},
        ]
        result = truncate_messages(msgs, max_tokens=50)
        assert result[-1]["content"] == "Final question"

    def test_system_message_preserved(self):
        msgs = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "a" * 1000},
            {"role": "user", "content": "final"},
        ]
        result = truncate_messages(msgs, max_tokens=30, keep_system=True)
        assert result[0]["role"] == "system"
        assert result[-1]["content"] == "final"


class TestCountTokensApprox:
    def test_empty(self):
        assert count_tokens_approx("") >= 1

    def test_roughly_four_chars_per_token(self):
        text = "a" * 400
        approx = count_tokens_approx(text)
        assert approx == 100

    def test_custom_ratio(self):
        text = "a" * 100
        assert count_tokens_approx(text, chars_per_token=5.0) == 20


class TestMergeToolCallChunks:
    def test_single_chunk(self):
        chunks = [
            {"index": 0, "id": "call_1", "type": "function", "function": {"name": "search", "arguments": '{"q"'}},
        ]
        merged = merge_tool_call_chunks(chunks)
        assert len(merged) == 1
        assert merged[0]["function"]["name"] == "search"

    def test_multi_chunk_arguments_concatenated(self):
        chunks = [
            {"index": 0, "id": "call_1", "type": "function", "function": {"name": "search", "arguments": '{"q": '}},
            {"index": 0, "type": "function", "function": {"name": "", "arguments": '"hello"}'}},
        ]
        merged = merge_tool_call_chunks(chunks)
        assert len(merged) == 1
        assert merged[0]["function"]["arguments"] == '{"q": "hello"}'

    def test_multiple_tool_calls(self):
        chunks = [
            {"index": 0, "id": "c1", "type": "function", "function": {"name": "fn1", "arguments": "{}"}},
            {"index": 1, "id": "c2", "type": "function", "function": {"name": "fn2", "arguments": "{}"}},
        ]
        merged = merge_tool_call_chunks(chunks)
        assert len(merged) == 2
        assert merged[0]["function"]["name"] == "fn1"
        assert merged[1]["function"]["name"] == "fn2"
