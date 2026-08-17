"""
Synchronous HTTP transport layer built on ``httpx``.

Handles:
- Session / connection pool reuse
- Automatic retries with exponential backoff
- Timeout propagation
- Consistent error mapping to SDK exceptions
- Safe header logging (no secret leakage)
- SSE streaming
"""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

import httpx

from polyai._version import __version__
from polyai.exceptions import (
    ConnectionError,
    TimeoutError,
    _from_http_status,
)
from polyai.http.retry import RetryPolicy
from polyai.middleware import MiddlewareRegistry, RequestHookPayload, ResponseHookPayload

logger = logging.getLogger(__name__)

_SDK_USER_AGENT = f"universal-ai-python/{__version__}"


def _safe_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return a copy of headers with auth values masked."""
    out = {}
    for k, v in headers.items():
        if k.lower() in ("authorization", "x-api-key"):
            out[k] = f"{v[:6]}****" if len(v) > 6 else "****"
        else:
            out[k] = v
    return out


class SyncTransport:
    """Thread-safe synchronous HTTP client with retry logic.

    Args:
        base_url:     Provider base URL.
        headers:      Default headers sent with every request.
        timeout:      Request timeout in seconds.
        retry_policy: ``RetryPolicy`` instance.
        proxy:        HTTP/S proxy URL.
        verify_ssl:   Verify TLS certificates.
        user_agent:   Optional custom user agent suffix.
        middleware:   Optional ``MiddlewareRegistry`` for request / response hooks.
    """

    def __init__(
        self,
        *,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        timeout: float = 60.0,
        retry_policy: RetryPolicy | None = None,
        proxy: str | None = None,
        verify_ssl: bool = True,
        user_agent: str | None = None,
        middleware: MiddlewareRegistry | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_policy = retry_policy or RetryPolicy()

        ua = _SDK_USER_AGENT
        if user_agent:
            ua = f"{ua} {user_agent}"

        default_headers: dict[str, str] = {
            "User-Agent": ua,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if headers:
            default_headers.update(headers)

        client_kwargs: dict[str, Any] = {
            "headers": default_headers,
            "timeout": httpx.Timeout(timeout),
            "follow_redirects": True,
            "verify": verify_ssl,
        }
        if proxy:
            client_kwargs["proxy"] = proxy

        self._client = httpx.Client(**client_kwargs)
        self._middleware = middleware

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        provider: str = "",
    ) -> dict[str, Any]:
        """Execute a JSON request and return the parsed response body.

        Automatically retries on transient errors per the ``RetryPolicy``.

        If a ``MiddlewareRegistry`` was supplied at construction time, request
        hooks are invoked before the request is sent (they may inject extra
        headers or query parameters via the payload) and response hooks are
        invoked once the request completes or fails.
        """
        middleware = self._middleware
        url = self._build_url(path)
        merged_headers = dict(headers or {})

        if middleware is not None:
            payload = middleware.dispatch_request(
                RequestHookPayload(
                    method=method,
                    url=url,
                    provider=provider,
                    json_body=json_body,
                    extra_headers={},
                    extra_params=dict(params or {}),
                )
            )
            merged_headers.update(payload.extra_headers)
            params = payload.extra_params

        started_at = time.monotonic()
        tracker: dict[str, Any] = {"code": 0, "body": None}
        exception: BaseException | None = None
        try:
            result = self._request_with_retry(
                method,
                url,
                json_body,
                params,
                merged_headers,
                timeout,
                provider,
                status_tracker=tracker,
            )
            tracker["body"] = result
            return result
        except Exception as exc:  # noqa: BLE001 — observers must never break requests
            exception = exc
            raise
        finally:
            if middleware is not None:
                middleware.dispatch_response(
                    ResponseHookPayload(
                        method=method,
                        url=url,
                        provider=provider,
                        status_code=tracker["code"],
                        elapsed_seconds=time.monotonic() - started_at,
                        body=tracker["body"],
                        exception=exception,
                    )
                )

    def _request_with_retry(
        self,
        method: str,
        url: str,
        json_body: dict[str, Any] | None,
        params: dict[str, Any] | None,
        merged_headers: dict[str, str],
        timeout: float | None,
        provider: str,
        status_tracker: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform the request with retry handling, returning the parsed JSON.

        The optional ``status_tracker`` dict is updated in place with the
        final ``status_code`` and parsed ``body`` so that response hooks
        receive accurate outcome information.
        """
        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                response = self._client.request(
                    method,
                    url,
                    json=json_body,
                    params=params,
                    headers=merged_headers,
                    timeout=timeout or self.timeout,
                )
                logger.debug(
                    "%s %s → %d (attempt %d)",
                    method,
                    url,
                    response.status_code,
                    attempt,
                )

                if response.status_code >= 400:
                    retry_after = self._parse_retry_after(response)
                    if self.retry_policy.should_retry(attempt, status_code=response.status_code):
                        self.retry_policy.sleep(attempt, retry_after)
                        continue
                    if status_tracker is not None:
                        status_tracker["code"] = response.status_code
                    self._raise_for_status(response, provider)

                parsed = response.json()
                if status_tracker is not None:
                    status_tracker["code"] = response.status_code
                    status_tracker["body"] = parsed
                return parsed

            except httpx.TimeoutException as exc:
                if self.retry_policy.should_retry(attempt, is_timeout=True):
                    self.retry_policy.sleep(attempt)
                    continue
                if status_tracker is not None:
                    status_tracker["code"] = 0
                raise TimeoutError(
                    f"Request timed out after {timeout or self.timeout}s",
                    provider=provider,
                ) from exc

            except httpx.NetworkError as exc:
                if self.retry_policy.should_retry(attempt, is_network_error=True):
                    self.retry_policy.sleep(attempt)
                    continue
                if status_tracker is not None:
                    status_tracker["code"] = 0
                raise ConnectionError(
                    f"Network error: {exc}",
                    provider=provider,
                ) from exc

        if status_tracker is not None:
            status_tracker["code"] = 0
        raise ConnectionError("All retry attempts exhausted", provider=provider)

    def stream(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        provider: str = "",
    ) -> Generator[str, None, None]:
        """Execute a streaming request and yield raw SSE line strings.

        Yields each non-empty, non-comment SSE ``data:`` value.

        If a ``MiddlewareRegistry`` was supplied at construction time, request
        hooks are invoked before the stream starts. Streaming requests report
        ``status_code`` and ``body=None`` to response hooks.
        """
        middleware = self._middleware
        url = self._build_url(path)
        merged_headers = {"Accept": "text/event-stream", **(headers or {})}

        if middleware is not None:
            payload = middleware.dispatch_request(
                RequestHookPayload(
                    method=method,
                    url=url,
                    provider=provider,
                    json_body=json_body,
                    extra_headers={},
                    extra_params={},
                )
            )
            merged_headers.update(payload.extra_headers)

        started_at = time.monotonic()
        tracker: dict[str, Any] = {"code": 0}
        exception: BaseException | None = None
        try:
            with self._client.stream(
                method,
                url,
                json=json_body,
                headers=merged_headers,
                timeout=timeout or self.timeout,
            ) as response:
                tracker["code"] = response.status_code
                if response.status_code >= 400:
                    body = response.read()
                    self._raise_for_status_raw(
                        response.status_code, body.decode("utf-8", "replace"), provider
                    )

                for line in response.iter_lines():
                    line = line.strip()
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data == "[DONE]":
                            return
                        yield data

        except httpx.TimeoutException as exc:
            exception = exc
            raise TimeoutError("Stream timed out", provider=provider) from exc
        except httpx.NetworkError as exc:
            exception = exc
            raise ConnectionError(f"Stream network error: {exc}", provider=provider) from exc
        except Exception as exc:  # noqa: BLE001 — report stream failures to observers
            exception = exc
            raise
        finally:
            if middleware is not None:
                middleware.dispatch_response(
                    ResponseHookPayload(
                        method=method,
                        url=url,
                        provider=provider,
                        status_code=tracker["code"],
                        elapsed_seconds=time.monotonic() - started_at,
                        body=None,
                        exception=exception,
                    )
                )

    def get_bytes(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        provider: str = "",
    ) -> tuple[bytes, str]:
        """GET a binary response. Returns ``(bytes, content_type)``."""
        url = self._build_url(path)
        try:
            response = self._client.get(
                url,
                params=params,
                headers=dict(headers or {}),
                timeout=timeout or self.timeout,
            )
            if response.status_code >= 400:
                self._raise_for_status(response, provider)
            content_type = response.headers.get("content-type", "application/octet-stream")
            return response.content, content_type
        except httpx.TimeoutException as exc:
            raise TimeoutError("Binary GET timed out", provider=provider) from exc

    def post_bytes(
        self,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        provider: str = "",
    ) -> tuple[bytes, str]:
        """POST and return a binary response. Returns ``(bytes, content_type)``."""
        url = self._build_url(path)
        try:
            response = self._client.post(
                url,
                json=json_body,
                headers=dict(headers or {}),
                timeout=timeout or self.timeout,
            )
            if response.status_code >= 400:
                self._raise_for_status(response, provider)
            content_type = response.headers.get("content-type", "application/octet-stream")
            return response.content, content_type
        except httpx.TimeoutException as exc:
            raise TimeoutError("Binary POST timed out", provider=provider) from exc

    def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        self._client.close()

    def __enter__(self) -> SyncTransport:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> float | None:
        header = response.headers.get("retry-after") or response.headers.get(
            "x-ratelimit-reset-requests"
        )
        if header:
            try:
                return float(header)
            except ValueError:
                pass
        return None

    def _raise_for_status(self, response: httpx.Response, provider: str) -> None:
        try:
            body = response.json()
            message = (
                body.get("error", {}).get("message")
                or body.get("message")
                or body.get("detail")
                or response.text
            )
        except Exception:
            body = {}
            message = response.text or f"HTTP {response.status_code}"

        raise _from_http_status(
            response.status_code,
            str(message),
            provider=provider,
            body=body if isinstance(body, dict) else {},
            response=response,
        )

    def _raise_for_status_raw(self, status_code: int, text: str, provider: str) -> None:
        try:
            body = json.loads(text)
            message = body.get("error", {}).get("message") or body.get("message") or text
        except Exception:
            body = {}
            message = text

        raise _from_http_status(
            status_code,
            str(message),
            provider=provider,
            body=body if isinstance(body, dict) else {},
        )
