"""
Asynchronous HTTP transport layer built on ``httpx.AsyncClient``.

Mirror of ``SyncTransport`` for async/await usage.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

import httpx

from polyai._version import __version__
from polyai.exceptions import ConnectionError, TimeoutError, _from_http_status
from polyai.http.retry import RetryPolicy

logger = logging.getLogger(__name__)

_SDK_USER_AGENT = f"universal-ai-python/{__version__}"


class AsyncTransport:
    """Async HTTP client with retry logic.

    Must be used inside an ``async with`` block, or ``await transport.aclose()``
    must be called when finished.
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
        """Execute an async JSON request with retries."""
        url = self._build_url(path)
        merged_headers = dict(headers or {})

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

                return response.json()

            except httpx.TimeoutException as exc:
                if self.retry_policy.should_retry(attempt, is_timeout=True):
                    await self.retry_policy.async_sleep(attempt)
                    continue
                raise TimeoutError(f"Request timed out after {timeout or self.timeout}s", provider=provider) from exc

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
        """Execute an async streaming request and yield SSE data lines."""
        url = self._build_url(path)
        merged_headers = {"Accept": "text/event-stream", **(headers or {})}

        try:
            async with self._client.stream(
                method,
                url,
                json=json_body,
                headers=merged_headers,
                timeout=timeout or self.timeout,
            ) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    self._raise_for_status_raw(response.status_code, body.decode("utf-8", "replace"), provider)

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
            raise TimeoutError("Stream timed out", provider=provider) from exc
        except httpx.NetworkError as exc:
            raise ConnectionError(f"Stream network error: {exc}", provider=provider) from exc

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
            return response.content, response.headers.get("content-type", "application/octet-stream")
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
            return response.content, response.headers.get("content-type", "application/octet-stream")
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
        header = response.headers.get("retry-after") or response.headers.get("x-ratelimit-reset-requests")
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
        raise _from_http_status(response.status_code, str(message), provider=provider, body=body if isinstance(body, dict) else {})

    def _raise_for_status_raw(self, status_code: int, text: str, provider: str) -> None:
        try:
            body = json.loads(text)
            message = body.get("error", {}).get("message") or body.get("message") or text
        except Exception:
            body = {}
            message = text
        raise _from_http_status(status_code, str(message), provider=provider, body=body if isinstance(body, dict) else {})
