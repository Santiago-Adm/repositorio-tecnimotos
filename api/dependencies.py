"""
Inyección de dependencias y wrappers de respuesta (03 §6.8).
Envelope obligatorio en todo endpoint: {data, meta} / {error}.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from src.shared.infrastructure.settings import get_settings


def success_response(data: Any, status_code: int = 200, request_id: str = "") -> dict[str, Any]:
    if not request_id:
        request_id = str(uuid.uuid4())
    return {
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
        },
    }


def error_response(
    code: str,
    message: str,
    detail: str = "",
    request_id: str = "",
) -> dict[str, Any]:
    if not request_id:
        request_id = str(uuid.uuid4())
    return {
        "error": {
            "code": code,
            "message": message,
            "detail": detail,
            "request_id": request_id,
        }
    }


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))
