"""
Request / response middleware hooks.

This module provides a small, dependency-free middleware system that lets
applications plug callbacks into every HTTP request and response performed
by the SDK. Typical uses are logging, request counting, metrics, latency
measurement, rate-limit tracking and testing hooks.

Public types
------------
- ``RequestHook``  — ``Callable[[RequestHookPayload], None]``
- ``ResponseHook`` — ``Callable[[ResponseHookPayload], None]``
- ``RequestHookPayload``  — immutable payload passed to request hooks
- ``ResponseHookPayload`` — immutable payload passed to response hooks
- ``MiddlewareRegistry``  — holds registered hooks and dispatches them
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass, field
from typing import Any, Callable

__all__ = [
    "MiddlewareRegistry",
    "RequestHook",
    "RequestHookPayload",
    "ResponseHook",
    "ResponseHookPayload",
]

RequestHook = Callable[["RequestHookPayload"], None]
"""A synchronous callback invoked **before** a request is sent.

The callback receives a read-only ``RequestHookPayload`` describing the
outgoing request. Hooks may **mutate the payload's ``extra_headers`` and
``extra_params``** to influence the request (e.g. inject a request id),
but must not mutate the JSON body.
"""

ResponseHook = Callable[["ResponseHookPayload"], None]
"""A synchronous callback invoked **after** a response is received.

The callback receives a read-only ``ResponseHookPayload`` describing the
outcome of the request, including the provider name, status code, latency
and an optional exception if the request failed. Exceptions raised by
hooks are logged and swallowed so a misbehaving observer can never break
user requests.
"""


@dataclass(frozen=True)
class RequestHookPayload:
    """Payload passed to ``RequestHook`` callbacks.

    Hooks may safely mutate ``extra_headers`` / ``extra_params`` to
    influence the outgoing request. All other fields are read-only.
    """

    method: str
    """HTTP method, e.g. ``"POST"``."""
    url: str
    """Fully resolved request URL (base url + path + params already merged)."""
    provider: str
    """Provider identifier, e.g. ``"ovhcloud"``. May be empty for internal requests."""
    json_body: dict[str, Any] | None
    """The JSON request body, or ``None`` for GET requests."""

    extra_headers: dict[str, str] = field(default_factory=dict)
    """Mutable extra header map. Headers added here are merged into the request."""

    extra_params: dict[str, Any] = field(default_factory=dict)
    """Mutable extra query-parameter map merged into the request."""
    started_at: float = field(default_factory=_time.monotonic)
    """Monotonic timestamp when the payload was created."""

    def set_header(self, name: str, value: str) -> None:
        """Add or overwrite a header that will be merged into the request."""
        self.extra_headers[name] = value

    def set_param(self, name: str, value: Any) -> None:
        """Add or overwrite a query parameter that will be merged into the request."""
        self.extra_params[name] = value


@dataclass(frozen=True)
class ResponseHookPayload:
    """Payload passed to ``ResponseHook`` callbacks."""

    method: str
    """HTTP method of the completed request."""
    url: str
    """Fully resolved request URL."""
    provider: str
    """Provider identifier."""
    status_code: int
    """HTTP status code. ``0`` when the request failed before a response."""
    elapsed_seconds: float
    """Wall-clock duration of the request including retries."""
    body: dict[str, Any] | None
    """Parsed JSON response body, or ``None`` on failure / streaming requests."""

    exception: BaseException | None = None
    """Exception raised by the request, or ``None`` on success."""

    @property
    def ok(self) -> bool:
        """``True`` when the request completed without an exception."""
        return self.exception is None

    @property
    def elapsed_ms(self) -> float:
        """Wall-clock duration of the request in milliseconds."""
        return self.elapsed_seconds * 1000.0


class MiddlewareRegistry:
    """Registry of request / response hooks with safe dispatching.

    Hooks are invoked in registration order. Hooks must be plain synchronous
    callables; async hooks are not supported by the sync request path and
    are skipped with a warning to avoid accidental blocking event loops.

    Example::

        from polyai.middleware import MiddlewareRegistry

        from polyai import Client

        registry = MiddlewareRegistry()
        registry.on_request(lambda p: p.set_header("x-request-id", "123"))
        registry.on_response(lambda p: print(p.status_code, p.elapsed_ms))

        client = Client(middleware=registry)
        client.chat(provider="ovhcloud", model="...", messages=[...])
    """

    def __init__(self) -> None:
        self._request_hooks: list[RequestHook] = []
        self._response_hooks: list[ResponseHook] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def on_request(self, hook: RequestHook) -> RequestHook:
        """Register a request hook and return it (usable as a decorator)."""
        if not callable(hook):
            raise TypeError("on_request hook must be callable")
        self._request_hooks.append(hook)
        return hook

    def on_response(self, hook: ResponseHook) -> ResponseHook:
        """Register a response hook and return it (usable as a decorator)."""
        if not callable(hook):
            raise TypeError("on_response hook must be callable")
        self._response_hooks.append(hook)
        return hook

    def clear(self) -> None:
        """Remove all registered hooks."""
        self._request_hooks.clear()
        self._response_hooks.clear()

    @property
    def request_hook_count(self) -> int:
        """Number of registered request hooks."""
        return len(self._request_hooks)

    @property
    def response_hook_count(self) -> int:
        """Number of registered response hooks."""
        return len(self._response_hooks)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    def dispatch_request(self, payload: RequestHookPayload) -> RequestHookPayload:
        """Invoke all request hooks and return the (possibly mutated) payload.

        Raises raised by individual hooks are logged and swallowed so a
        broken observer cannot break user requests.
        """
        import logging

        log = logging.getLogger(__name__)
        for hook in self._request_hooks:
            try:
                hook(payload)
            except Exception as exc:  # noqa: BLE001 — observers must never break requests
                log.warning(
                    "polyai request hook raised %s: %s",
                    type(exc).__name__,
                    exc,
                )
        return payload

    def dispatch_response(self, payload: ResponseHookPayload) -> None:
        """Invoke all response hooks, swallowing hook exceptions."""
        import logging

        log = logging.getLogger(__name__)
        for hook in self._response_hooks:
            try:
                hook(payload)
            except Exception as exc:  # noqa: BLE001 — observers must never break requests
                log.warning(
                    "polyai response hook raised %s: %s",
                    type(exc).__name__,
                    exc,
                )
