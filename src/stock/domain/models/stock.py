"""
Entidades del dominio stock (02 §1.3, §2.1).
Sin imports de FastAPI, SQLAlchemy ni Redis.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


# ── Errores de dominio ────────────────────────────────────────────────────────

class DomainError(Exception):
    pass


class StockInsuficienteError(DomainError):
    pass


class StockNoEncontradoError(DomainError):
    pass


class ReabastecimientoNoEncontradoError(DomainError):
    pass


class TransicionEstadoInvalidaError(DomainError):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class EstadoReabastecimiento(str, Enum):
    SOLICITADO           = "SOLICITADO"
    CONFIRMADO_PROVEEDOR = "CONFIRMADO_PROVEEDOR"
    EN_TRANSITO          = "EN_TRANSITO"
    RECIBIDO             = "RECIBIDO"
    CANCELADO            = "CANCELADO"


class TipoMovimiento(str, Enum):
    ENTRADA_REABASTECIMIENTO = "ENTRADA_REABASTECIMIENTO"
    SALIDA_VENTA             = "SALIDA_VENTA"
    SALIDA_TALLER            = "SALIDA_TALLER"
    AJUSTE_MANUAL            = "AJUSTE_MANUAL"
    RESERVA                  = "RESERVA"
    LIBERACION_RESERVA       = "LIBERACION_RESERVA"


# ── Entidades de valor ────────────────────────────────────────────────────────

@dataclass
class MovimientoStock:
    repuesto_id: str
    tipo_movimiento: TipoMovimiento
    cantidad: int
    estado_origen: str
    estado_destino: str
    actor_id: str
    referencia_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise DomainError("cantidad del movimiento debe ser > 0")


@dataclass
class ReabastecimientoItem:
    repuesto_id: str
    codigo: str
    cantidad_solicitada: int
    precio_costo_unitario: Decimal
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cantidad_recibida: int = 0

    def __post_init__(self) -> None:
        if self.cantidad_solicitada <= 0:
            raise DomainError("cantidad_solicitada debe ser > 0")
        if self.precio_costo_unitario <= Decimal("0"):
            raise DomainError("precio_costo_unitario debe ser > 0")


# ── Agregados ─────────────────────────────────────────────────────────────────

@dataclass
class StockRepuesto:
    """
    Agregado raíz del módulo stock.
    Representa el estado de stock de un repuesto en tres cantidades.
    Invariante crítica: cantidad_disponible >= 0 siempre (02 §2.1).
    """
    repuesto_id: str
    codigo: str
    cantidad_disponible: int = 0
    cantidad_apartada: int = 0
    cantidad_en_transito: int = 0
    umbral_minimo: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    movimientos: list[MovimientoStock] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validar_invariantes()

    def _validar_invariantes(self) -> None:
        if self.cantidad_disponible < 0:
            raise DomainError(
                f"Stock {self.codigo}: cantidad_disponible no puede ser negativa"
            )
        if self.cantidad_apartada < 0:
            raise DomainError(
                f"Stock {self.codigo}: cantidad_apartada no puede ser negativa"
            )

    def stock_total(self) -> int:
        return self.cantidad_disponible + self.cantidad_apartada + self.cantidad_en_transito

    def esta_agotado(self) -> bool:
        return self.cantidad_disponible == 0

    def esta_bajo_umbral(self) -> bool:
        return self.umbral_minimo > 0 and self.cantidad_disponible <= self.umbral_minimo

    def registrar_entrada(
        self,
        cantidad: int,
        actor_id: str,
        referencia_id: str = "",
    ) -> MovimientoStock:
        if cantidad <= 0:
            raise DomainError("cantidad de entrada debe ser > 0")
        self.cantidad_disponible += cantidad
        mov = MovimientoStock(
            repuesto_id=self.repuesto_id,
            tipo_movimiento=TipoMovimiento.ENTRADA_REABASTECIMIENTO,
            cantidad=cantidad,
            estado_origen="en_transito",
            estado_destino="disponible",
            actor_id=actor_id,
            referencia_id=referencia_id,
        )
        self.movimientos.append(mov)
        return mov

    def apartar(
        self,
        cantidad: int,
        actor_id: str,
        referencia_id: str = "",
    ) -> MovimientoStock:
        if cantidad <= 0:
            raise DomainError("cantidad a apartar debe ser > 0")
        if self.cantidad_disponible < cantidad:
            raise StockInsuficienteError(
                f"Stock insuficiente para {self.codigo}: "
                f"disponible={self.cantidad_disponible}, solicitado={cantidad}"
            )
        self.cantidad_disponible -= cantidad
        self.cantidad_apartada += cantidad
        mov = MovimientoStock(
            repuesto_id=self.repuesto_id,
            tipo_movimiento=TipoMovimiento.RESERVA,
            cantidad=cantidad,
            estado_origen="disponible",
            estado_destino="apartado",
            actor_id=actor_id,
            referencia_id=referencia_id,
        )
        self.movimientos.append(mov)
        self._validar_invariantes()
        return mov

    def liberar_apartado(
        self,
        cantidad: int,
        actor_id: str,
        referencia_id: str = "",
    ) -> MovimientoStock:
        if cantidad <= 0:
            raise DomainError("cantidad a liberar debe ser > 0")
        if self.cantidad_apartada < cantidad:
            raise DomainError(
                f"No hay suficiente stock apartado para {self.codigo}: "
                f"apartado={self.cantidad_apartada}, solicitado={cantidad}"
            )
        self.cantidad_apartada -= cantidad
        self.cantidad_disponible += cantidad
        mov = MovimientoStock(
            repuesto_id=self.repuesto_id,
            tipo_movimiento=TipoMovimiento.LIBERACION_RESERVA,
            cantidad=cantidad,
            estado_origen="apartado",
            estado_destino="disponible",
            actor_id=actor_id,
            referencia_id=referencia_id,
        )
        self.movimientos.append(mov)
        return mov

    def descontar_venta(
        self,
        cantidad: int,
        actor_id: str,
        tipo: TipoMovimiento = TipoMovimiento.SALIDA_VENTA,
        referencia_id: str = "",
    ) -> MovimientoStock:
        """Descuento directo de disponible — venta mostrador o ajuste."""
        if cantidad <= 0:
            raise DomainError("cantidad a descontar debe ser > 0")
        if self.cantidad_disponible < cantidad:
            raise StockInsuficienteError(
                f"Stock insuficiente para {self.codigo}: "
                f"disponible={self.cantidad_disponible}, solicitado={cantidad}"
            )
        self.cantidad_disponible -= cantidad
        mov = MovimientoStock(
            repuesto_id=self.repuesto_id,
            tipo_movimiento=tipo,
            cantidad=cantidad,
            estado_origen="disponible",
            estado_destino="descontado",
            actor_id=actor_id,
            referencia_id=referencia_id,
        )
        self.movimientos.append(mov)
        self._validar_invariantes()
        return mov

    def descontar_apartado_taller(
        self,
        cantidad: int,
        actor_id: str,
        referencia_id: str = "",
    ) -> MovimientoStock:
        """Descuento de apartado al cierre de orden_trabajo (02 §3.2)."""
        if cantidad <= 0:
            raise DomainError("cantidad a descontar debe ser > 0")
        if self.cantidad_apartada < cantidad:
            raise StockInsuficienteError(
                f"Stock apartado insuficiente para {self.codigo}: "
                f"apartado={self.cantidad_apartada}, solicitado={cantidad}"
            )
        self.cantidad_apartada -= cantidad
        mov = MovimientoStock(
            repuesto_id=self.repuesto_id,
            tipo_movimiento=TipoMovimiento.SALIDA_TALLER,
            cantidad=cantidad,
            estado_origen="apartado",
            estado_destino="consumido",
            actor_id=actor_id,
            referencia_id=referencia_id,
        )
        self.movimientos.append(mov)
        return mov

    def ajustar_umbral(self, nuevo_umbral: int) -> None:
        if nuevo_umbral < 0:
            raise DomainError("umbral_minimo no puede ser negativo")
        self.umbral_minimo = nuevo_umbral


@dataclass
class Reabastecimiento:
    """
    Ciclo de vida de solicitud de reabastecimiento a proveedor (02 §1.3).
    Cinco estados: SOLICITADO → CONFIRMADO_PROVEEDOR → EN_TRANSITO → RECIBIDO | CANCELADO.
    """
    proveedor: str
    solicitado_por: str
    items: list[ReabastecimientoItem] = field(default_factory=list)
    estado: EstadoReabastecimiento = EstadoReabastecimiento.SOLICITADO
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    notas: str = ""
    precio_costo_anterior: Optional[Decimal] = None

    _TRANSICIONES_VALIDAS: dict[EstadoReabastecimiento, list[EstadoReabastecimiento]] = field(
        default_factory=lambda: {
            EstadoReabastecimiento.SOLICITADO: [
                EstadoReabastecimiento.CONFIRMADO_PROVEEDOR,
                EstadoReabastecimiento.CANCELADO,
            ],
            EstadoReabastecimiento.CONFIRMADO_PROVEEDOR: [
                EstadoReabastecimiento.EN_TRANSITO,
                EstadoReabastecimiento.CANCELADO,
            ],
            EstadoReabastecimiento.EN_TRANSITO: [
                EstadoReabastecimiento.RECIBIDO,
            ],
            EstadoReabastecimiento.RECIBIDO: [],
            EstadoReabastecimiento.CANCELADO: [],
        },
        init=False,
    )

    def __post_init__(self) -> None:
        if not self.proveedor.strip():
            raise DomainError("proveedor no puede estar vacío")

    def avanzar_estado(self, nuevo_estado: EstadoReabastecimiento) -> None:
        permitidos = self._TRANSICIONES_VALIDAS.get(self.estado, [])
        if nuevo_estado not in permitidos:
            raise TransicionEstadoInvalidaError(
                f"Transición inválida: {self.estado.value} → {nuevo_estado.value}"
            )
        self.estado = nuevo_estado

    def agregar_item(self, item: ReabastecimientoItem) -> None:
        if self.estado != EstadoReabastecimiento.SOLICITADO:
            raise DomainError("Solo se pueden agregar ítems en estado SOLICITADO")
        self.items.append(item)

    def esta_recibido(self) -> bool:
        return self.estado == EstadoReabastecimiento.RECIBIDO

    def esta_cancelado(self) -> bool:
        return self.estado == EstadoReabastecimiento.CANCELADO
