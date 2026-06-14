"""Image generation response types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ImageData:
    """A single generated image.

    Attributes:
        url:            Direct URL to the image (when the provider returns a URL).
        b64_json:       Base64-encoded image data (when the provider returns base64).
        revised_prompt: Revised prompt used by the model, if provided.
    """

    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None

    def save(self, path: str) -> None:
        """Save the image to a local file.

        Works with either ``url`` (downloads) or ``b64_json`` (decodes).
        """
        if self.b64_json:
            import base64
            data = base64.b64decode(self.b64_json)
            with open(path, "wb") as f:
                f.write(data)
        elif self.url:
            import urllib.request
            urllib.request.urlretrieve(self.url, path)
        else:
            raise ValueError("ImageData has neither url nor b64_json")


@dataclass
class ImageResponse:
    """Normalised response from an image generation request.

    Attributes:
        images:   List of generated images.
        model:    Model ID used for generation.
        provider: Provider name.
        raw:      Raw provider response.
    """

    images: List[ImageData] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def url(self) -> Optional[str]:
        """URL of the first generated image, for convenience."""
        if self.images:
            return self.images[0].url
        return None

    @property
    def urls(self) -> List[str]:
        """URLs of all generated images."""
        return [img.url for img in self.images if img.url]

    @classmethod
    def from_openai_dict(cls, data: Dict[str, Any], provider: str) -> "ImageResponse":
        images = [
            ImageData(
                url=item.get("url"),
                b64_json=item.get("b64_json"),
                revised_prompt=item.get("revised_prompt"),
            )
            for item in data.get("data", [])
        ]
        return cls(images=images, model=data.get("model", ""), provider=provider, raw=data)
