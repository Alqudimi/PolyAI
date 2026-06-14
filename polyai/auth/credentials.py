"""
Credential strategies for each provider's authentication scheme.

All credential classes expose an ``apply(headers)`` method that injects
the necessary auth headers without ever logging the key value.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class Credentials(ABC):
    """Abstract credential strategy."""

    @abstractmethod
    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject auth information into ``headers`` (in place) and return it."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if credentials are non-empty / usable."""


class NoAuthCredentials(Credentials):
    """No authentication — for mlvoca and anonymous DevToolbox / OVHcloud tiers."""

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        return headers

    def is_configured(self) -> bool:
        return True

    def __repr__(self) -> str:
        return "NoAuthCredentials()"


class BearerCredentials(Credentials):
    """``Authorization: Bearer <token>`` — used by OVHcloud and Pollinations."""

    def __init__(self, token: str) -> None:
        self._token = token

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def is_configured(self) -> bool:
        return bool(self._token)

    def __repr__(self) -> str:
        masked = (self._token[:4] + "****") if self._token else "(not set)"
        return f"BearerCredentials(token={masked!r})"


class ApiKeyHeaderCredentials(Credentials):
    """``X-API-Key: <key>`` — used by DevToolbox premium tier."""

    def __init__(self, key: str, header_name: str = "X-API-Key") -> None:
        self._key = key
        self._header_name = header_name

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        if self._key:
            headers[self._header_name] = self._key
        return headers

    def is_configured(self) -> bool:
        return bool(self._key)

    def __repr__(self) -> str:
        masked = (self._key[:4] + "****") if self._key else "(not set)"
        return f"ApiKeyHeaderCredentials(key={masked!r})"
