"""
Core performance benchmarks for PolyAI.

Measures the hot paths that affect every caller: client instantiation,
provider resolution, config lookups, and message truncation / token counting
on the request-preparation path. These benchmarks run fully offline (no
network calls, no API keys) so they stay deterministic across CI runs.

Run:
    pytest tests/benchmarks -v --benchmark-only
"""

from __future__ import annotations

import pytest

from polyai import Client
from polyai.config import ClientConfig
from polyai.utils.helpers import (
    count_tokens_approx,
    truncate_messages,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def config() -> ClientConfig:
    return ClientConfig(timeout=120.0, max_retries=2)


@pytest.fixture(scope="module")
def client(config: ClientConfig) -> Client:
    instance = Client(config=config)
    yield instance
    instance.close()


@pytest.fixture(scope="module")
def long_messages():
    """A realistic 50-turn conversation with varying message sizes."""
    return [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg-{i}: " + "x" * 200}
        for i in range(100)
    ]


@pytest.fixture(scope="module")
def long_text() -> str:
    return "word " * 10_000


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------


class TestClientInstantiation:
    """Client construction happens once per application lifecycle, but it
    builds the internal provider registry wiring, so it is worth watching."""

    def test_client_init(self, benchmark, config):
        benchmark(Client, config=config)

    def test_client_with_provider(self, benchmark, client):
        benchmark(client.with_provider, "mlvoca")


class TestProviderLookup:
    """Provider resolution is exercised on every resource call."""

    def test_get_provider(self, benchmark, client):
        benchmark(client._get_provider, "mlvoca")

    def test_provider_config_lookup(self, benchmark, config):
        benchmark(config.provider_config, "pollinations")

    def test_api_key_lookup(self, benchmark, config):
        benchmark(config.get_api_key, "mlvoca")

    def test_timeout_lookup(self, benchmark, config):
        benchmark(config.get_timeout, "ovhcloud")

    def test_max_retries_lookup(self, benchmark, config):
        benchmark(config.get_max_retries, "devtoolbox")


class TestRequestPreparation:
    """Truncation and token counting run on the hot request path."""

    def test_truncate_messages_short_context(self, benchmark, long_messages):
        benchmark(truncate_messages, long_messages, max_tokens=2000)

    def test_truncate_messages_medium_context(self, benchmark, long_messages):
        benchmark(truncate_messages, long_messages, max_tokens=8000)

    def test_count_tokens_small(self, benchmark):
        benchmark(count_tokens_approx, "The quick brown fox jumps over the lazy dog.")

    def test_count_tokens_large(self, benchmark, long_text):
        benchmark(count_tokens_approx, long_text)
