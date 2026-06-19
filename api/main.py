"""
Punto de entrada FastAPI — api-server (03 §4.1).
CorrelationMiddleware establece request_id antes de call_next (02 §1.6).
"""
from __future__ import annotations

import uuid
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.dependencies import error_response, success_response
from api.routes import catalogo as catalogo_router
from src.catalogo.infrastructure.repositories.repuesto_repository_inmemory import (
    InMemoryRepuestoRepository,
)
from src.shared.events.event_bus import InMemoryEventBus
from src.shared.infrastructure.logging import configure_logging, request_id_var
from src.shared.infrastructure.settings import get_settings

settings = get_settings()
configure_logging(
    service="catalogo",
    version=settings.api_version,
    environment=settings.environment,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Tecnimotos API",
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CorrelationMiddleware — establece request_id ANTES de call_next (02 §1.6)
    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_var.set(rid)
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        request_id_var.reset(token)
        return response

    # Estado de la aplicación — repositorios y bus de eventos
    app.state.catalogo_repo = InMemoryRepuestoRepository()
    app.state.event_bus = InMemoryEventBus()

    # Routers
    app.include_router(catalogo_router.router)

    @app.get("/v1/health", tags=["health"])
    async def health(request: Request):
        return success_response(
            {"estado": "ok", "version": settings.api_version},
            request_id=request.state.request_id,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Error no manejado", extra={"error": str(exc)}, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=error_response(
                "ERROR_INTERNO",
                "Error interno del servidor",
                request_id=getattr(request.state, "request_id", ""),
            ),
        )

    return app


app = create_app()
