"""Shared infrastructure: logging, metrics, middleware, circuit breaker."""

from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from .logging import configure_logging, get_logger, get_request_id, set_request_id
from .metrics import (
    Timer,
    get_metrics,
    http_request_duration_seconds,
    http_requests_total,
    llm_requests_total,
    llm_tokens_total,
)

__all__ = [
    "configure_logging",
    "get_logger",
    "get_request_id",
    "set_request_id",
    "Timer",
    "get_metrics",
    "http_request_duration_seconds",
    "http_requests_total",
    "llm_requests_total",
    "llm_tokens_total",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
]
