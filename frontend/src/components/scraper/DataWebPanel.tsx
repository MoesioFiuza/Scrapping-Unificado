import { useQuery } from '@tanstack/react-query'
import { Database, Download, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import type { Processo, DataWebResult } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export type { DataWebResult }

interface DataWebPanelProps {
  processos: Processo[]
  disabled?: boolean
  onBusyChange?: (busy: boolean) => void
  result: DataWebResult | null
  onResult: (result: DataWebResult | null) => void
}

export function DataWebPanel({
  processos,
  disabled,
  onBusyChange,
  result,
  onResult,
}: DataWebPanelProps) {
  const cnjs = processos.map((p) => p.numero_processo).filter(Boolean)
  const lotes = Math.ceil(cnjs.length / 500)

  const { data: healthData, isLoading: healthLoading } = useQuery({
    queryKey: ['dataweb', 'health'],
    queryFn: () => api.dataweb.health(),
    refetchInterval: 60_000,
    staleTime: 30_000,
  })

  const healthy = healthData?.healthy

  const processar = async () => {
    if (!cnjs.length) {
      toast.error('Faça upload de uma planilha com CNJs primeiro')
      return
    }
    onBusyChange?.(true)
    onResult(null)
    try {
      const res = await api.dataweb.processar(cnjs)
      if (res.success && res.extracao_id && res.filename && res.total_cnjs != null) {
        const item: DataWebResult = {
          extracaoId: res.extracao_id,
          filename: res.filename,
          totalCnjs: res.total_cnjs,
        }
        onResult(item)
        toast.success('Planilha DataWeb gerada com sucesso!')
      } else {
        toast.error(res.error || 'Erro ao processar no DataWeb')
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Erro ao contactar DataWeb')
    } finally {
      onBusyChange?.(false)
    }
  }

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
        Consulta a API pública do DataJud via microserviço DataWeb. Envie os CNJs da planilha
        carregada e receba um Excel com abas Dados Completos, Movimentações Recentes, Resumo e
        Análise. O processamento é síncrono e pode levar vários minutos (até 10 min).
      </p>

      <div className="flex flex-wrap gap-3">
        <Button
          onClick={() => void processar()}
          disabled={disabled || !cnjs.length || healthy === false}
          size="lg"
          className="min-w-[200px]"
        >
          {disabled ? (
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
