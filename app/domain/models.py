"""Entidades e Value Objects do domínio."""
from dataclasses import dataclass
from typing import Optional
from app.domain.enums import Complexity, Priority, ModelTier


@dataclass(frozen=True)
class BugReport:
    """Entidade representando um relato de bug/log a ser triado."""
    project_name: str
    service: str
    timestamp: str
    content: str


@dataclass(frozen=True)
class TokenUsage:
    """Métricas de tokens consumidos na chamada do LLM."""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@dataclass(frozen=True)
class LLMCallMetrics:
    """Métricas operacionais da invocação do modelo."""
    requested_model: str
    effective_model: str
    latency_ms: float
    usage: TokenUsage


@dataclass(frozen=True)
class BugClassification:
    """Resultado da categorização de um bug gerada pelo modelo."""
    complexity: Complexity
    reasoning: str
    priority: Priority
    metrics: LLMCallMetrics


@dataclass(frozen=True)
class TriageResult:
    """Resultado final da triagem associado à requisição."""
    trace_id: str
    complexity: Complexity
    reasoning: str
    priority: Priority
    timestamp: str
    metrics: LLMCallMetrics
