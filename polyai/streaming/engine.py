"""
Streaming engine — utilities for accumulating streaming chat responses.

``StreamAccumulator`` collects ``ChatChunk`` objects and builds the final
``ChatResponse`` once the stream is exhausted. This is convenient when
callers want to print tokens as they arrive but also need the final object.

Usage (sync)::

    chunks = []
    acc = StreamAccumulator()
    for chunk in client.chat_stream(provider="ovhcloud", model="...", messages=[...]):
        print(chunk.delta, end="", flush=True)
        acc.add(chunk)
    response = acc.result()
    print(response.usage)

Usage (async)::

    acc = AsyncStreamAccumulator()
    async for chunk in client.async_chat_stream(...):
        print(chunk.delta, end="", flush=True)
        acc.add(chunk)
    response = acc.result()
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from polyai.types.chat import ChatChunk, ChatResponse
from polyai.types.common import Usage


class StreamAccumulator:
    """Accumulates ``ChatChunk`` objects from a sync stream.

    Thread-safe for single-consumer patterns; if multiple threads share an
    accumulator, use external locking.
    """

    def __init__(self) -> None:
        self._chunks: List[ChatChunk] = []
        self._text_parts: List[str] = []

    def add(self, chunk: ChatChunk) -> None:
        """Add a chunk to the accumulator."""
        self._chunks.append(chunk)
        if chunk.delta:
            self._text_parts.append(chunk.delta)

    def result(self) -> ChatResponse:
        """Build and return the accumulated ``ChatResponse``.

        Must only be called after the stream is fully consumed.
        """
        text = "".join(self._text_parts)
        last = self._chunks[-1] if self._chunks else None
        first = self._chunks[0] if self._chunks else None

        return ChatResponse(
            text=text,
            model=last.model if last else "",
            provider=last.provider if last else "",
            finish_reason=last.finish_reason or "stop" if last else "stop",
            id=last.id if last else "",
            usage=Usage(),
            raw={"chunks": [c.raw for c in self._chunks]},
        )

    def from_iterable(self, chunks: Iterable[ChatChunk]) -> ChatResponse:
        """Consume a full iterable of chunks and return the ``ChatResponse``."""
        for chunk in chunks:
            self.add(chunk)
        return self.result()

    @property
    def text(self) -> str:
        """Current accumulated text (safe to call mid-stream)."""
        return "".join(self._text_parts)

    def __len__(self) -> int:
        return len(self._chunks)

    def reset(self) -> None:
        """Reset state for reuse."""
        self._chunks.clear()
        self._text_parts.clear()


class AsyncStreamAccumulator(StreamAccumulator):
    """Async-compatible version of ``StreamAccumulator``.

    Identical to the sync version — ``asyncio`` streams do not require
    different data structures; this class exists for semantic clarity.

    Usage::

        acc = AsyncStreamAccumulator()
        async for chunk in client.async_chat_stream(...):
            acc.add(chunk)
        response = acc.result()
    """

    async def from_async_iterable(self, chunks) -> ChatResponse:
        """Consume an async iterable of chunks and return the ``ChatResponse``."""
        async for chunk in chunks:
            self.add(chunk)
        return self.result()
