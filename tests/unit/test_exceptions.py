"""Unit tests for the exception hierarchy."""

from __future__ import annotations

import pytest

from polyai.exceptions import (
    AuthenticationError,
    ConnectionError,
    ContentFilterError,
    ContextLengthExceededError,
    FeatureNotSupportedError,
    InvalidRequestError,
    ModelNotFoundError,
    PermissionDeniedError,
    ProviderError,
    ProviderNotSupportedError,
    ProviderUnavailableError,
    RateLimitError,
    RetryExhaustedError,
    StreamingError,
    TimeoutError,
    UniversalAIError,
    _from_http_status,
)


class TestExceptionHierarchy:
    def test_base_exception(self):
        exc = UniversalAIError("test error")
        assert str(exc) == "test error"
        assert isinstance(exc, Exception)

    def test_all_inherit_from_base(self):
        for cls in [
            AuthenticationError, RateLimitError, InvalidRequestError,
            ModelNotFoundError, ProviderError, TimeoutError, ConnectionError,
            StreamingError, ProviderUnavailableError,
        ]:
            exc = cls("msg")
            assert isinstance(exc, UniversalAIError)

    def test_authentication_error_attributes(self):
        exc = AuthenticationError("bad key", provider="ovhcloud", status_code=401)
        assert exc.provider == "ovhcloud"
        assert exc.status_code == 401

    def test_rate_limit_error_retry_after(self):
        exc = RateLimitError("too many requests", retry_after=30.0)
        assert exc.retry_after == 30.0

    def test_invalid_request_param(self):
        exc = InvalidRequestError("bad value", param="temperature")
        assert exc.param == "temperature"

    def test_model_not_found_model(self):
        exc = ModelNotFoundError("no such model", model="gpt-99")
        assert exc.model == "gpt-99"

    def test_retry_exhausted_attributes(self):
        inner = ConnectionError("timeout")
        exc = RetryExhaustedError("all retries failed", attempts=3, last_error=inner)
        assert exc.attempts == 3
        assert exc.last_error is inner

    def test_repr(self):
        exc = AuthenticationError("bad key", provider="ovhcloud", status_code=401)
        r = repr(exc)
        assert "AuthenticationError" in r
        assert "ovhcloud" in r

    def test_provider_unavailable_is_provider_error(self):
        exc = ProviderUnavailableError("down")
        assert isinstance(exc, ProviderError)

    def test_context_length_exceeded_is_invalid_request(self):
        exc = ContextLengthExceededError("too long")
        assert isinstance(exc, InvalidRequestError)


class TestFromHttpStatus:
    def test_400(self):
        exc = _from_http_status(400, "bad request")
        assert isinstance(exc, InvalidRequestError)

    def test_401(self):
        exc = _from_http_status(401, "unauthorized", provider="ovhcloud")
        assert isinstance(exc, AuthenticationError)
        assert exc.provider == "ovhcloud"

    def test_403(self):
        exc = _from_http_status(403, "forbidden")
        assert isinstance(exc, PermissionDeniedError)

    def test_404(self):
        exc = _from_http_status(404, "model not found")
        assert isinstance(exc, ModelNotFoundError)

    def test_429(self):
        exc = _from_http_status(429, "rate limit exceeded")
        assert isinstance(exc, RateLimitError)

    def test_500(self):
        exc = _from_http_status(500, "internal server error")
        assert isinstance(exc, ProviderError)

    def test_503(self):
        exc = _from_http_status(503, "service unavailable")
        assert isinstance(exc, ProviderUnavailableError)

    def test_unknown_status(self):
        exc = _from_http_status(418, "I'm a teapot")
        assert isinstance(exc, UniversalAIError)
