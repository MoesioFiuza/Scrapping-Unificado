import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: React.ReactNode
  className?: string
}

export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div className={cn('mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between', className)}>
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
        {description && (
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string | number
  hint?: string
  tone?: 'default' | 'success' | 'warning' | 'error'
}

const toneStyles = {
  default: 'bg-white border-border',
  success: 'bg-emerald-50/80 border-emerald-200/60',
  warning: 'bg-amber-50/80 border-amber-200/60',
  error: 'bg-red-50/80 border-red-200/60',
}

export function StatCard({ label, value, hint, tone = 'default' }: StatCardProps) {
  return (
    <div className={cn('rounded-xl border px-4 py-3', toneStyles[tone])}>
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}
