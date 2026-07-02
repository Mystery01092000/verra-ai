"""HTTPMetricsMiddleware — records request count + duration per service."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from ..metrics import http_request_duration_seconds, http_requests_total


class HTTPMetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, service: str) -> None:
        super().__init__(app)
        self._service = service

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.time()
        handler = request.url.path
        status = "500"
        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        except Exception:
            raise
        finally:
            elapsed = time.time() - start
            labels = {
                "service": self._service,
                "method": request.method,
                "handler": handler,
                "status": status,
            }
            http_requests_total.labels(**labels).inc()
            http_request_duration_seconds.labels(**labels).observe(elapsed)
