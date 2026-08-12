import { useQuery } from '@tanstack/react-query'
import { Download, RefreshCw, Loader2, Package, HardDrive } from 'lucide-react'
import { api } from '@/lib/api'
import { withBase } from '@/lib/paths'
import { Button } from '@/components/ui/button'
import { TopBar } from '@/components/layout/TopBar'
import { DarkStatCard } from '@/components/layout/DarkStatCard'

function formatDate(iso: string) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export function DownloadsPage() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['downloads'],
    queryFn: () => api.downloads.list(),
  })

  const apps = (data?.apps ?? []).filter(
    (app) => (app.files?.length ?? 0) > 0 || Boolean(app.version),
  )

  return (
    <div className="space-y-6">
      <TopBar
        title="Downloads"
        subtitle="Última versão dos aplicativos do escritório (Valença Suite e outros)."
      />

      <div className="flex justify-end">
        <Button variant="outline" onClick={() => void refetch()} disabled={isFetching}>
          {isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Atualizar
        </Button>
      </div>

      {!isLoading && apps.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          <DarkStatCard label="Aplicativos" value={apps.length} icon={Package} />
          <DarkStatCard
            label="Ficheiros disponíveis"
            value={apps.reduce((s, a) => s + (a.files?.length || 0), 0)}
            icon={HardDrive}
            iconClass="bg-violet-500/15 text-violet-400"
          />
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : apps.length === 0 ? (
        <div className="surface-card flex flex-col items-center px-6 py-20 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-muted">
            <Download className="h-7 w-7 text-muted-foreground" />
          </div>
          <p className="text-lg font-medium">Nenhum aplicativo publicado ainda</p>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Quando o GitHub Actions publicar uma versão, os instaladores aparecerão aqui.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {apps.map((app) => (
            <div key={app.app_id} className="surface-card p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-foreground">{app.name}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {app.version ? (
                      <>
                        Versão <span className="font-medium text-foreground">v{app.version}</span>
                        {app.released_at ? ` · ${formatDate(app.released_at)}` : null}
                      </>
                    ) : (
                      'Aguardando publicação'
                    )}
                  </p>
                  {app.notes ? (
                    <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{app.notes}</p>
                  ) : null}
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                {(app.files || []).length === 0 ? (
                  <p className="text-sm text-muted-foreground">Arquivos ainda não disponíveis no servidor.</p>
                ) : (
                  (app.files || []).map((file) => (
                    <Button key={file.filename} asChild variant="default">
                      <a
                        href={withBase(
                          `/api/downloads/file/${encodeURIComponent(app.app_id)}/${encodeURIComponent(file.filename)}`,
                        )}
                        download
                      >
                        <Download className="h-4 w-4" />
                        {file.label || file.filename}
                      </a>
                    </Button>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
