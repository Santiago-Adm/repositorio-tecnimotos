"""
Casos de uso para galería de imágenes de repuesto.
  - SubirImagenUseCase      (EP-CAT-08)
  - EliminarImagenUseCase   (EP-CAT-09)
  - ReemplazarImagenUseCase (EP-CAT-11)
  - ReordenarImagenesUseCase (EP-CAT-12)
  - ListarImagenesUseCase   (uso interno por EP-CAT-01/EP-CAT-02)
"""
from __future__ import annotations

from dataclasses import dataclass

from src.catalogo.domain.models.imagen_repuesto import ImagenRepuesto
from src.catalogo.domain.models.repuesto import RepuestoNoEncontradoError
from src.catalogo.domain.ports.imagen_repuesto_repository import ImagenRepuestoRepository
from src.catalogo.domain.ports.imagen_storage_port import ImagenStoragePort
from src.catalogo.domain.ports.repuesto_repository import RepuestoRepository


class ImagenNoEncontradaError(Exception):
    pass


class ImagenNoPertenecerAlRepuestoError(Exception):
    pass


@dataclass
class SubirImagenCommand:
    codigo_repuesto: str
    contenido: bytes
    nombre_archivo: str
    tipo_contenido: str
    subido_por: str


@dataclass
class EliminarImagenCommand:
    codigo_repuesto: str
    imagen_id: str
    eliminado_por: str


class SubirImagenUseCase:
    def __init__(
        self,
        repuesto_repo: RepuestoRepository,
        imagen_repo: ImagenRepuestoRepository,
        storage: ImagenStoragePort,
    ) -> None:
        self._repuesto_repo = repuesto_repo
        self._imagen_repo = imagen_repo
        self._storage = storage

    async def execute(self, cmd: SubirImagenCommand) -> ImagenRepuesto:
        repuesto = await self._repuesto_repo.obtener_por_codigo(cmd.codigo_repuesto)
        if repuesto is None:
            raise RepuestoNoEncontradoError(f"Repuesto {cmd.codigo_repuesto!r} no encontrado")

        url = await self._storage.subir(cmd.contenido, cmd.nombre_archivo, cmd.tipo_contenido)
        orden = await self._imagen_repo.siguiente_orden(repuesto.id)
        imagen = ImagenRepuesto(
            repuesto_id=repuesto.id,
            url=url,
            orden=orden,
            subido_por=cmd.subido_por,
        )
        return await self._imagen_repo.guardar(imagen)


class EliminarImagenUseCase:
    def __init__(
        self,
        repuesto_repo: RepuestoRepository,
        imagen_repo: ImagenRepuestoRepository,
        storage: ImagenStoragePort,
    ) -> None:
        self._repuesto_repo = repuesto_repo
        self._imagen_repo = imagen_repo
        self._storage = storage

    async def execute(self, cmd: EliminarImagenCommand) -> None:
        repuesto = await self._repuesto_repo.obtener_por_codigo(cmd.codigo_repuesto)
        if repuesto is None:
            raise RepuestoNoEncontradoError(f"Repuesto {cmd.codigo_repuesto!r} no encontrado")

        imagen = await self._imagen_repo.obtener_por_id(cmd.imagen_id)
        if imagen is None:
            raise ImagenNoEncontradaError(f"Imagen {cmd.imagen_id!r} no encontrada")
        if imagen.repuesto_id != repuesto.id:
            raise ImagenNoPertenecerAlRepuestoError(
                f"La imagen {cmd.imagen_id!r} no pertenece al repuesto {cmd.codigo_repuesto!r}"
            )

        await self._storage.eliminar(imagen.url)
        await self._imagen_repo.eliminar(cmd.imagen_id)


class ReordenInvalidoError(Exception):
    pass


@dataclass
class ReemplazarImagenCommand:
    codigo_repuesto: str
    imagen_id: str
    contenido: bytes
    nombre_archivo: str
    tipo_contenido: str
    reemplazado_por: str


@dataclass
class ReordenarImagenesCommand:
    codigo_repuesto: str
    nuevo_orden: list[str]  # lista completa de imagen_ids en el orden deseado
    reordenado_por: str


class ReemplazarImagenUseCase:
    """EP-CAT-11: reemplaza la referencia R2 de una imagen sin cambiar su id/orden/repuesto_id.
    Orden de operaciones: subir nueva → actualizar registro → eliminar objeto anterior.
    La key de R2 se regenera (nuevo UUID) porque el puerto subir() no admite key fija."""

    def __init__(
        self,
        repuesto_repo: RepuestoRepository,
        imagen_repo: ImagenRepuestoRepository,
        storage: ImagenStoragePort,
    ) -> None:
        self._repuesto_repo = repuesto_repo
        self._imagen_repo = imagen_repo
        self._storage = storage

    async def execute(self, cmd: ReemplazarImagenCommand) -> ImagenRepuesto:
        repuesto = await self._repuesto_repo.obtener_por_codigo(cmd.codigo_repuesto)
        if repuesto is None:
            raise RepuestoNoEncontradoError(f"Repuesto {cmd.codigo_repuesto!r} no encontrado")

        imagen = await self._imagen_repo.obtener_por_id(cmd.imagen_id)
        if imagen is None:
            raise ImagenNoEncontradaError(f"Imagen {cmd.imagen_id!r} no encontrada")
        if imagen.repuesto_id != repuesto.id:
            raise ImagenNoPertenecerAlRepuestoError(
                f"La imagen {cmd.imagen_id!r} no pertenece al repuesto {cmd.codigo_repuesto!r}"
            )

        url_anterior = imagen.url

        # 1. Subir nuevo archivo — genera nueva key en R2
        nueva_url = await self._storage.subir(cmd.contenido, cmd.nombre_archivo, cmd.tipo_contenido)

        # 2. Actualizar registro — mismo id, mismo orden, nueva URL
        imagen.reemplazar_url(nueva_url)
        await self._imagen_repo.actualizar(imagen)

        # 3. Solo tras confirmar actualización, eliminar objeto anterior de R2
        await self._storage.eliminar(url_anterior)

        return imagen


class ReordenarImagenesUseCase:
    """EP-CAT-12: aplica un nuevo orden completo a las imágenes de un repuesto.
    Validación estricta: la lista recibida debe contener exactamente los IDs existentes."""

    def __init__(
        self,
        repuesto_repo: RepuestoRepository,
        imagen_repo: ImagenRepuestoRepository,
    ) -> None:
        self._repuesto_repo = repuesto_repo
        self._imagen_repo = imagen_repo

    async def execute(self, cmd: ReordenarImagenesCommand) -> list[ImagenRepuesto]:
        repuesto = await self._repuesto_repo.obtener_por_codigo(cmd.codigo_repuesto)
        if repuesto is None:
            raise RepuestoNoEncontradoError(f"Repuesto {cmd.codigo_repuesto!r} no encontrado")

        imagenes = await self._imagen_repo.listar_por_repuesto(repuesto.id)
        ids_en_db = {img.id for img in imagenes}
        ids_en_request = set(cmd.nuevo_orden)

        ids_foraneos = ids_en_request - ids_en_db
        ids_faltantes = ids_en_db - ids_en_request

        if ids_foraneos or ids_faltantes:
            detalles = []
            if ids_faltantes:
                detalles.append(f"IDs faltantes en la lista recibida: {sorted(ids_faltantes)}")
            if ids_foraneos:
                detalles.append(f"IDs no pertenecen a este repuesto: {sorted(ids_foraneos)}")
            raise ReordenInvalidoError("; ".join(detalles))

        actualizaciones = [
            (imagen_id, posicion) for posicion, imagen_id in enumerate(cmd.nuevo_orden)
        ]
        await self._imagen_repo.reordenar_imagenes(actualizaciones)

        return await self._imagen_repo.listar_por_repuesto(repuesto.id)


class ListarImagenesUseCase:
    def __init__(self, imagen_repo: ImagenRepuestoRepository) -> None:
        self._imagen_repo = imagen_repo

    async def execute(self, repuesto_id: str) -> list[ImagenRepuesto]:
        return await self._imagen_repo.listar_por_repuesto(repuesto_id)
