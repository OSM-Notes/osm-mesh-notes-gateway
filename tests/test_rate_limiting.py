"""Tests for rate limiting."""

import pytest
import time
from gateway.rate_limiter import RateLimiter
from gateway.config import USER_RATE_LIMIT_WINDOW, USER_RATE_LIMIT_MAX_MESSAGES


@pytest.fixture
def rate_limiter():
    """Create rate limiter."""
    return RateLimiter()


def test_rate_limit_allows_under_limit(rate_limiter):
    """Test that rate limiter allows messages under the limit."""
    node_id = "test_node"
    
    # Send messages up to limit - 1
    for i in range(USER_RATE_LIMIT_MAX_MESSAGES - 1):
        allowed, msg = rate_limiter.check_rate_limit(node_id)
        assert allowed is True
        assert msg is None


def test_rate_limit_blocks_over_limit(rate_limiter):
    """Test that rate limiter blocks messages over the limit."""
    node_id = "test_node"
    
    # Send messages up to limit
    for i in range(USER_RATE_LIMIT_MAX_MESSAGES):
        allowed, msg = rate_limiter.check_rate_limit(node_id)
        assert allowed is True  # All should be allowed up to limit
    
    # Next message should be blocked
    allowed, msg = rate_limiter.check_rate_limit(node_id)
    assert allowed is False
    assert msg is not None
    assert "Límite de mensajes" in msg


def test_rate_limit_resets_after_window(rate_limiter, monkeypatch):
    """Test that rate limit resets after the time window."""
    node_id = "test_node"
    
    # Fill up the limit
    for i in range(USER_RATE_LIMIT_MAX_MESSAGES):
        rate_limiter.check_rate_limit(node_id)
    
    # Should be blocked
    allowed, _ = rate_limiter.check_rate_limit(node_id)
    assert allowed is False
    
    # Simulate time passing (move timestamps back)
    if node_id in rate_limiter.user_messages:
        # Move all timestamps back by more than the window
        old_timestamps = rate_limiter.user_messages[node_id]
        rate_limiter.user_messages[node_id] = [
            ts - USER_RATE_LIMIT_WINDOW - 1 for ts in old_timestamps
        ]
    
    # Should now be allowed (cleanup will remove old entries)
    allowed, msg = rate_limiter.check_rate_limit(node_id)
    assert allowed is True
    assert msg is None


def test_rate_limit_per_user(rate_limiter):
    """Test that rate limit is per user."""
    node1 = "node1"
    node2 = "node2"
    
    # Fill up limit for node1
    for i in range(USER_RATE_LIMIT_MAX_MESSAGES):
        rate_limiter.check_rate_limit(node1)
    
    # node1 should be blocked
    allowed, _ = rate_limiter.check_rate_limit(node1)
    assert allowed is False
    
    # node2 should still be allowed
    allowed, _ = rate_limiter.check_rate_limit(node2)
    assert allowed is True


def test_rate_limit_cleanup(rate_limiter):
    """Test that old entries are cleaned up."""
    node_id = "test_node"
    
    # Add old entries manually (outside window)
    old_time = time.time() - (USER_RATE_LIMIT_WINDOW + 1)
    rate_limiter.user_messages[node_id] = [old_time]
    
    # Trigger cleanup by checking rate limit (which calls cleanup if needed)
    rate_limiter._last_cleanup = time.time() - (rate_limiter._cleanup_interval + 1)
    rate_limiter.check_rate_limit(node_id)
    
    # Old entries should be removed (check_rate_limit removes entries outside window)
    # The entry might still exist but should be empty after cleanup
    if node_id in rate_limiter.user_messages:
        # After check_rate_limit, old entries are filtered out
        # So the list should only contain new entries (the one we just added)
        assert len(rate_limiter.user_messages[node_id]) <= 1
