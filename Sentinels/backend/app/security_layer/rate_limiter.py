"""
Rate Limiter — Per-IP sliding window rate limiter for API protection.

Design:
- In-memory sliding window (no external dependency like Redis)
- Configurable window size and max requests
- Burst protection via short-window secondary limit
- Thread-safe using a threading lock
- Automatic cleanup of expired entries to prevent memory leaks

Usage:
    from app.security_layer.rate_limiter import check_rate_limit

    is_allowed, retry_after = check_rate_limit(client_ip)
    if not is_allowed:
        raise HTTPException(429, f"Rate limited. Retry after {retry_after}s")
"""

import time
import threading
from typing import Dict, List, Tuple
from collections import defaultdict


# ── Configuration ────────────────────────────────────────────────────────────
DEFAULT_WINDOW_SECONDS = 60       # 1-minute sliding window
DEFAULT_MAX_REQUESTS = 10         # Max 10 requests per window

BURST_WINDOW_SECONDS = 5          # 5-second burst window
BURST_MAX_REQUESTS = 3            # Max 3 requests in burst window

CLEANUP_INTERVAL_SECONDS = 300    # Clean expired entries every 5 minutes


# ── State ────────────────────────────────────────────────────────────────────
_request_log: Dict[str, List[float]] = defaultdict(list)
_lock = threading.Lock()
_last_cleanup: float = time.time()


# ── Core Functions ───────────────────────────────────────────────────────────

def _cleanup_expired_entries() -> None:
    """Remove entries older than the window to prevent memory leaks."""
    global _last_cleanup
    now = time.time()

    if now - _last_cleanup < CLEANUP_INTERVAL_SECONDS:
        return

    cutoff = now - DEFAULT_WINDOW_SECONDS
    keys_to_delete = []

    for ip, timestamps in _request_log.items():
        # Remove old timestamps
        _request_log[ip] = [ts for ts in timestamps if ts > cutoff]
        if not _request_log[ip]:
            keys_to_delete.append(ip)

    for key in keys_to_delete:
        del _request_log[key]

    _last_cleanup = now


def check_rate_limit(
    client_ip: str,
    window: int = DEFAULT_WINDOW_SECONDS,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    burst_window: int = BURST_WINDOW_SECONDS,
    burst_max: int = BURST_MAX_REQUESTS,
) -> Tuple[bool, int]:
    """
    Check if a request from the given IP is within rate limits.

    Uses a dual-window approach:
    1. Standard window (60s / 10 req) — sustained rate limit
    2. Burst window (5s / 3 req) — prevents rapid-fire abuse

    Returns:
        (is_allowed: bool, retry_after_seconds: int)
        - If is_allowed is True, retry_after is 0
        - If is_allowed is False, retry_after tells the client when to retry
    """
    now = time.time()

    with _lock:
        _cleanup_expired_entries()

        timestamps = _request_log[client_ip]

        # Prune timestamps outside the main window
        timestamps = [ts for ts in timestamps if ts > now - window]
        _request_log[client_ip] = timestamps

        # Check burst limit (short window)
        burst_count = sum(1 for ts in timestamps if ts > now - burst_window)
        if burst_count >= burst_max:
            oldest_burst = min((ts for ts in timestamps if ts > now - burst_window), default=now)
            retry_after = int(burst_window - (now - oldest_burst)) + 1
            return False, max(retry_after, 1)

        # Check standard rate limit (main window)
        if len(timestamps) >= max_requests:
            oldest_in_window = min(timestamps)
            retry_after = int(window - (now - oldest_in_window)) + 1
            return False, max(retry_after, 1)

        # Request allowed — record it
        timestamps.append(now)
        return True, 0


def reset_rate_limit(client_ip: str) -> None:
    """Reset rate limit for a specific IP (useful for testing)."""
    with _lock:
        if client_ip in _request_log:
            del _request_log[client_ip]


def reset_all() -> None:
    """Reset all rate limit state (useful for testing)."""
    global _last_cleanup
    with _lock:
        _request_log.clear()
        _last_cleanup = time.time()
