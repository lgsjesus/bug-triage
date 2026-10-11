"""Cliente assíncrono para o LiteLLM Proxy."""
import httpx
from openai import AsyncOpenAI
from app.infrastructure.config import settings


class LiteLLMClientProvider:
    """Gerencia instâncias de clientes HTTP e AsyncOpenAI para o LiteLLM Proxy."""

    def __init__(
        self,
        base_url: str = settings.litellm_base_url,
        api_key: str = settings.effective_litellm_api_key,
        timeout: float = settings.llm_timeout_seconds,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._openai_client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )

    def get_openai_client(self) -> AsyncOpenAI:
        return self._openai_client

    async def check_proxy_health(self, timeout: float = settings.llm_health_timeout_seconds) -> bool:
        """Verifica a rota /health/liveliness ou /health do LiteLLM Proxy."""
        health_urls = [
            f"{self.base_url}/health/liveliness",
            f"{self.base_url}/health",
        ]
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient(timeout=timeout) as http_client:
            for url in health_urls:
                try:
                    response = await http_client.get(url, headers=headers)
                    if response.status_code == 200:
                        return True
                except Exception:
                    continue
        return False
