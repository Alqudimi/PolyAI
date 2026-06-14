"""
Synchronous Client — the primary entry point for the polyai SDK.

Quick start::

    from polyai import Client

    # Use OVHcloud (free anonymous tier — no key needed)
    client = Client()
    response = client.chat(
        provider="ovhcloud",
        model="meta-llama-3_3-70b-instruct",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.text)

    # Stream tokens
    for chunk in client.chat_stream(
        provider="pollinations",
        model="openai",
        messages=[{"role": "user", "content": "Tell me a story"}],
    ):
        print(chunk.delta, end="", flush=True)

    # Generate an image
    img = client.images.generate(
        provider="pollinations",
        prompt="a futuristic city at sunset",
        model="flux",
    )
    print(img.url)

    # Per-provider clients
    ovh = client.with_provider("ovhcloud")
    response = ovh.chat.complete(
        messages=[...],
        model="mistral-nemo-instruct-2407",
    )
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Generator, List, Optional, Union

from polyai._version import __version__
from polyai.config import ClientConfig
from polyai.exceptions import ProviderNotSupportedError
from polyai.providers import PROVIDER_REGISTRY
from polyai.providers.base import BaseProvider
from polyai.resources.audio import AudioResource
from polyai.resources.chat import ChatResource
from polyai.resources.devtools import DevToolsResource
from polyai.resources.embeddings import EmbeddingsResource
from polyai.resources.images import ImagesResource
from polyai.resources.models import ModelsResource
from polyai.streaming.engine import StreamAccumulator
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


class ProviderClient:
    """A provider-bound client exposing resource namespaces.

    Returned by ``Client.with_provider(name)``. Provides a clean namespaced API::

        ovh = client.with_provider("ovhcloud")
        ovh.chat.complete(messages=[...], model="...")
        ovh.images.generate(prompt="...")
        ovh.embeddings.create("hello", model="bge-m3")
        ovh.models.list()
    """

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider
        self.chat = ChatResource(provider)
        self.images = ImagesResource(provider)
        self.audio = AudioResource(provider)
        self.embeddings = EmbeddingsResource(provider)
        self.devtools = DevToolsResource(provider)
        self.models = ModelsResource(provider)

    @property
    def name(self) -> str:
        return self._provider.name

    @property
    def capabilities(self):
        return self._provider.capabilities

    def close(self) -> None:
        self._provider.close()

    def __enter__(self) -> "ProviderClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class Client:
    """Synchronous polyai client.

    Provides a unified interface for all supported providers. Credentials are
    read from environment variables by default; see ``ClientConfig`` for full
    configuration options.

    Args:
        config:              Pre-built ``ClientConfig``. If omitted, a default
                             config is built from environment variables.
        ovhcloud_api_key:    OVHcloud API key (overrides ``OVHCLOUD_API_KEY`` env var).
        pollinations_api_key: Pollinations API key (overrides ``POLLINATIONS_API_KEY`` env var).
        devtoolbox_api_key:  DevToolbox API key (overrides ``DEVTOOLBOX_API_KEY`` env var).
        timeout:             Default request timeout in seconds.
        max_retries:         Default maximum retry count.
        **kwargs:            Additional keyword args forwarded to ``ClientConfig``.

    Examples::

        # Minimal — reads credentials from environment
        client = Client()

        # Explicit credentials
        client = Client(ovhcloud_api_key="my-key", timeout=30)

        # Custom config
        from polyai import ClientConfig
        config = ClientConfig(timeout=120, max_retries=5)
        client = Client(config=config)
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
        logger.debug("polyai Client v%s initialized", __version__)

    # ------------------------------------------------------------------
    # Provider access
    # ------------------------------------------------------------------

    def with_provider(self, name: str) -> ProviderClient:
        """Return a ``ProviderClient`` bound to the specified provider.

        Args:
            name: Provider name (``"ovhcloud"``, ``"pollinations"``, ``"mlvoca"``,
                  ``"devtoolbox"``).

        Returns:
            A ``ProviderClient`` with ``.chat``, ``.images``, ``.audio``,
            ``.embeddings``, ``.devtools``, and ``.models`` resource namespaces.

        Raises:
            ``ProviderNotSupportedError`` if the provider name is not recognised.
        """
        return ProviderClient(self._get_provider(name))

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
    # Top-level unified interface
    # ------------------------------------------------------------------

    def chat(
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
        """Send a chat completion request to the specified provider.

        Args:
            provider:        Provider name (``"ovhcloud"``, ``"pollinations"``,
                             ``"mlvoca"``, ``"devtoolbox"``).
            model:           Model identifier.
            messages:        Conversation messages (list of role/content dicts).
            temperature:     Sampling temperature (0 – 2). Default: provider default.
            max_tokens:      Maximum tokens to generate.
            top_p:           Nucleus sampling probability.
            tools:           Tools the model may call (function calling).
            tool_choice:     Tool selection control.
            response_format: Output format (e.g. ``{"type": "json_object"}``).
            system:          Convenience system prompt (prepended to messages).
            json_mode:       Shortcut to enable JSON output mode.
            timeout:         Per-request timeout override in seconds.
            **extra:         Provider-specific parameters passed through.

        Returns:
            ``ChatResponse`` with ``.text``, ``.model``, ``.usage``, and ``.tool_calls``.

        Example::

            response = client.chat(
                provider="ovhcloud",
                model="meta-llama-3_3-70b-instruct",
                messages=[{"role": "user", "content": "What is 2+2?"}],
                temperature=0.2,
            )
            print(response.text)
        """
        return self.with_provider(provider).chat.complete(
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

    def chat_stream(
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
    ) -> Generator[ChatChunk, None, None]:
        """Stream a chat completion, yielding ``ChatChunk`` objects.

        Example::

            for chunk in client.chat_stream(
                provider="pollinations",
                model="openai",
                messages=[{"role": "user", "content": "Tell me a joke"}],
            ):
                print(chunk.delta, end="", flush=True)
        """
        yield from self.with_provider(provider).chat.stream(
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
        )

    def chat_accumulate(
        self,
        provider: str,
        model: str,
        messages: List[ChatMessage],
        *,
        on_chunk=None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Stream a chat and return the fully accumulated ``ChatResponse``.

        Optionally provide ``on_chunk`` callback for real-time display::

            response = client.chat_accumulate(
                provider="ovhcloud",
                model="meta-llama-3_3-70b-instruct",
                messages=[{"role": "user", "content": "Tell me a story"}],
                on_chunk=lambda c: print(c.delta, end="", flush=True),
            )
            print(f"\\nTotal tokens: {response.usage.total_tokens}")
        """
        acc = StreamAccumulator()
        for chunk in self.chat_stream(provider, model, messages, **kwargs):
            if on_chunk:
                on_chunk(chunk)
            acc.add(chunk)
        return acc.result()

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------

    def generate_image(
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
        """Generate an image from a text prompt.

        Example::

            img = client.generate_image(
                provider="pollinations",
                prompt="a serene mountain lake at dawn",
                model="flux",
                width=1280,
                height=720,
            )
            print(img.url)
        """
        return self.with_provider(provider).images.generate(
            prompt,
            model=model,
            n=n,
            size=size,
            width=width,
            height=height,
            response_format=response_format,
            timeout=timeout,
            **extra,
        )

    # ------------------------------------------------------------------
    # Audio
    # ------------------------------------------------------------------

    def text_to_speech(
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
        """Convert text to speech audio.

        Example::

            audio = client.text_to_speech(
                provider="pollinations",
                text="Hello, world!",
                voice="alloy",
            )
            audio.save("hello.mp3")
        """
        return self.with_provider(provider).audio.speech(
            text,
            model=model,
            voice=voice,
            response_format=response_format,
            speed=speed,
            timeout=timeout,
            **extra,
        )

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def embed(
        self,
        provider: str,
        input: Union[str, List[str]],
        model: str,
        *,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> EmbeddingResponse:
        """Generate text embeddings.

        Example::

            result = client.embed(
                provider="ovhcloud",
                input=["Hello world", "Bonjour monde"],
                model="bge-m3",
            )
            similarity = result.embeddings[0].cosine_similarity(result.embeddings[1])
            print(f"Similarity: {similarity:.4f}")
        """
        return self.with_provider(provider).embeddings.create(
            input,
            model=model,
            timeout=timeout,
            **extra,
        )

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------

    def list_models(self, provider: str, *, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """List available models for a provider.

        Example::

            models = client.list_models("ovhcloud")
            for m in models:
                print(m["id"])
        """
        return self.with_provider(provider).models.list(timeout=timeout)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close all provider transports and release connections."""
        for provider in self._providers.values():
            try:
                provider.close()
            except Exception:
                pass

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        providers = list(self._providers.keys()) or ["(none initialised)"]
        return f"Client(providers={providers})"
