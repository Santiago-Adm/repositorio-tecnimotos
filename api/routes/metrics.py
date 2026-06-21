"""
EP-OBS-01: GET /v1/metrics — cuatro señales doradas (08 §8.1 Observabilidad).
No requiere autenticación — scraped por monitor externo o Prometheus en Fase 2.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Request

from api.dependencies import get_request_id, success_response

router = APIRouter(prefix="/v1", tags=["observabilidad"])

_start_time = time.time()


@router.get("/metrics", summary="EP-OBS-01: Métricas cuatro señales doradas")
async def metrics(request: Request) -> dict:
    m = getattr(request.app.state, "_metrics", {})
    total = m.get("requests_total", 0)
    latencia_prom = round(m.get("latencia_total_ms", 0.0) / total, 1) if total > 0 else 0.0
    error_rate = round(m.get("requests_error", 0) / total, 4) if total > 0 else 0.0

    return success_response(
        {
            "uptime_segundos": round(time.time() - _start_time, 1),
            "requests_total": total,
            "error_rate": error_rate,
            "latencia_promedio_ms": latencia_prom,
            "saturation": "n/a — implementar con psutil en Fase 2",
        },
        request_id=get_request_id(request),
    )
