"""Testes unitários para a Camada Anticorrupção (ACL) do LiteLLM."""
import pytest
from types import SimpleNamespace
from openai import APITimeoutError, APIConnectionError, OpenAIError

from app.adapters.outbound.litellm.prompt_builder import PromptBuilder
from app.adapters.outbound.litellm.response_translator import ResponseTranslator
from app.adapters.outbound.litellm.error_mapper import ErrorMapper
from app.domain.models import BugReport
from app.domain.enums import Complexity, Priority
from app.domain.exceptions import (
    InvalidLLMResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
)


def test_prompt_builder_gera_mensagens_esperadas():
    report = BugReport(
        project_name="pagamentos",
        service="pix-gateway",
        timestamp="2026-10-10T14:00:00Z",
        content="Timeout de conexão com banco de dados",
    )
    messages = PromptBuilder.build_messages(report)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "JSON puro" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "pix-gateway" in messages[1]["content"]


def test_response_translator_json_valido_com_markdown_fence():
    raw_with_fence = """```json
    {
        "complexity": "alta",
        "reasoning": "Parágrafo 1.\\n\\nParágrafo 2.\\n\\nParágrafo 3.",
        "priority": "alta"
    }
    ```"""
    comp, reason, prio = ResponseTranslator.parse_and_validate(raw_with_fence)
    assert comp == Complexity.ALTA
    assert prio == Priority.ALTA
    assert "Parágrafo 1" in reason


def test_response_translator_normaliza_variacoes_sem_acento_e_ingles():
    payload = '{"complexity": "media", "reasoning": "Log moderado", "priority": "high"}'
    comp, reason, prio = ResponseTranslator.parse_and_validate(payload)
    assert comp == Complexity.MEDIA
    assert prio == Priority.ALTA

    payload_low = '{"complexity": "low", "reasoning": "Simples typo", "priority": "baixa"}'
    comp, _, prio = ResponseTranslator.parse_and_validate(payload_low)
    assert comp == Complexity.BAIXA
    assert prio == Priority.BAIXA


def test_response_translator_limita_em_no_maximo_3_paragrafos():
    raw = """{
        "complexity": "baixa",
        "reasoning": "P1\\n\\nP2\\n\\nP3\\n\\nP4\\n\\nP5",
        "priority": "baixa"
    }"""
    _, reason, _ = ResponseTranslator.parse_and_validate(raw)
    paragraphs = reason.split("\n\n")
    assert len(paragraphs) <= 3


def test_response_translator_rejeita_json_invalido():
    with pytest.raises(InvalidLLMResponseError) as exc:
        ResponseTranslator.parse_and_validate("isto não é json")
    assert "Falha ao decodificar" in str(exc.value)


def test_response_translator_rejeita_valores_desconhecidos():
    raw = '{"complexity": "desconhecida", "reasoning": "...", "priority": "alta"}'
    with pytest.raises(InvalidLLMResponseError) as exc:
        ResponseTranslator.parse_and_validate(raw)
    assert "Complexidade 'desconhecida' não reconhecida" in str(exc.value)


def test_response_translator_extrai_token_usage_com_seguranca():
    # Com dados preenchidos
    usage_mock = SimpleNamespace(prompt_tokens=50, completion_tokens=30, total_tokens=80)
    usage = ResponseTranslator.extract_token_usage(usage_mock)
    assert usage.prompt_tokens == 50
    assert usage.completion_tokens == 30
    assert usage.total_tokens == 80

    # Com objeto nulo / None
    none_usage = ResponseTranslator.extract_token_usage(None)
    assert none_usage.prompt_tokens is None
    assert none_usage.completion_tokens is None


def test_error_mapper_converte_excecoes_adequadamente():
    # Timeout
    timeout_exc = APITimeoutError(request=None)
    mapped = ErrorMapper.map_exception(timeout_exc)
    assert isinstance(mapped, LLMTimeoutError)

    # Conexão
    conn_exc = APIConnectionError(request=None)
    mapped_conn = ErrorMapper.map_exception(conn_exc)
    assert isinstance(mapped_conn, LLMUnavailableError)

    # Erro genérico OpenAI
    gen_exc = OpenAIError("Erro geral no proxy")
    mapped_gen = ErrorMapper.map_exception(gen_exc)
    assert isinstance(mapped_gen, LLMUnavailableError)
