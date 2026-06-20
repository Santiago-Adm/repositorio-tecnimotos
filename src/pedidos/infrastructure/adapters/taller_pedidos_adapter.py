"""
Implementación de TallerPedidosPort (03 §8.2).
Consumido por taller para verificar cobro antes de cerrar OT.
"""
from __future__ import annotations

from src.pedidos.domain.ports.pedido_repository import PedidoRepository


class TallerPedidosServiceImpl:
    """
    Implementación real de TallerPedidosPort.
    Consulta el repositorio de pedidos para verificar cobro.
    """

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def verificar_cobro_confirmado(self, orden_trabajo_id: str) -> bool:
        pedidos = await self._repo.listar_todos()
        for pedido in pedidos:
            if pedido.ot_id == orden_trabajo_id:
                from src.pedidos.domain.models.pedido import EstadoPedido
                return pedido.estado in (EstadoPedido.CONFIRMADO, EstadoPedido.ENTREGADO)
        return False


class InMemoryTallerPedidosService:
    """
    Fake de TallerPedidosPort para tests de contrato LSP (04 §6.2).
    """

    def __init__(self) -> None:
        self._cobros: dict[str, bool] = {}

    def registrar_cobro(self, orden_trabajo_id: str, confirmado: bool) -> None:
        self._cobros[orden_trabajo_id] = confirmado

    async def verificar_cobro_confirmado(self, orden_trabajo_id: str) -> bool:
        return self._cobros.get(orden_trabajo_id, False)
