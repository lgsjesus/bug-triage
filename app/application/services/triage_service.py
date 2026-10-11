"""Serviço de aplicação para orquestração da triagem de bugs."""
from app.application.ports.inbound import TriageUseCase
from app.application.ports.outbound import BugClassifierPort, AppLoggerPort
from app.application.services.model_selection_service import ModelSelectionService
from app.domain.models import BugReport, TriageResult
from app.domain.exceptions import ContentTooLargeError


class TriageService(TriageUseCase):
    """Orquestrador do fluxo de triagem."""

    def __init__(
        self,
        classifier: BugClassifierPort,
        logger: AppLoggerPort,
        model_selector: ModelSelectionService,
        max_content_length: int = 50000,
    ):
        self._classifier = classifier
        self._logger = logger
        self._model_selector = model_selector
        self._max_content_length = max_content_length

    async def execute(self, report: BugReport, trace_id: str) -> TriageResult:
        content_len = len(report.content or "")
        if content_len > self._max_content_length:
            self._logger.log_step(
                event="content_length_exceeded",
                trace_id=trace_id,
                payload={
                    "project_name": report.project_name,
                    "service": report.service,
                    "content_length": content_len,
                    "max_allowed": self._max_content_length,
                },
                level="warning",
            )
            raise ContentTooLargeError(
                f"O conteúdo excede o tamanho máximo de {self._max_content_length} caracteres."
            )

        # 1. Auditoria inicial da requisição (nunca grava o conteúdo sensível)
        self._logger.log_step(
            event="request_received",
            trace_id=trace_id,
            payload={
                "project_name": report.project_name,
                "service": report.service,
                "content_length": content_len,
            },
        )

        # 2. Seleção de modelo / tier
        tier, tier_reason = self._model_selector.select_tier(report.content)
        self._logger.log_step(
            event="tier_selected",
            trace_id=trace_id,
            payload={
                "tier": tier.value,
                "reason": tier_reason,
            },
        )

        # 3. Invocação da porta de classificação (camada anticorrupção LiteLLM)
        classification = await self._classifier.classify(report, tier, trace_id)

        # 4. Auditoria de pós-processamento do resultado
        paragraphs = [p for p in classification.reasoning.split("\n\n") if p.strip()]
        self._logger.log_step(
            event="llm_response_parsed",
            trace_id=trace_id,
            payload={
                "complexity": classification.complexity.value,
                "priority": classification.priority.value,
                "paragraphs_count": len(paragraphs),
            },
        )

        return TriageResult(
            trace_id=trace_id,
            complexity=classification.complexity,
            reasoning=classification.reasoning,
            priority=classification.priority,
            timestamp=report.timestamp,
            metrics=classification.metrics,
        )
