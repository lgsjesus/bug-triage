"""Provedores de dependências (Depends) para endpoints do FastAPI."""
from fastapi import Request
from app.application.ports.inbound import TriageUseCase, HealthUseCase
from app.infrastructure.container import container


def get_triage_use_case() -> TriageUseCase:
    """Fornece a instância do caso de uso de triagem."""
    return container.triage_service


def get_health_use_case() -> HealthUseCase:
    """Fornece a instância do caso de uso de verificação de saúde."""
    return container.health_service


def get_request_trace_id(request: Request) -> str:
    """Extrai o trace_id gerado pelo middleware para a requisição atual."""
    return getattr(request.state, "trace_id", "unknown")
