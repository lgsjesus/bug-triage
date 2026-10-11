"""Configuração global de fixtures e fakes para pytest."""
import pytest
from typing import List, Dict, Any
from fastapi.testclient import TestClient

from app.main import app
from app.application.ports.outbound import AppLoggerPort, BugClassifierPort, LLMHealthPort
from app.domain.enums import ModelTier, Complexity, Priority
from app.domain.models import BugReport, BugClassification, LLMCallMetrics, TokenUsage


class FakeLogger(AppLoggerPort):
    """Fake de logging que grava eventos em memória para inspeção nos testes."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def log_step(
        self,
        event: str,
        trace_id: str,
        payload: Dict[str, Any],
        level: str = "info",
    ) -> None:
        self.events.append({
            "event": event,
            "trace_id": trace_id,
            "payload": payload,
            "level": level,
        })


class FakeBugClassifier(BugClassifierPort):
    """Fake de classificador LLM controlável."""

    def __init__(
        self,
        complexity: Complexity = Complexity.BAIXA,
        reasoning: str = "Causa identificada com sucesso.\n\nSugestão aplicada.",
        priority: Priority = Priority.BAIXA,
        effective_model: str = "gemini-2.5-flash-lite",
        latency_ms: float = 120.5,
        tokens: TokenUsage = TokenUsage(prompt_tokens=40, completion_tokens=25, total_tokens=65),
    ):
        self.complexity = complexity
        self.reasoning = reasoning
        self.priority = priority
        self.effective_model = effective_model
        self.latency_ms = latency_ms
        self.tokens = tokens
        self.calls: List[Dict[str, Any]] = []
        self.exception_to_raise: Exception = None

    async def classify(self, report: BugReport, tier: ModelTier, trace_id: str) -> BugClassification:
        self.calls.append({"report": report, "tier": tier, "trace_id": trace_id})
        if self.exception_to_raise:
            raise self.exception_to_raise

        return BugClassification(
            complexity=self.complexity,
            reasoning=self.reasoning,
            priority=self.priority,
            metrics=LLMCallMetrics(
                requested_model=tier.value,
                effective_model=self.effective_model,
                latency_ms=self.latency_ms,
                usage=self.tokens,
            ),
        )


class FakeLLMHealth(LLMHealthPort):
    """Fake para simulação de integridade do LiteLLM Proxy."""

    def __init__(self, healthy: bool = True):
        self.healthy = healthy

    async def is_healthy(self) -> bool:
        return self.healthy


@pytest.fixture
def fake_logger() -> FakeLogger:
    return FakeLogger()


@pytest.fixture
def fake_classifier() -> FakeBugClassifier:
    return FakeBugClassifier()


@pytest.fixture
def fake_health() -> FakeLLMHealth:
    return FakeLLMHealth()


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)
