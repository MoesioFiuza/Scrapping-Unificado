import { useQuery } from '@tanstack/react-query'
import { Database, Download, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { api } from '@/lib/api'
import { useDataWebJob } from '@/hooks/useDataWebJob'
import type { Processo } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface DataWebPanelProps {
  processos: Processo[]
}

export function DataWebPanel({ processos }: DataWebPanelProps) {
  const cnjs = processos.map((p) => p.numero_processo).filter(Boolean)
  const lotes = Math.ceil(cnjs.length / 500)
  const { busy, startJob, result, error, loteAtual, totalLotes, totalCnjs } = useDataWebJob()

  const { data: healthData, isLoading: healthLoading } = useQuery({
    queryKey: ['dataweb', 'health'],
    queryFn: () => api.dataweb.health(),
    refetchInterval: 60_000,
    staleTime: 30_000,
  })

  const healthy = healthData?.healthy
  const progressPct =
    totalLotes > 1 ? Math.round((Math.max(loteAtual, busy ? 1 : 0) / totalLotes) * 100) : undefined

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <div
          className={cn(
            'flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium',
            healthLoading && 'border-border-subtle text-muted-foreground',
            !healthLoading && healthy && 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
            !healthLoading && healthy === false && 'border-red-500/30 bg-red-500/10 text-red-400',
          )}
        >
          {healthLoading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : healthy ? (
            <CheckCircle2 className="h-3.5 w-3.5" />
          ) : (
            <XCircle className="h-3.5 w-3.5" />
          )}
          DataWeb {healthLoading ? '…' : healthy ? 'online' : 'indisponível'}
        </div>
        <Badge variant="outline" className="text-[10px]">
          {cnjs.length} CNJ(s)
          {lotes > 1 ? ` · ${lotes} lotes` : ''}
        </Badge>
      </div>

      <p className="rounded-xl border border-border-subtle bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
        Consulta a API pública do DataJud via microserviço DataWeb. O processamento corre em
        segundo plano — pode mudar de aba enquanto aguarda. Planilhas grandes são divididas em
        lotes automáticos.
      </p>

      {busy && (
        <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-semibold text-indigo-200">DataWeb em curso</span>
            <span className="text-indigo-300/80">
              {totalLotes > 1 ? `Lote ${loteAtual || 1}/${totalLotes}` : `${totalCnjs || cnjs.length} CNJ(s)`}
            </span>
          </div>
          {progressPct !== undefined && <Progress value={progressPct} className="h-2" />}
        </div>
      )}

      {error && !busy && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <Button
          onClick={() => void startJob(cnjs)}
          disabled={busy || !cnjs.length || healthy === false}
          size="lg"
          className="min-w-[200px]"
        >
          {busy ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Processando no DataWeb…
            </>
          ) : (
            <>
              <Database className="h-4 w-4" />
              Processar no DataWeb
            </>
          )}
        </Button>

        {result && (
          <Button asChild variant="outline" size="lg">
            <a href={api.extracoes.downloadUrl(result.extracaoId)} download>
              <Download className="h-4 w-4" />
              Baixar planilha
            </a>
          </Button>
        )}
      </div>

      {result && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm">
          <p className="font-medium text-emerald-200">Planilha pronta</p>
          <p className="mt-1 font-mono text-xs text-emerald-300/90">{result.filename}</p>
          <p className="mt-1 text-xs text-emerald-400/80">
            {result.totalCnjs} CNJ(s) processados · também disponível em Extrações
          </p>
        </div>
      )}
    </div>
  )
}
