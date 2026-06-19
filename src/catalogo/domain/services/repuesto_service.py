"""
Reglas de negocio puras del catálogo (02 §2.1).
Sin imports de FastAPI, SQLAlchemy ni Redis.
"""
from __future__ import annotations

from decimal import Decimal

from src.catalogo.domain.models.repuesto import (
    DomainError,
    Repuesto,
    RepuestoDadoDeBajaError,
    RepuestoNoEncontradoError,
    UniversoRepuesto,
)


class RepuestoService:
    """
    Reglas de negocio del catálogo.
    No accede a base de datos ni a red — es puro dominio.
    """

    @staticmethod
    def validar_separacion_universo(
        repuesto: Repuesto,
        universo_solicitado: UniversoRepuesto,
    ) -> None:
        """
        Un repuesto de universo mototaxi nunca aparece en resultados
        de universo motolineal y viceversa (02 §1.5, RNN-05).
        """
        if repuesto.universo != universo_solicitado:
            raise DomainError(
                f"Repuesto {repuesto.codigo} pertenece a universo "
                f"{repuesto.universo.value}, no a {universo_solicitado.value}"
            )

    @staticmethod
    def validar_activo(repuesto: Repuesto) -> None:
        if not repuesto.activo:
            raise RepuestoDadoDeBajaError(
                f"Repuesto {repuesto.codigo} está dado de baja"
            )

    @staticmethod
    def calcular_visibilidad_precio(
        consultas_realizadas: int,
        max_consultas: int,
        es_cliente: bool,
        nivel_visibilidad: int = 0,
    ) -> tuple[bool, str | None]:
        """
        Calcula si el precio es visible para un cliente (02 §4.2).
        Retorna (precio_visible, mensaje_limite_si_aplica).
        Nivel 0: visitante sin cuenta → siempre False.
        Nivel 1: cliente autenticado → depende del contador.
        Nivel 2: autorización manual activa → siempre True.
        """
        if nivel_visibilidad == 2:
            return True, None
        if not es_cliente or nivel_visibilidad == 0:
            return False, None
        if consultas_realizadas >= max_consultas:
            return False, "Para ver más precios visítanos en tienda o contáctanos"
        return True, None

    @staticmethod
    def verificar_puede_dar_de_baja(repuesto: Repuesto) -> None:
        if not repuesto.activo:
            raise DomainError(
                f"Repuesto {repuesto.codigo} ya está dado de baja"
            )
