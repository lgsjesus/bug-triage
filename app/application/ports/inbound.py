"""Portas de entrada (Inbound Ports / Use Cases)."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.domain.models import BugReport, TriageResult


class TriageUseCase(ABC):
    """Caso de uso de triagem e categorização de bugs."""

    @abstractmethod
    async def execute(self, report: BugReport, trace_id: str) -> TriageResult:
        """Executa o processo de triagem para o bug report fornecido."""
        pass


class HealthUseCase(ABC):
    """Caso de uso para verificação de integridade da aplicação."""

    @abstractmethod
    async def check_health(self, trace_id: str) -> Dict[str, Any]:
        """Verifica a saúde da aplicação e de suas dependências externas."""
        pass
