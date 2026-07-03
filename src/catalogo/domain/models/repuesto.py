"""
Entidad Repuesto y enums de dominio (02 §1.1, §1.3, §1.5).
Nunca usar: Producto, Item, Articulo, Pieza, Componente, Material.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


class UniversoRepuesto(str, Enum):
    MOTOLINEAL = "motolineal"
    MOTOTAXI_3R = "mototaxi_3r"
    MOTOTAXI_4R = "mototaxi_4r"


class EstadoStockUnidad(str, Enum):
    DISPONIBLE = "disponible"
    APARTADO = "apartado"
    EN_TRANSITO = "en_transito"


class CategoriaRepuesto(str, Enum):
    MOTOR = "motor"
    TRANSMISION = "transmision"
    FRENOS = "frenos"
    ELECTRICO = "electrico"
    CARROCERIA = "carroceria"
    SUSPENSION = "suspension"
    TECNICO_ESPECIALIZADO = "tecnico_especializado"
    CONSUMIBLE = "consumible"
    OTRO = "otro"


class DomainError(Exception):
    pass


class RepuestoNoEncontradoError(DomainError):
    pass


class RepuestoDadoDeBajaError(DomainError):
    pass


class PrecioInvalidoError(DomainError):
    pass


@dataclass
class HistorialPrecio:
    precio_anterior: Decimal
    precio_nuevo: Decimal
    modificado_por: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Repuesto:
    """
    Registro maestro de repuesto del catálogo.
    Un repuesto de universo mototaxi NUNCA aparece en resultados de motolineal (02 §1.5).
    """
    codigo: str
    nombre: str
    universo: UniversoRepuesto
    modelo: str
    año: Optional[int]
    categoria: CategoriaRepuesto
    precio_venta: Decimal
    descripcion: str = ""
    activo: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    eliminado_en: Optional[datetime] = None
    historial_precio: list[HistorialPrecio] = field(default_factory=list)
    imagen_url: Optional[str] = None
    destacado: bool = False

    def __post_init__(self) -> None:
        if self.precio_venta <= Decimal("0"):
            raise PrecioInvalidoError(
                f"precio_venta debe ser mayor a 0, recibido: {self.precio_venta}"
            )
        if self.año is not None and not (1990 <= self.año <= 2100):
            raise DomainError(f"año debe estar entre 1990 y 2100, recibido: {self.año}")

    def actualizar_precio(self, nuevo_precio: Decimal, modificado_por: str) -> HistorialPrecio:
        """Actualiza precio y registra historial. Precio siempre manual (RNN-01)."""
        if nuevo_precio <= Decimal("0"):
            raise PrecioInvalidoError(
                f"precio_venta debe ser mayor a 0, recibido: {nuevo_precio}"
            )
        entrada = HistorialPrecio(
            precio_anterior=self.precio_venta,
            precio_nuevo=nuevo_precio,
            modificado_por=modificado_por,
        )
        self.historial_precio.append(entrada)
        self.precio_venta = nuevo_precio
        self.updated_at = datetime.now(timezone.utc)
        return entrada

    def actualizar_datos(
        self,
        nombre: Optional[str] = None,
        descripcion: Optional[str] = None,
        categoria: Optional["CategoriaRepuesto"] = None,
        modelo: Optional[str] = None,
        año: Optional[int] = None,
    ) -> None:
        """Actualiza campos descriptivos. Nunca toca precio_venta ni dispara eventos."""
        if nombre is not None:
            self.nombre = nombre
        if descripcion is not None:
            self.descripcion = descripcion
        if categoria is not None:
            self.categoria = categoria
        if modelo is not None:
            self.modelo = modelo
        if año is not None:
            if not (1990 <= año <= 2100):
                raise DomainError(f"año debe estar entre 1990 y 2100, recibido: {año}")
            self.año = año
        self.updated_at = datetime.now(timezone.utc)

    def establecer_imagen(self, url: str) -> None:
        """Reemplaza la imagen del repuesto (convención de key fija — siempre 1 imagen)."""
        self.imagen_url = url
        self.updated_at = datetime.now(timezone.utc)

    def marcar_destacado(self, valor: bool) -> None:
        """Selección editorial manual para la landing pública — nunca automática."""
        self.destacado = valor
        self.updated_at = datetime.now(timezone.utc)

    def dar_de_baja(self, motivo: str) -> None:
        """Baja lógica — el repuesto no se elimina físicamente (EP-CAT-05)."""
        self.activo = False
        self.eliminado_en = datetime.now(timezone.utc)
        self.updated_at = self.eliminado_en

    def es_tecnico_especializado(self) -> bool:
        return self.categoria == CategoriaRepuesto.TECNICO_ESPECIALIZADO

    def requiere_advertencia_instalacion(self) -> bool:
        return self.es_tecnico_especializado()
