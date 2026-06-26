"""
Endpoints de soporte EP-SOP-01 y EP-SOP-02 (HU-INT-08, 02 §5.1).
EP-SOP-01 POST /v1/soporte/reportes — todos los roles autenticados.
EP-SOP-02 GET  /v1/soporte/reportes — SUPERADMIN exclusivo.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from api.auth import ALL_AUTH_ROLES, require_roles
from api.dependencies import get_request_id, success_response
from src.shared.application.use_cases.soporte_use_cases import SoporteService
from src.shared.domain.models.reporte_soporte import ReporteSoporte

router = APIRouter(prefix="/v1/soporte", tags=["soporte"])


class CrearReporteSoporteRequest(BaseModel):
    descripcion: str = Field(..., min_length=1, max_length=2000)


def _reporte_to_dict(r: ReporteSoporte) -> dict[str, Any]:
    return {
        "id": r.id,
        "usuario_reportante_id": r.usuario_reportante_id,
        "rol_usuario_reportante": r.rol_usuario_reportante,
        "descripcion": r.descripcion,
        "estado": r.estado.value,
        "creado_en": r.creado_en.isoformat(),
        "resuelto_en": r.resuelto_en.isoformat() if r.resuelto_en else None,
        "resuelto_por": r.resuelto_por,
    }


def _get_soporte_service(request: Request) -> SoporteService:
    return SoporteService(request.app.state.soporte_repo)


@router.post(
    "/reportes",
    status_code=status.HTTP_201_CREATED,
    summary="EP-SOP-01: Crear reporte de soporte",
)
async def crear_reporte_soporte(
    body: CrearReporteSoporteRequest,
    request: Request,
    _auth: dict = Depends(require_roles(*ALL_AUTH_ROLES)),
) -> dict[str, Any]:
    """Cualquier rol autenticado crea un reporte sobre un problema propio."""
    svc = _get_soporte_service(request)
    reporte = await svc.crear_reporte(
        usuario_reportante_id=request.state.user_id,
        rol_usuario_reportante=request.state.user_rol,
        descripcion=body.descripcion,
    )
    return success_response(_reporte_to_dict(reporte), request_id=get_request_id(request))


@router.get(
    "/reportes",
    summary="EP-SOP-02: Listar reportes activos",
)
async def listar_reportes_soporte(
    request: Request,
    _auth: dict = Depends(require_roles("SUPERADMIN")),
) -> dict[str, Any]:
    """SUPERADMIN: lista reportes ABIERTO/EN_INVESTIGACION para vincular a impersonación."""
    svc = _get_soporte_service(request)
    reportes = await svc.listar_reportes_activos()
    return success_response(
        {"reportes": [_reporte_to_dict(r) for r in reportes], "total": len(reportes)},
        request_id=get_request_id(request),
    )
