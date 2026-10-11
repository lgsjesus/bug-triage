"""Middleware ASGI para geração de trace ID e telemetria HTTP."""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.logging.context import set_current_trace_id
from app.application.ports.outbound import AppLoggerPort


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Gera um UUID4 exclusivo por requisição e injeta nos cabeçalhos e contexto."""

    def __init__(self, app, logger: AppLoggerPort):
        super().__init__(app)
        self._logger = logger

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        set_current_trace_id(trace_id)

        start_time = time.perf_counter()

        response = await call_next(request)

        total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Trace-Id"] = trace_id

        # Auditoria de conclusão da requisição
        self._logger.log_step(
            event="request_completed",
            trace_id=trace_id,
            payload={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": total_latency_ms,
            },
        )

        return response
