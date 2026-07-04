"""
Servicio de dominio: "OT activa" (ADR-015 — glosario formal).
Una OT es activa cuando su estado está en el conjunto configurable de
estados "activos" Y los días transcurridos desde su apertura no superan el
umbral configurable — ambos ajustables por ADMINISTRADOR/SUPERADMIN vía
GET/PATCH /v1/admin/parametros (parametros_sistema: `taller.ot_activa.estados`
y `taller.ot_activa.dias_maximo`). Compartido entre el listado de OTs
(api/routes/taller.py) y las métricas de negocio (api/routes/admin.py) para
no duplicar la regla en dos lugares.
"""
from __future__ import annotations

from datetime import datetime, timezone


class ConfigOtActiva:
    __slots__ = ("estados", "dias_maximo")

    def __init__(self, estados: set[str], dias_maximo: int) -> None:
        self.estados = estados
        self.dias_maximo = dias_maximo


async def obtener_config_ot_activa(parametros_svc) -> ConfigOtActiva:
    estados_resp = await parametros_svc.obtener_parametro("taller.ot_activa.estados")
    dias_resp = await parametros_svc.obtener_parametro("taller.ot_activa.dias_maximo")
    estados = {e.strip() for e in str(estados_resp.valor).split(",") if e.strip()}
    dias_maximo = int(dias_resp.valor)
    return ConfigOtActiva(estados=estados, dias_maximo=dias_maximo)


def es_ot_activa(ot, config: ConfigOtActiva, ahora: datetime | None = None) -> bool:
    ahora = ahora or datetime.now(timezone.utc)
    if ot.estado.value not in config.estados:
        return False
    dias_abierta = (ahora - ot.created_at).days
    return dias_abierta <= config.dias_maximo
