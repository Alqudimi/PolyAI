"""
polyai — Production-grade unified Python SDK for OVHcloud AI Endpoints,
Pollinations.AI, mlvoca, and DevToolbox API.

Quick start::

    from polyai import Client

    client = Client()
    response = client.chat(
        provider="ovhcloud",
        model="llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.text)

Async::

    from polyai import AsyncClient

    async with AsyncClient() as client:
        response = await client.chat(provider="pollinations", model="openai", messages=[...])
"""

from polyai._version import __version__
from polyai.client import Client, ProviderClient
from polyai.async_client import AsyncClient, AsyncProviderClient
from polyai.config import ClientConfig, ProviderConfig
from polyai.exceptions import (
    UniversalAIError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    InvalidRequestError,
    ModelNotFoundError,
    ProviderError,
    ProviderUnavailableError,
    TimeoutError,
    ConnectionError,
    StreamingError,
    ContentFilterError,
    ContextLengthExceededError,
    RetryExhaustedError,
    ProviderNotSupportedError,
    FeatureNotSupportedError,
)
from polyai.types import (
    Usage,
    Tool,
    ToolCall,
    FunctionDefinition,
    ChatMessage,
    ChatResponse,
    ChatChunk,
    ChatDelta,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    ImageResponse,
    ImageData,
    AudioResponse,
    AudioTranscription,
    EmbeddingResponse,
    Embedding,
)
from polyai.streaming import StreamAccumulator, AsyncStreamAccumulator

__all__ = [
    # Version
    "__version__",
    # Clients
    "Client",
    "AsyncClient",
    "ProviderClient",
    "AsyncProviderClient",
    # Configuration
    "ClientConfig",
    "ProviderConfig",
    # Exceptions
    "UniversalAIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "RateLimitError",
    "InvalidRequestError",
    "ModelNotFoundError",
    "ProviderError",
    "ProviderUnavailableError",
    "TimeoutError",
    "ConnectionError",
    "StreamingError",
    "ContentFilterError",
    "ContextLengthExceededError",
    "RetryExhaustedError",
    "ProviderNotSupportedError",
    "FeatureNotSupportedError",
    # Types
    "Usage",
    "Tool",
    "ToolCall",
    "FunctionDefinition",
    "ChatMessage",
    "ChatResponse",
    "ChatChunk",
    "ChatDelta",
    "SystemMessage",
    "UserMessage",
    "AssistantMessage",
    "ToolMessage",
    "ImageResponse",
    "ImageData",
    "AudioResponse",
    "AudioTranscription",
    "EmbeddingResponse",
    "Embedding",
    # Streaming
    "StreamAccumulator",
    "AsyncStreamAccumulator",
]
