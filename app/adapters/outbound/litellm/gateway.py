"""Gateway LiteLLM que implementa as portas de saída BugClassifierPort e LLMHealthPort."""
import time
from typing import Optional
from app.application.ports.outbound import BugClassifierPort, LLMHealthPort, AppLoggerPort
from app.domain.enums import ModelTier
from app.domain.models import BugReport, BugClassification, LLMCallMetrics
from app.domain.exceptions import InvalidLLMResponseError, DomainError
from app.adapters.outbound.litellm.client import LiteLLMClientProvider
from app.adapters.outbound.litellm.prompt_builder import PromptBuilder
from app.adapters.outbound.litellm.response_translator import ResponseTranslator
from app.adapters.outbound.litellm.error_mapper import ErrorMapper


class LiteLLMGateway(BugClassifierPort, LLMHealthPort):
    """Adaptador de saída anticorrupção para integração com o LiteLLM."""

    def __init__(
        self,
        client_provider: LiteLLMClientProvider,
        logger: AppLoggerPort,
        max_retries: int = 1,
    ):
        self._client_provider = client_provider
        self._logger = logger
        self._max_retries = max_retries

    async def is_healthy(self) -> bool:
        """Verifica a conectividade com o proxy upstream."""
        return await self._client_provider.check_proxy_health()

    async def classify(self, report: BugReport, tier: ModelTier, trace_id: str) -> BugClassification:
        client = self._client_provider.get_openai_client()
        messages = PromptBuilder.build_messages(report)
        model_name = tier.value

        attempts = 0
        max_attempts = 1 + self._max_retries
        last_exception: Optional[Exception] = None

        while attempts < max_attempts:
            attempts += 1
            start_time = time.perf_counter()

            self._logger.log_step(
                event="llm_call_started",
                trace_id=trace_id,
                payload={
                    "requested_model": model_name,
                    "attempt": attempts,
                    "max_attempts": max_attempts,
                },
            )

            try:
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    response_format={"type": "json_object"},
                )

                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                raw_content = response.choices[0].message.content or ""
                effective_model = response.model or model_name
                token_usage = ResponseTranslator.extract_token_usage(response.usage)

                # Parsing e validação da resposta
                complexity, reasoning, priority = ResponseTranslator.parse_and_validate(raw_content)

                metrics = LLMCallMetrics(
                    requested_model=model_name,
                    effective_model=effective_model,
                    latency_ms=latency_ms,
                    usage=token_usage,
                )

                # Registro de telemetria completa da chamada
                self._logger.log_step(
                    event="llm_call_completed",
                    trace_id=trace_id,
                    payload={
                        "requested_model": model_name,
                        "effective_model": effective_model,
                        "latency_ms": latency_ms,
                        "prompt_tokens": token_usage.prompt_tokens,
                        "completion_tokens": token_usage.completion_tokens,
                        "total_tokens": token_usage.total_tokens,
                        "attempt": attempts,
                    },
                )

                return BugClassification(
                    complexity=complexity,
                    reasoning=reasoning,
                    priority=priority,
                    metrics=metrics,
                )

            except InvalidLLMResponseError as exc:
                last_exception = exc
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                if attempts < max_attempts:
                    self._logger.log_step(
                        event="llm_retry",
                        trace_id=trace_id,
                        payload={
                            "reason": "invalid_response",
                            "attempt": attempts,
                            "error": str(exc),
                            "latency_ms": latency_ms,
                        },
                        level="warning",
                    )
                    continue

                self._logger.log_step(
                    event="llm_call_failed",
                    trace_id=trace_id,
                    payload={
                        "error_type": "InvalidLLMResponseError",
                        "error": str(exc),
                        "latency_ms": latency_ms,
                    },
                    level="error",
                )
                raise exc

            except Exception as exc:
                mapped_error = ErrorMapper.map_exception(exc)
                last_exception = mapped_error
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

                self._logger.log_step(
                    event="llm_call_failed",
                    trace_id=trace_id,
                    payload={
                        "error_type": mapped_error.__class__.__name__,
                        "error": str(mapped_error),
                        "latency_ms": latency_ms,
                        "attempt": attempts,
                    },
                    level="error",
                )

                if attempts < max_attempts:
                    self._logger.log_step(
                        event="llm_retry",
                        trace_id=trace_id,
                        payload={
                            "reason": "upstream_error",
                            "attempt": attempts,
                            "error": str(mapped_error),
                        },
                        level="warning",
                    )
                    continue

                raise mapped_error from exc

        if last_exception:
            if isinstance(last_exception, DomainError):
                raise last_exception
            raise ErrorMapper.map_exception(last_exception)

        raise InvalidLLMResponseError("Falha desconhecida na comunicação com o LLM.")
