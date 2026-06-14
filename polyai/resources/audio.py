"""Audio resource — text-to-speech and speech-to-text."""

from __future__ import annotations

from typing import Any, Optional

from polyai.providers.base import BaseProvider
from polyai.types import AudioResponse


class AudioResource:
    """Synchronous audio resource.

    Accessed via ``Client.audio.speech(...)`` and ``Client.audio.transcribe(...)``.
    """

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def speech(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> AudioResponse:
        """Convert text to speech audio.

        Args:
            text:            The text to synthesize.
            model:           TTS model identifier.
            voice:           Voice name / identifier (provider-specific).
            response_format: Audio format (``"mp3"``, ``"wav"``, ``"opus"``, ``"aac"``).
            speed:           Speaking speed multiplier (0.25 – 4.0).
            timeout:         Per-request timeout override in seconds.
            **extra:         Provider-specific parameters.

        Returns:
            ``AudioResponse`` with ``.content`` (bytes) and ``.save(path)`` method.
        """
        return self._provider.text_to_speech(
            text,
            model=model,
            voice=voice,
            response_format=response_format,
            speed=speed,
            timeout=timeout,
            extra=extra or None,
        )


class AsyncAudioResource:
    """Asynchronous audio resource."""

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    async def speech(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> AudioResponse:
        """Async TTS. See ``AudioResource.speech`` for full docs."""
        return await self._provider.async_text_to_speech(
            text,
            model=model,
            voice=voice,
            response_format=response_format,
            speed=speed,
            timeout=timeout,
            extra=extra or None,
        )
