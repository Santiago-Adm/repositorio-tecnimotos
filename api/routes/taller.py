"""
Router FastAPI para el módulo taller — 12 endpoints EP-TAL-01 a EP-TAL-12 (03 §6.5).
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import error_response, get_request_id, success_response
from src.taller.application.use_cases.gestionar_ot import (
    AbrirOrdenTrabajoCommand,
    AbrirOrdenTrabajoUseCase,
    AgregarRepuestoCommand,
    AgregarRepuestoUseCase,
    AplicarAprobacionesTacitasUseCase,
    AprobarListaCommand,
    AprobarListaUseCase,
    AutorizarPrecioCommand,
    AutorizarPrecioUseCase,
    CancelarOTCommand,
    CancelarOrdenTrabajoUseCase,
    CerrarOTCommand,
    CerrarOrdenTrabajoUseCase,
    CobroParcialCommand,
    CobroParcialUseCase,
    ConfirmarAdicionalCommand,
    ConfirmarAdicionalUseCase,
    ConsultarDisponibilidadUseCase,
    LiberarVehiculoCommand,
    LiberarVehiculoUseCase,
    ObtenerOrdenTrabajoUseCase,
    RevisionFinalCommand,
    RevisionFinalUseCase,
)
from src.taller.domain.models.orden_trabajo import (
    CobroNoConfirmadoError,
    DomainError,
    EstadoOrdenTrabajo,
    ListaNoConfirmadaError,
    ModalidadIntervencion,
    NivelUrgencia,
    OrdenTrabajoNoEncontradaError,
    TransicionEstadoInvalidaError,
    VehiculoNoEncontradoError,
)

router = APIRouter(prefix="/v1", tags=["taller"])
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_repo(request: Request):
    return request.app.state.taller_repo


def _get_event_publisher(request: Request):
    return request.app.state.event_bus


def _get_catalogo(request: Request):
    return request.app.state.catalogo_taller_adapter


def _ot_to_dict(ot) -> dict:
    return {
        "ot_id": ot.id,
        "estado": ot.estado.value,
        "vehiculo_id": ot.vehiculo_id,
        "mecanico_master_id": ot.mecanico_master_id,
        "modalidad": ot.modalidad.value,
        "urgencia": ot.urgencia.value,
        "monto_estimado": str(ot.monto_estimado),
        "costo_mano_obra": str(ot.costo_mano_obra) if ot.costo_mano_obra else None,
        "cobro_confirmado": ot.cobro_confirmado,
        "cliente_aprobo_lista": ot.cliente_aprobo_lista,
        "lista_repuestos": [
            {
                "item_id": i.id,
                "repuesto_id": i.repuesto_id,
                "codigo": i.codigo,
                "cantidad": i.cantidad,
                "precio_unitario": str(i.precio_unitario),
                "aprobacion": i.aprobacion_cliente.value,
                "tramo": i.tramo_precio.value if i.tramo_precio else None,
            }
            for i in ot.lista_repuestos
        ],
        "created_at": ot.created_at.isoformat(),
    }


# ── Schemas ───────────────────────────────────────────────────────────────────

class AbrirOTRequest(BaseModel):
    vehiculo_id: str
    mecanico_master_id: str
    modalidad: ModalidadIntervencion
    urgencia: NivelUrgencia
    mecanico_junior_id: Optional[str] = None
    cliente_id: Optional[str] = None


class AgregarRepuestoRequest(BaseModel):
    codigo: str = Field(min_length=1)
    cantidad: int = Field(gt=0)


class RevisionFinalRequest(BaseModel):
    costo_mano_obra: Decimal = Field(ge=0)


class CobroParcialRequest(BaseModel):
    monto_pagado: Decimal = Field(gt=0)
    plazo_dias: int = Field(gt=0)


class CancelarOTRequest(BaseModel):
    motivo: str = Field(min_length=1)


class AutorizarPrecioRequest(BaseModel):
    cliente_id: str


class ConfirmarAdicionalRequest(BaseModel):
    item_id: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/ordenes-trabajo",
    status_code=status.HTTP_201_CREATED,
    summary="EP-TAL-01: Abrir orden de trabajo",
)
async def abrir_ot(request: Request, body: AbrirOTRequest) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = AbrirOrdenTrabajoUseCase(repo, pub)
    try:
        ot = await uc.execute(AbrirOrdenTrabajoCommand(
            vehiculo_id=body.vehiculo_id,
            mecanico_master_id=body.mecanico_master_id,
            modalidad=body.modalidad,
            urgencia=body.urgencia,
            actor_id=getattr(request.state, "usuario_id", ""),
            mecanico_junior_id=body.mecanico_junior_id,
            cliente_id=body.cliente_id,
        ))
    except VehiculoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Vehículo {body.vehiculo_id} no encontrado", request_id=get_request_id(request)),
        )
    return success_response(_ot_to_dict(ot), status_code=201, request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/repuestos",
    status_code=status.HTTP_201_CREATED,
    summary="EP-TAL-02: Agregar repuesto a orden de trabajo",
)
async def agregar_repuesto(
    request: Request, ot_id: str, body: AgregarRepuestoRequest
) -> dict[str, Any]:
    repo = _get_repo(request)
    catalogo = _get_catalogo(request)
    pub = _get_event_publisher(request)
    uc = AgregarRepuestoUseCase(repo, catalogo, pub)
    try:
        ot = await uc.execute(AgregarRepuestoCommand(
            ot_id=ot_id,
            codigo=body.codigo,
            cantidad=body.cantidad,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("VALIDACION_FALLIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_ot_to_dict(ot), status_code=201, request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/aprobar-lista",
    summary="EP-TAL-03: Aprobar lista → EN_EJECUCION",
)
async def aprobar_lista(request: Request, ot_id: str) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = AprobarListaUseCase(repo, pub)
    try:
        ot = await uc.execute(AprobarListaCommand(
            ot_id=ot_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("APROBACION_REQUERIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/confirmar-adicional",
    summary="EP-TAL-04: Cliente confirma costo adicional manual",
)
async def confirmar_adicional(
    request: Request, ot_id: str, body: ConfirmarAdicionalRequest
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ConfirmarAdicionalUseCase(repo)
    try:
        ot = await uc.execute(ConfirmarAdicionalCommand(
            ot_id=ot_id,
            item_id=body.item_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("VALIDACION_FALLIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/autorizar-precio",
    summary="EP-TAL-05: Autorizar visibilidad de precio al cliente",
)
async def autorizar_precio(
    request: Request, ot_id: str, body: AutorizarPrecioRequest
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = AutorizarPrecioUseCase(repo)
    try:
        ot = await uc.execute(AutorizarPrecioCommand(
            ot_id=ot_id,
            cliente_id=body.cliente_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    return success_response(
        {"ot_id": ot.id, "visibilidad_precio_cliente": ot.visibilidad_precio_cliente},
        request_id=get_request_id(request),
    )


@router.post(
    "/ordenes-trabajo/{ot_id}/revision-final",
    summary="EP-TAL-06: Declarar revisión final → REVISION_FINAL",
)
async def revision_final(
    request: Request, ot_id: str, body: RevisionFinalRequest
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = RevisionFinalUseCase(repo, pub)
    try:
        ot = await uc.execute(RevisionFinalCommand(
            ot_id=ot_id,
            costo_mano_obra=body.costo_mano_obra,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    except (DomainError, TransicionEstadoInvalidaError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("APROBACION_REQUERIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/cobro-parcial",
    summary="EP-TAL-07: Registrar cobro parcial con excepción 80%",
)
async def cobro_parcial(
    request: Request, ot_id: str, body: CobroParcialRequest
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = CobroParcialUseCase(repo)
    try:
        resultado = await uc.execute(CobroParcialCommand(
            ot_id=ot_id,
            monto_pagado=body.monto_pagado,
            plazo_dias=body.plazo_dias,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("COBRO_INSUFICIENTE", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        {k: str(v) if isinstance(v, Decimal) else v for k, v in resultado.items()},
        request_id=get_request_id(request),
    )


@router.post(
    "/ordenes-trabajo/{ot_id}/cerrar",
    summary="EP-TAL-08: Cerrar orden de trabajo",
)
async def cerrar_ot(request: Request, ot_id: str) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = CerrarOrdenTrabajoUseCase(repo, pub)
    try:
        ot = await uc.execute(CerrarOTCommand(
            ot_id=ot_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    except (CobroNoConfirmadoError, ListaNoConfirmadaError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("APROBACION_REQUERIDA", str(exc), request_id=get_request_id(request)),
        )
    except (DomainError, TransicionEstadoInvalidaError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("TRANSICION_ESTADO_INVALIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/cancelar",
    summary="EP-TAL-09: Cancelar orden de trabajo",
)
async def cancelar_ot(
    request: Request, ot_id: str, body: CancelarOTRequest
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = CancelarOrdenTrabajoUseCase(repo, pub)
    try:
        ot = await uc.execute(CancelarOTCommand(
            ot_id=ot_id,
            motivo=body.motivo,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    except (DomainError, TransicionEstadoInvalidaError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("TRANSICION_ESTADO_INVALIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/liberar-vehiculo",
    summary="EP-TAL-10: Liberar vehículo tras prueba de ruta",
)
async def liberar_vehiculo(request: Request, ot_id: str) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = LiberarVehiculoUseCase(repo, pub)
    try:
        ot = await uc.execute(LiberarVehiculoCommand(
            ot_id=ot_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("TRANSICION_ESTADO_INVALIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        {"ot_id": ot.id, "vehiculo_id": ot.vehiculo_id, "estado": ot.estado.value},
        request_id=get_request_id(request),
    )


@router.get(
    "/taller/disponibilidad",
    summary="EP-TAL-11: Consultar disponibilidad de mecánicos",
)
async def consultar_disponibilidad(request: Request) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ConsultarDisponibilidadUseCase(repo)
    mecanicos = await uc.execute()
    return success_response(
        {
            "mecanicos_disponibles": [
                {"mecanico_id": m.id, "nivel": m.nivel.value}
                for m in mecanicos
            ],
            "total": len(mecanicos),
        },
        request_id=get_request_id(request),
    )


@router.get(
    "/ordenes-trabajo/{ot_id}",
    summary="EP-TAL-12: Obtener orden de trabajo",
)
async def obtener_ot(request: Request, ot_id: str) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ObtenerOrdenTrabajoUseCase(repo)
    try:
        ot = await uc.execute(ot_id)
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))
