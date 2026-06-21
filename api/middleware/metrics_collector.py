"""
Middleware que actualiza contadores de métricas en app.state.
Leído por GET /v1/metrics (08 §8.1 Observabilidad — 4 señales doradas).
"""
from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class MetricsCollectorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        state = request.app.state
        if not hasattr(state, "_metrics"):
            state._metrics = {
                "requests_total": 0,
                "requests_error": 0,
                "latencia_total_ms": 0.0,
            }

        m = state._metrics
        m["requests_total"] += 1
        m["latencia_total_ms"] += elapsed_ms
        if response.status_code >= 500:
            m["requests_error"] += 1

        return response
