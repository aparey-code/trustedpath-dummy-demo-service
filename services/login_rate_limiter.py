"""In-memory rate limiter for login attempts, keyed by client IP."""

import threading
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class _IPState:
    """Mutable state for a single IP address."""

    __slots__ = ("failures", "window_start")

    def __init__(self) -> None:
        self.failures: int = 0
        self.window_start: datetime = datetime.now(timezone.utc)


class LoginRateLimiter:
    """Track failed login attempts per IP and enforce a sliding-window limit.

    Thread-safe for multi-threaded WSGI/ASGI servers. Not shared across
    multiple processes; for multi-process deployments, back this with Redis
    or a shared store instead.

    Args:
        max_failures: Maximum allowed failures before the IP is blocked.
        window_seconds: Length of the sliding window in seconds.
    """

    def __init__(self, max_failures: int = 5, window_seconds: int = 600) -> None:
        self._max_failures = max_failures
        self._window = timedelta(seconds=window_seconds)
        self._state: dict[str, _IPState] = defaultdict(_IPState)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def is_limited(self, ip: str) -> bool:
        """Return True if the IP has exceeded the failure threshold."""
        with self._lock:
            state = self._state[ip]
            self._maybe_reset(state)
            return state.failures >= self._max_failures

    def record_failure(self, ip: str) -> None:
        """Increment the failure counter for an IP after a bad login."""
        with self._lock:
            state = self._state[ip]
            self._maybe_reset(state)
            state.failures += 1
            logger.warning(
                "Failed login from %s — attempt %d/%d in current window",
                ip,
                state.failures,
                self._max_failures,
            )

    def reset(self, ip: str) -> None:
        """Clear the failure counter for an IP after a successful login."""
        with self._lock:
            if ip in self._state:
                self._state[ip].failures = 0
                self._state[ip].window_start = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _maybe_reset(self, state: _IPState) -> None:
        """Reset the window if it has expired. Must be called under the lock."""
        now = datetime.now(timezone.utc)
        if now - state.window_start >= self._window:
            state.failures = 0
            state.window_start = now


# Module-level singleton used by the login handler.
# Override by replacing this reference in tests or with a DI container.
login_rate_limiter: LoginRateLimiter | None = None


def get_login_rate_limiter() -> LoginRateLimiter:
    """Return (and lazily create) the module-level LoginRateLimiter.

    The limiter is configured from application settings on first call so
    that environment variables are honoured at runtime rather than import
    time.
    """
    global login_rate_limiter  # noqa: PLW0603
    if login_rate_limiter is None:
        from conf.settings import LOGIN_MAX_FAILURES, LOGIN_WINDOW_SECS

        login_rate_limiter = LoginRateLimiter(
            max_failures=LOGIN_MAX_FAILURES,
            window_seconds=LOGIN_WINDOW_SECS,
        )
    return login_rate_limiter
