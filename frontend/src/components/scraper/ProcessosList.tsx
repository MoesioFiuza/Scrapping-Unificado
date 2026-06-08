import { useMemo, useState } from 'react'
import type { Processo, ProcessoStatus } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { CheckCircle2, XCircle, Loader2, Clock, Search } from 'lucide-react'

const statusConfig: Record<
  ProcessoStatus,
  { label: string; variant: 'success' | 'error' | 'warning' | 'secondary'; icon: typeof Clock }
> = {
  pendente: { label: 'Pendente', variant: 'secondary', icon: Clock },
  processando: { label: 'Processando', variant: 'warning', icon: Loader2 },
  sucesso: { label: 'Sucesso', variant: 'success', icon: CheckCircle2 },
  erro: { label: 'Erro', variant: 'error', icon: XCircle },
}

type FilterStatus = 'todos' | ProcessoStatus

interface ProcessosListProps {
  processos: Processo[]
  tribunaisMap: Record<string, string>
}

export function ProcessosList({ processos, tribunaisMap }: ProcessosListProps) {
  const [filter, setFilter] = useState<FilterStatus>('todos')
  const [search, setSearch] = useState('')

  const stats = useMemo(
    () =>
      processos.reduce(
        (acc, p) => {
          acc[p.status] = (acc[p.status] || 0) + 1
          return acc
        },
        {} as Record<string, number>,
      ),
    [processos],
  )

  const filtered = useMemo(() => {
    let list = processos
    if (filter !== 'todos') list = list.filter((p) => p.status === filter)
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      list = list.filter((p) => p.numero_processo.toLowerCase().includes(q))
    }
    return list
  }, [processos, filter, search])

  if (processos.length === 0) return null

  const filters: { key: FilterStatus; label: string; count?: number }[] = [
    { key: 'todos', label: 'Todos', count: processos.length },
    { key: 'pendente', label: 'Pendentes', count: stats.pendente },
    { key: 'processando', label: 'A processar', count: stats.processando },
    { key: 'sucesso', label: 'Sucesso', count: stats.sucesso },
    { key: 'erro', label: 'Erros', count: stats.erro },
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-1.5">
          {filters.map((f) =>
            f.count !== undefined && f.key !== 'todos' && f.count === 0 ? null : (
              <button
                key={f.key}
                type="button"
                onClick={() => setFilter(f.key)}
                className={cn(
                  'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                  filter === f.key
                    ? 'bg-indigo-600 text-white'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80',
                )}
              >
                {f.label}
                {f.count !== undefined ? ` (${f.count})` : ''}
              </button>
            ),
          )}
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar processo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-9 pl-8 text-sm"
          />
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Processo</TableHead>
            <TableHead>Tribunal</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="hidden md:table-cell">Observação</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filtered.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="py-8 text-center text-muted-foreground">
                Nenhum processo encontrado com estes filtros.
              </TableCell>
            </TableRow>
          ) : (
            filtered.map((p, i) => {
              const cfg = statusConfig[p.status]
              const Icon = cfg.icon
              return (
                <TableRow key={`${p.numero_processo}-${i}`}>
                  <TableCell className="font-mono text-sm font-medium">{p.numero_processo}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {tribunaisMap[p.tribunal ?? ''] || p.tribunal || '—'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={cfg.variant} className="gap-1">
                      <Icon className={cn('h-3 w-3', p.status === 'processando' && 'animate-spin')} />
                      {cfg.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="hidden max-w-xs truncate text-sm text-red-400 md:table-cell">
                    {p.erro || '—'}
                  </TableCell>
                </TableRow>
              )
            })
          )}
        </TableBody>
      </Table>
      <p className="text-xs text-muted-foreground">
        A mostrar {filtered.length} de {processos.length} processos
      </p>
    </div>
  )
}
