"""Testes unitários para o TriageService e HealthService."""
import pytest
from app.application.services.triage_service import TriageService
from app.application.services.health_service import HealthService
from app.application.services.model_selection_service import ModelSelectionService
from app.domain.models import BugReport
from app.domain.enums import Complexity, Priority, ModelTier
from app.domain.exceptions import ContentTooLargeError
from tests.conftest import FakeLogger, FakeBugClassifier, FakeLLMHealth


@pytest.mark.asyncio
async def test_triage_service_fluxo_com_sucesso():
    logger = FakeLogger()
    classifier = FakeBugClassifier(
        complexity=Complexity.ALTA,
        reasoning="Parágrafo 1: Falha grave de concorrência.\n\nParágrafo 2: Recomenda-se lock distribuído.",
        priority=Priority.ALTA,
        effective_model="gemini-2.5-flash",
    )
    model_selector = ModelSelectionService()
    service = TriageService(
        classifier=classifier,
        logger=logger,
        model_selector=model_selector,
        max_content_length=1000,
    )

    report = BugReport(
        project_name="checkout",
        service="order-service",
        timestamp="2026-10-10T15:30:00-03:00",
        content="Possível deadlock identificado na transação #4492",
    )

    result = await service.execute(report=report, trace_id="trace-1234")

    assert result.trace_id == "trace-1234"
    assert result.complexity == Complexity.ALTA
    assert result.priority == Priority.ALTA
    assert result.timestamp == "2026-10-10T15:30:00-03:00"
    assert "Falha grave" in result.reasoning

    # Verifica que o classificador foi chamado com o tier HIGH devido ao deadlock
    assert len(classifier.calls) == 1
    assert classifier.calls[0]["tier"] == ModelTier.HIGH

    # Verifica auditoria dos eventos no logger
    event_names = [e["event"] for e in logger.events]
    assert event_names == ["request_received", "tier_selected", "llm_response_parsed"]

    # GARANTIA DE PRIVACIDADE: O conteúdo sensível NUNCA está nos logs, apenas content_length
    for e in logger.events:
        payload = e["payload"]
        assert "content" not in payload
        assert "Possível deadlock identificado" not in str(payload)

    # Verifica detalhes do request_received
    req_event = next(e for e in logger.events if e["event"] == "request_received")
    assert req_event["payload"]["project_name"] == "checkout"
    assert req_event["payload"]["service"] == "order-service"
    assert req_event["payload"]["content_length"] == len(report.content)


@pytest.mark.asyncio
async def test_triage_service_rejeita_conteudo_acima_do_limite():
    logger = FakeLogger()
    classifier = FakeBugClassifier()
    model_selector = ModelSelectionService()
    service = TriageService(
        classifier=classifier,
        logger=logger,
        model_selector=model_selector,
        max_content_length=100,
    )

    report = BugReport(
        project_name="billing",
        service="invoice-job",
        timestamp="2026-10-10T12:00:00Z",
        content="x" * 101,
    )

    with pytest.raises(ContentTooLargeError) as exc_info:
        await service.execute(report=report, trace_id="trace-overflow")

    assert "tamanho máximo" in str(exc_info.value)
    assert len(classifier.calls) == 0

    overflow_event = logger.events[0]
    assert overflow_event["event"] == "content_length_exceeded"
    assert overflow_event["payload"]["content_length"] == 101


@pytest.mark.asyncio
async def test_health_service_retorna_ok_quando_proxy_online():
    logger = FakeLogger()
    health_port = FakeLLMHealth(healthy=True)
    service = HealthService(llm_health=health_port, logger=logger)

    res = await service.check_health("trace-health-1")
    assert res["status"] == "ok"
    assert res["dependencies"]["litellm"] == "up"
    assert res["trace_id"] == "trace-health-1"
    assert "timestamp" in res


@pytest.mark.asyncio
async def test_health_service_retorna_degraded_quando_proxy_offline():
    logger = FakeLogger()
    health_port = FakeLLMHealth(healthy=False)
    service = HealthService(llm_health=health_port, logger=logger)

    res = await service.check_health("trace-health-2")
    assert res["status"] == "degraded"
    assert res["dependencies"]["litellm"] == "down"
    assert res["trace_id"] == "trace-health-2"
