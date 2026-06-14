"""
Integration tests for DevToolbox API.

No API key required for the free tier.
Gated behind UNIVERSAL_AI_INTEGRATION_TESTS=1.

Run:
    UNIVERSAL_AI_INTEGRATION_TESTS=1 pytest tests/integration/test_devtoolbox.py -v
"""

from __future__ import annotations

import os

import pytest

from polyai import Client
from polyai.config import ClientConfig

SKIP_REASON = "Set UNIVERSAL_AI_INTEGRATION_TESTS=1 to run integration tests"
INTEGRATION = pytest.mark.skipif(
    os.environ.get("UNIVERSAL_AI_INTEGRATION_TESTS") != "1",
    reason=SKIP_REASON,
)


@pytest.fixture(scope="module")
def client():
    config = ClientConfig(timeout=30.0, max_retries=2)
    c = Client(config=config)
    yield c
    c.close()


@INTEGRATION
class TestDevToolboxChat:
    def test_generate(self, client):
        resp = client.chat(
            provider="devtoolbox",
            model="devtoolbox-ai",
            messages=[{"role": "user", "content": "Write a haiku about the ocean."}],
        )
        assert resp.text.strip()
        assert resp.provider == "devtoolbox"


@INTEGRATION
class TestDevToolboxAI:
    @pytest.fixture
    def devtools(self, client):
        return client.with_provider("devtoolbox").devtools

    def test_summarize(self, devtools):
        long_text = "Python is a high-level programming language. " * 10
        result = devtools.summarize(long_text, max_length=100)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_translate(self, devtools):
        result = devtools.translate("Hello, how are you?", "fr")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_explain_code(self, devtools):
        code = "const sum = arr.reduce((acc, val) => acc + val, 0);"
        result = devtools.explain_code(code)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_regex(self, devtools):
        result = devtools.generate_regex("match email addresses")
        assert isinstance(result, str)
        assert len(result) > 0


@INTEGRATION
class TestDevToolboxUtilities:
    @pytest.fixture
    def devtools(self, client):
        return client.with_provider("devtoolbox").devtools

    def test_generate_uuid(self, devtools):
        uuid = devtools.generate_uuid()
        assert isinstance(uuid, str)
        assert len(uuid) > 0

    def test_hash_sha256(self, devtools):
        result = devtools.hash("sha256", "hello")
        assert isinstance(result, dict)

    def test_generate_password(self, devtools):
        pwd = devtools.generate_password(length=16)
        assert isinstance(pwd, str)
        assert len(pwd) >= 8

    def test_lorem_ipsum(self, devtools):
        text = devtools.lorem_ipsum(paragraphs=2)
        assert isinstance(text, str)
        assert len(text) > 0
