"""RequestIDMiddleware — assigns X-Request-ID to every request and propagates it via ContextVar."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from ..logging import get_logger, set_request_id

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info("request_completed", status_code=response.status_code)
            return response
        except Exception as exc:
            logger.error("request_failed", error=str(exc), exc_info=True)
            raise
