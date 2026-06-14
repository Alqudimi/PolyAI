"""
Exception hierarchy for polyai SDK.

All exceptions inherit from UniversalAIError, enabling broad or narrow catching:

    except UniversalAIError:          # catch everything
    except RateLimitError:            # catch only rate limits
    except (AuthenticationError, ProviderError):  # selective
"""

from __future__ import annotations
from typing import Any, Dict, Optional


class UniversalAIError(Exception):
    """Base class for all polyai exceptions."""

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
        response: Optional[Any] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.provider = provider
        self.status_code = status_code
        self.request_id = request_id
        self.response = response
        self.body = body or {}
        super().__init__(message)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={str(self)!r}, "
            f"provider={self.provider!r}, "
            f"status_code={self.status_code!r}"
            f")"
        )


class AuthenticationError(UniversalAIError):
    """Raised when an API key or credential is missing, invalid, or expired.

    HTTP status: 401, 403
    """


class PermissionDeniedError(UniversalAIError):
    """Raised when the credential lacks permission for the requested operation.

    HTTP status: 403
    """


class RateLimitError(UniversalAIError):
    """Raised when the provider's rate limit or quota has been exceeded.

    HTTP status: 429

    Attributes:
        retry_after: Number of seconds to wait before retrying, if provided.
    """

    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class InvalidRequestError(UniversalAIError):
    """Raised when the request payload is malformed or contains invalid values.

    HTTP status: 400, 422
    """

    def __init__(self, message: str, *, param: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.param = param


class ModelNotFoundError(UniversalAIError):
    """Raised when the specified model does not exist for the provider.

    HTTP status: 404
    """

    def __init__(self, message: str, *, model: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.model = model


class ProviderError(UniversalAIError):
    """Raised when the provider returns an unexpected server-side error.

    HTTP status: 500, 502, 503, 504
    """


class ProviderUnavailableError(ProviderError):
    """Raised when the provider is temporarily unavailable (overloaded / maintenance).

    HTTP status: 503
    """


class TimeoutError(UniversalAIError):
    """Raised when a request exceeds the configured timeout."""


class ConnectionError(UniversalAIError):
    """Raised when a network-level connection failure occurs (DNS, TCP, TLS)."""


class StreamingError(UniversalAIError):
    """Raised when an error occurs mid-stream during a streaming response."""


class ContentFilterError(UniversalAIError):
    """Raised when content is blocked by the provider's safety filters."""


class ContextLengthExceededError(InvalidRequestError):
    """Raised when the input exceeds the model's maximum context length."""


class RetryExhaustedError(UniversalAIError):
    """Raised when all retry attempts have been exhausted.

    Attributes:
        attempts: Number of attempts made.
        last_error: The final underlying error.
    """

    def __init__(
        self,
        message: str,
        *,
        attempts: int = 0,
        last_error: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.attempts = attempts
        self.last_error = last_error


class ProviderNotSupportedError(UniversalAIError):
    """Raised when the operation is not supported by the specified provider."""


class FeatureNotSupportedError(UniversalAIError):
    """Raised when a feature (e.g., vision, audio) is not supported by the model/provider."""


def _from_http_status(
    status_code: int,
    message: str,
    provider: Optional[str] = None,
    body: Optional[Dict[str, Any]] = None,
    response: Optional[Any] = None,
) -> UniversalAIError:
    """Factory: map an HTTP status code to the appropriate exception class."""
    kwargs: Dict[str, Any] = {
        "provider": provider,
        "status_code": status_code,
        "body": body or {},
        "response": response,
    }
    if status_code == 400:
        return InvalidRequestError(message, **kwargs)
    if status_code == 401:
        return AuthenticationError(message, **kwargs)
    if status_code == 403:
        return PermissionDeniedError(message, **kwargs)
    if status_code == 404:
        return ModelNotFoundError(message, **kwargs)
    if status_code == 422:
        return InvalidRequestError(message, **kwargs)
    if status_code == 429:
        return RateLimitError(message, **kwargs)
    if status_code in (500, 502, 503, 504):
        if status_code == 503:
            return ProviderUnavailableError(message, **kwargs)
        return ProviderError(message, **kwargs)
    return UniversalAIError(message, **kwargs)
