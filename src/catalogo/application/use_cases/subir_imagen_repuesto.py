"""
Caso de uso: subir imagen de repuesto (campo único imagen_url — 03 §5.2 extendido).
Convención de key en R2: repuestos/{codigo}/1.jpg — un repuesto, una imagen,
key fija (no gallery). Ver .doc3/adr-010-imagen-repuesto-campo-unico.md.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from src.catalogo.domain.models.repuesto import RepuestoNoEncontradoError
from src.catalogo.domain.ports.repuesto_repository import RepuestoRepository

logger = logging.getLogger(__name__)


@dataclass
class SubirImagenRepuestoCommand:
    codigo: str
    contenido: bytes
    extension: str
    tipo_contenido: str
    subido_por: str = ""


class SubirImagenRepuestoUseCase:
    """Solo ADMINISTRADOR y SUPERADMIN (aplicado en la capa HTTP)."""

    def __init__(self, repo: RepuestoRepository, storage) -> None:
        self._repo = repo
        self._storage = storage

    async def execute(self, command: SubirImagenRepuestoCommand) -> str:
        repuesto = await self._repo.obtener_por_codigo(command.codigo)
        if repuesto is None:
            raise RepuestoNoEncontradoError(f"Repuesto {command.codigo} no encontrado")

        key = f"repuestos/{command.codigo}/1.{command.extension}"
        url = await self._storage.subir_con_key(command.contenido, key, command.tipo_contenido)

        repuesto.establecer_imagen(url)
        await self._repo.actualizar(repuesto)

        logger.info(
            "Imagen de repuesto actualizada",
            extra={"codigo": command.codigo, "subido_por": command.subido_por},
        )
        return url
