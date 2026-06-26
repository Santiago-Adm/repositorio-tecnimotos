"""
Casos de uso para ReporteSoporte — HU-INT-08 (02 §5.1).
"""
from __future__ import annotations

import logging

from src.shared.domain.models.reporte_soporte import (
    ReporteSoporte,
    ReporteSoporteNoEncontradoError,
)
from src.shared.domain.ports.reporte_soporte_repository import ReporteSoporteRepository

logger = logging.getLogger(__name__)


class SoporteService:
    def __init__(self, repo: ReporteSoporteRepository) -> None:
        self._repo = repo

    async def crear_reporte(
        self,
        usuario_reportante_id: str,
        rol_usuario_reportante: str,
        descripcion: str,
    ) -> ReporteSoporte:
        reporte = ReporteSoporte(
            usuario_reportante_id=usuario_reportante_id,
            rol_usuario_reportante=rol_usuario_reportante,
            descripcion=descripcion,
        )
        await self._repo.guardar(reporte)
        logger.info(
            "reporte_soporte.creado",
            extra={
                "reporte_id": reporte.id,
                "usuario": usuario_reportante_id,
                "rol": rol_usuario_reportante,
            },
        )
        return reporte

    async def listar_reportes_activos(self) -> list[ReporteSoporte]:
        return await self._repo.listar_activos()

    async def activar_investigacion(self, reporte_soporte_id: str) -> ReporteSoporte:
        """
        ABIERTO → EN_INVESTIGACION al vincular sesión de impersonación.
        Llamado por el endpoint de impersonación (DEP-10-001 — no construido aún).
        """
        reporte = await self._repo.obtener_por_id(reporte_soporte_id)
        if reporte is None:
            raise ReporteSoporteNoEncontradoError(reporte_soporte_id)
        reporte.activar_investigacion()
        await self._repo.guardar(reporte)
        logger.info(
            "reporte_soporte.en_investigacion",
            extra={"reporte_id": reporte.id},
        )
        return reporte
