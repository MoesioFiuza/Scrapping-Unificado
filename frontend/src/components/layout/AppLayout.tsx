import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  PlusCircle,
  FolderOpen,
  Download,
  Shield,
  BarChart3,
  LogOut,
  Scale,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/useAuth'
import { DataWebProgressBanner } from '@/components/scraper/DataWebProgressBanner'
import { ValencaUpdateBanner } from '@/components/layout/ValencaUpdateBanner'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: 'Nova Extração', icon: PlusCircle, end: true },
  { to: '/extracoes', label: 'Extrações', icon: FolderOpen },
  { to: '/downloads', label: 'Downloads', icon: Download },
  { to: '/admin/dashboard', label: 'Dashboard', icon: BarChart3, adminOnly: true },
  { to: '/admin', label: 'Administração', icon: Shield, adminOnly: true },
]

export function AppLayout() {
  const { isAdmin, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[248px] flex-col border-r border-sidebar-border bg-sidebar lg:flex">
        <div className="flex items-center gap-3 px-5 py-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-950/50">
            <Scale className="h-5 w-5 text-white" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">Scraper Unificado</p>
            <p className="truncate text-[10px] uppercase tracking-wider text-sidebar-muted">
              Extração processual
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-0.5 px-3">
          {navItems
            .filter((item) => !item.adminOnly || isAdmin)
            .map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-all',
                    isActive
                      ? 'bg-indigo-600/90 text-white shadow-md shadow-indigo-950/40'
                      : 'text-sidebar-muted hover:bg-white/[0.04] hover:text-sidebar-foreground',
                  )
                }
              >
                <Icon className="h-[18px] w-[18px] shrink-0 opacity-90" />
                {label}
              </NavLink>
            ))}
        </nav>

        <div className="mx-3 mb-4 rounded-xl border border-sidebar-border bg-white/[0.03] p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-sidebar-muted">
            Plano atual
          </p>
          <p className="mt-1 text-sm font-semibold text-white">Enterprise</p>
          <p className="mt-0.5 text-[11px] text-sidebar-muted">Acesso interno · Ilimitado</p>
        </div>

        <div className="border-t border-sidebar-border p-3">
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-sidebar-muted hover:bg-white/[0.04] hover:text-white"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4" />
            Terminar sessão
          </Button>
        </div>
      </aside>

      {/* Mobile nav */}
      <div className="fixed inset-x-0 top-0 z-20 flex h-14 items-center justify-between border-b border-border bg-card/95 px-4 backdrop-blur lg:hidden">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
            <Scale className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-semibold">Scraper Unificado</span>
        </div>
        <div className="flex gap-1">
          {navItems
            .filter((item) => !item.adminOnly || isAdmin)
            .map(({ to, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn('rounded-lg p-2', isActive ? 'bg-indigo-600 text-white' : 'text-muted-foreground')
                }
              >
                <Icon className="h-4 w-4" />
              </NavLink>
            ))}
        </div>
      </div>

      <div className="flex min-h-screen flex-1 flex-col lg:pl-[248px]">
        <main className="flex-1 px-4 pb-8 pt-16 lg:px-6 lg:pt-6 xl:px-8">
          <div className="mx-auto max-w-[1600px]">
            <ValencaUpdateBanner />
            <DataWebProgressBanner />
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
