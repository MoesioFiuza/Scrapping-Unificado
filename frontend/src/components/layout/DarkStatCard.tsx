import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DarkStatCardProps {
  label: string
  value: string | number
  icon: LucideIcon
  iconClass?: string
  hint?: string
}

export function DarkStatCard({ label, value, icon: Icon, iconClass, hint }: DarkStatCardProps) {
  return (
    <div className="surface-card flex items-center gap-4 p-4">
      <div
        className={cn(
          'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl',
          iconClass ?? 'bg-indigo-500/15 text-indigo-400',
        )}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0">
        <p className="text-2xl font-bold tabular-nums tracking-tight">{value}</p>
        <p className="truncate text-xs text-muted-foreground">{label}</p>
        {hint && <p className="mt-0.5 truncate text-[10px] text-muted-foreground/80">{hint}</p>}
      </div>
    </div>
  )
}
