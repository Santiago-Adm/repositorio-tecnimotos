"""
ParametrosRepositoryPG — implementa ParametrosSistemaPort contra la tabla
real `parametros_sistema` (ADR-015). Tabla migrada desde el inicio
(`2c9eda3438e9_initial_schema_33_tablas.py`) pero nunca conectada — hasta
esta sesión todo pasaba por InMemoryParametrosService sin persistencia.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Registra UsuarioModel en el metadata compartido (Base) antes de que
# ParametrosSistemaModel intente resolver el FK modificado_por → usuario.id
# (mismo patrón que stock_repository_pg.py con RepuestoModel).
import src.shared.infrastructure.models.usuario_model  # noqa: F401

from src.shared.domain.parametros_port import ParametroNoEncontradoError, ParametroResponse
from src.shared.infrastructure.models.sistema_model import ParametrosSistemaModel

_TIPOS: dict[type, str] = {bool: "bool", int: "int", float: "float", str: "str"}


def _serializar(valor: Any) -> tuple[str, str]:
    if isinstance(valor, bool):
        return ("true" if valor else "false"), "bool"
    if isinstance(valor, int):
        return str(valor), "int"
    if isinstance(valor, float):
        return str(valor), "float"
    return str(valor), "str"


def _deserializar(valor: str, tipo_valor: str) -> Any:
    if tipo_valor == "bool":
        return valor.strip().lower() == "true"
    if tipo_valor == "int":
        return int(valor)
    if tipo_valor == "float":
        return float(valor)
    return valor


class ParametrosRepositoryPG:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def obtener_parametro(self, clave: str) -> ParametroResponse:
        model = await self._buscar(clave)
        if model is None:
            raise ParametroNoEncontradoError(f"Parámetro {clave!r} no encontrado")
        return self._to_response(model)

    async def listar(self) -> list[ParametroResponse]:
        stmt = select(ParametrosSistemaModel).order_by(ParametrosSistemaModel.modulo, ParametrosSistemaModel.clave)
        result = await self._session.execute(stmt)
        return [self._to_response(m) for m in result.scalars().all()]

    async def establecer(self, clave: str, valor: Any) -> ParametroResponse:
        model = await self._buscar(clave)
        if model is None:
            raise ParametroNoEncontradoError(f"Parámetro {clave!r} no encontrado")
        valor_str, tipo_valor = _serializar(valor)
        model.valor = valor_str
        model.tipo_valor = tipo_valor
        await self._session.flush()
        return self._to_response(model)

    async def _buscar(self, clave: str) -> ParametrosSistemaModel | None:
        stmt = select(ParametrosSistemaModel).where(ParametrosSistemaModel.clave == clave)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def _to_response(self, model: ParametrosSistemaModel) -> ParametroResponse:
        return ParametroResponse(
            clave=model.clave,
            valor=_deserializar(model.valor, model.tipo_valor),
            desde_cache=False,
            modificable_por=model.modificable_por,
        )
