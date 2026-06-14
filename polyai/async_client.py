"""
Asynchronous Client — async/await version of the polyai SDK.

Quick start::

    import asyncio
    from polyai import AsyncClient

    async def main():
        async with AsyncClient() as client:
            response = await client.chat(
                provider="ovhcloud",
                model="meta-llama-3_3-70b-instruct",
                messages=[{"role": "user", "content": "Hello!"}],
            )
            print(response.text)

            async for chunk in client.chat_stream(
                provider="pollinations",
                model="openai",
                messages=[{"role": "user", "content": "Tell me a story"}],
            ):
                print(chunk.delta, end="", flush=True)

    asyncio.run(main())
"""

from __future__ import annotations

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from polyai._version import __version__
from polyai.config import ClientConfig
from polyai.exceptions import ProviderNotSupportedError
from polyai.providers import PROVIDER_REGISTRY
from polyai.providers.base import BaseProvider
from polyai.resources.audio import AsyncAudioResource
from polyai.resources.chat import AsyncChatResource
from polyai.resources.devtools import AsyncDevToolsResource
from polyai.resources.embeddings import AsyncEmbeddingsResource
from polyai.resources.images import AsyncImagesResource
from polyai.resources.models import AsyncModelsResource
from polyai.streaming.engine import AsyncStreamAccumulator
from polyai.types import (
    AudioResponse,
    ChatChunk,
    ChatMessage,
    ChatResponse,
    EmbeddingResponse,
    ImageResponse,
    Tool,
)

logger = logging.getLogger(__name__)


class AsyncProviderClient:
    """An async provider-bound client exposing resource namespaces.

    Returned by ``AsyncClient.with_provider(name)``::

        ovh = client.with_provider("ovhcloud")
        response = await ovh.chat.complete(messages=[...], model="...")
        img = await ovh.images.generate(prompt="...")
    """

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider
        self.chat = AsyncChatResource(provider)
        self.images = AsyncImagesResource(provider)
        self.audio = AsyncAudioResource(provider)
        self.embeddings = AsyncEmbeddingsResource(provider)
        self.devtools = AsyncDevToolsResource(provider)
        self.models = AsyncModelsResource(provider)

    @property
    def name(self) -> str:
        return self._provider.name

    @property
    def capabilities(self):
        return self._provider.capabilities

    async def aclose(self) -> None:
        await self._provider.aclose()

    async def __aenter__(self) -> "AsyncProviderClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()


class AsyncClient:
    """Async polyai client.

    Designed for high-throughput concurrent workloads. All provider I/O uses
    ``httpx.AsyncClient`` under the hood, enabling true async concurrency.

    Args:
        config:               Pre-built ``ClientConfig``.
        ovhcloud_api_key:     OVHcloud API key.
        pollinations_api_key: Pollinations API key.
        devtoolbox_api_key:   DevToolbox API key.
        timeout:              Default request timeout in seconds.
        max_retries:          Default maximum retry count.
        **kwargs:             Additional keyword args forwarded to ``ClientConfig``.

    Best practice — use as an async context manager::

        async with AsyncClient() as client:
            response = await client.chat(...)
    """

    def __init__(
        self,
        *,
        config: Optional[ClientConfig] = None,
        ovhcloud_api_key: Optional[str] = None,
        pollinations_api_key: Optional[str] = None,
        devtoolbox_api_key: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = ClientConfig(
                ovhcloud_api_key=ovhcloud_api_key,
                pollinations_api_key=pollinations_api_key,
                devtoolbox_api_key=devtoolbox_api_key,
                timeout=timeout,
                max_retries=max_retries,
                **kwargs,
            )
        self._config = config
        self._providers: Dict[str, BaseProvider] = {}
        logger.debug("polyai AsyncClient v%s initialized", __version__)

    # ------------------------------------------------------------------
    # Provider access
    # ------------------------------------------------------------------

    def with_provider(self, name: str) -> AsyncProviderClient:
        """Return an ``AsyncProviderClient`` bound to the specified provider."""
        return AsyncProviderClient(self._get_provider(name))

    def _get_provider(self, name: str) -> BaseProvider:
        name = name.lower()
        if name not in self._providers:
            cls = PROVIDER_REGISTRY.get(name)
            if cls is None:
                raise ProviderNotSupportedError(
                    f"Unknown provider '{name}'. "
                    f"Available: {sorted(PROVIDER_REGISTRY.keys())}",
                    provider=name,
                )
            self._providers[name] = cls(self._config)
        return self._providers[name]

    # ------------------------------------------------------------------
    # Top-level unified async interface
    # ------------------------------------------------------------------

    async def chat(
        self,
        provider: str,
        model: str,
        messages: List[ChatMessage],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Union[Tool, Dict[str, Any]]]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        json_mode: bool = False,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> ChatResponse:
        """Async chat completion.

        Example::

            response = await client.chat(
                provider="pollinations",
                model="openai",
                messages=[{"role": "user", "content": "Hello!"}],
            )
            print(response.text)
        """
        return await self.with_provider(provider).chat.complete(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            response_format=response_format,
            system=system,
            json_mode=json_mode,
            timeout=timeout,
            **extra,
        )

    async def chat_stream(
        self,
        provider: str,
        model: str,
        messages: List[ChatMessage],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Union[Tool, Dict[str, Any]]]] = None,
        tool_choice: Optional[Any] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> AsyncGenerator[ChatChunk, None]:
        """Async streaming chat completion, yielding ``ChatChunk`` objects.

        Example::

            async for chunk in await client.chat_stream(
                provider="ovhcloud",
                model="meta-llama-3_3-70b-instruct",
                messages=[{"role": "user", "content": "Tell me a story"}],
            ):
                print(chunk.delta, end="", flush=True)
        """
        async for chunk in self.with_provider(provider).chat.stream(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            system=system,
            timeout=timeout,
            **extra,
        ):
            yield chunk

    async def chat_accumulate(
        self,
        provider: str,
        model: str,
        messages: List[ChatMessage],
        *,
        on_chunk=None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Stream and accumulate into a full ``ChatResponse``.

        Example::

            response = await client.chat_accumulate(
                provider="ovhcloud",
                model="meta-llama-3_3-70b-instruct",
                messages=[{"role": "user", "content": "Tell me a story"}],
                on_chunk=lambda c: print(c.delta, end="", flush=True),
            )
        """
        acc = AsyncStreamAccumulator()
        async for chunk in self.chat_stream(provider, model, messages, **kwargs):
            if on_chunk:
                on_chunk(chunk)
            acc.add(chunk)
        return acc.result()

    # ------------------------------------------------------------------
    # Concurrent helpers
    # ------------------------------------------------------------------

    async def chat_many(
        self,
        requests: List[Dict[str, Any]],
        *,
        max_concurrency: int = 10,
    ) -> List[ChatResponse]:
        """Send multiple chat requests concurrently.

        Args:
            requests:        List of kwarg dicts matching ``chat()`` signature.
            max_concurrency: Maximum parallel requests. Default: 10.

        Returns:
            List of ``ChatResponse`` objects in the same order as ``requests``.

        Example::

            responses = await client.chat_many([
                {"provider": "ovhcloud", "model": "llama-3.1-8b-instruct",
                 "messages": [{"role": "user", "content": "Question 1"}]},
                {"provider": "pollinations", "model": "openai",
                 "messages": [{"role": "user", "content": "Question 2"}]},
            ])
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrency)

        async def _bounded(req: Dict[str, Any]) -> ChatResponse:
            async with semaphore:
                return await self.chat(**req)

        return list(await asyncio.gather(*[_bounded(r) for r in requests]))

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------

    async def generate_image(
        self,
        provider: str,
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
        """Async image generation."""
        return await self.with_provider(provider).images.generate(
            prompt, model=model, n=n, size=size, width=width, height=height,
            response_format=response_format, timeout=timeout, **extra,
        )

    # ------------------------------------------------------------------
    # Audio
    # ------------------------------------------------------------------

    async def text_to_speech(
        self,
        provider: str,
        text: str,
        *,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> AudioResponse:
        """Async text-to-speech."""
        return await self.with_provider(provider).audio.speech(
            text, model=model, voice=voice, response_format=response_format,
            speed=speed, timeout=timeout, **extra,
        )

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    async def embed(
        self,
        provider: str,
        input: Union[str, List[str]],
        model: str,
        *,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> EmbeddingResponse:
        """Async embedding generation."""
        return await self.with_provider(provider).embeddings.create(
            input, model=model, timeout=timeout, **extra,
        )

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------

    async def list_models(self, provider: str, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """Async list of available models."""
        return await self.with_provider(provider).models.list(timeout=timeout)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def aclose(self) -> None:
        """Close all provider async transports."""
        for provider in self._providers.values():
            try:
                await provider.aclose()
            except Exception:
                pass

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        providers = list(self._providers.keys()) or ["(none initialised)"]
        return f"AsyncClient(providers={providers})"
