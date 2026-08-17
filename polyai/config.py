"""
Configuration system for polyai SDK.

Credentials are read from the environment automatically; never hard-code secrets.

Environment variables:
    OVHCLOUD_API_KEY         — OVHcloud AI Endpoints API key
    POLLINATIONS_API_KEY     — Pollinations sk_… key
    DEVTOOLBOX_API_KEY       — DevToolbox dtb_… key (optional)
    MLVOCA_BASE_URL          — Override mlvoca base URL (optional)
    UNIVERSAL_AI_TIMEOUT     — Default request timeout in seconds
    UNIVERSAL_AI_MAX_RETRIES — Default max retry count
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ProviderConfig:
    """Per-provider configuration."""

    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: Optional[float] = None
    max_retries: Optional[int] = None
    extra_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class ClientConfig:
    """Top-level SDK configuration.

    Args:
        ovhcloud_api_key:     OVHcloud API key. Defaults to OVHCLOUD_API_KEY env var.
        pollinations_api_key: Pollinations API key. Defaults to POLLINATIONS_API_KEY env var.
        devtoolbox_api_key:   DevToolbox API key. Defaults to DEVTOOLBOX_API_KEY env var.
        timeout:              Default request timeout (seconds). Default: 60.0.
        max_retries:          Maximum automatic retries. Default: 3.
        retry_on_status:      HTTP status codes that trigger a retry.
        providers:            Per-provider overrides keyed by provider name.
        user_agent:           Custom User-Agent suffix appended to the SDK default.
        proxy:                HTTP/S proxy URL.
        verify_ssl:           Verify TLS certificates. Default: True.
        log_level:            Logging level ("DEBUG", "INFO", "WARNING", "ERROR").
        middleware:           Optional ``MiddlewareRegistry`` for request / response hooks.
    """

    ovhcloud_api_key: Optional[str] = None
    pollinations_api_key: Optional[str] = None
    devtoolbox_api_key: Optional[str] = None

    timeout: float = 60.0
    max_retries: int = 3
    retry_on_status: tuple = (429, 500, 502, 503, 504)

    providers: Dict[str, ProviderConfig] = field(default_factory=dict)

    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    verify_ssl: bool = True

    log_level: str = "WARNING"

    middleware: Optional[Any] = None

    def __post_init__(self) -> None:
        if self.ovhcloud_api_key is None:
            self.ovhcloud_api_key = os.environ.get("OVHCLOUD_API_KEY", "")
        if self.pollinations_api_key is None:
            self.pollinations_api_key = os.environ.get("POLLINATIONS_API_KEY", "")
        if self.devtoolbox_api_key is None:
            self.devtoolbox_api_key = os.environ.get("DEVTOOLBOX_API_KEY", "")

        env_timeout = os.environ.get("UNIVERSAL_AI_TIMEOUT")
        if env_timeout:
            self.timeout = float(env_timeout)

        env_retries = os.environ.get("UNIVERSAL_AI_MAX_RETRIES")
        if env_retries:
            self.max_retries = int(env_retries)

    def provider_config(self, name: str) -> ProviderConfig:
        """Return the ProviderConfig for the given provider, creating a default if absent."""
        if name not in self.providers:
            self.providers[name] = ProviderConfig()
        return self.providers[name]

    def get_api_key(self, provider: str) -> str:
        """Return the effective API key for a provider (provider-level > top-level > env)."""
        pc = self.providers.get(provider)
        if pc and pc.api_key:
            return pc.api_key
        mapping = {
            "ovhcloud": self.ovhcloud_api_key or "",
            "pollinations": self.pollinations_api_key or "",
            "devtoolbox": self.devtoolbox_api_key or "",
            "mlvoca": "",
        }
        return mapping.get(provider, "")

    def get_timeout(self, provider: str) -> float:
        """Return the effective timeout for a provider."""
        pc = self.providers.get(provider)
        if pc and pc.timeout is not None:
            return pc.timeout
        return self.timeout

    def get_max_retries(self, provider: str) -> int:
        """Return the effective max_retries for a provider."""
        pc = self.providers.get(provider)
        if pc and pc.max_retries is not None:
            return pc.max_retries
        return self.max_retries

    def masked_repr(self) -> str:
        """Return a safe repr with secrets masked — suitable for logs."""

        def _mask(v: Optional[str]) -> str:
            if not v:
                return "(not set)"
            return v[:4] + "****" + v[-2:] if len(v) > 6 else "****"

        return (
            f"ClientConfig("
            f"ovhcloud_api_key={_mask(self.ovhcloud_api_key)}, "
            f"pollinations_api_key={_mask(self.pollinations_api_key)}, "
            f"devtoolbox_api_key={_mask(self.devtoolbox_api_key)}, "
            f"timeout={self.timeout}, "
            f"max_retries={self.max_retries})"
        )
