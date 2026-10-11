"""Serviço de integridade do sistema."""
from typing import Dict, Any
from datetime import datetime, timezone
from app.application.ports.inbound import HealthUseCase
from app.application.ports.outbound import LLMHealthPort, AppLoggerPort


class HealthService(HealthUseCase):
    """Verifica saúde da API e status de dependências upstream."""

    def __init__(self, llm_health: LLMHealthPort, logger: AppLoggerPort):
        self._llm_health = llm_health
        self._logger = logger

    async def check_health(self, trace_id: str) -> Dict[str, Any]:
        is_litellm_ok = await self._llm_health.is_healthy()
        status = "ok" if is_litellm_ok else "degraded"
        litellm_status = "up" if is_litellm_ok else "down"

        self._logger.log_step(
            event="health_check_performed",
            trace_id=trace_id,
            payload={
                "status": status,
                "litellm": litellm_status,
            },
            level="info" if is_litellm_ok else "warning",
        )

        return {
            "status": status,
            "dependencies": {
                "litellm": litellm_status,
            },
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
