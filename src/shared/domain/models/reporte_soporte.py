"""
Entidad ReporteSoporte y enum EstadoReporteSoporte (02 §1.3).
Nunca usar: Ticket, Issue, CasoSoporte.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class EstadoReporteSoporte(str, Enum):
    ABIERTO                = "ABIERTO"
    EN_INVESTIGACION       = "EN_INVESTIGACION"
    RESUELTO               = "RESUELTO"
    CERRADO_SIN_RESOLUCION = "CERRADO_SIN_RESOLUCION"


class ReporteSoporteNoEncontradoError(Exception):
    pass


class TransicionEstadoReporteSoporteInvalidaError(Exception):
    pass


@dataclass
class ReporteSoporte:
    """
    Caso de soporte reportado por un usuario autenticado.
    Vincula acciones de impersonación a un caso concreto (02 §1.3).
    Nunca usar: Ticket, Issue, CasoSoporte.
    """
    usuario_reportante_id: str
    rol_usuario_reportante: str
    descripcion: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    estado: EstadoReporteSoporte = field(default=EstadoReporteSoporte.ABIERTO)
    creado_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resuelto_en: Optional[datetime] = None
    resuelto_por: Optional[str] = None

    def activar_investigacion(self) -> None:
        """ABIERTO → EN_INVESTIGACION al vincular sesión de impersonación (02 §1.3)."""
        if self.estado != EstadoReporteSoporte.ABIERTO:
            raise TransicionEstadoReporteSoporteInvalidaError(
                f"Solo ABIERTO puede pasar a EN_INVESTIGACION; estado actual: {self.estado}"
            )
        self.estado = EstadoReporteSoporte.EN_INVESTIGACION

    def resolver(self, resuelto_por: str) -> None:
        """EN_INVESTIGACION → RESUELTO."""
        if self.estado != EstadoReporteSoporte.EN_INVESTIGACION:
            raise TransicionEstadoReporteSoporteInvalidaError(
                f"Solo EN_INVESTIGACION puede pasar a RESUELTO; estado actual: {self.estado}"
            )
        self.estado = EstadoReporteSoporte.RESUELTO
        self.resuelto_en = datetime.now(timezone.utc)
        self.resuelto_por = resuelto_por

    def cerrar_sin_resolucion(self) -> None:
        """Cierre sin resolución desde cualquier estado activo."""
        if self.estado in (EstadoReporteSoporte.RESUELTO, EstadoReporteSoporte.CERRADO_SIN_RESOLUCION):
            raise TransicionEstadoReporteSoporteInvalidaError(
                f"Reporte ya cerrado; estado actual: {self.estado}"
            )
        self.estado = EstadoReporteSoporte.CERRADO_SIN_RESOLUCION
