"""Mapeador de erros do SDK/Proxy para exceções puras de domínio."""
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
    OpenAIError,
)
from app.domain.exceptions import LLMUnavailableError, LLMTimeoutError, DomainError


class ErrorMapper:
    """Converte exceções técnicas de fornecedor em exceções de domínio."""

    @staticmethod
    def map_exception(exc: Exception) -> DomainError:
        if isinstance(exc, APITimeoutError):
            return LLMTimeoutError(f"Tempo limite excedido na comunicação com o LLM: {exc}")

        if isinstance(exc, (APIConnectionError, InternalServerError)):
            return LLMUnavailableError(f"Serviço LiteLLM / upstream indisponível ou inacessível: {exc}")

        if isinstance(exc, RateLimitError):
            return LLMUnavailableError(f"Limite de taxa (rate limit) excedido no provedor LLM: {exc}")

        if isinstance(exc, AuthenticationError):
            return LLMUnavailableError(f"Falha de autenticação na API do LiteLLM Proxy: {exc}")

        if isinstance(exc, OpenAIError):
            return LLMUnavailableError(f"Erro na execução da chamada ao LiteLLM: {exc}")

        return LLMUnavailableError(f"Erro inesperado de comunicação com modelo: {exc}")
