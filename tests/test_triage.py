"""Testes de integração real com o LiteLLM Proxy em execução."""
import os
import pytest
from app.adapters.outbound.litellm.client import LiteLLMClientProvider
from app.adapters.outbound.litellm.gateway import LiteLLMGateway
from app.infrastructure.logging.logger_adapter import JsonLoggerAdapter
from app.domain.models import BugReport
from app.domain.enums import ModelTier


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="Defina RUN_INTEGRATION=1 e inicie o LiteLLM Proxy")
@pytest.mark.asyncio
async def test_integracao_real_litellm_proxy():
    """Valida chamada real ponta a ponta contra o LiteLLM Proxy."""
    provider = LiteLLMClientProvider()
    logger = JsonLoggerAdapter()
    gateway = LiteLLMGateway(client_provider=provider, logger=logger)

    report = BugReport(
        project_name="e-commerce",
        service="checkout",
        timestamp="2026-10-10T12:00:00Z",
        content="NullPointerException at OrderController.java:42 when processing cart",
    )

    result = await gateway.classify(report=report, tier=ModelTier.LOW, trace_id="integration-test-trace")

    assert result.complexity in ["alta", "média", "baixa"]
    assert result.priority in ["alta", "média", "baixa"]
    assert result.reasoning
    assert result.metrics.effective_model
    assert result.metrics.latency_ms > 0
