"""Unit tests for ClientConfig."""

from __future__ import annotations

import os

import pytest

from polyai.config import ClientConfig, ProviderConfig


class TestClientConfig:
    def test_defaults(self):
        config = ClientConfig()
        assert config.timeout == 60.0
        assert config.max_retries == 3
        assert config.verify_ssl is True

    def test_explicit_keys(self):
        config = ClientConfig(
            ovhcloud_api_key="ovh-key",
            pollinations_api_key="sk_poll",
            devtoolbox_api_key="dtb_key",
        )
        assert config.get_api_key("ovhcloud") == "ovh-key"
        assert config.get_api_key("pollinations") == "sk_poll"
        assert config.get_api_key("devtoolbox") == "dtb_key"
        assert config.get_api_key("mlvoca") == ""

    def test_env_variables(self, monkeypatch):
        monkeypatch.setenv("OVHCLOUD_API_KEY", "env-ovh-key")
        monkeypatch.setenv("POLLINATIONS_API_KEY", "env-poll-key")
        config = ClientConfig()
        assert config.get_api_key("ovhcloud") == "env-ovh-key"
        assert config.get_api_key("pollinations") == "env-poll-key"

    def test_timeout_env_override(self, monkeypatch):
        monkeypatch.setenv("UNIVERSAL_AI_TIMEOUT", "120")
        config = ClientConfig()
        assert config.timeout == 120.0

    def test_retries_env_override(self, monkeypatch):
        monkeypatch.setenv("UNIVERSAL_AI_MAX_RETRIES", "5")
        config = ClientConfig()
        assert config.max_retries == 5

    def test_provider_config_override(self):
        config = ClientConfig()
        config.providers["ovhcloud"] = ProviderConfig(api_key="provider-level-key", timeout=30.0)
        assert config.get_api_key("ovhcloud") == "provider-level-key"
        assert config.get_timeout("ovhcloud") == 30.0

    def test_get_timeout_fallback(self):
        config = ClientConfig(timeout=45.0)
        assert config.get_timeout("ovhcloud") == 45.0

    def test_masked_repr_hides_secrets(self):
        config = ClientConfig(ovhcloud_api_key="super-secret-key-12345")
        masked = config.masked_repr()
        assert "super-secret-key-12345" not in masked
        assert "****" in masked

    def test_provider_config_auto_created(self):
        config = ClientConfig()
        pc = config.provider_config("ovhcloud")
        assert isinstance(pc, ProviderConfig)
        assert "ovhcloud" in config.providers
