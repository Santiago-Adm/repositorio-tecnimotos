"""
Punto de entrada FastAPI — api-server (03 §4.1).
CorrelationMiddleware establece request_id antes de call_next (02 §1.6).
DatabaseSessionMiddleware: crea AsyncSession por request → repos PG activos cuando la BD existe.
"""
from __future__ import annotations

import asyncio
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.dependencies import error_response, success_response
from api.middleware.database_session import DatabaseSessionMiddleware
from api.middleware.metrics_collector import MetricsCollectorMiddleware
from api.middleware.rate_limiter import RateLimiterMiddleware
from api.routes import admin as admin_router
from api.routes import auth_routes as auth_router
from api.routes import catalogo as catalogo_router
from api.routes import metrics as metrics_router
from api.routes import pedidos as pedidos_router
from api.routes import privacidad as privacidad_router
from api.routes import soporte as soporte_router
from api.routes import stock as stock_router
from api.routes import taller as taller_router
from api.routes import usuarios as usuarios_router
from src.catalogo.infrastructure.repositories.repuesto_repository_inmemory import (
    InMemoryRepuestoRepository,
)
from src.stock.infrastructure.repositories.stock_repository_inmemory import (
    InMemoryStockRepository,
)
from src.pedidos.infrastructure.repositories.pedido_repository_inmemory import (
    InMemoryPedidoRepository,
)
from src.pedidos.infrastructure.adapters.catalogo_adapter import (
    InMemoryCatalogoAdapter,
    InMemoryStockAdapter,
)
from src.taller.infrastructure.repositories.taller_repository_inmemory import (
    InMemoryTallerRepository,
)
from src.taller.infrastructure.adapters.catalogo_taller_adapter import (
    InMemoryCatalogoTallerAdapter,
)
from api.auth_stores import InMemorySessionStore, InMemoryUserStore
from src.shared.events.event_bus import InMemoryEventBus
from src.shared.infrastructure.logging import configure_logging, request_id_var
from src.shared.infrastructure.parametros_adapters import InMemoryParametrosService
from src.shared.infrastructure.repositories.reporte_soporte_repository_inmemory import (
    InMemoryReporteSoporteRepository,
)
from src.catalogo.infrastructure.repositories.imagen_repuesto_repository_inmemory import (
    InMemoryImagenRepuestoRepository,
)
from src.catalogo.infrastructure.storage.inmemory_imagen_storage import InMemoryImagenStorage
from src.catalogo.infrastructure.storage.r2_imagen_storage import R2ImagenStorage
from src.shared.infrastructure.settings import get_settings
from src.pedidos.application.use_cases.gestionar_plan_mantenimiento import (
    ProcesarRecordatoriosMantenimientoUseCase,
)

settings = get_settings()
configure_logging(
    service="catalogo",
    version=settings.api_version,
    environment=settings.environment,
)

logger = logging.getLogger(__name__)


async def _job_recordatorios_mantenimiento(app: FastAPI) -> None:
    """Ciclo de 24 horas: procesa planes de mantenimiento con 30+ días sin recordatorio."""
    _INTERVALO_HORAS = 24
    while True:
        await asyncio.sleep(_INTERVALO_HORAS * 3600)
        try:
            repo = app.state.pedidos_repo
            uc = ProcesarRecordatoriosMantenimientoUseCase(repo)
            procesados = await uc.execute()
            if procesados:
                logger.info("Job recordatorios: %d planes notificados", len(procesados))
        except Exception as exc:
            logger.error("Job recordatorios mantenimiento falló: %s", exc)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Intenta conectar a PostgreSQL al arranque; si falla, usa InMemory."""
    from sqlalchemy import text
    from src.shared.infrastructure.database import create_engine, create_session_factory

    try:
        engine = create_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        app.state.db_session_factory = create_session_factory(engine)
        app.state._pg_engine = engine
        logger.info("PostgreSQL conectado — repos PG activos")
    except Exception as exc:
        app.state.db_session_factory = None
        app.state._pg_engine = None
        logger.info("PostgreSQL no disponible (%s) — repos InMemory", exc)

    task = asyncio.create_task(_job_recordatorios_mantenimiento(app))

    yield

    task.cancel()
    engine = getattr(app.state, "_pg_engine", None)
    if engine is not None:
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Tecnimotos API",
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=_lifespan,
    )

    # Middleware order: outer → inner.
    # DatabaseSession crea la sesión PG por request (si BD disponible).
    # MetricsCollector registra DESPUÉS de rate limit.
    app.add_middleware(MetricsCollectorMiddleware)
    app.add_middleware(RateLimiterMiddleware)
    app.add_middleware(DatabaseSessionMiddleware)

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
    app.state.imagen_repuesto_repo = InMemoryImagenRepuestoRepository()
    if settings.r2_endpoint:
        _r2_kwargs = dict(
            endpoint_url=settings.r2_endpoint,
            access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key,
            bucket_name=settings.r2_bucket_name,
            public_url=settings.r2_public_url,
        )
        app.state.imagen_storage = R2ImagenStorage(**_r2_kwargs, prefix="repuestos")
        app.state.documento_storage = R2ImagenStorage(**_r2_kwargs, prefix="documentos")
        logger.info("imagen_storage / documento_storage → R2 (bucket=%s)", settings.r2_bucket_name)
    else:
        app.state.imagen_storage = InMemoryImagenStorage()
        app.state.documento_storage = InMemoryImagenStorage()
        logger.info("imagen_storage / documento_storage → InMemory (R2_ENDPOINT no configurado)")
    app.state.stock_repo = InMemoryStockRepository()
    app.state.pedidos_repo = InMemoryPedidoRepository()
    app.state.catalogo_adapter = InMemoryCatalogoAdapter()
    app.state.stock_adapter = InMemoryStockAdapter()
    app.state.taller_repo = InMemoryTallerRepository()
    app.state.catalogo_taller_adapter = InMemoryCatalogoTallerAdapter()
    app.state.event_bus = InMemoryEventBus()
    app.state.user_store = InMemoryUserStore()
    app.state.session_store = InMemorySessionStore()
    app.state.parametros_service = InMemoryParametrosService()
    app.state.soporte_repo = InMemoryReporteSoporteRepository()

    # Clave de bootstrap SUPERADMIN — vacío si no está configurada (EP-AUTH-06)
    app.state.superadmin_bootstrap_key = settings.superadmin_bootstrap_key

    # Claves JWT RS256 — None si los archivos no existen (tests usan app.state directo)
    try:
        with open(settings.jwt_public_key_path) as _f:
            app.state.jwt_public_key = _f.read()
    except (FileNotFoundError, OSError):
        app.state.jwt_public_key = None
        logger.warning("jwt_public_key_path '%s' no encontrado — auth desactivado", settings.jwt_public_key_path)
    try:
        with open(settings.jwt_private_key_path) as _f:
            app.state.jwt_private_key = _f.read()
    except (FileNotFoundError, OSError):
        app.state.jwt_private_key = None

    # Routers
    app.include_router(auth_router.router)
    app.include_router(admin_router.router)
    app.include_router(catalogo_router.router)
    app.include_router(stock_router.router)
    app.include_router(pedidos_router.router)
    app.include_router(taller_router.router)
    app.include_router(metrics_router.router)
    app.include_router(privacidad_router.router)
    app.include_router(soporte_router.router)
    app.include_router(usuarios_router.router)

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
