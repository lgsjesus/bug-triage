"""DTOs (Data Transfer Objects) para as APIs HTTP."""
from typing import Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TriageRequest(BaseModel):
    """Schema de requisição para triagem de logs."""
    project_name: str = Field(..., min_length=1, description="Nome do projeto de origem do log")
    service: str = Field(..., min_length=1, description="Nome do microsserviço ou componente")
    timestamp: str = Field(..., min_length=1, description="Data e hora do log em formato ISO 8601")
    content: str = Field(..., min_length=1, description="Conteúdo do log, stack trace ou mensagem")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        """Garante que o timestamp seja compatível com ISO 8601."""
        try:
            # datetime.fromisoformat aceita formatos padrão ISO 8601 (inclusive com timezone ou 'Z')
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception as exc:
            raise ValueError(f"Formato de timestamp inválido. Deve ser ISO 8601: {exc}")
        return v


class TriageResponse(BaseModel):
    """Schema de resposta com a classificação do bug."""
    trace_id: str = Field(..., description="UUID identificador da requisição para rastreabilidade")
    complexity: str = Field(..., description="Complexidade avaliada: alta, média ou baixa")
    reasoning: str = Field(..., description="Justificativa em no máximo 3 parágrafos")
    priority: str = Field(..., description="Prioridade calculada: alta, média ou baixa")
    timestamp: str = Field(..., description="Data e hora ecoada do request")


class HealthResponse(BaseModel):
    """Schema de resposta do health check."""
    status: str = Field(..., description="ok ou degraded")
    dependencies: Dict[str, str] = Field(..., description="Status dos componentes upstream")
    trace_id: str = Field(..., description="UUID da requisição de health check")
    timestamp: str = Field(..., description="Timestamp da verificação")


class ErrorResponse(BaseModel):
    """Schema padronizado para respostas de erro."""
    trace_id: str
    detail: str
