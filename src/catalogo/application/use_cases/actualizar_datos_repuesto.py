"""
Caso de uso: actualizar datos descriptivos de repuesto (EP-CAT-10).
Separado deliberadamente de ActualizarPrecioVentaUseCase para que
una corrección de texto nunca dispare repuesto.precio_actualizado.
Campos editables: nombre, descripcion, categoria, modelo, año.
Campos NO editables aquí: codigo (identificador canónico), universo,
precio_venta (exclusivo de EP-CAT-04).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    RepuestoDadoDeBajaError,
    RepuestoNoEncontradoError,
)
from src.catalogo.domain.ports.repuesto_repository import RepuestoRepository
from src.catalogo.domain.services.repuesto_service import RepuestoService


@dataclass
class ActualizarDatosCommand:
    codigo: str
    modificado_por: str
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[CategoriaRepuesto] = None
    modelo: Optional[str] = None
    año: Optional[int] = None
    destacado: Optional[bool] = None


class ActualizarDatosRepuestoUseCase:
    """
    EP-CAT-10: PATCH /v1/repuestos/{codigo}
    Solo ADMINISTRADOR y SUPERADMIN.
    No publica ningún evento — no hay efecto lateral de precio.
    """

    def __init__(self, repo: RepuestoRepository) -> None:
        self._repo = repo

    async def execute(self, command: ActualizarDatosCommand) -> Repuesto:
        repuesto = await self._repo.obtener_por_codigo(command.codigo)
        if repuesto is None:
            raise RepuestoNoEncontradoError(
                f"Repuesto con código {command.codigo!r} no encontrado"
            )
        RepuestoService.validar_activo(repuesto)

        repuesto.actualizar_datos(
            nombre=command.nombre,
            descripcion=command.descripcion,
            categoria=command.categoria,
            modelo=command.modelo,
            año=command.año,
        )
        if command.destacado is not None:
            repuesto.marcar_destacado(command.destacado)
        return await self._repo.actualizar(repuesto)
