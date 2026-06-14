"""Unit tests for the streaming engine."""

from __future__ import annotations

import pytest

from polyai.streaming.engine import AsyncStreamAccumulator, StreamAccumulator
from polyai.types import ChatChunk


def make_chunk(delta: str, model: str = "test-model", finish_reason=None) -> ChatChunk:
    return ChatChunk(delta=delta, model=model, provider="test", finish_reason=finish_reason)


class TestStreamAccumulator:
    def test_empty(self):
        acc = StreamAccumulator()
        resp = acc.result()
        assert resp.text == ""
        assert resp.model == ""

    def test_accumulate_chunks(self):
        acc = StreamAccumulator()
        acc.add(make_chunk("Hello"))
        acc.add(make_chunk(", "))
        acc.add(make_chunk("world!", finish_reason="stop"))
        assert acc.text == "Hello, world!"

    def test_result(self):
        acc = StreamAccumulator()
        acc.add(make_chunk("foo", model="llama"))
        acc.add(make_chunk("bar", model="llama", finish_reason="stop"))
        resp = acc.result()
        assert resp.text == "foobar"
        assert resp.model == "llama"
        assert resp.finish_reason == "stop"

    def test_from_iterable(self):
        chunks = [make_chunk("a"), make_chunk("b"), make_chunk("c", finish_reason="stop")]
        acc = StreamAccumulator()
        resp = acc.from_iterable(chunks)
        assert resp.text == "abc"

    def test_len(self):
        acc = StreamAccumulator()
        acc.add(make_chunk("x"))
        acc.add(make_chunk("y"))
        assert len(acc) == 2

    def test_reset(self):
        acc = StreamAccumulator()
        acc.add(make_chunk("hello"))
        acc.reset()
        assert acc.text == ""
        assert len(acc) == 0

    def test_mid_stream_text(self):
        acc = StreamAccumulator()
        acc.add(make_chunk("Hello"))
        assert acc.text == "Hello"
        acc.add(make_chunk(" world"))
        assert acc.text == "Hello world"


@pytest.mark.asyncio
class TestAsyncStreamAccumulator:
    async def test_from_async_iterable(self):
        async def gen():
            for token in ["async ", "stream ", "test"]:
                yield make_chunk(token)
            yield make_chunk("", finish_reason="stop")

        acc = AsyncStreamAccumulator()
        resp = await acc.from_async_iterable(gen())
        assert resp.text == "async stream test"
