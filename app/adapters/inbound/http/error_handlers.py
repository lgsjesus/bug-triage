"""Tratadores de exceções globais para mapeamento em respostas HTTP padronizadas."""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

from app.domain.exceptions import (
    ContentTooLargeError,
    InvalidLLMResponseError,
    LLMUnavailableError,
    LLMTimeoutError,
)
from app.infrastructure.logging.context import get_current_trace_id


def register_error_handlers(app: FastAPI) -> None:
    """Registra manipuladores de exceções da aplicação e do domínio."""

    @app.exception_handler(ContentTooLargeError)
    async def content_too_large_handler(request: Request, exc: ContentTooLargeError):
        trace_id = getattr(request.state, "trace_id", get_current_trace_id() or "unknown")
        return JSONResponse(
            status_code=422,
            content={"trace_id": trace_id, "detail": str(exc)},
            headers={"X-Trace-Id": trace_id},
        )

    @app.exception_handler(InvalidLLMResponseError)
    async def invalid_llm_response_handler(request: Request, exc: InvalidLLMResponseError):
        trace_id = getattr(request.state, "trace_id", get_current_trace_id() or "unknown")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"trace_id": trace_id, "detail": f"Resposta inválida do modelo upstream: {exc}"},
            headers={"X-Trace-Id": trace_id},
        )

    @app.exception_handler(LLMUnavailableError)
    async def llm_unavailable_handler(request: Request, exc: LLMUnavailableError):
        trace_id = getattr(request.state, "trace_id", get_current_trace_id() or "unknown")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"trace_id": trace_id, "detail": f"Serviço LiteLLM ou provedor indisponível: {exc}"},
            headers={"X-Trace-Id": trace_id},
        )

    @app.exception_handler(LLMTimeoutError)
    async def llm_timeout_handler(request: Request, exc: LLMTimeoutError):
        trace_id = getattr(request.state, "trace_id", get_current_trace_id() or "unknown")
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"trace_id": trace_id, "detail": f"Tempo limite esgotado ao aguardar resposta do modelo: {exc}"},
            headers={"X-Trace-Id": trace_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        trace_id = getattr(request.state, "trace_id", get_current_trace_id() or "unknown")
        return JSONResponse(
            status_code=422,
            content={
                "trace_id": trace_id,
                "detail": "Erro de validação dos dados enviados.",
                "errors": jsonable_encoder(exc.errors()),
            },
            headers={"X-Trace-Id": trace_id},
        )
