import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Download, X } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'

const STORAGE_KEY = 'valenca_suite_dismissed_version'

function readDismissed(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) || ''
  } catch {
    return ''
  }
}

function writeDismissed(version: string) {
  try {
    localStorage.setItem(STORAGE_KEY, version)
  } catch {
    /* ignore */
  }
}

export function ValencaUpdateBanner() {
  const [dismissed, setDismissed] = useState(readDismissed)

  const { data } = useQuery({
    queryKey: ['downloads', 'valenca-banner'],
    queryFn: () => api.downloads.latest('valenca'),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })

  const app = data?.app
  const version = (app?.version || '').trim()
  const hasFiles = (app?.files?.length || 0) > 0

  const visible = useMemo(() => {
    if (!version || !hasFiles) return false
    if (dismissed && dismissed === version) return false
    return true
  }, [version, hasFiles, dismissed])

  if (!visible || !app) return null

  const dismiss = () => {
    writeDismissed(version)
    setDismissed(version)
  }

  return (
    <div className="mb-4 rounded-xl border border-violet-500/35 bg-violet-500/10 px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-sm font-semibold text-violet-100">
            <Download className="h-4 w-4 shrink-0" />
            Nova versão disponível: {app.name || 'Valença Suite'} v{version}
          </div>
          <p className="mt-1 text-xs text-violet-200/75">
            {app.notes?.trim() ||
              'Há um instalador atualizado para download. Atualize no seu PC para corrigir erros e receber melhorias.'}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button asChild size="sm" className="bg-violet-600 hover:bg-violet-500">
            <Link to="/downloads">Baixar agora</Link>
          </Button>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="h-8 w-8 text-violet-200 hover:bg-violet-500/20 hover:text-white"
            onClick={dismiss}
            aria-label="Dispensar aviso"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
