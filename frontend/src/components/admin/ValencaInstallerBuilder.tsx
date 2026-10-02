import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Download, ExternalLink, Loader2, Package } from 'lucide-react'
import { api } from '@/lib/api'
import { withBase } from '@/lib/paths'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export function ValencaInstallerBuilder() {
  const queryClient = useQueryClient()
  const [selectedModules, setSelectedModules] = useState<string[]>([])
  const [buildUsername, setBuildUsername] = useState('__none__')

  const { data: usersData } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => api.admin.users(),
  })

  const { data: modulesData } = useQuery({
    queryKey: ['admin-modules'],
    queryFn: () => api.admin.modules(),
  })

  const { data: buildsData } = useQuery({
    queryKey: ['admin-builds'],
    queryFn: () => api.admin.builds(),
    refetchInterval: (query) =>
      (query.state.data?.builds ?? []).some((b) => b.status === 'pendente') ? 8000 : false,
  })

  const createBuildMutation = useMutation({
    mutationFn: () =>
      api.admin.createBuild(
        selectedModules,
        buildUsername === '__none__' ? '' : buildUsername,
      ),
    onSuccess: (res) => {
      if (res.success) {
        toast.success(res.message || 'Build pedido')
        void queryClient.invalidateQueries({ queryKey: ['admin-builds'] })
        void queryClient.invalidateQueries({ queryKey: ['downloads'] })
      } else {
        toast.error(res.error || 'Falha ao gerar instalador')
      }
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const users = usersData?.users ?? []

  return (
    <div className="surface-card overflow-hidden">
      <div className="border-b border-border-subtle px-6 py-4">
        <h3 className="flex items-center gap-2 font-semibold">
          <Package className="h-4 w-4 text-indigo-400" />
          Gerar instalador Valença Suite
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Marque os fluxos que a pessoa deve ter. O site dispara o GitHub Actions e não altera o
          instalador oficial. O build costuma levar 5–6 minutos — não clique de novo à toa.
        </p>
      </div>
      <div className="space-y-5 p-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {(modulesData?.categories ?? []).map((cat) => (
            <div key={cat.id} className="rounded-xl border border-border-subtle p-4">
              <p className="mb-3 text-sm font-semibold">{cat.label}</p>
              <div className="space-y-2">
                {cat.modules.map((mod) => {
                  const checked = selectedModules.includes(mod.id)
                  return (
                    <label key={mod.id} className="flex cursor-pointer items-start gap-2 text-sm">
                      <input
                        type="checkbox"
                        className="mt-1 h-4 w-4 rounded border-border-subtle"
                        checked={checked}
                        onChange={() =>
                          setSelectedModules((prev) =>
                            checked ? prev.filter((id) => id !== mod.id) : [...prev, mod.id],
                          )
                        }
                      />
                      <span>{mod.label}</span>
                    </label>
                  )
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="space-y-2 sm:min-w-64">
            <Label>Utilizador destino (opcional)</Label>
            <Select value={buildUsername} onValueChange={setBuildUsername}>
              <SelectTrigger>
                <SelectValue placeholder="Só admins vêem" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">Ninguém específico (só admins)</SelectItem>
                {users.map((u) => (
                  <SelectItem key={u.username} value={u.username}>
                    {u.username}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button
            onClick={() => createBuildMutation.mutate()}
            disabled={createBuildMutation.isPending || selectedModules.length === 0}
          >
            {createBuildMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Confirmar e gerar
          </Button>
        </div>

        <div className="space-y-3">
          {(buildsData?.builds ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">Nenhum pedido ainda.</p>
          ) : (
            (buildsData?.builds ?? []).map((b) => (
              <div key={b.id} className="rounded-xl border border-border-subtle p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium">{b.app_id || '—'}</p>
                  <Badge
                    variant={
                      b.status === 'pronto' ? 'success' : b.status === 'falha' ? 'error' : 'warning'
                    }
                  >
                    {b.status === 'pronto' ? 'Pronto' : b.status === 'falha' ? 'Falha' : 'Pendente'}
                  </Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {b.created_at ? new Date(b.created_at).toLocaleString('pt-BR') : ''}
                  {' · destino: '}
                  {b.username || 'só admins'}
                  {b.cached ? ' · reutilizado' : ''}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  módulos: {(b.modules || []).join(', ') || '—'}
                </p>
                {b.error ? <p className="mt-2 text-sm text-destructive">{b.error}</p> : null}
                <div className="mt-3 flex flex-wrap gap-2">
                  {b.status === 'pronto' && b.app_id && b.setup_filename ? (
                    <Button size="sm" asChild>
                      <a
                        href={withBase(
                          `/api/downloads/file/${encodeURIComponent(b.app_id)}/${encodeURIComponent(b.setup_filename)}`,
                        )}
                        download
                      >
                        <Download className="h-4 w-4" />
                        Baixar .exe
                      </a>
                    </Button>
                  ) : null}
                  {b.status === 'falha' && b.actions_url ? (
                    <Button size="sm" variant="outline" asChild>
                      <a href={b.actions_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4" />
                        Ver Actions
                      </a>
                    </Button>
                  ) : null}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
