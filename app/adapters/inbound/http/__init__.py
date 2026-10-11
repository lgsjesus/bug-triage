"""Adaptadores Inbound HTTP."""
from app.adapters.inbound.http.controllers.triage_controller import router as triage_router
from app.adapters.inbound.http.controllers.health_controller import router as health_router
from app.adapters.inbound.http.middleware import TraceIdMiddleware
from app.adapters.inbound.http.error_handlers import register_error_handlers

__all__ = [
    "triage_router",
    "health_router",
    "TraceIdMiddleware",
    "register_error_handlers",
]
