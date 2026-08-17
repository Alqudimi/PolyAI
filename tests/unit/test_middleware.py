"""Tests for the request / response middleware hooks.

All tests run fully offline: the transports are exercised with mocked HTTP
responses so no external API calls are made.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import httpx
import pytest

from polyai.exceptions import InvalidRequestError, ConnectionError, TimeoutError
from polyai.http.transport import SyncTransport
from polyai.middleware import MiddlewareRegistry, RequestHookPayload, ResponseHookPayload


@pytest.fixture
def registry():
    """A fresh middleware registry for each test."""
    return MiddlewareRegistry()


def _make_transport(registry, max_retries=0):
    """Build a SyncTransport whose underlying HTTP client is mocked."""
    transport = SyncTransport(
        base_url="https://api.example.test",
        timeout=5.0,
        middleware=registry,
    )
    transport.retry_policy.max_retries = max_retries
    return transport


def _mock_ok_response(json_body, status=200, headers=None):
    response = MagicMock(spec=httpx.Response)
    response.status_code = status
    response.json.return_value = json_body
    response.headers = headers or {}
    response.text = json.dumps(json_body)
    return response


def test_request_and_response_hooks_fire_once_per_request(registry):
    """Hooks must be invoked exactly once per completed request."""
    events = []
    registry.on_request(lambda p: events.append(("req", p.method, p.provider)))
    registry.on_response(lambda p: events.append(("res", p.status_code, p.provider)))

    transport = _make_transport(registry)
    transport._client.request = MagicMock(return_value=_mock_ok_response({"ok": True}))

    result = transport.request("POST", "chat", json_body={"q": 1}, provider="ovhcloud")

    assert result == {"ok": True}
    assert events == [
        ("req", "POST", "ovhcloud"),
        ("res", 200, "ovhcloud"),
    ]


def test_request_hook_can_inject_headers(registry):
    """Mutating extra_headers in a request hook must propagate to the HTTP call."""
    def header_hook(payload: RequestHookPayload) -> None:
        payload.set_header("x-trace-id", "trace-42")

    registry.on_request(header_hook)

    transport = _make_transport(registry)
    captured = {}

    def fake_request(method, url, **kwargs):
        captured["headers"] = dict(kwargs.get("headers", {}))
        return _mock_ok_response({"ok": True})

    transport._client.request = MagicMock(side_effect=fake_request)
    transport.request("POST", "chat", json_body={}, provider="mlvoca")

    assert captured["headers"].get("x-trace-id") == "trace-42"


def test_request_hook_can_inject_query_params(registry):
    """Mutating extra_params must be merged into the outgoing request params."""
    def param_hook(payload: RequestHookPayload) -> None:
        payload.set_param("beta", "true")

    registry.on_request(param_hook)

    transport = _make_transport(registry)
    captured = {}

    def fake_request(method, url, **kwargs):
        captured["params"] = dict(kwargs.get("params", {}))
        return _mock_ok_response({"ok": True})

    transport._client.request = MagicMock(side_effect=fake_request)
    transport.request("GET", "models", params={"limit": 10}, provider="pollinations")

    assert captured["params"] == {"limit": 10, "beta": "true"}


def test_request_hook_receives_url_and_provider(registry):
    """The request payload must expose the resolved URL and provider."""
    payload_seen = {}

    def collector(payload: RequestHookPayload) -> None:
        payload_seen.update({
            "url": payload.url,
            "provider": payload.provider,
            "json_body": payload.json_body,
        })

    registry.on_request(collector)

    transport = _make_transport(registry)
    transport._client.request = MagicMock(return_value=_mock_ok_response({"ok": True}))
    transport.request("POST", "v1/chat", json_body={"m": "x"}, provider="devtoolbox")

    assert payload_seen["url"] == "https://api.example.test/v1/chat"
    assert payload_seen["provider"] == "devtoolbox"
    assert payload_seen["json_body"] == {"m": "x"}


def test_response_hook_receives_latency_and_body(registry):
    """Response payloads must carry the status, elapsed time and parsed body."""
    payload_seen = {}

    def collector(payload: ResponseHookPayload) -> None:
        payload_seen.update({
            "status": payload.status_code,
            "elapsed": payload.elapsed_seconds,
            "body": payload.body,
            "ok": payload.ok,
            "ms": payload.elapsed_ms,
        })

    registry.on_response(collector)

    transport = _make_transport(registry)
    transport._client.request = MagicMock(return_value=_mock_ok_response({"model": "m1"}))
    transport.request("GET", "models", provider="mlvoca")

    assert payload_seen["status"] == 200
    assert payload_seen["body"] == {"model": "m1"}
    assert payload_seen["ok"] is True
    assert payload_seen["elapsed"] >= 0
    assert abs(payload_seen["ms"] - payload_seen["elapsed"] * 1000) < 1e-6


def test_response_hook_runs_on_http_error(registry):
    """Failed HTTP responses must still be reported to response hooks."""
    payload_seen = {}
    registry.on_response(lambda p: payload_seen.update({"status": p.status_code, "ok": p.ok}))

    transport = _make_transport(registry)
    transport._client.request = MagicMock(
        return_value=_mock_ok_response({"error": {"message": "bad"}}, status=400)
    )

    with pytest.raises(InvalidRequestError):
        transport.request("POST", "chat", json_body={}, provider="ovhcloud")

    assert payload_seen == {"status": 400, "ok": False}


def test_response_hook_runs_on_exception(registry):
    """Exceptions must be surfaced to response hooks before being re-raised."""
    payload_seen = {}

    def collector(payload: ResponseHookPayload) -> None:
        payload_seen.update({
            "status": payload.status_code,
            "ok": payload.ok,
            "exc_type": type(payload.exception).__name__ if payload.exception else None,
        })

    registry.on_response(collector)

    transport = _make_transport(registry)
    transport._client.request = MagicMock(side_effect=httpx.TimeoutException("x"))

    with pytest.raises(TimeoutError):
        transport.request("POST", "chat", json_body={}, provider="ovhcloud")

    assert payload_seen["ok"] is False
    assert payload_seen["exc_type"] == "TimeoutError"


def test_response_hook_runs_on_connection_error(registry):
    """Network failures must also trigger response hooks with the original exception."""
    payload_seen = {}
    registry.on_response(lambda p: payload_seen.update({"ok": p.ok, "exc": type(p.exception).__name__}))

    transport = _make_transport(registry)
    transport._client.request = MagicMock(side_effect=httpx.ConnectError("network down"))

    with pytest.raises(ConnectionError):
        transport.request("POST", "chat", json_body={}, provider="pollinations")

    assert payload_seen["ok"] is False
    assert payload_seen["exc"] == "ConnectionError"


def test_hook_exception_is_swallowed(registry):
    """A misbehaving hook must never break the user request."""
    registry.on_request(lambda _p: 1 / 0)  # raises ZeroDivisionError

    transport = _make_transport(registry)
    transport._client.request = MagicMock(return_value=_mock_ok_response({"ok": True}))

    result = transport.request("POST", "chat", json_body={}, provider="mlvoca")
    assert result == {"ok": True}

    registry.on_response(lambda _p: (_ for _ in ()).throw(RuntimeError("boom")))
    transport.request("POST", "chat", json_body={}, provider="mlvoca")


def test_zero_cost_without_middleware():
    """Without a registry, no hooks are consulted and the transport works as before."""
    transport = SyncTransport(base_url="https://api.example.test", timeout=5.0)
    assert transport._middleware is None
    transport._client.request = MagicMock(return_value=_mock_ok_response({"ok": True}))
    assert transport.request("POST", "chat", json_body={}, provider="ovhcloud") == {"ok": True}


def test_registry_registration_api(registry):
    """on_request / on_response accept callables and return them (decorator usage)."""
    def my_hook(_p):
        pass

    returned = registry.on_request(my_hook)
    assert returned is my_hook
    assert registry.request_hook_count == 1

    returned2 = registry.on_response(my_hook)
    assert returned2 is my_hook
    assert registry.response_hook_count == 1

    registry.clear()
    assert registry.request_hook_count == 0
    assert registry.response_hook_count == 0


def test_registry_rejects_non_callable(registry):
    with pytest.raises(TypeError):
        registry.on_request("not-a-hook")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        registry.on_response(42)  # type: ignore[arg-type]


def test_streaming_requests_report_status_to_hooks(registry):
    """Streaming requests report the final status code to response hooks."""
    payload_seen = {}
    registry.on_response(lambda p: payload_seen.update({"status": p.status_code, "body": p.body}))

    transport = _make_transport(registry)
    stream_response = MagicMock(spec=httpx.Response)
    stream_response.status_code = 200
    stream_response.iter_lines.return_value = iter(["data: hello", "data: [DONE]"])

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=stream_response)
    ctx.__exit__ = MagicMock(return_value=False)
    transport._client.stream = MagicMock(return_value=ctx)

    lines = list(transport.stream("POST", "chat", json_body={}, provider="ovhcloud"))
    assert lines == ["hello"]
    assert payload_seen["status"] == 200
    assert payload_seen["body"] is None


@pytest.mark.asyncio
async def test_async_transport_dispatches_hooks():
    """AsyncTransport must invoke both request and response hooks."""
    registry = MiddlewareRegistry()
    events = []
    registry.on_request(lambda p: events.append(("req", p.method, p.provider)))
    registry.on_response(lambda p: events.append(("res", p.status_code)))

    transport = _make_async_transport(registry)

    async def fake_request(method, url, **_kwargs):
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.json.return_value = {"id": "m1"}
        response.headers = {}
        response.text = "{}"
        return response

    transport._client.request = fake_request

    result = await transport.request("GET", "models", provider="pollinations")
    assert result == {"id": "m1"}
    assert events == [("req", "GET", "pollinations"), ("res", 200)]


def _ok_response(**overrides):
    response = MagicMock(spec=httpx.Response)
    response.status_code = overrides.get("status", 200)
    response.json.return_value = overrides.get("body", {"ok": True})
    response.headers = {}
    response.text = "{}"
    return response


def _make_async_transport(registry):
    from polyai.http.async_transport import AsyncTransport

    transport = AsyncTransport(
        base_url="https://api.example.test",
        timeout=5.0,
        middleware=registry,
    )
    transport.retry_policy.max_retries = 0
    return transport


@pytest.mark.asyncio
async def test_async_hook_exception_is_swallowed():
    """An async request must still succeed when a hook misbehaves."""
    registry = MiddlewareRegistry()
    registry.on_request(lambda _p: (_ for _ in ()).throw(ValueError("bad hook")))

    transport = _make_async_transport(registry)

    async def fake_request(method, url, **_kwargs):
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.json.return_value = {"ok": True}
        response.headers = {}
        response.text = "{}"
        return response

    transport._client.request = fake_request
    result = await transport.request("POST", "chat", json_body={}, provider="mlvoca")
    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_async_response_hook_reports_exception():
    """Async failures must be reported to response hooks before re-raising."""
    registry = MiddlewareRegistry()
    payload_seen = {}
    registry.on_response(lambda p: payload_seen.update({"ok": p.ok, "exc": type(p.exception).__name__}))

    transport = _make_async_transport(registry)

    async def fake_request(method, url, **_kwargs):
        raise httpx.TimeoutException("x")

    transport._client.request = fake_request

    with pytest.raises(TimeoutError):
        await transport.request("POST", "chat", json_body={}, provider="ovhcloud")

    assert payload_seen["ok"] is False
    assert payload_seen["exc"] == "TimeoutError"
