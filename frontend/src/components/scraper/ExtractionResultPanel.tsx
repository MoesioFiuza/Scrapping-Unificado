import { CheckCircle2, Download, FileSpreadsheet, XCircle } from 'lucide-react'
import { api } from '@/lib/api'
import { labelCliFilename } from '@/lib/extracoes'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { ScraperModo } from '@/types'
import type { CliDownloadItem } from '@/types'

export type { CliDownloadItem }

interface ExtractionResultPanelProps {
  modo: ScraperModo
  stats: { total: number; sucesso: number; erro: number }
  successRate: string
  durationLabel?: string | null
  cliDownloads?: CliDownloadItem[]
  onExportRaspado?: () => void
  onExportTratado?: () => void
}

export function ExtractionResultPanel({
  modo,
  stats,
  successRate,
  durationLabel,
  cliDownloads = [],
  onExportRaspado,
  onExportTratado,
}: ExtractionResultPanelProps) {
  const allFailed = stats.sucesso === 0 && stats.erro > 0
  const hasCliFiles = cliDownloads.length > 0

  return (
    <div className="surface-card overflow-hidden border-emerald-500/25">
      <div className="border-b border-border-subtle bg-emerald-500/5 px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              <h2 className="text-lg font-semibold">Resultado da extração</h2>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {modo === 'cli'
                ? 'Extração CLI concluída. Descarregue os ficheiros gerados abaixo.'
                : 'Scraping concluído. Exporte as planilhas raspada e tratada.'}
            </p>
          </div>
          <Badge variant="success">Concluído</Badge>
        </div>
      </div>

      <div className="space-y-6 p-6">
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-border-subtle bg-muted/30 px-4 py-3">
            <p className="text-xs text-muted-foreground">Total</p>
            <p className="mt-1 text-2xl font-bold tabular-nums">{stats.total}</p>
          </div>
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
            <p className="text-xs text-emerald-400/80">Sucesso</p>
            <p className="mt-1 text-2xl font-bold tabular-nums text-emerald-300">{stats.sucesso}</p>
          </div>
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
            <p className="text-xs text-red-400/80">Erros</p>
            <p className="mt-1 text-2xl font-bold tabular-nums text-red-300">{stats.erro}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          <span>
            Taxa de sucesso: <strong className="text-foreground">{successRate}</strong>
          </span>
          {durationLabel && (
            <span>
              Duração: <strong className="text-foreground">{durationLabel}</strong>
            </span>
          )}
        </div>

        {allFailed && (
          <div className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>Nenhum processo foi extraído com sucesso. Revise os erros na lista abaixo e tente novamente.</p>
          </div>
        )}

        {modo === 'normal' && stats.sucesso > 0 && (
          <div className="flex flex-wrap gap-3 border-t border-border-subtle pt-4">
            <Button onClick={onExportRaspado} className="min-w-[160px]">
              <Download className="h-4 w-4" />
              Exportar raspado
            </Button>
            <Button variant="outline" onClick={onExportTratado} className="min-w-[160px]">
              <Download className="h-4 w-4" />
              Exportar tratado
            </Button>
          </div>
        )}

        {modo === 'cli' && hasCliFiles && (
          <div className="space-y-3 border-t border-border-subtle pt-4">
            <p className="text-sm font-medium text-foreground">Ficheiros gerados</p>
            <ul className="space-y-2">
              {cliDownloads.map((item) => (
                <li
                  key={item.id}
                  className="flex items-center justify-between gap-3 rounded-xl border border-border-subtle bg-muted/20 px-4 py-3"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-500/15 text-indigo-400">
                      <FileSpreadsheet className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium">{labelCliFilename(item.filename)}</p>
                      <p className="truncate font-mono text-xs text-muted-foreground">{item.filename}</p>
                    </div>
                  </div>
                  <Button asChild size="sm" variant="outline">
                    <a href={api.extracoes.downloadUrl(item.id)} download>
                      <Download className="h-4 w-4" />
                      Download
                    </a>
                  </Button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {modo === 'cli' && !hasCliFiles && !allFailed && (
          <p className="text-sm text-muted-foreground">
            Os ficheiros foram registados. Consulte também a secção{' '}
            <strong className="text-foreground">Extrações recentes</strong> abaixo.
          </p>
        )}
      </div>
    </div>
  )
}
