"""
Entidad IncidenteSistema (ADR-019) — registro operativo de incidentes/bugs
del sistema, reportado manualmente por ADMINISTRADOR/SUPERADMIN.

No confundir con `ReporteSoporte` (src/shared/domain/models/reporte_soporte.py):
ReporteSoporte es un caso de soporte iniciado por un usuario cualquiera y
vinculado a una sesión de impersonación para investigarlo — sin severidad,
sin persistencia PG (solo InMemory hoy). IncidenteSistema es un registro
operativo propio de ADMIN/SUPERADMIN, con severidad y persistencia real,
sin relación con impersonación.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class SeveridadIncidente(str, Enum):
    BAJA    = "BAJA"
    MEDIA   = "MEDIA"
    ALTA    = "ALTA"
    CRITICA = "CRITICA"


class EstadoIncidente(str, Enum):
    ABIERTO  = "ABIERTO"
    RESUELTO = "RESUELTO"


class IncidenteNoEncontradoError(Exception):
    pass


class IncidenteYaResueltoError(Exception):
    pass


@dataclass
class IncidenteSistema:
    descripcion: str
    severidad: SeveridadIncidente
    reportado_por: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    estado: EstadoIncidente = EstadoIncidente.ABIERTO
    resuelto_por: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resuelto_at: Optional[datetime] = None

    def resolver(self, resuelto_por: str) -> None:
        if self.estado == EstadoIncidente.RESUELTO:
            raise IncidenteYaResueltoError(f"Incidente {self.id} ya está resuelto")
        self.estado = EstadoIncidente.RESUELTO
        self.resuelto_por = resuelto_por
        self.resuelto_at = datetime.now(timezone.utc)
