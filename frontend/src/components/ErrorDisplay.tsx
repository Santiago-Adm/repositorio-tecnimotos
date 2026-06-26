'use client'

const ERROR_MESSAGES: Record<string, string> = {
  REPUESTO_SIN_STOCK: 'Este repuesto no tiene stock disponible ahora.',
  STOCK_INSUFICIENTE: 'Este repuesto no tiene stock disponible ahora.',
  RESERVA_EXPIRADA: 'Tu reserva venció. Puedes crear una nueva.',
  RESERVA_SIN_PAGO_REQUERIDO: 'Esta reserva necesita pago para continuar.',
  COBRO_INSUFICIENTE: 'El pago registrado no cubre el mínimo requerido.',
  APROBACION_REQUERIDA: 'Esta acción espera una aprobación antes de continuar.',
  DISCREPANCIA_STOCK: 'Hay una diferencia entre lo registrado y el stock real — el equipo fue notificado.',
  ACCESO_DENEGADO: 'No tienes acceso a esta acción.',
  VALIDACION_FALLIDA: 'Revisa los datos ingresados.',
  AUTENTICACION_REQUERIDA: 'Correo o contraseña incorrectos.',
  ERROR_INTERNO: 'Ocurrió un error inesperado. Intenta de nuevo.',
  TIMEOUT: 'Sin conexión — intenta de nuevo cuando tengas señal.',
}

interface Props {
  code: string
  onRetry?: () => void
  context?: string
}

export default function ErrorDisplay({ code, onRetry, context }: Props) {
  const message = ERROR_MESSAGES[code] ?? 'Ocurrió un error. Intenta de nuevo.'

  return (
    <div className="rounded-xl border border-red-900/40 bg-red-950/20 p-5 flex flex-col gap-3">
      <p className="text-sm font-body text-red-300">{message}</p>
      {context && <p className="text-xs text-red-400/70 font-body">{context}</p>}
      {onRetry && (
        <button
          onClick={onRetry}
          className="self-start px-4 py-2 rounded-lg bg-red-900/30 text-red-300 text-sm font-body hover:bg-red-900/50 transition-colors"
        >
          Reintentar
        </button>
      )}
    </div>
  )
}
