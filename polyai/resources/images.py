"""Image generation resource."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from polyai.providers.base import BaseProvider
from polyai.types import ImageResponse


class ImagesResource:
    """Synchronous image generation resource.

    Accessed via ``Client.images.generate(...)``.
    """

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def generate(
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
        **extra: Any,
    ) -> ImageResponse:
        """Generate one or more images from a text prompt.

        Args:
            prompt:          Text description of the image to generate.
            model:           Model to use (provider-specific identifier).
            n:               Number of images to generate (default: 1).
            size:            Image dimensions as ``"WxH"`` string (e.g. ``"1024x1024"``).
            width:           Image width in pixels (alternative to ``size``).
            height:          Image height in pixels (alternative to ``size``).
            response_format: Output format (``"url"`` or ``"b64_json"``).
            timeout:         Per-request timeout override in seconds.
            **extra:         Provider-specific parameters.

        Returns:
            ``ImageResponse`` with ``.url``, ``.urls``, and ``.images`` attributes.
        """
        return self._provider.generate_image(
            prompt,
            model=model,
            n=n,
            size=size,
            width=width,
            height=height,
            response_format=response_format,
            timeout=timeout,
            extra=extra or None,
        )


class AsyncImagesResource:
    """Asynchronous image generation resource."""

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    async def generate(
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
        **extra: Any,
    ) -> ImageResponse:
        """Async image generation. See ``ImagesResource.generate`` for full docs."""
        return await self._provider.async_generate_image(
            prompt,
            model=model,
            n=n,
            size=size,
            width=width,
            height=height,
            response_format=response_format,
            timeout=timeout,
            extra=extra or None,
        )
