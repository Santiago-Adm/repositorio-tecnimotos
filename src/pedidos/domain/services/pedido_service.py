"""
Reglas de negocio puras del módulo pedidos (02 §2.2).
Sin imports de FastAPI, SQLAlchemy ni Redis.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.pedidos.domain.models.pedido import (
    Comprobante,
    DeudaActiva,
    DomainError,
    EstadoComprobante,
    EstadoPedido,
    Pedido,
    Reserva,
    SegmentoCliente,
    TipoComprobante,
    TransicionEstadoInvalidaError,
    ttl_para_segmento,
)

# Umbral de excepción del 80% (02 §2.2)
PORCENTAJE_MINIMO_PAGO = Decimal("0.80")

# Umbrales de costo adicional por tramos (02 §2.2, HU-INT-03)
UMBRAL_APROBACION_AUTOMATICA = Decimal("30.00")
UMBRAL_APROBACION_TACITA = Decimal("100.00")


class PedidoService:

    @staticmethod
    def verificar_cancelacion_permitida(
        pedido: Pedido, es_cliente: bool
    ) -> None:
        """Cliente solo puede cancelar en BORRADOR (02 §2.2)."""
        if es_cliente and pedido.estado != EstadoPedido.BORRADOR:
            raise DomainError(
                "El cliente solo puede cancelar pedidos en estado BORRADOR"
            )

    @staticmethod
    def verificar_pago_minimo(
        monto_total: Decimal,
        monto_pagado: Decimal,
        tiene_aprobacion_conjunta: bool = False,
    ) -> tuple[bool, Decimal]:
        """
        Verifica regla del 80%.
        Retorna (pago_ok, deuda_activa).
        """
        if monto_pagado >= monto_total:
            return True, Decimal("0")

        porcentaje = monto_pagado / monto_total if monto_total > 0 else Decimal("0")
        if porcentaje >= PORCENTAJE_MINIMO_PAGO and tiene_aprobacion_conjunta:
            return True, monto_total - monto_pagado

        return False, monto_total - monto_pagado

    @staticmethod
    def determinar_tipo_tramo(precio_unitario: Decimal) -> str:
        """
        Clasifica el tramo de precio adicional en OT (HU-INT-03).
        Retorna: 'automatico' | 'tacito' | 'manual'
        """
        if precio_unitario < UMBRAL_APROBACION_AUTOMATICA:
            return "automatico"
        if precio_unitario <= UMBRAL_APROBACION_TACITA:
            return "tacito"
        return "manual"

    @staticmethod
    def comprobante_requiere_validacion(rol_emisor: str) -> bool:
        """
        VENDEDOR SIEMPRE genera PENDIENTE_VALIDACION (07 ABAC-06 corregido).
        ADMINISTRADOR y SUPERADMIN pueden emitir directamente.
        """
        return rol_emisor == "VENDEDOR"

    @staticmethod
    def determinar_tipo_comprobante(
        monto: Decimal, tiene_ruc: bool
    ) -> TipoComprobante:
        """Boleta si monto > S/20 sin RUC; factura si monto > S/60 con RUC."""
        if tiene_ruc and monto > Decimal("60"):
            return TipoComprobante.FACTURA
        if monto > Decimal("20"):
            return TipoComprobante.BOLETA
        return TipoComprobante.TICKET

    @staticmethod
    def reserva_libera_stock(reserva: Reserva) -> bool:
        """Solo ACTIVA y CONFIRMADA descuentan stock (02 §1.3)."""
        from src.pedidos.domain.models.pedido import EstadoReserva
        return reserva.estado in (EstadoReserva.ACTIVA, EstadoReserva.CONFIRMADA)
