"""Gerenciamento de contexto assíncrono para o trace ID."""
from contextvars import ContextVar

_trace_id_context: ContextVar[str] = ContextVar("trace_id", default="")


def get_current_trace_id() -> str:
    """Retorna o trace ID atual no contexto assíncrono."""
    return _trace_id_context.get()


def set_current_trace_id(trace_id: str) -> None:
    """Define o trace ID no contexto assíncrono."""
    _trace_id_context.set(trace_id)
