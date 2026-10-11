"""Exceções de domínio independentes de frameworks externos."""


class DomainError(Exception):
    """Exceção base do domínio."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class LLMUnavailableError(DomainError):
    """LiteLLM proxy ou provedor indisponível."""
    pass


class LLMTimeoutError(DomainError):
    """Tempo limite esgotado ao aguardar o LLM."""
    pass


class InvalidLLMResponseError(DomainError):
    """Resposta retornada pelo LLM é inválida ou não adere ao contrato."""
    pass


class ContentTooLargeError(DomainError):
    """Conteúdo do log excede o limite configurado."""
    pass
