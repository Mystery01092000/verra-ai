"""Redis-backed distributed circuit breaker (CLOSED → OPEN → HALF_OPEN → CLOSED).

Prevents cascade failures when a downstream service repeatedly fails.
State is stored in Redis so all replicas share the same view.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any

from .logging import get_logger

logger = get_logger(__name__)


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit is OPEN and callers should fail fast."""


class CircuitBreaker:
    """Distributed circuit breaker backed by Redis.

    Args:
        service_name:       Name of the owning service (for key namespacing).
        dependency_name:    Name of the downstream dependency being protected.
        redis_url:          Redis connection URL.
        failure_threshold:  Consecutive failures before opening.
        timeout_seconds:    Seconds to wait before attempting HALF_OPEN.
        success_threshold:  Successes in HALF_OPEN before closing.
    """

    def __init__(
        self,
        service_name: str,
        dependency_name: str,
        redis_url: str = "redis://redis:6379",
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2,
    ) -> None:
        self.service_name = service_name
        self.dependency_name = dependency_name
        self.failure_threshold = failure_threshold
        self.timeout = timeout_seconds
        self.success_threshold = success_threshold
        self._redis_url = redis_url

        ns = f"cb:{service_name}:{dependency_name}"
        self._state_key = f"{ns}:state"
        self._fail_key = f"{ns}:failures"
        self._success_key = f"{ns}:successes"
        self._opened_key = f"{ns}:opened_at"

    def _redis(self) -> Any:
        import redis as _redis

        return _redis.from_url(self._redis_url, decode_responses=True)

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute *func* through the circuit breaker.

        Raises CircuitBreakerOpenError when OPEN and the timeout has not elapsed.
        Fails open (executes *func* without breaker accounting) when Redis is
        unreachable — losing breaker state must never take the caller down.
        """
        import redis as _redis_mod

        try:
            r = self._redis()
            state = CircuitState(r.get(self._state_key) or CircuitState.CLOSED)
        except (_redis_mod.RedisError, OSError) as exc:
            logger.warning(
                "circuit_breaker_redis_unavailable",
                service=self.service_name,
                dependency=self.dependency_name,
                error=str(exc),
            )
            return func(*args, **kwargs)

        if state == CircuitState.OPEN:
            opened_str: str | None = r.get(self._opened_key)
            if opened_str:
                elapsed = (datetime.utcnow() - datetime.fromisoformat(opened_str)).total_seconds()
                if elapsed >= self.timeout:
                    self._transition(r, CircuitState.OPEN, CircuitState.HALF_OPEN)
                    r.set(self._success_key, 0)
                    state = CircuitState.HALF_OPEN
            if state == CircuitState.OPEN:
                logger.warning(
                    "circuit_open_blocked",
                    service=self.service_name,
                    dependency=self.dependency_name,
                )
                raise CircuitBreakerOpenError(
                    f"Circuit open for {self.service_name}→{self.dependency_name}"
                )

        try:
            result = func(*args, **kwargs)
            self._record(self._on_success, r, state)
            return result
        except Exception:
            self._record(self._on_failure, r, state)
            raise

    def _record(
        self, hook: Callable[[Any, CircuitState], None], r: Any, state: CircuitState
    ) -> None:
        """Run a breaker-accounting hook, tolerating Redis loss mid-call."""
        import redis as _redis_mod

        try:
            hook(r, state)
        except (_redis_mod.RedisError, OSError) as exc:
            logger.warning(
                "circuit_breaker_accounting_skipped",
                service=self.service_name,
                dependency=self.dependency_name,
                error=str(exc),
            )

    def _on_success(self, r: Any, state: CircuitState) -> None:
        if state == CircuitState.HALF_OPEN:
            successes = int(r.incr(self._success_key))
            if successes >= self.success_threshold:
                self._transition(r, CircuitState.HALF_OPEN, CircuitState.CLOSED)
                r.set(self._fail_key, 0)
                r.delete(self._opened_key)
        elif state == CircuitState.CLOSED:
            r.set(self._fail_key, 0)

    def _on_failure(self, r: Any, state: CircuitState) -> None:
        if state == CircuitState.HALF_OPEN:
            self._transition(r, CircuitState.HALF_OPEN, CircuitState.OPEN)
            r.set(self._opened_key, datetime.utcnow().isoformat())
        elif state == CircuitState.CLOSED:
            failures = int(r.incr(self._fail_key))
            if failures >= self.failure_threshold:
                self._transition(r, CircuitState.CLOSED, CircuitState.OPEN)
                r.set(self._opened_key, datetime.utcnow().isoformat())
                r.set(self._success_key, 0)
                logger.error(
                    "circuit_opened",
                    service=self.service_name,
                    dependency=self.dependency_name,
                    failures=failures,
                )

    def _transition(self, r: Any, from_state: CircuitState, to_state: CircuitState) -> None:
        r.set(self._state_key, to_state.value)
        logger.info(
            "circuit_state_change",
            service=self.service_name,
            dependency=self.dependency_name,
            from_state=from_state,
            to_state=to_state,
        )
