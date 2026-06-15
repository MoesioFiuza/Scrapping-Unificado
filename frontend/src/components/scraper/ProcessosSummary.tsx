import { useMemo, useState } from 'react'
import type { Processo, ProcessoStatus } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CheckCircle2, Clock, Loader2, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ProcessosList } from '@/components/scraper/ProcessosList'

interface ProcessosSummaryProps {
  processos: Processo[]
  tribunaisMap: Record<string, string>
}

const statusMeta: Record<
  ProcessoStatus,
  { label: string; variant: 'success' | 'error' | 'warning' | 'secondary'; icon: typeof Clock }
> = {
  pendente: { label: 'Pendentes', variant: 'secondary', icon: Clock },
  processando: { label: 'A processar', variant: 'warning', icon: Loader2 },
  sucesso: { label: 'Sucesso', variant: 'success', icon: CheckCircle2 },
  erro: { label: 'Erros', variant: 'error', icon: XCircle },
}

export function ProcessosSummary({ processos, tribunaisMap }: ProcessosSummaryProps) {
  const [expanded, setExpanded] = useState(false)

  const stats = useMemo(() => {
    const counts: Record<string, number> = {
      pendente: 0,
      processando: 0,
      sucesso: 0,
      erro: 0,
    }
    const tribunais: Record<string, number> = {}
    for (const p of processos) {
      counts[p.status] = (counts[p.status] || 0) + 1
      if (p.tribunal) {
        tribunais[p.tribunal] = (tribunais[p.tribunal] || 0) + 1
      }
    }
    return { counts, tribunais }
  }, [processos])

  const topTribunais = useMemo(
    () =>
      Object.entries(stats.tribunais)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5),
    [stats.tribunais],
  )

  if (processos.length === 0) return null

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {(Object.keys(statusMeta) as ProcessoStatus[]).map((key) => {
          const count = stats.counts[key] ?? 0
          if (count === 0 && key !== 'pendente') return null
          const meta = statusMeta[key]
          const Icon = meta.icon
          return (
            <div
              key={key}
              className="rounded-xl border border-border-subtle bg-muted/30 px-4 py-3"
            >
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">{meta.label}</p>
                <Icon
                  className={cn(
                    'h-3.5 w-3.5 text-muted-foreground',
                    key === 'processando' && count > 0 && 'animate-spin text-amber-400',
                  )}
                />
              </div>
              <p className="mt-1 text-2xl font-semibold tabular-nums">{count}</p>
            </div>
          )
        })}
      </div>

      {topTribunais.length > 0 && (
        <div className="rounded-xl border border-border-subtle bg-muted/20 px-4 py-3">
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            Tribunais na planilha ({Object.keys(stats.tribunais).length})
          </p>
          <div className="flex flex-wrap gap-2">
            {topTribunais.map(([codigo, count]) => (
              <Badge key={codigo} variant="outline" className="text-[11px]">
                {tribunaisMap[codigo] || codigo} · {count}
              </Badge>
            ))}
            {Object.keys(stats.tribunais).length > 5 && (
              <Badge variant="secondary" className="text-[11px]">
                +{Object.keys(stats.tribunais).length - 5} outros
              </Badge>
            )}
          </div>
        </div>
      )}

      <p className="text-sm text-muted-foreground">
        {processos.length} processo(s) carregados — resumo da planilha atual.
      </p>

      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => setExpanded((v) => !v)}
        className="gap-2"
      >
        {expanded ? (
          <>
            <ChevronUp className="h-4 w-4" />
            Ocultar lista completa
          </>
        ) : (
          <>
            <ChevronDown className="h-4 w-4" />
            Ver lista completa
          </>
        )}
      </Button>

      {expanded && <ProcessosList processos={processos} tribunaisMap={tribunaisMap} />}
    </div>
  )
}
