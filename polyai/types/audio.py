"""Audio response types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AudioTranscription:
    """Text transcription of an audio file.

    Attributes:
        text:     Full transcription text.
        language: Detected language code, if provided.
        duration: Audio duration in seconds, if provided.
        segments: Word/segment-level details, if provided.
        raw:      Raw provider response.
    """

    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: List[Dict[str, Any]] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.text


@dataclass
class AudioResponse:
    """Binary audio response from a text-to-speech request.

    Attributes:
        content:       Raw audio bytes.
        content_type:  MIME type (``"audio/mpeg"``, ``"audio/wav"``, etc.).
        provider:      Provider name.
        model:         Model used for synthesis.
    """

    content: bytes
    content_type: str = "audio/mpeg"
    provider: str = ""
    model: str = ""

    def save(self, path: str) -> None:
        """Save the audio bytes to a file."""
        with open(path, "wb") as f:
            f.write(self.content)

    def __len__(self) -> int:
        return len(self.content)
