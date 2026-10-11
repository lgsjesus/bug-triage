"""Testes dos endpoints HTTP do FastAPI com TestClient."""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.adapters.inbound.http.dependencies import get_triage_use_case, get_health_use_case
from app.application.services.triage_service import TriageService
from app.application.services.health_service import HealthService
from app.application.services.model_selection_service import ModelSelectionService
from app.domain.enums import Complexity, Priority
from app.domain.exceptions import (
    InvalidLLMResponseError,
    LLMUnavailableError,
    LLMTimeoutError,
)
from tests.conftest import FakeLogger, FakeBugClassifier, FakeLLMHealth


def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def test_health_check_endpoint_retorna_200_quando_saudavel():
    fake_h = FakeLLMHealth(healthy=True)
    fake_l = FakeLogger()
    app.dependency_overrides[get_health_use_case] = lambda: HealthService(fake_h, fake_l)

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["dependencies"]["litellm"] == "up"
    assert is_valid_uuid(data["trace_id"])
    assert response.headers.get("X-Trace-Id") == data["trace_id"]

    app.dependency_overrides.clear()


def test_health_check_endpoint_retorna_503_quando_degradado():
    fake_h = FakeLLMHealth(healthy=False)
    fake_l = FakeLogger()
    app.dependency_overrides[get_health_use_case] = lambda: HealthService(fake_h, fake_l)

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["litellm"] == "down"
    assert is_valid_uuid(data["trace_id"])

    app.dependency_overrides.clear()


def test_triage_endpoint_sucesso_retorna_200_com_trace_id_e_mesmo_timestamp():
    fake_c = FakeBugClassifier(
        complexity=Complexity.MEDIA,
        reasoning="Parágrafo 1 de análise.\\n\\nParágrafo 2 de correção recomendada.",
        priority=Priority.ALTA,
    )
    fake_l = FakeLogger()
    triage_service = TriageService(
        classifier=fake_c,
        logger=fake_l,
        model_selector=ModelSelectionService(),
    )
    app.dependency_overrides[get_triage_use_case] = lambda: triage_service

    client = TestClient(app)
    payload = {
        "project_name": "checkout",
        "service": "payment-api",
        "timestamp": "2026-10-10T15:30:00-03:00",
        "content": "Database pool exhausted on high traffic peak",
    }

    response = client.post("/api/v1/triage", json=payload)

    assert response.status_code == 200
    body = response.json()

    # Validação do trace_id
    assert is_valid_uuid(body["trace_id"])
    assert response.headers["X-Trace-Id"] == body["trace_id"]

    # Validação de retorno das classificações
    assert body["complexity"] == "média"
    assert body["priority"] == "alta"
    assert "Parágrafo 1" in body["reasoning"]

    # Validação do timestamp ecoado
    assert body["timestamp"] == "2026-10-10T15:30:00-03:00"

    app.dependency_overrides.clear()


def test_requisicoes_sucessivas_geram_trace_ids_distintos():
    fake_c = FakeBugClassifier()
    fake_l = FakeLogger()
    app.dependency_overrides[get_triage_use_case] = lambda: TriageService(
        classifier=fake_c, logger=fake_l, model_selector=ModelSelectionService()
    )

    client = TestClient(app)
    payload = {
        "project_name": "auth",
        "service": "login",
        "timestamp": "2026-10-10T10:00:00Z",
        "content": "invalid password count",
    }

    resp1 = client.post("/api/v1/triage", json=payload)
    resp2 = client.post("/api/v1/triage", json=payload)

    trace1 = resp1.json()["trace_id"]
    trace2 = resp2.json()["trace_id"]

    assert trace1 != trace2
    assert is_valid_uuid(trace1)
    assert is_valid_uuid(trace2)

    app.dependency_overrides.clear()


def test_triage_endpoint_valida_campos_obrigatorios_retornando_422():
    client = TestClient(app)
    # Payload vazio
    resp = client.post("/api/v1/triage", json={})
    assert resp.status_code == 422
    assert is_valid_uuid(resp.json()["trace_id"])

    # Timestamp inválido
    invalid_ts = {
        "project_name": "p1",
        "service": "s1",
        "timestamp": "nao-eh-uma-data-valida",
        "content": "erro",
    }
    resp_ts = client.post("/api/v1/triage", json=invalid_ts)
    assert resp_ts.status_code == 422


def test_triage_endpoint_retorna_502_quando_llm_falha():
    fake_c = FakeBugClassifier()
    fake_c.exception_to_raise = InvalidLLMResponseError("JSON mal formatado")
    fake_l = FakeLogger()
    app.dependency_overrides[get_triage_use_case] = lambda: TriageService(
        classifier=fake_c, logger=fake_l, model_selector=ModelSelectionService()
    )

    client = TestClient(app)
    payload = {
        "project_name": "x",
        "service": "y",
        "timestamp": "2026-10-10T10:00:00Z",
        "content": "erro normal",
    }

    response = client.post("/api/v1/triage", json=payload)
    assert response.status_code == 502
    assert is_valid_uuid(response.json()["trace_id"])
    assert "Resposta inválida" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_triage_endpoint_retorna_504_em_timeout():
    fake_c = FakeBugClassifier()
    fake_c.exception_to_raise = LLMTimeoutError("Gateway demorou mais que 30s")
    fake_l = FakeLogger()
    app.dependency_overrides[get_triage_use_case] = lambda: TriageService(
        classifier=fake_c, logger=fake_l, model_selector=ModelSelectionService()
    )

    client = TestClient(app)
    payload = {
        "project_name": "x",
        "service": "y",
        "timestamp": "2026-10-10T10:00:00Z",
        "content": "erro lento",
    }

    response = client.post("/api/v1/triage", json=payload)
    assert response.status_code == 504
    assert is_valid_uuid(response.json()["trace_id"])
    assert "Tempo limite" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_rota_antiga_analyze_bug_removida_retorna_404():
    client = TestClient(app)
    response = client.post("/analyze-bug", json={"title": "bug", "description": "desc"})
    assert response.status_code == 404
