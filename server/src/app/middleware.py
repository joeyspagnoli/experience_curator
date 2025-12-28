import logging
import time
import uuid
from typing import Optional

logger = logging.getLogger("app")


def _get_incoming_trace_id(scope: dict, header_name_bytes: bytes) -> Optional[str]:
    """Extract a trace id header value from the incoming ASGI scope."""
    headers = scope.get("headers") or []
    for name, value in headers:
        if name.lower() == header_name_bytes:
            try:
                return value.decode("latin-1")
            except Exception:
                return None
    return None


class TraceMiddleware:
    """Attach a trace id to each request and log timing and status."""
    def __init__(self, app, header_name: str = "x-trace-id") -> None:
        """Initialize middleware with a configurable trace header name."""
        self.app = app
        self.header_name = header_name
        self.header_name_bytes = header_name.encode("latin-1")

    async def __call__(self, scope: dict, receive, send) -> None:
        """Wrap request handling to inject trace id and structured logs."""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        trace_id = _get_incoming_trace_id(scope, self.header_name_bytes)
        if not trace_id:
            trace_id = uuid.uuid4().hex

        scope["trace_id"] = trace_id

        start_time = time.perf_counter()
        method = scope.get("method")
        path = scope.get("path")
        logger.info(
            "request.start trace_id=%s, method=%s, path=%s",
            trace_id,
            method,
            path,
        )

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self.header_name_bytes, trace_id.encode("latin-1")))
                message["headers"] = headers

                duration_ms = (time.perf_counter() - start_time) * 1000
                status_code = message.get("status")
                logger.info(
                    "request.end trace_id=%s, status_code=%s, duration_ms=%.2f",
                    trace_id,
                    status_code,
                    duration_ms,
                )

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            logger.exception("request.exception trace_id=%s", trace_id)
            raise
