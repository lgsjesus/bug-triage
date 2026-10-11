"""Container simples de injeção de dependências para composição do sistema."""
from app.infrastructure.config import settings
from app.infrastructure.logging.logger_adapter import JsonLoggerAdapter
from app.adapters.outbound.litellm.client import LiteLLMClientProvider
from app.adapters.outbound.litellm.gateway import LiteLLMGateway
from app.application.services.model_selection_service import ModelSelectionService
from app.application.services.triage_service import TriageService
from app.application.services.health_service import HealthService
from app.application.ports.inbound import TriageUseCase, HealthUseCase
from app.application.ports.outbound import AppLoggerPort


class AppContainer:
    """Contém as instâncias singleton e fábricas de serviços do sistema."""

    def __init__(self):
        self.logger: AppLoggerPort = JsonLoggerAdapter()
        self.client_provider = LiteLLMClientProvider(
            base_url=settings.litellm_base_url,
            api_key=settings.effective_litellm_api_key,
            timeout=settings.llm_timeout_seconds,
        )
        self.gateway = LiteLLMGateway(
            client_provider=self.client_provider,
            logger=self.logger,
            max_retries=settings.llm_max_retries,
        )
        self.model_selector = ModelSelectionService()
        self.triage_service: TriageUseCase = TriageService(
            classifier=self.gateway,
            logger=self.logger,
            model_selector=self.model_selector,
            max_content_length=settings.max_content_length,
        )
        self.health_service: HealthUseCase = HealthService(
            llm_health=self.gateway,
            logger=self.logger,
        )


container = AppContainer()
