"""
DevTools resource — DevToolbox-specific developer utilities.

Accessible as ``Client.devtools`` when the client is configured for the
``devtoolbox`` provider.  For other providers, these methods raise
``ProviderNotSupportedError``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from polyai.exceptions import ProviderNotSupportedError
from polyai.providers.base import BaseProvider
from polyai.providers.devtoolbox import DevToolboxProvider


class DevToolsResource:
    """Synchronous DevToolbox-specific utility resource."""

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def _require_devtoolbox(self) -> DevToolboxProvider:
        if not isinstance(self._provider, DevToolboxProvider):
            raise ProviderNotSupportedError(
                "DevTools utilities are only available with the 'devtoolbox' provider.",
                provider=self._provider.name,
            )
        return self._provider  # type: ignore[return-value]

    def summarize(self, text: str, *, max_length: Optional[int] = None, timeout: Optional[float] = None) -> str:
        """Summarize text. DevToolbox provider only."""
        return self._require_devtoolbox().summarize(text, max_length=max_length, timeout=timeout)

    def translate(self, text: str, target_lang: str, *, timeout: Optional[float] = None) -> str:
        """Translate text to a target language. DevToolbox provider only."""
        return self._require_devtoolbox().translate(text, target_lang, timeout=timeout)

    def explain_code(self, code: str, *, timeout: Optional[float] = None) -> str:
        """Explain a code snippet. DevToolbox provider only."""
        return self._require_devtoolbox().explain_code(code, timeout=timeout)

    def generate_regex(self, description: str, *, timeout: Optional[float] = None) -> str:
        """Generate a regex from a natural language description. DevToolbox provider only."""
        return self._require_devtoolbox().generate_regex(description, timeout=timeout)

    def hash(self, algorithm: str, input: str, *, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Generate a cryptographic hash."""
        return self._require_devtoolbox().hash(algorithm, input, timeout=timeout)

    def generate_uuid(self, *, timeout: Optional[float] = None) -> str:
        """Generate a UUID v4."""
        return self._require_devtoolbox().generate_uuid(timeout=timeout)

    def generate_password(self, length: int = 16, symbols: bool = True, *, timeout: Optional[float] = None) -> str:
        """Generate a secure random password."""
        return self._require_devtoolbox().generate_password(length, symbols, timeout=timeout)

    def lorem_ipsum(self, paragraphs: int = 1, *, timeout: Optional[float] = None) -> str:
        """Generate Lorem Ipsum placeholder text."""
        return self._require_devtoolbox().lorem_ipsum(paragraphs, timeout=timeout)

    def qr_code(self, data: str, size: int = 300, *, timeout: Optional[float] = None) -> bytes:
        """Generate a QR code PNG and return raw bytes."""
        return self._require_devtoolbox().qr_code(data, size, timeout=timeout)


class AsyncDevToolsResource:
    """Asynchronous DevToolbox-specific utility resource."""

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def _require_devtoolbox(self) -> DevToolboxProvider:
        if not isinstance(self._provider, DevToolboxProvider):
            raise ProviderNotSupportedError(
                "DevTools utilities are only available with the 'devtoolbox' provider.",
                provider=self._provider.name,
            )
        return self._provider  # type: ignore[return-value]

    async def summarize(self, text: str, *, max_length: Optional[int] = None, timeout: Optional[float] = None) -> str:
        return await self._require_devtoolbox().async_summarize(text, max_length=max_length, timeout=timeout)

    async def translate(self, text: str, target_lang: str, *, timeout: Optional[float] = None) -> str:
        return await self._require_devtoolbox().async_translate(text, target_lang, timeout=timeout)

    async def explain_code(self, code: str, *, timeout: Optional[float] = None) -> str:
        return await self._require_devtoolbox().async_explain_code(code, timeout=timeout)

    async def generate_regex(self, description: str, *, timeout: Optional[float] = None) -> str:
        return await self._require_devtoolbox().async_generate_regex(description, timeout=timeout)
