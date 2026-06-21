"""
Rate limiting por IP — ventana deslizante 60 seg (08 §8.1 Seguridad).
/v1/auth/*: 20 req/min · resto: 60 req/min.
Para producción horizontal: reemplazar _counters por Redis.
07 §2.5: bloqueo 15 min por 10 intentos fallidos de login — gestionado en auth_stores.
"""
from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_GLOBAL_LIMIT = 60
_AUTH_LIMIT = 20
_WINDOW = 60  # segundos
_SKIP_PATHS = {"/v1/health", "/v1/metrics", "/v1/privacidad", "/docs", "/redoc", "/openapi.json"}


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._counters: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        ip = request.client.host if request.client else "0.0.0.0"
        now = time.monotonic()
        limit = _AUTH_LIMIT if request.url.path.startswith("/v1/auth") else _GLOBAL_LIMIT

        bucket = self._counters[ip]
        self._counters[ip] = [t for t in bucket if now - t < _WINDOW]

        if len(self._counters[ip]) >= limit:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(_WINDOW)},
                content={
                    "error": "RATE_LIMIT_EXCEDIDO",
                    "mensaje": f"Límite de {limit} solicitudes/{_WINDOW}s superado. Espere e intente nuevamente.",
                },
            )

        self._counters[ip].append(now)
        return await call_next(request)
