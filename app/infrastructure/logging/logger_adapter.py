"""Adaptador de logging estruturado em formato JSON."""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.application.ports.outbound import AppLoggerPort
from app.infrastructure.logging.context import get_current_trace_id


class StructuredJsonFormatter(logging.Formatter):
    """Formatador que produz linhas em JSON contendo metadados e payload."""

    def format(self, record: logging.LogRecord) -> str:
        record_dict: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", "log_message"),
            "trace_id": getattr(record, "trace_id", get_current_trace_id() or "unknown"),
        }

        # Anexa payload de auditoria se existir
        payload = getattr(record, "payload", None)
        if isinstance(payload, dict):
            record_dict.update(payload)
        elif record.getMessage():
            record_dict["message"] = record.getMessage()

        if record.exc_info:
            record_dict["exception"] = self.formatException(record.exc_info)

        return json.dumps(record_dict, ensure_ascii=False)


class JsonLoggerAdapter(AppLoggerPort):
    """Implementação da porta AppLoggerPort emitindo JSON estruturado."""

    def __init__(self, logger_name: str = "bug_triage"):
        self._logger = logging.getLogger(logger_name)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(StructuredJsonFormatter())
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)
            self._logger.propagate = False

    def log_step(
        self,
        event: str,
        trace_id: str,
        payload: Dict[str, Any],
        level: str = "info",
    ) -> None:
        effective_trace_id = trace_id or get_current_trace_id() or "unknown"
        log_level = getattr(logging, level.upper(), logging.INFO)

        extra = {
            "event": event,
            "trace_id": effective_trace_id,
            "payload": payload,
        }

        self._logger.log(
            log_level,
            f"Event: {event}",
            extra=extra,
        )
