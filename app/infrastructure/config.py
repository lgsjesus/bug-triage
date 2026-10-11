"""Configurações da aplicação utilizando pydantic-settings."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Bug Triage API"
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # LiteLLM Proxy
    litellm_base_url: str = "http://localhost:4000"
    litellm_api_key: str = "sk-proxy-secret-1234"
    litellm_master_key: str = "sk-proxy-secret-1234"

    # Timeouts e retries
    llm_timeout_seconds: float = 30.0
    llm_health_timeout_seconds: float = 5.0
    llm_max_retries: int = 1

    # Limites
    max_content_length: int = 50000

    @property
    def effective_litellm_api_key(self) -> str:
        return self.litellm_api_key or self.litellm_master_key or "sk-proxy-secret-1234"


settings = Settings()
