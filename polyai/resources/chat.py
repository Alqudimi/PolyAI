"""
Chat resource — unified interface for chat completions across all providers.

This resource is accessible as ``client.chat`` and ``client.chat_stream``,
providing a consistent, provider-agnostic API.
"""

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, Generator, List, Optional, Union

from polyai.providers.base import BaseProvider
from polyai.types import ChatMessage, ChatResponse, ChatChunk, Tool


class ChatResource:
    """Synchronous chat completions resource.

    Accessed via ``Client.chat(...)`` and ``Client.chat_stream(...)``.
    """

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def complete(
        self,
        messages: List[ChatMessage],
        *,
        model: str,
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
        """Send a blocking chat completion request.

        Args:
            messages:        Conversation messages (list of role/content dicts).
            model:           Model identifier string.
            temperature:     Sampling temperature (0 – 2).
            max_tokens:      Maximum tokens to generate.
            top_p:           Nucleus sampling probability.
            tools:           List of tools the model may call.
            tool_choice:     Control tool selection (``"auto"``, ``"none"``, or specific).
            response_format: Output format override (e.g. ``{"type": "json_object"}``).
            system:          Convenience system prompt (prepended to messages).
            json_mode:       Shortcut for ``response_format={"type": "json_object"}``.
            timeout:         Per-request timeout override in seconds.
            **extra:         Provider-specific extra parameters passed through.

        Returns:
            A normalised ``ChatResponse`` object.
        """
        if json_mode and not response_format:
            response_format = {"type": "json_object"}

        serialised_tools = None
        if tools:
            serialised_tools = [t.to_dict() if isinstance(t, Tool) else t for t in tools]

        return self._provider.chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            tools=serialised_tools,
            tool_choice=tool_choice,
            response_format=response_format,
            system=system,
            timeout=timeout,
            extra=extra or None,
        )

    def stream(
        self,
        messages: List[ChatMessage],
        *,
        model: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Union[Tool, Dict[str, Any]]]] = None,
        tool_choice: Optional[Any] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> Generator[ChatChunk, None, None]:
        """Send a streaming chat completion request, yielding ``ChatChunk`` objects.

        Args:
            messages:    Conversation messages.
            model:       Model identifier.
            temperature: Sampling temperature.
            max_tokens:  Maximum tokens to generate.
            top_p:       Nucleus sampling probability.
            tools:       Tools the model may call.
            tool_choice: Tool selection control.
            system:      Convenience system prompt.
            timeout:     Per-request timeout override.
            **extra:     Provider-specific parameters.

        Yields:
            ``ChatChunk`` objects with a ``delta`` attribute containing incremental text.
        """
        serialised_tools = None
        if tools:
            serialised_tools = [t.to_dict() if isinstance(t, Tool) else t for t in tools]

        yield from self._provider.chat_stream(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            tools=serialised_tools,
            tool_choice=tool_choice,
            system=system,
            timeout=timeout,
            extra=extra or None,
        )


class AsyncChatResource:
    """Asynchronous chat completions resource.

    Accessed via ``AsyncClient.chat(...)`` and ``AsyncClient.chat_stream(...)``.
    """

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    async def complete(
        self,
        messages: List[ChatMessage],
        *,
        model: str,
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
        """Async chat completion. See ``ChatResource.complete`` for full docs."""
        if json_mode and not response_format:
            response_format = {"type": "json_object"}

        serialised_tools = None
        if tools:
            serialised_tools = [t.to_dict() if isinstance(t, Tool) else t for t in tools]

        return await self._provider.async_chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            tools=serialised_tools,
            tool_choice=tool_choice,
            response_format=response_format,
            system=system,
            timeout=timeout,
            extra=extra or None,
        )

    async def stream(
        self,
        messages: List[ChatMessage],
        *,
        model: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Union[Tool, Dict[str, Any]]]] = None,
        tool_choice: Optional[Any] = None,
        system: Optional[str] = None,
        timeout: Optional[float] = None,
        **extra: Any,
    ) -> AsyncGenerator[ChatChunk, None]:
        """Async streaming chat completion. Yields ``ChatChunk`` objects."""
        serialised_tools = None
        if tools:
            serialised_tools = [t.to_dict() if isinstance(t, Tool) else t for t in tools]

        async for chunk in self._provider.async_chat_stream(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            tools=serialised_tools,
            tool_choice=tool_choice,
            system=system,
            timeout=timeout,
            extra=extra or None,
        ):
            yield chunk
