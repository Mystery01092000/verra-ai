"""Prometheus metrics shared across all Verra services."""

from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Histogram

# ── HTTP ─────────────────────────────────────────────────────────────────────

http_requests_total = Counter(
    "verra_http_requests_total",
    "Total HTTP requests",
    ["service", "method", "handler", "status"],
)

http_request_duration_seconds = Histogram(
    "verra_http_request_duration_seconds",
    "HTTP request duration",
    ["service", "method", "handler", "status"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ── LLM ──────────────────────────────────────────────────────────────────────

llm_requests_total = Counter(
    "verra_llm_requests_total",
    "Total LLM requests",
    ["service", "provider", "status"],
)

llm_tokens_total = Counter(
    "verra_llm_tokens_total",
    "Total LLM tokens consumed",
    ["service", "provider", "token_type"],
)

# ── Circuit Breaker ───────────────────────────────────────────────────────────

circuit_breaker_calls_total = Counter(
    "verra_circuit_breaker_calls_total",
    "Circuit breaker call attempts",
    ["service", "dependency", "state", "allowed"],
)

circuit_breaker_state_changes_total = Counter(
    "verra_circuit_breaker_state_changes_total",
    "Circuit breaker state transitions",
    ["service", "dependency", "from_state", "to_state"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────


class Timer:
    """Context manager that records elapsed time to a Prometheus histogram observer."""

    def __init__(self, metric_observer: Any = None) -> None:
        self.metric_observer = metric_observer
        self.start_time: float | None = None
        self.end_time: float | None = None

    def __enter__(self) -> Timer:
        self.start_time = time.time()
        return self

    def __exit__(self, *_: Any) -> None:
        self.end_time = time.time()
        if self.start_time is not None and self.metric_observer is not None:
            self.metric_observer.observe(self.end_time - self.start_time)

    @property
    def elapsed(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time


def get_metrics() -> tuple[bytes, str]:
    """Aggregate Prometheus metrics from all processes and return (content, content_type)."""
    from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest
    from prometheus_client.multiprocess import MultiProcessCollector

    agg = CollectorRegistry()
    MultiProcessCollector(agg)  # type: ignore[no-untyped-call]
    return generate_latest(agg), CONTENT_TYPE_LATEST


def prepare_multiproc_dir(path: str) -> None:
    """Create the prometheus multiprocess dir and clear stale per-process files.

    Synchronous by design: called once at service startup before serving traffic.
    """
    from pathlib import Path

    d = Path(path)
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.db"):
        f.unlink(missing_ok=True)
