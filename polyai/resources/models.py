"""Models listing resource."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from polyai.providers.base import BaseProvider


class ModelsResource:
    """Synchronous models listing resource.

    Accessed via ``Client.models.list()``.
    """

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def list(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """List available models for the current provider.

        Returns:
            List of model dicts, each containing at least an ``"id"`` key.
        """
        return self._provider.list_models(timeout=timeout)


class AsyncModelsResource:
    """Asynchronous models listing resource."""

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    async def list(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """Async list of available models."""
        return await self._provider.async_list_models(timeout=timeout)
