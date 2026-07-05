export interface ItemPedido {
  repuesto_id: string
  codigo: string
  cantidad: number
  precio_unitario: string
  subtotal: string
}

export interface Pedido {
  pedido_id: string
  estado: string
  canal_origen: string
  cliente_id: string | null
  monto_total: string
  monto_efectivo: string
  items: ItemPedido[]
  created_at: string
}

const ESTADO_BADGE: Record<string, string> = {
  BORRADOR: 'bg-slate-700 text-slate-300',
  CONFIRMADO: 'bg-teal/20 text-teal',
  EN_PREPARACION: 'bg-electric/20 text-electric',
  DESPACHADO: 'bg-electric/20 text-electric',
  ENTREGADO: 'bg-teal/20 text-teal',
  INCIDENCIA: 'bg-red-900/30 text-red-400',
  CANCELADO: 'bg-red-900/30 text-red-400',
}

function formatearFecha(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' })
  } catch {
    return iso
  }
}

export default function PedidoCard({ pedido, extra }: { pedido: Pedido; extra?: React.ReactNode }) {
  return (
    <div className="rounded-xl bg-slate-800 border border-slate-700 p-4 space-y-2 hover:border-teal/50 hover:shadow-[0_0_20px_rgba(13,148,136,0.15)] hover:-translate-y-0.5 transition-all duration-300">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-mono text-slate-200 truncate max-w-[220px]">{pedido.pedido_id}</p>
          <p className="text-xs text-slate-400 font-body">{formatearFecha(pedido.created_at)} · {pedido.canal_origen}</p>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-body ${ESTADO_BADGE[pedido.estado] ?? 'bg-slate-700 text-slate-400'}`}>
          {pedido.estado}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-400 font-body">
          {pedido.items.length} {pedido.items.length === 1 ? 'repuesto' : 'repuestos'}
        </p>
        <span className="text-sm font-mono font-semibold text-teal">
          S/. {Number(pedido.monto_total).toFixed(2)}
        </span>
      </div>
      {extra}
    </div>
  )
}
