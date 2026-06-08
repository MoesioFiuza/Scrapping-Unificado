import { Bell } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'

function initials(email?: string) {
  if (!email) return '?'
  const part = email.split('@')[0] ?? email
  return part.slice(0, 2).toUpperCase()
}

interface TopBarProps {
  title?: string
  subtitle?: string
  actions?: React.ReactNode
}

export function TopBar({ title, subtitle, actions }: TopBarProps) {
  const { username, isAdmin } = useAuth()

  return (
    <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      {(title || subtitle) && (
        <div className="min-w-0 flex-1">
          {title && <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>}
          {subtitle && <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>}
        </div>
      )}
      <div className={cn('flex flex-wrap items-center gap-3', !title && !subtitle && 'ml-auto')}>
        {actions}
        <div className={cn('flex items-center gap-3', !title && !subtitle && 'ml-auto')}>
        <button
          type="button"
          className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-border-subtle bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label="Notificações"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-primary" />
        </button>
        <div className="flex items-center gap-3 rounded-xl border border-border-subtle bg-card py-1.5 pl-1.5 pr-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-xs font-bold text-white">
            {initials(username)}
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium leading-tight">{isAdmin ? 'Admin' : 'Utilizador'}</p>
            <p className="max-w-[140px] truncate text-[11px] text-muted-foreground">{username}</p>
          </div>
        </div>
        </div>
      </div>
    </header>
  )
}
