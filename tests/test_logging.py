"""Testes unitários para o serviço de logging estruturado."""
import json
import logging
from app.infrastructure.logging.logger_adapter import StructuredJsonFormatter, JsonLoggerAdapter
from app.infrastructure.logging.context import set_current_trace_id


def test_structured_json_formatter_produz_json_valido():
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Teste de mensagem",
        args=(),
        exc_info=None,
    )
    record.event = "llm_call_completed"
    record.trace_id = "trace-uuid-777"
    record.payload = {
        "requested_model": "tier-high",
        "effective_model": "gemini-2.5-flash",
        "latency_ms": 350.2,
        "prompt_tokens": 120,
        "completion_tokens": 45,
        "total_tokens": 165,
    }

    formatted_str = formatter.format(record)
    parsed = json.loads(formatted_str)

    assert parsed["event"] == "llm_call_completed"
    assert parsed["trace_id"] == "trace-uuid-777"
    assert parsed["level"] == "INFO"
    assert parsed["requested_model"] == "tier-high"
    assert parsed["effective_model"] == "gemini-2.5-flash"
    assert parsed["latency_ms"] == 350.2
    assert parsed["total_tokens"] == 165
    assert "timestamp" in parsed


def test_logger_adapter_utiliza_trace_id_do_contexto(monkeypatch):
    adapter = JsonLoggerAdapter("test_context_logger")
    set_current_trace_id("context-trace-abc")

    captured_logs = []

    def mock_log(level, msg, extra=None):
        captured_logs.append(extra)

    monkeypatch.setattr(adapter._logger, "log", mock_log)

    adapter.log_step(
        event="step_x",
        trace_id="",  # Vazio, deve usar do contextvar
        payload={"chave": "valor"},
    )

    assert len(captured_logs) == 1
    assert captured_logs[0]["trace_id"] == "context-trace-abc"
    assert captured_logs[0]["event"] == "step_x"
