'use client'

interface Props {
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
}

export default function EmptyState({ title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center gap-4 py-16 px-6 text-center">
      <p className="text-lg font-display font-semibold text-slate-300">{title}</p>
      {description && <p className="text-sm text-slate-400 max-w-sm font-body">{description}</p>}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-2 px-4 py-2 rounded-lg bg-teal text-white text-sm font-body hover:bg-teal/90 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
