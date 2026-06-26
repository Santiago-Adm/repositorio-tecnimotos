'use client'

interface Props {
  message?: string
  fullScreen?: boolean
}

export default function LoadingIndicator({ message, fullScreen = false }: Props) {
  const inner = (
    <div className="flex flex-col items-center gap-3 py-8">
      <div className="w-8 h-8 rounded-full border-4 border-teal border-t-transparent animate-spin" />
      {message && <p className="text-sm text-slate-400 font-body">{message}</p>}
    </div>
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface-dark/80">
        {inner}
      </div>
    )
  }

  return inner
}
