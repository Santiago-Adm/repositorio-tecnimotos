"""
Endpoints de analítica agregada para los dashboards por rol (sesión
"Dashboards deterministas por rol"). Agregación en Python sobre los
listados ya expuestos por cada módulo (mismo patrón que
`admin.py::metricas_negocio`) — sin SQL cruzado entre módulos, respeta
los límites del monolito modular.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request

from api.auth import ADMIN_ROLES, ALL_AUTH_ROLES, CLIENTE_ROLES, INTERNO_ROLES, require_roles
from api.dependencies import get_request_id, success_response

router = APIRouter(prefix="/v1/analitica", tags=["analitica"])

_ESTADOS_PAGADO = {"EMITIDO", "ENVIADO_CLIENTE"}


def _get_pedido_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.pedidos.infrastructure.repositories.pedido_repository_pg import PedidoRepositoryPG
        return PedidoRepositoryPG(db)
    return request.app.state.pedidos_repo


def _get_taller_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.taller.infrastructure.repositories.taller_repository_pg import TallerRepositoryPG
        return TallerRepositoryPG(db)
    return request.app.state.taller_repo


def _get_stock_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.stock.infrastructure.repositories.stock_repository_pg import StockRepositoryPG
        return StockRepositoryPG(db)
    return request.app.state.stock_repo


def _get_catalogo_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.catalogo.infrastructure.repositories.repuesto_repository_pg import RepuestoRepositoryPG
        return RepuestoRepositoryPG(db)
    return request.app.state.catalogo_repo


def _get_user_store(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.shared.infrastructure.repositories.usuario_repository_pg import UsuarioRepositoryPG
        return UsuarioRepositoryPG(db)
    return request.app.state.user_store


async def _contar_clientes_nuevos_por_dia(request: Request, dias: int) -> dict[str, int]:
    """Solo PG expone `cliente.created_at` real — InMemory no modela Cliente
    como entidad propia (ver `PedidoRepositoryInMemory.obtener_cliente_id_por_usuario`).
    Sin BD, retorna serie vacía en vez de inventar un dato."""
    db = getattr(request.state, "db", None)
    if db is None:
        return {}
    from sqlalchemy import select, func
    from src.pedidos.infrastructure.repositories.models.pedido_models import ClienteModel

    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    stmt = select(ClienteModel.created_at).where(ClienteModel.created_at >= desde)
    result = await db.execute(stmt)
    conteo: dict[str, int] = defaultdict(int)
    for (created_at,) in result.all():
        conteo[created_at.date().isoformat()] += 1
    return conteo


def _fechas_ultimos_n_dias(n: int) -> list[str]:
    hoy = datetime.now(timezone.utc).date()
    return [(hoy - timedelta(days=i)).isoformat() for i in range(n - 1, -1, -1)]


@router.get("/ingresos-mensuales", summary="Ingresos emitidos agrupados por mes, últimos N meses (una sola consulta)")
async def obtener_ingresos_mensuales(
    request: Request,
    meses: int = Query(default=12, ge=1, le=36),
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """
    Sustituye el patrón ingenuo de llamar metricas-negocio N veces (una por
    mes) — cada llamada recorre OTs/pedidos/stock completos aunque solo se
    necesite el ingreso del mes. Una sola lectura de comprobantes + agregación
    en Python, mismo costo que un mes individual.
    """
    ahora = datetime.now(timezone.utc)
    inicio_rango = (ahora.replace(day=1) - timedelta(days=31 * (meses - 1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    pedido_repo = _get_pedido_repo(request)
    comprobantes = await pedido_repo.listar_comprobantes()

    etiquetas = []
    cursor = inicio_rango
    for _ in range(meses):
        etiquetas.append(cursor.strftime("%Y-%m"))
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    totales = {label: 0.0 for label in etiquetas}
    for c in comprobantes:
        if c.estado.value in _ESTADOS_PAGADO:
            key = c.created_at.strftime("%Y-%m")
            if key in totales:
                totales[key] += float(c.monto)

    return success_response(
        {"serie": [{"label": label, "ingresos": totales[label]} for label in etiquetas]},
        request_id=get_request_id(request),
    )


@router.get("/series", summary="Serie temporal diaria — ventas, ingresos o clientes nuevos")
async def obtener_serie(
    request: Request,
    metrica: str = Query(..., pattern="^(ventas|ingresos|clientes_nuevos)$"),
    dias: int = Query(default=7, ge=1, le=90),
    _auth: dict = Depends(require_roles(*ALL_AUTH_ROLES)),
) -> dict[str, Any]:
    """
    Scoping server-side por rol (mismo criterio IDOR-safe que GET /v1/pedidos):
    CLIENTE_* siempre ve solo su propio historial; VENDEDOR ve solo lo que él
    registró; roles de administración ven el agregado global.
    """
    rol = request.state.user_rol
    pedido_repo = _get_pedido_repo(request)

    cliente_id: Optional[str] = None
    actor_id: Optional[str] = None
    if rol in CLIENTE_ROLES:
        cliente_id = await pedido_repo.obtener_cliente_id_por_usuario(request.state.user_id)
    elif rol == "VENDEDOR":
        actor_id = request.state.user_id

    fechas = _fechas_ultimos_n_dias(dias)
    serie_map: dict[str, float] = {f: 0.0 for f in fechas}
    desde_dt = datetime.now(timezone.utc) - timedelta(days=dias)

    if metrica == "clientes_nuevos":
        if rol not in ADMIN_ROLES:
            return success_response({"serie": []}, request_id=get_request_id(request))
        conteo = await _contar_clientes_nuevos_por_dia(request, dias)
        for f in fechas:
            serie_map[f] = conteo.get(f, 0)
    elif metrica == "ventas":
        if cliente_id:
            pedidos = await pedido_repo.listar_por_cliente(cliente_id)
        elif actor_id:
            pedidos = await pedido_repo.listar_por_actor(actor_id)
        else:
            pedidos = await pedido_repo.listar_todos()
        for p in pedidos:
            if p.created_at >= desde_dt:
                key = p.created_at.date().isoformat()
                if key in serie_map:
                    serie_map[key] += 1
    else:  # ingresos / gasto
        comprobantes = await pedido_repo.listar_comprobantes()
        if cliente_id or actor_id:
            pedidos_propios = (
                await pedido_repo.listar_por_cliente(cliente_id) if cliente_id
                else await pedido_repo.listar_por_actor(actor_id)
            )
            ids_propios = {p.id for p in pedidos_propios}
            comprobantes = [c for c in comprobantes if c.pedido_id in ids_propios]
        for c in comprobantes:
            if c.estado.value in _ESTADOS_PAGADO and c.created_at >= desde_dt:
                key = c.created_at.date().isoformat()
                if key in serie_map:
                    serie_map[key] += float(c.monto)

    return success_response(
        {"serie": [{"fecha": f, "valor": serie_map[f]} for f in fechas]},
        request_id=get_request_id(request),
    )


@router.get("/rankings", summary="Top N vendedores por ventas o mecánicos por OTs completadas")
async def obtener_rankings(
    request: Request,
    tipo: str = Query(..., pattern="^(vendedores|mecanicos)$"),
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    limit: int = Query(default=3, ge=1, le=20),
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    ahora = datetime.now(timezone.utc)
    rango_desde = datetime.fromisoformat(desde).replace(tzinfo=timezone.utc) if desde else ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    rango_hasta = datetime.fromisoformat(hasta).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc) if hasta else ahora

    user_store = _get_user_store(request)
    usuarios = {u.usuario_id: u.nombre for u in await user_store.listar()}

    if tipo == "vendedores":
        pedido_repo = _get_pedido_repo(request)
        comprobantes = await pedido_repo.listar_comprobantes()
        totales: dict[str, float] = defaultdict(float)
        for c in comprobantes:
            if c.estado.value in _ESTADOS_PAGADO and rango_desde <= c.created_at <= rango_hasta:
                totales[c.emitido_por] += float(c.monto)
        ranking = [
            {"id": actor_id, "nombre": usuarios.get(actor_id, "—"), "total": total}
            for actor_id, total in totales.items()
        ]
    else:
        taller_repo = _get_taller_repo(request)
        historial = await taller_repo.listar_historial()
        totales: dict[str, float] = defaultdict(float)
        conteos: dict[str, int] = defaultdict(int)
        for h in historial:
            if rango_desde <= h.fecha_cierre <= rango_hasta:
                totales[h.mecanico_master_id] += float(h.monto_final)
                conteos[h.mecanico_master_id] += 1
        ranking = [
            {"id": mid, "nombre": usuarios.get(mid, "—"), "total": totales[mid], "ots_completadas": conteos[mid]}
            for mid in conteos
        ]

    ranking.sort(key=lambda r: r["total"], reverse=True)
    return success_response({"ranking": ranking[:limit]}, request_id=get_request_id(request))


@router.get("/distribucion", summary="Distribución de pedidos/ingresos por corte (universo, categoría, distrito, día de semana, estado de pago)")
async def obtener_distribucion(
    request: Request,
    por: str = Query(..., pattern="^(universo|categoria|distrito|dia_semana|estado_comprobante)$"),
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    ahora = datetime.now(timezone.utc)
    rango_desde = datetime.fromisoformat(desde).replace(tzinfo=timezone.utc) if desde else ahora - timedelta(days=28)
    rango_hasta = datetime.fromisoformat(hasta).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc) if hasta else ahora

    pedido_repo = _get_pedido_repo(request)

    if por == "estado_comprobante":
        comprobantes = await pedido_repo.listar_comprobantes()
        pagado = sum(1 for c in comprobantes if c.estado.value in _ESTADOS_PAGADO and rango_desde <= c.created_at <= rango_hasta)
        no_pagado = sum(1 for c in comprobantes if c.estado.value == "PENDIENTE_VALIDACION" and rango_desde <= c.created_at <= rango_hasta)
        return success_response(
            {"distribucion": [{"clave": "PAGADO", "valor": pagado}, {"clave": "NO_PAGADO", "valor": no_pagado}]},
            request_id=get_request_id(request),
        )

    if por == "dia_semana":
        pedidos = await pedido_repo.listar_todos()
        nombres = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
        conteo = {n: 0 for n in nombres}
        limite = ahora - timedelta(weeks=4)
        for p in pedidos:
            if p.created_at >= limite:
                conteo[nombres[p.created_at.weekday()]] += 1
        return success_response(
            {"distribucion": [{"clave": n, "valor": conteo[n]} for n in nombres]},
            request_id=get_request_id(request),
        )

    if por == "distrito":
        db = getattr(request.state, "db", None)
        if db is None:
            return success_response({"distribucion": []}, request_id=get_request_id(request))
        from sqlalchemy import select, func
        from src.pedidos.infrastructure.repositories.models.pedido_models import EnvioModel

        stmt = (
            select(EnvioModel.distrito, func.count(EnvioModel.id))
            .where(EnvioModel.distrito.isnot(None))
            .group_by(EnvioModel.distrito)
        )
        result = await db.execute(stmt)
        return success_response(
            {"distribucion": [{"clave": distrito, "valor": total} for distrito, total in result.all()]},
            request_id=get_request_id(request),
        )

    # universo / categoria — requiere cruzar pedido_item -> repuesto, solo disponible con BD real
    db = getattr(request.state, "db", None)
    if db is None:
        return success_response({"distribucion": []}, request_id=get_request_id(request))
    from sqlalchemy import select
    from src.pedidos.infrastructure.repositories.models.pedido_models import PedidoItemModel, PedidoModel
    from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel

    columna = RepuestoModel.universo if por == "universo" else RepuestoModel.categoria
    stmt = (
        select(columna, PedidoItemModel.cantidad, PedidoItemModel.precio_unitario)
        .join(RepuestoModel, RepuestoModel.id == PedidoItemModel.repuesto_id)
        .join(PedidoModel, PedidoModel.id == PedidoItemModel.pedido_id)
        .where(PedidoModel.created_at >= rango_desde, PedidoModel.created_at <= rango_hasta)
    )
    result = await db.execute(stmt)
    totales: dict[str, float] = defaultdict(float)
    for clave, cantidad, precio_unitario in result.all():
        totales[clave] += float(precio_unitario) * cantidad
    return success_response(
        {"distribucion": [{"clave": k, "valor": v} for k, v in totales.items()]},
        request_id=get_request_id(request),
    )


@router.get("/mis-categorias", summary="Mis categorías más compradas (CLIENTE_*)")
async def obtener_mis_categorias(
    request: Request,
    _auth: dict = Depends(require_roles(*CLIENTE_ROLES)),
) -> dict[str, Any]:
    pedido_repo = _get_pedido_repo(request)
    cliente_id = await pedido_repo.obtener_cliente_id_por_usuario(request.state.user_id)
    if cliente_id is None:
        return success_response({"distribucion": []}, request_id=get_request_id(request))

    db = getattr(request.state, "db", None)
    if db is None:
        return success_response({"distribucion": []}, request_id=get_request_id(request))

    from sqlalchemy import select, func
    from src.pedidos.infrastructure.repositories.models.pedido_models import PedidoItemModel, PedidoModel
    from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel

    stmt = (
        select(RepuestoModel.categoria, func.sum(PedidoItemModel.cantidad))
        .join(RepuestoModel, RepuestoModel.id == PedidoItemModel.repuesto_id)
        .join(PedidoModel, PedidoModel.id == PedidoItemModel.pedido_id)
        .where(PedidoModel.cliente_id == cliente_id)
        .group_by(RepuestoModel.categoria)
    )
    result = await db.execute(stmt)
    return success_response(
        {"distribucion": [{"categoria": cat, "cantidad": int(cant)} for cat, cant in result.all()]},
        request_id=get_request_id(request),
    )


@router.get("/stock-radar", summary="Repuestos por nivel de stock (crítico/bajo/óptimo) y categoría")
async def obtener_stock_radar(
    request: Request,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """Pieza G (sesión catálogo/UI, 2026-07-05) — versión original cargaba
    los 16 195 repuestos completos (3 llamadas a `catalogo_repo.buscar`) más
    todo `stock_repuesto` en memoria de Python para clasificar fila por fila
    (~2.98s medido en vivo, FASE 0.1). Con BD real se reemplaza por una sola
    agregación SQL (CASE + GROUP BY) que replica exactamente la regla de
    `StockRepuesto.esta_bajo_umbral()` — sin BD (InMemory/tests) se conserva
    el cálculo en Python como respaldo."""
    db = getattr(request.state, "db", None)
    if db is not None:
        from sqlalchemy import case, func, select
        from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel
        from src.stock.infrastructure.repositories.models.stock_model import StockRepuestoModel

        nivel = case(
            (
                (StockRepuestoModel.umbral_minimo > 0)
                & (StockRepuestoModel.cantidad_disponible <= StockRepuestoModel.umbral_minimo / 2),
                "CRITICO",
            ),
            (
                (StockRepuestoModel.umbral_minimo > 0)
                & (StockRepuestoModel.cantidad_disponible <= StockRepuestoModel.umbral_minimo),
                "BAJO",
            ),
            else_="OPTIMO",
        ).label("nivel")

        stmt = (
            select(RepuestoModel.categoria, nivel, func.count().label("total"))
            .select_from(StockRepuestoModel)
            .join(RepuestoModel, RepuestoModel.id == StockRepuestoModel.repuesto_id)
            .group_by(RepuestoModel.categoria, nivel)
        )
        result = await db.execute(stmt)
        niveles: dict[str, dict[str, int]] = defaultdict(lambda: {"CRITICO": 0, "BAJO": 0, "OPTIMO": 0})
        for categoria, nivel_valor, total in result.all():
            niveles[categoria][nivel_valor] = total
    else:
        stock_repo = _get_stock_repo(request)
        catalogo_repo = _get_catalogo_repo(request)
        from src.catalogo.domain.models.repuesto import UniversoRepuesto

        repuestos_por_codigo = {}
        for u in UniversoRepuesto:
            for r in await catalogo_repo.buscar(universo=u):
                repuestos_por_codigo[r.codigo] = r

        stocks = await stock_repo.listar_todos()
        niveles = defaultdict(lambda: {"CRITICO": 0, "BAJO": 0, "OPTIMO": 0})
        for s in stocks:
            r = repuestos_por_codigo.get(s.codigo)
            if r is None:
                continue
            if s.umbral_minimo > 0 and s.cantidad_disponible <= s.umbral_minimo // 2:
                nivel_valor = "CRITICO"
            elif s.esta_bajo_umbral():
                nivel_valor = "BAJO"
            else:
                nivel_valor = "OPTIMO"
            niveles[r.categoria][nivel_valor] += 1

    return success_response(
        {
            "radar": [
                {"categoria": cat, **conteo}
                for cat, conteo in niveles.items()
            ]
        },
        request_id=get_request_id(request),
    )


@router.get("/duracion-atencion", summary="Duración real de atención por pedido (scatter) — desde pedido_evento")
async def obtener_duracion_atencion(
    request: Request,
    limit: int = Query(default=200, ge=1, le=1000),
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    pedido_repo = _get_pedido_repo(request)
    pedidos = await pedido_repo.listar_todos()
    puntos = []
    for p in pedidos[:limit]:
        eventos = await pedido_repo.listar_eventos(p.id)
        if len(eventos) < 2:
            continue
        inicio = min(e.timestamp for e in eventos)
        fin = max(e.timestamp for e in eventos)
        horas = (fin - inicio).total_seconds() / 3600
        puntos.append({"pedido_id": p.id, "horas": round(horas, 2), "monto": float(p.monto_total)})
    return success_response({"puntos": puntos}, request_id=get_request_id(request))


@router.get("/ot-a-tiempo", summary="% de OTs cerradas dentro del umbral de días configurado (ADR-015)")
async def obtener_ot_a_tiempo(
    request: Request,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    from src.taller.domain.services.ot_activa_service import obtener_config_ot_activa

    taller_repo = _get_taller_repo(request)
    parametros_svc = getattr(request.app.state, "parametros_service", None)
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.shared.infrastructure.repositories.parametros_repository_pg import ParametrosRepositoryPG
        parametros_svc = ParametrosRepositoryPG(db)

    config = await obtener_config_ot_activa(parametros_svc)
    historial = await taller_repo.listar_historial()
    if not historial:
        return success_response({"porcentaje": None, "total_cerradas": 0}, request_id=get_request_id(request))

    a_tiempo = sum(
        1 for h in historial
        if (h.fecha_cierre - h.fecha_apertura).days <= config.dias_maximo
    )
    return success_response(
        {
            "porcentaje": round(a_tiempo / len(historial) * 100, 1),
            "total_cerradas": len(historial),
            "a_tiempo": a_tiempo,
        },
        request_id=get_request_id(request),
    )


@router.get("/reservas-totales", summary="Total de reservas registradas")
async def obtener_reservas_totales(
    request: Request,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    db = getattr(request.state, "db", None)
    if db is None:
        return success_response({"total": 0}, request_id=get_request_id(request))
    from sqlalchemy import select, func
    from src.pedidos.infrastructure.repositories.models.pedido_models import ReservaModel

    total = await db.scalar(select(func.count(ReservaModel.id))) or 0
    return success_response({"total": int(total)}, request_id=get_request_id(request))


@router.get("/repuestos-mas-vendidos", summary="Repuestos más vendidos por cantidad (últimos 30 días)")
async def obtener_repuestos_mas_vendidos(
    request: Request,
    limit: int = Query(default=5, ge=1, le=50),
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    db = getattr(request.state, "db", None)
    if db is None:
        return success_response({"repuestos": []}, request_id=get_request_id(request))
    from sqlalchemy import select, func
    from src.stock.infrastructure.repositories.models.stock_model import MovimientoStockModel
    from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel

    limite_30d = datetime.now(timezone.utc) - timedelta(days=30)
    stmt = (
        select(RepuestoModel.codigo, RepuestoModel.nombre, func.sum(MovimientoStockModel.cantidad).label("total"))
        .join(RepuestoModel, RepuestoModel.id == MovimientoStockModel.repuesto_id)
        .where(MovimientoStockModel.tipo_movimiento == "SALIDA_VENTA", MovimientoStockModel.timestamp >= limite_30d)
        .group_by(RepuestoModel.codigo, RepuestoModel.nombre)
        .order_by(func.sum(MovimientoStockModel.cantidad).desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return success_response(
        {"repuestos": [{"codigo": c, "nombre": n, "cantidad": int(t)} for c, n, t in result.all()]},
        request_id=get_request_id(request),
    )


async def _mis_ot_ids(request: Request, taller_repo) -> list[str]:
    mecanico_id = await taller_repo.obtener_mecanico_id_por_usuario(request.state.user_id)
    if mecanico_id is None:
        return []
    ots = await taller_repo.listar_ots()
    return [
        ot.id for ot in ots
        if ot.mecanico_master_id == mecanico_id or ot.mecanico_junior_id == mecanico_id
    ]


@router.get("/mecanico/repuestos-consumidos", summary="Cantidad de repuestos consumidos por el mecánico en sus OTs este mes")
async def obtener_repuestos_consumidos(
    request: Request,
    _auth: dict = Depends(require_roles(*INTERNO_ROLES)),
) -> dict[str, Any]:
    if request.state.user_rol not in ("MECANICO_MASTER", "MECANICO_JUNIOR"):
        return success_response({"cantidad": 0}, request_id=get_request_id(request))

    db = getattr(request.state, "db", None)
    if db is None:
        return success_response({"cantidad": 0}, request_id=get_request_id(request))

    taller_repo = _get_taller_repo(request)
    ot_ids = await _mis_ot_ids(request, taller_repo)
    if not ot_ids:
        return success_response({"cantidad": 0}, request_id=get_request_id(request))

    from sqlalchemy import select, func
    from src.stock.infrastructure.repositories.models.stock_model import MovimientoStockModel

    inicio_mes = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    stmt = select(func.coalesce(func.sum(MovimientoStockModel.cantidad), 0)).where(
        MovimientoStockModel.tipo_movimiento == "SALIDA_TALLER",
        MovimientoStockModel.referencia_id.in_(ot_ids),
        MovimientoStockModel.timestamp >= inicio_mes,
    )
    cantidad = await db.scalar(stmt) or 0
    return success_response({"cantidad": int(cantidad)}, request_id=get_request_id(request))


@router.get("/mecanico/ots-por-universo", summary="OTs del mecánico agrupadas por universo del vehículo")
async def obtener_ots_por_universo(
    request: Request,
    _auth: dict = Depends(require_roles(*INTERNO_ROLES)),
) -> dict[str, Any]:
    if request.state.user_rol not in ("MECANICO_MASTER", "MECANICO_JUNIOR"):
        return success_response({"distribucion": []}, request_id=get_request_id(request))

    db = getattr(request.state, "db", None)
    if db is None:
        return success_response({"distribucion": []}, request_id=get_request_id(request))

    taller_repo = _get_taller_repo(request)
    ot_ids = await _mis_ot_ids(request, taller_repo)
    if not ot_ids:
        return success_response({"distribucion": []}, request_id=get_request_id(request))

    from sqlalchemy import select, func
    from src.taller.infrastructure.repositories.models.taller_models import OrdenTrabajoModel, VehiculoModel

    stmt = (
        select(VehiculoModel.universo, func.count(OrdenTrabajoModel.id))
        .join(VehiculoModel, VehiculoModel.id == OrdenTrabajoModel.vehiculo_id)
        .where(OrdenTrabajoModel.id.in_(ot_ids))
        .group_by(VehiculoModel.universo)
    )
    result = await db.execute(stmt)
    return success_response(
        {"distribucion": [{"clave": u, "valor": c} for u, c in result.all()]},
        request_id=get_request_id(request),
    )
