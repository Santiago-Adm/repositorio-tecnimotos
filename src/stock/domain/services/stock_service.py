"""
Reglas de negocio puras del módulo stock (02 §2.1).
Sin imports de FastAPI, SQLAlchemy ni Redis.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.stock.domain.models.stock import (
    DomainError,
    Reabastecimiento,
    ReabastecimientoItem,
    StockInsuficienteError,
    StockRepuesto,
    TipoMovimiento,
)


class StockService:

    @staticmethod
    def validar_no_negativo(stock: StockRepuesto) -> None:
        """Invariante crítica: disponible nunca negativo (02 §2.1)."""
        if stock.cantidad_disponible < 0:
            raise DomainError(
                f"Violación de invariante: {stock.codigo} disponible < 0"
            )

    @staticmethod
    def verificar_disponibilidad(stock: StockRepuesto, cantidad: int) -> bool:
        return stock.cantidad_disponible >= cantidad

    @staticmethod
    def detectar_eventos_necesarios(
        stock_antes: StockRepuesto,
        stock_despues: StockRepuesto,
    ) -> list[str]:
        """
        Determina qué eventos de dominio publicar tras una operación.
        Retorna lista de tipos de evento.
        """
        eventos: list[str] = []

        estaba_agotado = stock_antes.esta_agotado()
        esta_agotado = stock_despues.esta_agotado()

        if not estaba_agotado and esta_agotado:
            eventos.append("stock.agotado")

        if estaba_agotado and not esta_agotado:
            eventos.append("stock.disponible")

        if (
            not estaba_agotado
            and not esta_agotado
            and stock_despues.esta_bajo_umbral()
            and not stock_antes.esta_bajo_umbral()
        ):
            eventos.append("stock.bajo_umbral")

        return eventos

    @staticmethod
    def calcular_alerta_margen(
        precio_costo_anterior: Optional[Decimal],
        precio_costo_nuevo: Decimal,
        umbral_porcentual: Decimal = Decimal("0.10"),
    ) -> bool:
        """Retorna True si la variación de precio supera el umbral (02 §3.2)."""
        if precio_costo_anterior is None or precio_costo_anterior == Decimal("0"):
            return False
        variacion = abs(precio_costo_nuevo - precio_costo_anterior) / precio_costo_anterior
        return variacion > umbral_porcentual

    @staticmethod
    def validar_descuento_atomico(
        stocks: list[StockRepuesto],
        descuentos: dict[str, int],
    ) -> None:
        """
        Verifica que todos los descuentos son posibles ANTES de ejecutar ninguno.
        Si alguno falla → rollback completo (02 §3.2 regla crítica).
        """
        for stock in stocks:
            cantidad = descuentos.get(stock.repuesto_id, 0)
            if cantidad > 0 and stock.cantidad_disponible < cantidad:
                raise StockInsuficienteError(
                    f"Stock insuficiente para descuento atómico: "
                    f"{stock.codigo} disponible={stock.cantidad_disponible}, "
                    f"requerido={cantidad}"
                )
