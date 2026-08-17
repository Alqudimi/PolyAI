"""
Retry policy with exponential backoff and jitter.

The default policy mirrors the behaviour of the official OpenAI Python SDK:
    - Up to ``max_retries`` attempts (not counting the initial attempt).
    - Retries on network errors and selected HTTP status codes.
    - Exponential backoff: ``base * (2 ** attempt)`` seconds, capped at ``max_wait``.
    - Full jitter: random fraction of the computed wait time.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    """Configure retry behaviour.

    Args:
        max_retries:      Maximum number of retry attempts. Default: 3.
        base_delay:       Starting back-off delay in seconds. Default: 0.5.
        max_delay:        Maximum back-off delay in seconds. Default: 60.0.
        jitter:           Apply random jitter to back-off. Default: True.
        retry_on_status:  HTTP status codes that should trigger a retry.
        retry_on_timeout: Retry on request timeout. Default: True.
        retry_on_network: Retry on low-level network errors. Default: True.
    """

    max_retries: int = 3
    base_delay: float = 0.5
    max_delay: float = 60.0
    jitter: bool = True
    retry_on_status: tuple[int, ...] = (429, 500, 502, 503, 504)
    retry_on_timeout: bool = True
    retry_on_network: bool = True

    def should_retry(self, attempt: int, status_code: int | None = None, is_network_error: bool = False, is_timeout: bool = False) -> bool:
        """Return True if the request should be retried."""
        if attempt >= self.max_retries:
            return False
        if is_timeout and self.retry_on_timeout:
            return True
        if is_network_error and self.retry_on_network:
            return True
        if status_code is not None and status_code in self.retry_on_status:
            return True
        return False

    def wait_time(self, attempt: int, retry_after: float | None = None) -> float:
        """Return the number of seconds to wait before the next attempt.

        Args:
            attempt:     0-indexed attempt number (0 = first retry).
            retry_after: Server-specified ``Retry-After`` value (seconds).
        """
        if retry_after is not None:
            return min(retry_after, self.max_delay)

        delay = self.base_delay * (2 ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            delay = random.uniform(0, delay)

        return delay

    def sleep(self, attempt: int, retry_after: float | None = None) -> None:
        """Block for the computed wait duration."""
        wait = self.wait_time(attempt, retry_after)
        logger.debug("Retrying in %.2f seconds (attempt %d)", wait, attempt + 1)
        time.sleep(wait)

    async def async_sleep(self, attempt: int, retry_after: float | None = None) -> None:
        """Async-sleep for the computed wait duration."""
        import asyncio
        wait = self.wait_time(attempt, retry_after)
        logger.debug("Retrying in %.2f seconds (attempt %d)", wait, attempt + 1)
        await asyncio.sleep(wait)
