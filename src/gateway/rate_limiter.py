"""Rate limiting per user."""

import time
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from .config import USER_RATE_LIMIT_WINDOW, USER_RATE_LIMIT_MAX_MESSAGES

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter for user messages.
    
    Tracks message timestamps per user and enforces rate limits to prevent
    spam or excessive API usage.
    """

    def __init__(self):
        # Dictionary mapping node_id -> list of timestamps
        self.user_messages: Dict[str, List[float]] = defaultdict(list)
        self._cleanup_interval = 300  # Clean up old entries every 5 minutes
        self._last_cleanup = time.time()

    def check_rate_limit(self, node_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limit.
        
        Args:
            node_id: Meshtastic node ID
            
        Returns:
            Tuple of (allowed, message):
            - allowed: True if within rate limit, False if exceeded
            - message: Optional error message if rate limit exceeded
        """
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_old_entries(now)
            self._last_cleanup = now
        
        # Get user's message timestamps
        timestamps = self.user_messages[node_id]
        
        # Remove timestamps outside the window
        window_start = now - USER_RATE_LIMIT_WINDOW
        timestamps[:] = [ts for ts in timestamps if ts > window_start]
        
        # Check if limit exceeded
        if len(timestamps) >= USER_RATE_LIMIT_MAX_MESSAGES:
            remaining_time = int(timestamps[0] + USER_RATE_LIMIT_WINDOW - now)
            error_msg = (
                f"❌ Límite de mensajes alcanzado.\n"
                f"Espera {remaining_time} segundos antes de enviar otro mensaje.\n"
                f"⚠️ No envíes datos personales ni emergencias médicas."
            )
            logger.warning(f"Rate limit exceeded for {node_id}: {len(timestamps)} messages in window")
            return False, error_msg
        
        # Record this message
        timestamps.append(now)
        return True, None

    def _cleanup_old_entries(self, now: float):
        """Remove entries for users with no recent messages."""
        window_start = now - USER_RATE_LIMIT_WINDOW
        to_remove = []
        
        for node_id, timestamps in self.user_messages.items():
            # Remove old timestamps
            timestamps[:] = [ts for ts in timestamps if ts > window_start]
            # Mark for removal if empty
            if not timestamps:
                to_remove.append(node_id)
        
        for node_id in to_remove:
            del self.user_messages[node_id]
        
        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} inactive users from rate limiter")
