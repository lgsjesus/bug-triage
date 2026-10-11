"""Portas de saída (Outbound Ports / Interfaces para adaptadores)."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.domain.models import BugReport, BugClassification
from app.domain.enums import ModelTier


class BugClassifierPort(ABC):
    """Porta para classificação de bug via modelo de IA."""

    @abstractmethod
    async def classify(self, report: BugReport, tier: ModelTier, trace_id: str) -> BugClassification:
        """Envia o bug report para o LLM e retorna a classificação com métricas."""
        pass


class LLMHealthPort(ABC):
    """Porta para verificação de disponibilidade do serviço de LLM / Proxy."""

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Retorna True se o proxy/LLM estiver respondendo adequadamente."""
        pass


class AppLoggerPort(ABC):
    """Porta para registrar passos de execução, modelos, tokens e latências."""

    @abstractmethod
    def log_step(
        self,
        event: str,
        trace_id: str,
        payload: Dict[str, Any],
        level: str = "info",
    ) -> None:
        """Registra um evento estruturado de auditoria / telemetria."""
        pass
