"""Serviço de seleção de tier de modelo com base nas características do log."""
from typing import Tuple
from app.domain.enums import ModelTier

CRITICAL_TERMS = (
    "deadlock",
    "memory leak",
    "race condition",
    "segfault",
    "corruption",
)
LONG_LOG_THRESHOLD = 300


class ModelSelectionService:
    """Aplica regras de negócio heurísticas para selecionar o tier de custo ideal."""

    def select_tier(self, content: str) -> Tuple[ModelTier, str]:
        """
        Retorna uma tupla (tier, reason) indicando qual tier utilizar
        e o motivo da seleção.
        """
        text_lower = (content or "").lower()

        for term in CRITICAL_TERMS:
            if term in text_lower:
                return ModelTier.HIGH, f"Termo crítico detectado: '{term}'"

        if len(content or "") > LONG_LOG_THRESHOLD:
            return ModelTier.MEDIUM, f"Log extenso ({len(content)} caracteres > {LONG_LOG_THRESHOLD})"

        return ModelTier.LOW, "Log de tamanho padrão sem termos críticos"
