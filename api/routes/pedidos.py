"""
Router FastAPI para el módulo pedidos — 19 endpoints EP-PED-01 a EP-PED-19 (03 §6.3).
EP-PED-18/19: Plan de mantenimiento preventivo (ciclo 30 días, solo CLIENTE_CONDUCTOR/CLIENTE_RURAL).
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, HTTPException, status
from api.auth import (
    ADMIN_ROLES, CLIENTE_ROLES, MECANICO_ROLES, VENDEDOR_ROLES, require_roles,
)
from pydantic import BaseModel, Field

from api.dependencies import error_response, get_request_id, success_response
from src.pedidos.application.use_cases.gestionar_pedido import (
    CancelarPedidoCommand,
    CancelarPedidoUseCase,
    ConfirmarPedidoCommand,
    ConfirmarPedidoUseCase,
    CrearPedidoCommand,
    CrearPedidoUseCase,
    ItemPedidoInput,
    ListarPedidosUseCase,
    ObtenerPedidoUseCase,
)
from src.pedidos.application.use_cases.gestionar_reserva import (
    CrearReservaCommand,
    CrearReservaUseCase,
    LiberarReservaCommand,
    LiberarReservaUseCase,
)
from src.pedidos.application.use_cases.gestionar_comprobante import (
    AprobarComprobanteCommand,
    AprobarComprobanteUseCase,
    AnularComprobanteCommand,
    AnularComprobanteUseCase,
    ConfirmarRecepcionUseCase,
    CrearListaReservaCommand,
    CrearListaReservaUseCase,
    EmitirProformaCommand,
    EmitirProformaUseCase,
    FormalizarListaReservaCommand,
    FormalizarListaReservaUseCase,
    GenerarComprobanteCommand,
    GenerarComprobanteUseCase,
    ItemListaInput,
    RegistrarEnvioCommand,
    RegistrarEnvioUseCase,
    RegistrarIncidenciaUseCase,
)
from src.pedidos.application.use_cases.gestionar_plan_mantenimiento import (
    ActivarPlanMantenimientoCommand,
    ActivarPlanMantenimientoUseCase,
    CancelarPlanMantenimientoCommand,
    CancelarPlanMantenimientoUseCase,
)
from src.pedidos.domain.models.pedido import (
    ComprobanteNoEncontradoError,
    ComprobanteYaEmitidoError,
    DomainError,
    EstadoComprobante,
    ListaReservaNoEncontradaError,
    PedidoNoEncontradoError,
    PlanMantenimientoNoEncontradoError,
    PlanYaActivoError,
    ProformaNoEncontradaError,
    ReservaNoEncontradaError,
    SegmentoCliente,
    TipoComprobante,
    TransicionEstadoInvalidaError,
)

router = APIRouter(prefix="/v1", tags=["pedidos"])
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.pedidos.infrastructure.repositories.pedido_repository_pg import PedidoRepositoryPG
        return PedidoRepositoryPG(db)
    return request.app.state.pedidos_repo


def _get_event_publisher(request: Request):
    return request.app.state.event_bus


def _get_catalogo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.pedidos.infrastructure.adapters.catalogo_adapter_pg import CatalogoAdapterPG
        return CatalogoAdapterPG(db)
    return request.app.state.catalogo_adapter


def _get_stock(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.pedidos.infrastructure.adapters.catalogo_adapter_pg import StockAdapterPG
        return StockAdapterPG(db)
    return request.app.state.stock_adapter


def _pedido_to_dict(p) -> dict:
    return {
        "pedido_id": p.id,
        "estado": p.estado.value,
        "canal_origen": p.canal_origen,
        "cliente_id": p.cliente_id,
        "monto_total": str(p.monto_total),
        "monto_efectivo": str(p.monto_efectivo()),
        "items": [
            {
                "repuesto_id": i.repuesto_id,
                "codigo": i.codigo,
                "cantidad": i.cantidad,
                "precio_unitario": str(i.precio_unitario),
                "subtotal": str(i.subtotal),
            }
            for i in p.items
        ],
        "created_at": p.created_at.isoformat(),
    }


# ── Schemas ───────────────────────────────────────────────────────────────────

class ItemInput(BaseModel):
    codigo: str
    cantidad: int = Field(gt=0)


class CrearPedidoRequest(BaseModel):
    canal_origen: str = Field(min_length=1)
    items: list[ItemInput] = Field(min_length=0)
    cliente_id: Optional[str] = None
    orden_trabajo_id: Optional[str] = None


class CancelarPedidoRequest(BaseModel):
    motivo: str = Field(min_length=1)
    es_cliente: bool = False


class CrearReservaRequest(BaseModel):
    cliente_id: str
    repuesto_id: str
    cantidad: int = Field(gt=0)
    segmento: SegmentoCliente
    pedido_id: Optional[str] = None


class LiberarReservaRequest(BaseModel):
    motivo: str = "LIBERADA_MANUAL"


class GenerarComprobanteRequest(BaseModel):
    tipo: TipoComprobante
    monto: Decimal = Field(gt=0)
    emitido_por: str
    rol_emisor: str
    ruc_cliente: Optional[str] = None


class RegistrarEnvioRequest(BaseModel):
    empresa_encomienda: str = Field(min_length=1)
    direccion_destino: str = Field(min_length=1)


class ItemListaRequest(BaseModel):
    repuesto_id: str
    codigo: str
    cantidad: int = Field(gt=0)
    precio_referencia: Decimal = Field(gt=0)


class CrearListaReservaRequest(BaseModel):
    cliente_id: str
    nombre: Optional[str] = None
    items: list[ItemListaRequest] = Field(min_length=0)


# ── Endpoints EP-PED-01 a EP-PED-05 ──────────────────────────────────────────

@router.post(
    "/pedidos",
    status_code=status.HTTP_201_CREATED,
    summary="EP-PED-01: Crear pedido",
)
async def crear_pedido(request: Request, body: CrearPedidoRequest) -> dict[str, Any]:
    repo = _get_repo(request)
    catalogo = _get_catalogo(request)
    pub = _get_event_publisher(request)
    uc = CrearPedidoUseCase(repo, catalogo, pub)
    try:
        pedido = await uc.execute(CrearPedidoCommand(
            canal_origen=body.canal_origen,
            actor_id=getattr(request.state, "usuario_id", ""),
            items=[ItemPedidoInput(codigo=i.codigo, cantidad=i.cantidad) for i in body.items],
            cliente_id=body.cliente_id,
            orden_trabajo_id=body.orden_trabajo_id,
        ))
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("VALIDACION_FALLIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_pedido_to_dict(pedido), status_code=201, request_id=get_request_id(request))


@router.get("/pedidos", summary="EP-PED-02: Listar pedidos")
async def listar_pedidos(
    request: Request, cliente_id: Optional[str] = None
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ListarPedidosUseCase(repo)
    pedidos = await uc.execute(cliente_id=cliente_id)
    return success_response(
        {"pedidos": [_pedido_to_dict(p) for p in pedidos], "total": len(pedidos)},
        request_id=get_request_id(request),
    )


@router.get("/pedidos/{pedido_id}", summary="EP-PED-03: Obtener pedido")
async def obtener_pedido(request: Request, pedido_id: str) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ObtenerPedidoUseCase(repo)
    try:
        pedido = await uc.execute(pedido_id)
    except PedidoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Pedido {pedido_id} no encontrado", request_id=get_request_id(request)),
        )
    return success_response(_pedido_to_dict(pedido), request_id=get_request_id(request))


@router.post("/pedidos/{pedido_id}/confirmar", summary="EP-PED-04: Confirmar pedido")
async def confirmar_pedido(request: Request, pedido_id: str) -> dict[str, Any]:
    repo = _get_repo(request)
    stock = _get_stock(request)
    pub = _get_event_publisher(request)
    uc = ConfirmarPedidoUseCase(repo, stock, pub)
    try:
        pedido = await uc.execute(ConfirmarPedidoCommand(
            pedido_id=pedido_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except PedidoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Pedido {pedido_id} no encontrado", request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("STOCK_INSUFICIENTE", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_pedido_to_dict(pedido), request_id=get_request_id(request))


@router.post("/pedidos/{pedido_id}/cancelar", summary="EP-PED-05: Cancelar pedido")
async def cancelar_pedido(
    request: Request, pedido_id: str, body: CancelarPedidoRequest
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = CancelarPedidoUseCase(repo, pub)
    try:
        pedido = await uc.execute(CancelarPedidoCommand(
            pedido_id=pedido_id,
            actor_id=getattr(request.state, "usuario_id", ""),
            motivo=body.motivo,
            es_cliente=body.es_cliente,
        ))
    except PedidoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Pedido {pedido_id} no encontrado", request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("TRANSICION_ESTADO_INVALIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_pedido_to_dict(pedido), request_id=get_request_id(request))


# ── Endpoints EP-PED-06 y EP-PED-07 ──────────────────────────────────────────

@router.post(
    "/reservas",
    status_code=status.HTTP_201_CREATED,
    summary="EP-PED-06: Crear reserva",
)
async def crear_reserva(request: Request, body: CrearReservaRequest) -> dict[str, Any]:
    repo = _get_repo(request)
    stock = _get_stock(request)
    pub = _get_event_publisher(request)
    uc = CrearReservaUseCase(repo, stock, pub)
    try:
        reserva = await uc.execute(CrearReservaCommand(
            cliente_id=body.cliente_id,
            repuesto_id=body.repuesto_id,
            cantidad=body.cantidad,
            segmento=body.segmento,
            actor_id=getattr(request.state, "usuario_id", body.cliente_id),
            pedido_id=body.pedido_id,
        ))
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("REPUESTO_SIN_STOCK", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        {
            "reserva_id": reserva.id,
            "repuesto_id": reserva.repuesto_id,
            "cantidad": reserva.cantidad,
            "estado": reserva.estado.value,
            "expira_en": reserva.expira_en.isoformat(),
            "segmento": reserva.segmento.value,
        },
        status_code=201,
        request_id=get_request_id(request),
    )


@router.post(
    "/reservas/{reserva_id}/liberar",
    summary="EP-PED-07: Liberar reserva",
)
async def liberar_reserva(
    request: Request, reserva_id: str, body: LiberarReservaRequest,
    _auth: dict = Depends(require_roles(*VENDEDOR_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    stock = _get_stock(request)
    pub = _get_event_publisher(request)
    uc = LiberarReservaUseCase(repo, stock, pub)
    try:
        reserva = await uc.execute(LiberarReservaCommand(
            reserva_id=reserva_id,
            actor_id=getattr(request.state, "usuario_id", ""),
            motivo=body.motivo,
        ))
    except ReservaNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Reserva {reserva_id} no encontrada", request_id=get_request_id(request)),
        )
    except (DomainError, TransicionEstadoInvalidaError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("TRANSICION_ESTADO_INVALIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        {"reserva_id": reserva.id, "estado": reserva.estado.value},
        request_id=get_request_id(request),
    )


# ── Endpoints EP-PED-08 a EP-PED-11 ──────────────────────────────────────────

@router.post(
    "/pedidos/{pedido_id}/proforma",
    status_code=status.HTTP_201_CREATED,
    summary="EP-PED-08: Emitir proforma",
)
async def emitir_proforma(
    request: Request, pedido_id: str,
    _auth: dict = Depends(require_roles(*VENDEDOR_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = EmitirProformaUseCase(repo)
    try:
        proforma = await uc.execute(EmitirProformaCommand(
            pedido_id=pedido_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except PedidoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Pedido {pedido_id} no encontrado", request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("VALIDACION_FALLIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        {
            "proforma_id": proforma.id,
            "numero_referencia": proforma.numero_referencia,
            "monto_total": str(proforma.monto_total),
            "estado": proforma.estado.value,
        },
        status_code=201,
        request_id=get_request_id(request),
    )


@router.post(
    "/pedidos/{pedido_id}/envio",
    status_code=status.HTTP_201_CREATED,
    summary="EP-PED-09: Registrar envío",
)
async def registrar_envio(
    request: Request, pedido_id: str, body: RegistrarEnvioRequest,
    _auth: dict = Depends(require_roles(*VENDEDOR_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = RegistrarEnvioUseCase(repo, pub)
    try:
        envio = await uc.execute(RegistrarEnvioCommand(
            pedido_id=pedido_id,
            empresa_encomienda=body.empresa_encomienda,
            direccion_destino=body.direccion_destino,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except PedidoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Pedido {pedido_id} no encontrado", request_id=get_request_id(request)),
        )
    except (DomainError, TransicionEstadoInvalidaError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("TRANSICION_ESTADO_INVALIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        {"envio_id": envio.id, "estado": envio.estado.value},
        status_code=201,
        request_id=get_request_id(request),
    )


@router.post(
    "/pedidos/{pedido_id}/confirmar-recepcion",
    summary="EP-PED-10: Confirmar recepción",
)
async def confirmar_recepcion(request: Request, pedido_id: str) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ConfirmarRecepcionUseCase(repo)
    try:
        await uc.execute(
            pedido_id=pedido_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        )
    except PedidoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Pedido {pedido_id} no encontrado", request_id=get_request_id(request)),
        )
    except (DomainError, TransicionEstadoInvalidaError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("TRANSICION_ESTADO_INVALIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response({"pedido_id": pedido_id, "estado": "ENTREGADO"}, request_id=get_request_id(request))


@router.post(
    "/pedidos/{pedido_id}/incidencia",
    summary="EP-PED-11: Registrar incidencia",
)
async def registrar_incidencia(request: Request, pedido_id: str) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = RegistrarIncidenciaUseCase(repo)
    try:
        await uc.execute(
            pedido_id=pedido_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        )
    except PedidoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Pedido {pedido_id} no encontrado", request_id=get_request_id(request)),
        )
    except (DomainError, TransicionEstadoInvalidaError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("TRANSICION_ESTADO_INVALIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response({"pedido_id": pedido_id, "estado": "INCIDENCIA"}, request_id=get_request_id(request))


# ── Endpoints EP-PED-12 a EP-PED-14 ──────────────────────────────────────────

@router.post(
    "/notificaciones/repuesto-disponible",
    summary="EP-PED-12: Solicitar notificación cuando repuesto esté disponible",
)
async def solicitar_notificacion_repuesto(
    request: Request,
    _auth: dict = Depends(require_roles(*CLIENTE_ROLES)),
) -> dict[str, Any]:
    return success_response(
        {"mensaje": "Notificación registrada"},
        request_id=get_request_id(request),
    )


@router.post(
    "/lista-reserva-progresiva",
    status_code=status.HTTP_201_CREATED,
    summary="EP-PED-13: Crear lista de reserva progresiva",
)
async def crear_lista_reserva(
    request: Request, body: CrearListaReservaRequest,
    _auth: dict = Depends(require_roles("CLIENTE_DISTRITO")),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = CrearListaReservaUseCase(repo)
    try:
        lista = await uc.execute(CrearListaReservaCommand(
            cliente_id=body.cliente_id,
            nombre=body.nombre,
            items=[
                ItemListaInput(
                    repuesto_id=i.repuesto_id,
                    codigo=i.codigo,
                    cantidad=i.cantidad,
                    precio_referencia=i.precio_referencia,
                )
                for i in body.items
            ],
        ))
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("VALIDACION_FALLIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        {"lista_id": lista.id, "estado": lista.estado.value, "total_items": len(lista.items)},
        status_code=201,
        request_id=get_request_id(request),
    )


@router.post(
    "/lista-reserva-progresiva/{lista_id}/formalizar",
    summary="EP-PED-14: Formalizar lista de reserva progresiva",
)
async def formalizar_lista_reserva(
    request: Request, lista_id: str,
    _auth: dict = Depends(require_roles("CLIENTE_DISTRITO")),
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = FormalizarListaReservaUseCase(repo, pub)
    try:
        await uc.execute(FormalizarListaReservaCommand(
            lista_id=lista_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except ListaReservaNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Lista {lista_id} no encontrada", request_id=get_request_id(request)),
        )
    except (DomainError, TransicionEstadoInvalidaError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("VALIDACION_FALLIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        {"lista_id": lista_id, "estado": "FORMALIZADA"},
        request_id=get_request_id(request),
    )


# ── Endpoints EP-PED-15 a EP-PED-17 ──────────────────────────────────────────

@router.post(
    "/pedidos/{pedido_id}/comprobante",
    status_code=status.HTTP_201_CREATED,
    summary="EP-PED-15: Generar comprobante",
)
async def generar_comprobante(
    request: Request, pedido_id: str, body: GenerarComprobanteRequest,
    _auth: dict = Depends(require_roles(*VENDEDOR_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = GenerarComprobanteUseCase(repo, pub)
    try:
        comp = await uc.execute(GenerarComprobanteCommand(
            pedido_id=pedido_id,
            tipo=body.tipo,
            monto=body.monto,
            emitido_por=body.emitido_por,
            rol_emisor=body.rol_emisor,
            ruc_cliente=body.ruc_cliente,
        ))
    except PedidoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Pedido {pedido_id} no encontrado", request_id=get_request_id(request)),
        )
    return success_response(
        {
            "comprobante_id": comp.id,
            "pedido_id": comp.pedido_id,
            "tipo": comp.tipo.value,
            "estado": comp.estado.value,
            "monto": str(comp.monto),
        },
        status_code=201,
        request_id=get_request_id(request),
    )


@router.post(
    "/comprobantes/{comprobante_id}/aprobar",
    summary="EP-PED-16: Aprobar y emitir comprobante",
)
async def aprobar_comprobante(
    request: Request, comprobante_id: str,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    repo = _get_repo(request)
    pub = _get_event_publisher(request)
    uc = AprobarComprobanteUseCase(repo, pub)
    try:
        comp = await uc.execute(AprobarComprobanteCommand(
            comprobante_id=comprobante_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except ComprobanteNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Comprobante {comprobante_id} no encontrado", request_id=get_request_id(request)),
        )
    except TransicionEstadoInvalidaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("COMPROBANTE_YA_EMITIDO", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        {"comprobante_id": comp.id, "estado": comp.estado.value},
        request_id=get_request_id(request),
    )


@router.post(
    "/comprobantes/{comprobante_id}/anular",
    summary="EP-PED-17: Anular comprobante",
)
async def anular_comprobante(
    request: Request, comprobante_id: str,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = AnularComprobanteUseCase(repo)
    try:
        comp = await uc.execute(AnularComprobanteCommand(
            comprobante_id=comprobante_id,
            actor_id=getattr(request.state, "usuario_id", ""),
        ))
    except ComprobanteNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Comprobante {comprobante_id} no encontrado", request_id=get_request_id(request)),
        )
    except TransicionEstadoInvalidaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("TRANSICION_ESTADO_INVALIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        {"comprobante_id": comp.id, "estado": comp.estado.value, "nota_credito_id": comp.nota_credito_id},
        request_id=get_request_id(request),
    )


# ── Plan de mantenimiento preventivo ─────────────────────────────────────────

_ROLES_PLAN_MANTENIMIENTO = ("CLIENTE_CONDUCTOR", "CLIENTE_RURAL")


class ActivarPlanRequest(BaseModel):
    vehiculo_id: str = Field(min_length=1)


def _plan_to_dict(plan) -> dict[str, Any]:
    return {
        "plan_id": plan.id,
        "cliente_id": plan.cliente_id,
        "vehiculo_id": plan.vehiculo_id,
        "estado": plan.estado.value,
        "fecha_activacion": plan.fecha_activacion.isoformat(),
        "fecha_ultimo_recordatorio": (
            plan.fecha_ultimo_recordatorio.isoformat()
            if plan.fecha_ultimo_recordatorio else None
        ),
        "proximo_recordatorio": plan.proximo_recordatorio().isoformat(),
    }


@router.post(
    "/pedidos/plan-mantenimiento",
    summary="EP-PED-18: Activar plan de mantenimiento",
    status_code=status.HTTP_201_CREATED,
)
async def activar_plan_mantenimiento(
    request: Request,
    body: ActivarPlanRequest,
    _auth: dict = Depends(require_roles(*_ROLES_PLAN_MANTENIMIENTO)),
) -> dict[str, Any]:
    """
    CLIENTE_CONDUCTOR · CLIENTE_RURAL.
    Activa un plan de mantenimiento preventivo con ciclo de 30 días.
    Un vehículo solo puede tener un plan ACTIVO a la vez.
    """
    cliente_id = getattr(request.state, "user_id", "")
    repo = _get_repo(request)
    uc = ActivarPlanMantenimientoUseCase(repo)
    try:
        plan = await uc.execute(ActivarPlanMantenimientoCommand(
            cliente_id=cliente_id,
            vehiculo_id=body.vehiculo_id,
        ))
    except PlanYaActivoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("PLAN_YA_ACTIVO", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_plan_to_dict(plan), request_id=get_request_id(request))


@router.post(
    "/pedidos/plan-mantenimiento/{plan_id}/cancelar",
    summary="EP-PED-19: Cancelar plan de mantenimiento",
)
async def cancelar_plan_mantenimiento(
    request: Request,
    plan_id: str,
    _auth: dict = Depends(require_roles(*_ROLES_PLAN_MANTENIMIENTO)),
) -> dict[str, Any]:
    """
    CLIENTE_CONDUCTOR · CLIENTE_RURAL.
    Cancela el plan; los recordatorios futuros se detienen inmediatamente.
    Solo el propietario del plan puede cancelarlo.
    """
    cliente_id = getattr(request.state, "user_id", "")
    repo = _get_repo(request)
    uc = CancelarPlanMantenimientoUseCase(repo)
    try:
        plan = await uc.execute(CancelarPlanMantenimientoCommand(
            plan_id=plan_id,
            cliente_id=cliente_id,
        ))
    except PlanMantenimientoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("RECURSO_NO_ENCONTRADO", f"Plan {plan_id} no encontrado", request_id=get_request_id(request)),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response("VALIDACION_FALLIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(_plan_to_dict(plan), request_id=get_request_id(request))
