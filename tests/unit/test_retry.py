"""Unit tests for RetryPolicy."""

from __future__ import annotations

import pytest

from polyai.http.retry import RetryPolicy


class TestRetryPolicy:
    def test_should_retry_on_status(self):
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(0, status_code=429) is True
        assert policy.should_retry(0, status_code=503) is True
        assert policy.should_retry(0, status_code=200) is False
        assert policy.should_retry(0, status_code=400) is False

    def test_should_not_retry_after_max(self):
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(3, status_code=429) is False
        assert policy.should_retry(3, status_code=503) is False

    def test_should_retry_timeout(self):
        policy = RetryPolicy(max_retries=3, retry_on_timeout=True)
        assert policy.should_retry(0, is_timeout=True) is True

    def test_should_retry_network(self):
        policy = RetryPolicy(max_retries=3, retry_on_network=True)
        assert policy.should_retry(0, is_network_error=True) is True

    def test_no_retry_timeout_disabled(self):
        policy = RetryPolicy(max_retries=3, retry_on_timeout=False)
        assert policy.should_retry(0, is_timeout=True) is False

    def test_wait_time_exponential(self):
        policy = RetryPolicy(base_delay=1.0, max_delay=60.0, jitter=False)
        assert policy.wait_time(0) == 1.0
        assert policy.wait_time(1) == 2.0
        assert policy.wait_time(2) == 4.0
        assert policy.wait_time(3) == 8.0

    def test_wait_time_capped(self):
        policy = RetryPolicy(base_delay=10.0, max_delay=20.0, jitter=False)
        assert policy.wait_time(5) == 20.0

    def test_wait_time_retry_after_override(self):
        policy = RetryPolicy(base_delay=1.0, max_delay=60.0, jitter=False)
        assert policy.wait_time(0, retry_after=15.0) == 15.0

    def test_wait_time_retry_after_capped_by_max(self):
        policy = RetryPolicy(base_delay=1.0, max_delay=10.0, jitter=False)
        assert policy.wait_time(0, retry_after=100.0) == 10.0

    def test_wait_time_with_jitter_in_range(self):
        policy = RetryPolicy(base_delay=1.0, max_delay=10.0, jitter=True)
        for _ in range(20):
            wait = policy.wait_time(0)
            assert 0.0 <= wait <= 1.0

    def test_zero_retries_never_retries(self):
        policy = RetryPolicy(max_retries=0)
        assert policy.should_retry(0, status_code=429) is False
        assert policy.should_retry(0, is_timeout=True) is False
