"""
Abstract base class for all provider adapters.

Every provider implements this interface. The resource layer (chat, images,
audio, embeddings) calls these methods through the adapter without needing to
know provider-specific details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from polyai.config import ClientConfig
from polyai.types import (
    AudioResponse,
    AudioTranscription,
    ChatChunk,
    ChatResponse,
    EmbeddingResponse,
    ImageResponse,
)


class ProviderCapabilities:
    """Declares which features a provider supports.

    Used by the SDK to raise FeatureNotSupportedError early rather than
    letting the request fail with an opaque provider error.
    """

    chat: bool = False
    streaming: bool = False
    vision: bool = False
    function_calling: bool = False
    structured_output: bool = False
    embeddings: bool = False
    reranking: bool = False
    image_generation: bool = False
    image_editing: bool = False
    tts: bool = False
    stt: bool = False
    models_endpoint: bool = False
    batch: bool = False


class BaseProvider(ABC):
    """Abstract provider adapter.

    Subclasses must implement ``chat()``, ``chat_stream()``, plus any
    optional capability methods they support.

    Args:
        config: SDK client configuration.
        name:   Provider identifier string (e.g. ``"ovhcloud"``).
    """

    name: str = ""
    capabilities: ProviderCapabilities = ProviderCapabilities()

    def __init__(self, config: ClientConfig) -> None:
        self.config = config
        self._transport: Optional[Any] = None
        self._async_transport: Optional[Any] = None

    # ------------------------------------------------------------------
    # Required: chat
    # ------------------------------------------------------------------

    @abstractmethod
    def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """Execute a blocking chat completion."""

    @abstractmethod
    def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Generator[ChatChunk, None, None]:
        """Execute a streaming chat completion, yielding ``ChatChunk`` objects."""

    @abstractmethod
    async def async_chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """Execute an async chat completion."""

    @abstractmethod
    async def async_chat_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[ChatChunk, None]:
        """Execute an async streaming chat completion."""

    # ------------------------------------------------------------------
    # Optional: embeddings
    # ------------------------------------------------------------------

    def embed(
        self,
        model: str,
        input: List[str],
        *,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> EmbeddingResponse:
        from polyai.exceptions import FeatureNotSupportedError
        raise FeatureNotSupportedError(
            f"Provider '{self.name}' does not support embeddings.",
            provider=self.name,
        )

    async def async_embed(
        self,
        model: str,
        input: List[str],
        *,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> EmbeddingResponse:
        from polyai.exceptions import FeatureNotSupportedError
        raise FeatureNotSupportedError(
            f"Provider '{self.name}' does not support embeddings.",
            provider=self.name,
        )

    # ------------------------------------------------------------------
    # Optional: image generation
    # ------------------------------------------------------------------

    def generate_image(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        n: int = 1,
        size: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        response_format: Optional[str] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ImageResponse:
        from polyai.exceptions import FeatureNotSupportedError
        raise FeatureNotSupportedError(
            f"Provider '{self.name}' does not support image generation.",
            provider=self.name,
        )

    async def async_generate_image(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        n: int = 1,
        size: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        response_format: Optional[str] = None,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ImageResponse:
        from polyai.exceptions import FeatureNotSupportedError
        raise FeatureNotSupportedError(
            f"Provider '{self.name}' does not support image generation.",
            provider=self.name,
        )

    # ------------------------------------------------------------------
    # Optional: audio
    # ------------------------------------------------------------------

    def text_to_speech(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> AudioResponse:
        from polyai.exceptions import FeatureNotSupportedError
        raise FeatureNotSupportedError(
            f"Provider '{self.name}' does not support text-to-speech.",
            provider=self.name,
        )

    async def async_text_to_speech(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        timeout: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> AudioResponse:
        from polyai.exceptions import FeatureNotSupportedError
        raise FeatureNotSupportedError(
            f"Provider '{self.name}' does not support text-to-speech.",
            provider=self.name,
        )

    # ------------------------------------------------------------------
    # Optional: models list
    # ------------------------------------------------------------------

    def list_models(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        from polyai.exceptions import FeatureNotSupportedError
        raise FeatureNotSupportedError(
            f"Provider '{self.name}' does not expose a models endpoint.",
            provider=self.name,
        )

    async def async_list_models(self, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        from polyai.exceptions import FeatureNotSupportedError
        raise FeatureNotSupportedError(
            f"Provider '{self.name}' does not expose a models endpoint.",
            provider=self.name,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Release sync transport resources."""
        if self._transport:
            self._transport.close()

    async def aclose(self) -> None:
        """Release async transport resources."""
        if self._async_transport:
            await self._async_transport.aclose()
