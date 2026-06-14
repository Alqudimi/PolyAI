"""Embeddings resource."""

from __future__ import annotations

from typing import Any, List, Optional, Union

from polyai.providers.base import BaseProvider
from polyai.types import EmbeddingResponse


class EmbeddingsResource:
    """Synchronous embeddings resource.

    Accessed via ``Client.embeddings.create(...)``.
    """

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def create(
        self,
        input: Union[str, List[str]],
        *,
        model: str,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> EmbeddingResponse:
        """Generate embeddings for one or more input strings.

        Args:
            input:   A single string or a list of strings to embed.
            model:   Embedding model identifier.
            timeout: Per-request timeout override in seconds.
            **extra: Provider-specific parameters.

        Returns:
            ``EmbeddingResponse`` with ``.embeddings``, ``.vectors``,
            and cosine-similarity utilities.
        """
        if isinstance(input, str):
            input = [input]

        return self._provider.embed(
            model=model,
            input=input,
            timeout=timeout,
            extra=extra or None,
        )


class AsyncEmbeddingsResource:
    """Asynchronous embeddings resource."""

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    async def create(
        self,
        input: Union[str, List[str]],
        *,
        model: str,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> EmbeddingResponse:
        """Async embedding generation. See ``EmbeddingsResource.create`` for full docs."""
        if isinstance(input, str):
            input = [input]

        return await self._provider.async_embed(
            model=model,
            input=input,
            timeout=timeout,
            extra=extra or None,
        )
