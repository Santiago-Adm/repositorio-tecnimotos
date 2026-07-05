"""
Router FastAPI para el módulo taller — 13 endpoints EP-TAL-01 a EP-TAL-13 (03 §6.5).
EP-TAL-13: prueba-ruta — registra salud_estimada del vehículo tras intervención.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, HTTPException, status
from api.auth import (
    ADMIN_ROLES, CLIENTE_ROLES, INTERNO_ROLES, MECANICO_JUNIOR_ROLES,
    MECANICO_ROLES, TAL_VENDEDOR_ROLES, require_roles,
)
from pydantic import BaseModel, Field

from api.dependencies import error_response, get_request_id, success_response
from src.taller.application.use_cases.gestionar_ot import (
    AbrirOrdenTrabajoCommand,
    AbrirOrdenTrabajoUseCase,
    AceptarOTCommand,
    AceptarOrdenTrabajoUseCase,
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
    RegistrarPruebaRutaCommand,
    RegistrarPruebaRutaUseCase,
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
    OrdenTrabajoEvento,
    OrdenTrabajoNoEncontradaError,
    OTYaAceptadaError,
    TransicionEstadoInvalidaError,
    VehiculoNoEncontradoError,
)

router = APIRouter(prefix="/v1", tags=["taller"])
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.taller.infrastructure.repositories.taller_repository_pg import TallerRepositoryPG
        return TallerRepositoryPG(db)
    return request.app.state.taller_repo


def _get_event_publisher(request: Request):
    return request.app.state.event_bus


def _get_catalogo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.taller.infrastructure.adapters.catalogo_taller_adapter_pg import CatalogoTallerAdapterPG
        return CatalogoTallerAdapterPG(db)
    return request.app.state.catalogo_taller_adapter


def _get_parametros(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.shared.infrastructure.repositories.parametros_repository_pg import ParametrosRepositoryPG
        return ParametrosRepositoryPG(db)
    return request.app.state.parametros_service


def _get_pedido_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.pedidos.infrastructure.repositories.pedido_repository_pg import PedidoRepositoryPG
        return PedidoRepositoryPG(db)
    return request.app.state.pedidos_repo


@router.get(
    "/mis-vehiculos",
    summary="EP-TAL-16: Listar mis vehículos (CLIENTE_*) — Pieza C, sesión de catálogo",
)
async def listar_mis_vehiculos(
    request: Request,
    _auth: dict = Depends(require_roles(*CLIENTE_ROLES)),
) -> dict[str, Any]:
    """Resuelve el cliente_id real del usuario autenticado (igual criterio que
    GET /v1/pedidos) y devuelve sus vehículos — sin esto, el catálogo no puede
    auto-filtrarse por universo/modelo del vehículo del cliente."""
    pedido_repo = _get_pedido_repo(request)
    cliente_id = await pedido_repo.obtener_cliente_id_por_usuario(request.state.user_id)
    if cliente_id is None:
        return success_response({"vehiculos": []}, request_id=get_request_id(request))

    repo = _get_repo(request)
    vehiculos = await repo.listar_vehiculos_por_cliente(cliente_id)
    return success_response(
        {
            "vehiculos": [
                {
                    "vehiculo_id": v.id,
                    "universo": v.universo,
                    "modelo": v.modelo,
                    "año": v.año,
                    "placa": v.placa,
                }
                for v in vehiculos
            ]
        },
        request_id=get_request_id(request),
    )


def _ot_to_dict(ot) -> dict:
    return {
        "ot_id": ot.id,
        "estado": ot.estado.value,
        "vehiculo_id": ot.vehiculo_id,
        "mecanico_master_id": ot.mecanico_master_id,
        "mecanico_junior_id": ot.mecanico_junior_id,
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
        "prueba_ruta_completada": ot.prueba_ruta_completada,
        "observaciones_prueba_ruta": ot.observaciones_prueba_ruta,
        "salud_resultado": ot.salud_resultado,
        "aceptada_en": ot.aceptada_en.isoformat() if ot.aceptada_en else None,
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
async def abrir_ot(
    request: Request, body: AbrirOTRequest,
    _auth: dict = Depends(require_roles(*INTERNO_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = AbrirOrdenTrabajoUseCase(repo, pub)
    try:
        ot = await uc.execute(AbrirOrdenTrabajoCommand(
            vehiculo_id=body.vehiculo_id,
            mecanico_master_id=body.mecanico_master_id,
            modalidad=body.modalidad,
            urgencia=body.urgencia,
            actor_id=request.state.user_id,
            mecanico_junior_id=body.mecanico_junior_id,
            cliente_id=body.cliente_id,
        ))
    except VehiculoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Vehículo {body.vehiculo_id} no encontrado", request_id=get_request_id(request)),
        )
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot.id,
        evento="EP-TAL-01-ABRIR",
        estado_anterior=ot.estado.value,
        estado_nuevo=ot.estado.value,
        actor_id=request.state.user_id,
    ))
    return success_response(_ot_to_dict(ot), status_code=201, request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/repuestos",
    status_code=status.HTTP_201_CREATED,
    summary="EP-TAL-02: Agregar repuesto a orden de trabajo",
)
async def agregar_repuesto(
    request: Request, ot_id: str, body: AgregarRepuestoRequest,
    _auth: dict = Depends(require_roles(*MECANICO_JUNIOR_ROLES)),
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
            actor_id=request.state.user_id,
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
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot.id,
        evento="EP-TAL-02-AGREGAR-REPUESTO",
        estado_anterior=ot.estado.value,
        estado_nuevo=ot.estado.value,
        actor_id=request.state.user_id,
    ))
    return success_response(_ot_to_dict(ot), status_code=201, request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/aprobar-lista",
    summary="EP-TAL-03: Aprobar lista → EN_EJECUCION",
)
async def aprobar_lista(
    request: Request, ot_id: str,
    _auth: dict = Depends(require_roles(*TAL_VENDEDOR_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = AprobarListaUseCase(repo, pub)
    try:
        ot = await uc.execute(AprobarListaCommand(
            ot_id=ot_id,
            actor_id=request.state.user_id,
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
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot.id,
        evento="EP-TAL-03-APROBAR-LISTA",
        estado_anterior=ot.estado.value,
        estado_nuevo=ot.estado.value,
        actor_id=request.state.user_id,
    ))
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/confirmar-adicional",
    summary="EP-TAL-04: Cliente confirma costo adicional manual",
)
async def confirmar_adicional(
    request: Request, ot_id: str, body: ConfirmarAdicionalRequest,
    _auth: dict = Depends(require_roles(*TAL_VENDEDOR_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ConfirmarAdicionalUseCase(repo)
    try:
        ot = await uc.execute(ConfirmarAdicionalCommand(
            ot_id=ot_id,
            item_id=body.item_id,
            actor_id=request.state.user_id,
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
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot.id,
        evento="EP-TAL-04-CONFIRMAR-ADICIONAL",
        estado_anterior=ot.estado.value,
        estado_nuevo=ot.estado.value,
        actor_id=request.state.user_id,
    ))
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/autorizar-precio",
    summary="EP-TAL-05: Autorizar visibilidad de precio al cliente",
)
async def autorizar_precio(
    request: Request, ot_id: str, body: AutorizarPrecioRequest,
    _auth: dict = Depends(require_roles(*MECANICO_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = AutorizarPrecioUseCase(repo)
    try:
        ot = await uc.execute(AutorizarPrecioCommand(
            ot_id=ot_id,
            cliente_id=body.cliente_id,
            actor_id=request.state.user_id,
        ))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot.id,
        evento="EP-TAL-05-AUTORIZAR-PRECIO",
        estado_anterior=ot.estado.value,
        estado_nuevo=ot.estado.value,
        actor_id=request.state.user_id,
    ))
    return success_response(
        {"ot_id": ot.id, "visibilidad_precio_cliente": ot.visibilidad_precio_cliente},
        request_id=get_request_id(request),
    )


@router.post(
    "/ordenes-trabajo/{ot_id}/revision-final",
    summary="EP-TAL-06: Declarar revisión final → REVISION_FINAL",
)
async def revision_final(
    request: Request, ot_id: str, body: RevisionFinalRequest,
    _auth: dict = Depends(require_roles(*MECANICO_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = RevisionFinalUseCase(repo, pub)
    try:
        ot = await uc.execute(RevisionFinalCommand(
            ot_id=ot_id,
            costo_mano_obra=body.costo_mano_obra,
            actor_id=request.state.user_id,
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
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot.id,
        evento="EP-TAL-06-REVISION-FINAL",
        estado_anterior=ot.estado.value,
        estado_nuevo=ot.estado.value,
        actor_id=request.state.user_id,
    ))
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/cobro-parcial",
    summary="EP-TAL-07: Registrar cobro parcial con excepción 80%",
)
async def cobro_parcial(
    request: Request, ot_id: str, body: CobroParcialRequest,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = CobroParcialUseCase(repo)
    try:
        resultado = await uc.execute(CobroParcialCommand(
            ot_id=ot_id,
            monto_pagado=body.monto_pagado,
            plazo_dias=body.plazo_dias,
            actor_id=request.state.user_id,
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
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot_id,
        evento="EP-TAL-07-COBRO-PARCIAL",
        estado_anterior=EstadoOrdenTrabajo.REVISION_FINAL.value,
        estado_nuevo=EstadoOrdenTrabajo.REVISION_FINAL.value,
        actor_id=request.state.user_id,
    ))
    return success_response(
        {k: str(v) if isinstance(v, Decimal) else v for k, v in resultado.items()},
        request_id=get_request_id(request),
    )


@router.post(
    "/ordenes-trabajo/{ot_id}/cerrar",
    summary="EP-TAL-08: Cerrar orden de trabajo",
)
async def cerrar_ot(
    request: Request, ot_id: str,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN", "MECANICO_MASTER")),
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = CerrarOrdenTrabajoUseCase(repo, pub)
    try:
        ot = await uc.execute(CerrarOTCommand(
            ot_id=ot_id,
            actor_id=request.state.user_id,
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
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot.id,
        evento="EP-TAL-08-CERRAR",
        estado_anterior=EstadoOrdenTrabajo.REVISION_FINAL.value,
        estado_nuevo=ot.estado.value,
        actor_id=request.state.user_id,
    ))
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/cancelar",
    summary="EP-TAL-09: Cancelar orden de trabajo",
)
async def cancelar_ot(
    request: Request, ot_id: str, body: CancelarOTRequest,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = CancelarOrdenTrabajoUseCase(repo, pub)
    ot_previa = await repo.obtener_ot(ot_id)
    estado_previo = ot_previa.estado.value if ot_previa else None
    try:
        ot = await uc.execute(CancelarOTCommand(
            ot_id=ot_id,
            motivo=body.motivo,
            actor_id=request.state.user_id,
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
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot.id,
        evento="EP-TAL-09-CANCELAR",
        estado_anterior=estado_previo or ot.estado.value,
        estado_nuevo=ot.estado.value,
        actor_id=request.state.user_id,
    ))
    return success_response(_ot_to_dict(ot), request_id=get_request_id(request))


@router.post(
    "/ordenes-trabajo/{ot_id}/liberar-vehiculo",
    summary="EP-TAL-10: Liberar vehículo tras prueba de ruta",
)
async def liberar_vehiculo(
    request: Request, ot_id: str,
    _auth: dict = Depends(require_roles(*MECANICO_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = LiberarVehiculoUseCase(repo, pub)
    try:
        ot = await uc.execute(LiberarVehiculoCommand(
            ot_id=ot_id,
            actor_id=request.state.user_id,
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
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot.id,
        evento="EP-TAL-10-LIBERAR-VEHICULO",
        estado_anterior=ot.estado.value,
        estado_nuevo=ot.estado.value,
        actor_id=request.state.user_id,
    ))
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


class PruebaRutaRequest(BaseModel):
    observaciones: Optional[str] = Field(default=None, max_length=2000)
    salud_declarada: Optional[int] = Field(default=None, ge=0, le=100)


@router.post(
    "/ordenes-trabajo/{ot_id}/prueba-ruta",
    summary="EP-TAL-13: Registrar prueba de ruta post-reparación",
)
async def registrar_prueba_ruta(
    request: Request,
    ot_id: str,
    body: PruebaRutaRequest,
    _auth: dict = Depends(require_roles("MECANICO_MASTER", "ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """
    MECANICO_MASTER · ADMINISTRADOR · SUPERADMIN.
    Registra el resultado de la prueba de ruta tras cerrar la OT.
    Requiere OT en estado CERRADA.
    - Sin observaciones: salud_estimada del vehículo = 100 automático.
    - Con observaciones: mecánico debe declarar salud_declarada (< 100 por convención).
    El valor queda visible para el cliente en EP-TAL-12.
    """
    repo = _get_repo(request)
    uc = RegistrarPruebaRutaUseCase(repo)
    try:
        ot, vehiculo = await uc.execute(
            RegistrarPruebaRutaCommand(
                ot_id=ot_id,
                observaciones=body.observaciones or None,
                salud_declarada=body.salud_declarada,
                actor_id=getattr(request.state, "user_id", ""),
            )
        )
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    except VehiculoNoEncontradoError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", str(exc), request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("VALIDACION_FALLIDA", str(exc), request_id=get_request_id(request)),
        )
    await repo.registrar_evento_ot(OrdenTrabajoEvento(
        ot_id=ot.id,
        evento="EP-TAL-13-PRUEBA-RUTA",
        estado_anterior=ot.estado.value,
        estado_nuevo=ot.estado.value,
        actor_id=request.state.user_id,
    ))
    return success_response(
        {
            **_ot_to_dict(ot),
            "vehiculo_salud_estimada": vehiculo.salud_estimada,
        },
        request_id=get_request_id(request),
    )


@router.get(
    "/ordenes-trabajo/{ot_id}/eventos",
    summary="EP-TAL-15: Auditoría de eventos de la OT (R29, FASE 2)",
)
async def listar_eventos_ot(
    request: Request,
    ot_id: str,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    ot = await repo.obtener_ot(ot_id)
    if ot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    eventos = await repo.listar_eventos_ot(ot_id)
    return success_response(
        {
            "eventos": [
                {
                    "evento": e.evento,
                    "estado_anterior": e.estado_anterior,
                    "estado_nuevo": e.estado_nuevo,
                    "actor_id": e.actor_id,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in eventos
            ],
            "total": len(eventos),
        },
        request_id=get_request_id(request),
    )


@router.get(
    "/ordenes-trabajo",
    summary="EP-TAL-14: Listar órdenes de trabajo (ADR-015)",
)
async def listar_ots(
    request: Request,
    estado: Optional[str] = None,
    mecanico_id: Optional[str] = None,
    activa: Optional[bool] = None,
    _auth: dict = Depends(require_roles(*INTERNO_ROLES)),
) -> dict[str, Any]:
    """
    Listado real de OTs — antes solo existía GET .../{ot_id} (una por una),
    hueco confirmado en sesión anterior y en FASE 0 de ADR-015.
    `activa` se calcula con la regla configurable de ADR-015 (estado +
    días abierta), no una regla fija — ver GET/PATCH /v1/admin/parametros.
    """
    from src.taller.domain.services.ot_activa_service import es_ot_activa, obtener_config_ot_activa

    repo = _get_repo(request)

    # MECANICO_MASTER/JUNIOR solo pueden listar sus propias OTs — se resuelve
    # su mecanico_id real (tabla `mecanico`, distinto del usuario_id del JWT)
    # server-side y se ignora cualquier mecanico_id recibido por query param
    # (evita que un mecánico consulte las OTs de otro).
    if request.state.user_rol in ("MECANICO_MASTER", "MECANICO_JUNIOR"):
        mecanico_id = await repo.obtener_mecanico_id_por_usuario(request.state.user_id)

    ots = await repo.listar_ots()

    if estado is not None:
        ots = [ot for ot in ots if ot.estado.value == estado.upper()]
    if mecanico_id is not None:
        ots = [
            ot for ot in ots
            if ot.mecanico_master_id == mecanico_id or ot.mecanico_junior_id == mecanico_id
        ]
    if activa is not None:
        parametros_svc = _get_parametros(request)
        config = await obtener_config_ot_activa(parametros_svc)
        ots = [ot for ot in ots if es_ot_activa(ot, config) == activa]

    # Pieza E — se embebe universo/modelo del vehículo para que "Mis OTs" pueda
    # reabrir el contexto de trabajo (catálogo filtrado) de una OT ya aceptada
    # sin una segunda llamada. Listas de tamaño acotado (OTs de un mecánico).
    dicts = []
    for ot in ots:
        d = _ot_to_dict(ot)
        vehiculo = await repo.obtener_vehiculo(ot.vehiculo_id)
        d["vehiculo"] = (
            {"universo": vehiculo.universo, "modelo": vehiculo.modelo, "año": vehiculo.año}
            if vehiculo else None
        )
        dicts.append(d)

    return success_response(
        {"ordenes_trabajo": dicts, "total": len(ots)},
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


@router.post(
    "/ordenes-trabajo/{ot_id}/aceptar",
    summary="EP-TAL-17: Aceptar OT asignada (Pieza E)",
)
async def aceptar_ot(
    request: Request,
    ot_id: str,
    _auth: dict = Depends(require_roles(*MECANICO_ROLES)),
) -> dict[str, Any]:
    """MECANICO_MASTER reconoce formalmente una OT ya asignada — registra
    `aceptada_en` (auditoría), no cambia `estado`. Solo el mecánico asignado
    a esta OT puede aceptarla."""
    repo = _get_repo(request)
    mecanico_id = await repo.obtener_mecanico_id_por_usuario(request.state.user_id)
    if mecanico_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response("ACCESO_DENEGADO", "Usuario no es un mecánico registrado", request_id=get_request_id(request)),
        )
    uc = AceptarOrdenTrabajoUseCase(repo)
    try:
        ot = await uc.execute(AceptarOTCommand(ot_id=ot_id, mecanico_id=mecanico_id))
    except OrdenTrabajoNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"OT {ot_id} no encontrada", request_id=get_request_id(request)),
        )
    except OTYaAceptadaError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("OT_YA_ACEPTADA", str(exc), request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response("ACCESO_DENEGADO", str(exc), request_id=get_request_id(request)),
        )

    vehiculo = await repo.obtener_vehiculo(ot.vehiculo_id)
    return success_response(
        {
            **_ot_to_dict(ot),
            "vehiculo": {
                "universo": vehiculo.universo if vehiculo else None,
                "modelo": vehiculo.modelo if vehiculo else None,
                "año": vehiculo.año if vehiculo else None,
            },
        },
        request_id=get_request_id(request),
    )
