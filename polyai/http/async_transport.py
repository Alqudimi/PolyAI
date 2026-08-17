"""
Asynchronous HTTP transport layer built on ``httpx.AsyncClient``.

Mirror of ``SyncTransport`` for async/await usage.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

import httpx

from polyai._version import __version__
from polyai.exceptions import ConnectionError, TimeoutError, _from_http_status
from polyai.http.retry import RetryPolicy
from polyai.middleware import MiddlewareRegistry, RequestHookPayload, ResponseHookPayload

logger = logging.getLogger(__name__)

_SDK_USER_AGENT = f"universal-ai-python/{__version__}"


class AsyncTransport:
    """Async HTTP client with retry logic.

    Must be used inside an ``async with`` block, or ``await transport.aclose()``
    must be called when finished.

    Args:
        middleware:   Optional ``MiddlewareRegistry`` for request / response hooks.
    """

    def __init__(
        self,
        *,
        base_url: str = "",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 60.0,
        retry_policy: Optional[RetryPolicy] = None,
        proxy: Optional[str] = None,
        verify_ssl: bool = True,
        user_agent: Optional[str] = None,
        middleware: Optional[MiddlewareRegistry] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_policy = retry_policy or RetryPolicy()

        ua = _SDK_USER_AGENT
        if user_agent:
            ua = f"{ua} {user_agent}"

        default_headers: Dict[str, str] = {
            "User-Agent": ua,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if headers:
            default_headers.update(headers)

        client_kwargs: Dict[str, Any] = {
            "headers": default_headers,
            "timeout": httpx.Timeout(timeout),
            "follow_redirects": True,
            "verify": verify_ssl,
        }
        if proxy:
            client_kwargs["proxy"] = proxy

        self._client = httpx.AsyncClient(**client_kwargs)
        self._middleware = middleware

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        provider: str = "",
    ) -> Dict[str, Any]:
        """Execute an async JSON request with retries.

        If a ``MiddlewareRegistry`` was supplied at construction time, request
        hooks are invoked before the request is sent and response hooks are
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
        tracker: Dict[str, Any] = {"code": 0, "body": None}
        exception: Optional[BaseException] = None
        try:
            result = await self._request_with_retry(
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

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        json_body: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
        merged_headers: Dict[str, str],
        timeout: Optional[float],
        provider: str,
        status_tracker: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform the async request with retry handling, returning parsed JSON."""
        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                response = await self._client.request(
                    method,
                    url,
                    json=json_body,
                    params=params,
                    headers=merged_headers,
                    timeout=timeout or self.timeout,
                )
                logger.debug("%s %s → %d (attempt %d)", method, url, response.status_code, attempt)

                if response.status_code >= 400:
                    retry_after = self._parse_retry_after(response)
                    if self.retry_policy.should_retry(attempt, status_code=response.status_code):
                        await self.retry_policy.async_sleep(attempt, retry_after)
                        continue
                    self._raise_for_status(response, provider)

                parsed = response.json()
                if status_tracker is not None:
                    status_tracker["code"] = response.status_code
                    status_tracker["body"] = parsed
                return parsed

            except httpx.TimeoutException as exc:
                if self.retry_policy.should_retry(attempt, is_timeout=True):
                    await self.retry_policy.async_sleep(attempt)
                    continue
                raise TimeoutError(
                    f"Request timed out after {timeout or self.timeout}s", provider=provider
                ) from exc

            except httpx.NetworkError as exc:
                if self.retry_policy.should_retry(attempt, is_network_error=True):
                    await self.retry_policy.async_sleep(attempt)
                    continue
                raise ConnectionError(f"Network error: {exc}", provider=provider) from exc

        raise ConnectionError("All retry attempts exhausted", provider=provider)

    async def stream(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        provider: str = "",
    ) -> AsyncGenerator[str, None]:
        """Execute an async streaming request and yield SSE data lines.

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
        tracker: Dict[str, Any] = {"code": 0}
        exception: Optional[BaseException] = None
        try:
            async with self._client.stream(
                method,
                url,
                json=json_body,
                headers=merged_headers,
                timeout=timeout or self.timeout,
            ) as response:
                tracker["code"] = response.status_code
                if response.status_code >= 400:
                    body = await response.aread()
                    self._raise_for_status_raw(
                        response.status_code, body.decode("utf-8", "replace"), provider
                    )
                async for line in response.aiter_lines():
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

    async def get_bytes(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        provider: str = "",
    ) -> Tuple[bytes, str]:
        """Async GET binary content. Returns ``(bytes, content_type)``."""
        url = self._build_url(path)
        try:
            response = await self._client.get(
                url,
                params=params,
                headers=dict(headers or {}),
                timeout=timeout or self.timeout,
            )
            if response.status_code >= 400:
                self._raise_for_status(response, provider)
            return response.content, response.headers.get(
                "content-type", "application/octet-stream"
            )
        except httpx.TimeoutException as exc:
            raise TimeoutError("Binary GET timed out", provider=provider) from exc

    async def post_bytes(
        self,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        provider: str = "",
    ) -> Tuple[bytes, str]:
        """Async POST binary content. Returns ``(bytes, content_type)``."""
        url = self._build_url(path)
        try:
            response = await self._client.post(
                url,
                json=json_body,
                headers=dict(headers or {}),
                timeout=timeout or self.timeout,
            )
            if response.status_code >= 400:
                self._raise_for_status(response, provider)
            return response.content, response.headers.get(
                "content-type", "application/octet-stream"
            )
        except httpx.TimeoutException as exc:
            raise TimeoutError("Binary POST timed out", provider=provider) from exc

    async def aclose(self) -> None:
        """Close the underlying async HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncTransport":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> Optional[float]:
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
