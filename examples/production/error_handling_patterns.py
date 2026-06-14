"""
Production Example: Comprehensive Error Handling Patterns

Demonstrates production-grade error handling strategies:
- Tiered exception handling
- Circuit breaker pattern
- Retry with jitter
- Graceful degradation
- Fallback responses
- Dead letter queue (logging)

Usage:
    python examples/production/error_handling_patterns.py
"""

from __future__ import annotations

import logging
import random
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Callable

from polyai import Client, ClientConfig
from polyai.exceptions import (
    AuthenticationError,
    ConnectionError,
    ContentFilterError,
    ContextLengthExceededError,
    FeatureNotSupportedError,
    InvalidRequestError,
    ModelNotFoundError,
    PermissionDeniedError,
    ProviderError,
    ProviderNotSupportedError,
    ProviderUnavailableError,
    RateLimitError,
    StreamingError,
    TimeoutError,
    UniversalAIError,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Pattern 1: Tiered exception handling
# ──────────────────────────────────────────────────────────────────────────────

def chat_with_tiered_handling(client: Client, messages: list[dict]) -> str | None:
    """Handle different error types differently."""
    try:
        response = client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=messages,
            max_tokens=200,
        )
        return response.text

    # Fix immediately — these won't resolve on retry
    except AuthenticationError:
        logger.error("CRITICAL: API key is invalid. Check OVHCLOUD_API_KEY.")
        raise  # re-raise; alert your ops team

    except PermissionDeniedError:
        logger.error("Permission denied. Check API key scopes.")
        raise

    except ModelNotFoundError as e:
        logger.error("Model not found: %s. Check model ID.", e)
        # Try with a known-good fallback model
        return client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",  # fallback to a stable model
            messages=messages,
            max_tokens=200,
        ).text

    # Recoverable — retry or degrade
    except RateLimitError as e:
        wait = e.retry_after or 60
        logger.warning("Rate limited. Waiting %ds.", wait)
        time.sleep(min(wait, 30))  # cap at 30s in examples
        return None  # caller can retry

    except ContextLengthExceededError:
        logger.warning("Context too long. Truncating...")
        # Keep only the last 2 messages
        truncated = messages[-2:] if len(messages) > 2 else messages
        return chat_with_tiered_handling(client, truncated)

    except ContentFilterError:
        logger.warning("Content was filtered. Returning safe default.")
        return "I'm unable to respond to that request."

    except TimeoutError:
        logger.warning("Request timed out.")
        return None

    except ConnectionError:
        logger.warning("Network error. Check connectivity.")
        return None

    except ProviderUnavailableError:
        logger.warning("Provider unavailable. Try later.")
        return None

    except InvalidRequestError as e:
        logger.error("Bad request: %s. Fix the parameters.", e)
        raise

    except FeatureNotSupportedError as e:
        logger.error("Feature not supported: %s.", e)
        raise

    except ProviderNotSupportedError as e:
        logger.error("Unknown provider: %s.", e)
        raise

    except StreamingError as e:
        logger.error("Streaming error: %s.", e)
        return None

    except ProviderError:
        logger.warning("Provider server error.")
        return None

    except UniversalAIError as e:
        logger.error("Unexpected AI error: %s (HTTP %s)", e, e.status_code)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Pattern 2: Circuit Breaker
# ──────────────────────────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Prevents cascading failures by stopping requests to a failing provider.

    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Provider is failing, requests are blocked
    - HALF-OPEN: Testing if provider recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._failure_count = 0
        self._success_count = 0
        self._state = "CLOSED"
        self._opened_at: datetime | None = None

    @property
    def state(self) -> str:
        if self._state == "OPEN":
            assert self._opened_at is not None
            if datetime.utcnow() - self._opened_at > timedelta(seconds=self.recovery_timeout):
                self._state = "HALF-OPEN"
                self._success_count = 0
        return self._state

    def can_request(self) -> bool:
        return self.state != "OPEN"

    def record_success(self) -> None:
        self._failure_count = 0
        if self._state == "HALF-OPEN":
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = "CLOSED"
                logger.info("Circuit breaker CLOSED (provider recovered)")

    def record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"
            self._opened_at = datetime.utcnow()
            logger.warning(
                "Circuit breaker OPEN (too many failures). "
                "Will retry in %ds.", self.recovery_timeout
            )


class CircuitBreakerClient:
    """Client wrapper with circuit breaker per provider."""

    def __init__(self, client: Client) -> None:
        self._client = client
        self._breakers: dict[str, CircuitBreaker] = {}

    def _get_breaker(self, provider: str) -> CircuitBreaker:
        if provider not in self._breakers:
            self._breakers[provider] = CircuitBreaker()
        return self._breakers[provider]

    def chat(self, provider: str, **kwargs) -> str | None:
        breaker = self._get_breaker(provider)
        if not breaker.can_request():
            logger.warning("Circuit OPEN for %s — request blocked", provider)
            return None

        try:
            response = self._client.chat(provider=provider, **kwargs)
            breaker.record_success()
            return response.text
        except (ProviderUnavailableError, ProviderError, TimeoutError, ConnectionError) as e:
            breaker.record_failure()
            logger.warning("Provider %s failed: %s (failures=%d)", provider, e, breaker._failure_count)
            return None
        except UniversalAIError:
            # Don't trip the breaker for auth errors, rate limits, etc.
            raise


# ──────────────────────────────────────────────────────────────────────────────
# Pattern 3: Retry with exponential backoff + jitter
# ──────────────────────────────────────────────────────────────────────────────

def retry_chat(
    fn: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
):
    """Retry a function with exponential backoff and full jitter."""
    last_error = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except (RateLimitError, ProviderError, ProviderUnavailableError, TimeoutError) as e:
            last_error = e
            if attempt < max_attempts - 1:
                cap = min(max_delay, base_delay * (2 ** attempt))
                wait = random.uniform(0, cap)  # full jitter
                logger.info("Attempt %d failed. Waiting %.1fs...", attempt + 1, wait)
                time.sleep(wait)
        except (AuthenticationError, InvalidRequestError, FeatureNotSupportedError):
            raise  # non-retryable
    raise last_error


# ──────────────────────────────────────────────────────────────────────────────
# Pattern 4: Fallback chain with degradation
# ──────────────────────────────────────────────────────────────────────────────

PROVIDER_CHAIN = [
    ("ovhcloud",     "meta-llama-3_3-70b-instruct"),  # best quality
    ("ovhcloud",     "llama-3.1-8b-instruct"),         # faster
    ("pollinations", "openai"),                         # fallback
    ("mlvoca",       "tinyllama"),                      # last resort
]

FALLBACK_RESPONSE = "I'm sorry, all AI services are temporarily unavailable. Please try again later."


def chat_with_fallback(client: Client, messages: list[dict], max_tokens: int = 200) -> str:
    """Try providers in order, return fallback if all fail."""
    for provider, model in PROVIDER_CHAIN:
        try:
            response = client.chat(
                provider=provider,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
            )
            logger.info("Succeeded with %s/%s", provider, model)
            return response.text
        except (AuthenticationError, PermissionDeniedError):
            raise  # configuration error — don't try next
        except UniversalAIError as e:
            logger.warning("Failed %s/%s: %s", provider, model, e)
            continue

    logger.error("All providers exhausted. Returning fallback response.")
    return FALLBACK_RESPONSE


# ──────────────────────────────────────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    config = ClientConfig(max_retries=1, timeout=30.0)
    client = Client(config=config)

    messages = [{"role": "user", "content": "What is 2 + 2?"}]

    print("Pattern 1: Tiered error handling")
    result = chat_with_tiered_handling(client, messages)
    print(f"Result: {result}\n")

    print("Pattern 2: Circuit breaker")
    cb_client = CircuitBreakerClient(client)
    result = cb_client.chat(
        provider="ovhcloud",
        model="llama-3.1-8b-instruct",
        messages=messages,
        max_tokens=50,
    )
    print(f"Result: {result}\n")

    print("Pattern 3: Retry with jitter")
    result = retry_chat(
        lambda: client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=messages,
            max_tokens=50,
        ).text,
        max_attempts=3,
    )
    print(f"Result: {result}\n")

    print("Pattern 4: Fallback chain")
    result = chat_with_fallback(client, messages)
    print(f"Result: {result}\n")


if __name__ == "__main__":
    main()
