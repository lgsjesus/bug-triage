"""Ponto de entrada da aplicação FastAPI (Composition Root)."""
from fastapi import FastAPI
from app.infrastructure.config import settings
from app.infrastructure.container import container
from app.adapters.inbound.http.controllers.triage_controller import router as triage_router
from app.adapters.inbound.http.controllers.health_controller import router as health_router
from app.adapters.inbound.http.middleware import TraceIdMiddleware
from app.adapters.inbound.http.error_handlers import register_error_handlers


def create_app() -> FastAPI:
    """Cria e configura a instância principal da aplicação FastAPI."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API de triagem inteligente de bugs via LiteLLM Proxy em Arquitetura Hexagonal",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Registro de Middlewares (ordem importa: TraceIdMiddleware engloba requisições)
    application.add_middleware(TraceIdMiddleware, logger=container.logger)

    # Registro de Handlers de Erro globais
    register_error_handlers(application)

    # Registro de Rotas
    application.include_router(health_router)
    application.include_router(triage_router)

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
