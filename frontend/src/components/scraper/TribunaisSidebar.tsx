import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Processo, Tribunal } from '@/types'
import { cn } from '@/lib/utils'
import { Loader2, Search } from 'lucide-react'
import { Input } from '@/components/ui/input'

interface TribunaisSidebarProps {
  processos?: Processo[]
}

export function TribunaisSidebar({ processos = [] }: TribunaisSidebarProps) {
  const [query, setQuery] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['tribunais'],
    queryFn: () => api.tribunais.list(),
  })

  const tribunais = data?.tribunais ?? []

  const counts = useMemo(() => {
    const map: Record<string, number> = {}
    for (const p of processos) {
      if (p.tribunal) map[p.tribunal] = (map[p.tribunal] || 0) + 1
    }
    return map
  }, [processos])

  const filtered = tribunais.filter(
    (t) =>
      t.nome.toLowerCase().includes(query.toLowerCase()) ||
      t.codigo.includes(query),
  )

  return (
    <div className="space-y-4">
      <div className="surface-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Tribunais disponíveis</h3>
          <span className="rounded-full bg-indigo-500/15 px-2 py-0.5 text-[10px] font-semibold text-indigo-400">
            {tribunais.length}
          </span>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Filtrar..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-9 border-border-subtle bg-background/60 pl-8 text-sm"
          />
        </div>
        <div className="mt-3 max-h-[320px] space-y-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            filtered.map((t: Tribunal) => {
              const count = counts[t.codigo] ?? 0
              return (
                <div
                  key={t.codigo}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-muted/60',
                    count > 0 && 'bg-indigo-500/5',
                  )}
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-[10px] font-bold text-muted-foreground">
                    {t.nome.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xs font-medium">{t.nome}</p>
                    <p className="text-[10px] text-muted-foreground">v{t.codigo}</p>
                  </div>
                  <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
