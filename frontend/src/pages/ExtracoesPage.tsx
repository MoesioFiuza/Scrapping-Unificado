import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Download, Trash2, RefreshCw, FileSpreadsheet, Loader2, FolderOpen, Hash, Terminal } from 'lucide-react'
import { api } from '@/lib/api'
import { labelTipo, TIPO_VARIANT } from '@/lib/extracoes'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { TopBar } from '@/components/layout/TopBar'
import { DarkStatCard } from '@/components/layout/DarkStatCard'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

function formatDate(iso: string) {
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

export function ExtracoesPage() {
  const queryClient = useQueryClient()

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['extracoes'],
    queryFn: () => api.extracoes.list(),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.extracoes.delete(id),
    onSuccess: () => {
      toast.success('Extração removida')
      void queryClient.invalidateQueries({ queryKey: ['extracoes'] })
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const extracoes = data?.extracoes ?? []
  const totalProcessos = extracoes.reduce((s, e) => s + (e.total_processos || 0), 0)

  return (
    <div className="space-y-6">
      <TopBar
        title="Extrações"
        subtitle="Histórico de planilhas geradas. Descarregue ou remova ficheiros anteriores."
      />

      <div className="flex justify-end">
        <Button variant="outline" onClick={() => void refetch()} disabled={isFetching}>
          {isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Atualizar
        </Button>
      </div>

      {!isLoading && extracoes.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-3">
          <DarkStatCard label="Ficheiros" value={extracoes.length} icon={FolderOpen} />
          <DarkStatCard label="Processos totais" value={totalProcessos} icon={Hash} iconClass="bg-violet-500/15 text-violet-400" />
          <DarkStatCard
            label="Tipos CLI"
            value={extracoes.filter((e) => e.tipo.includes('_cli')).length}
            icon={Terminal}
            iconClass="bg-emerald-500/15 text-emerald-400"
          />
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : extracoes.length === 0 ? (
        <div className="surface-card flex flex-col items-center px-6 py-20 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-muted">
            <FileSpreadsheet className="h-7 w-7 text-muted-foreground" />
          </div>
          <p className="text-lg font-medium">Nenhuma extração ainda</p>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Quando concluir uma extração CLI ou exportação, os ficheiros aparecerão aqui.
          </p>
        </div>
      ) : (
        <div className="surface-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ficheiro</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Processos</TableHead>
                <TableHead>Data</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {extracoes.map((ex) => (
                <TableRow key={ex.id}>
                  <TableCell>
                    <p className="max-w-[280px] truncate font-mono text-sm font-medium">{ex.filename}</p>
                    {ex.username && (
                      <p className="text-xs text-muted-foreground">{ex.username}</p>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant={TIPO_VARIANT[ex.tipo] || 'secondary'}>
                      {labelTipo(ex.tipo)}
                    </Badge>
                  </TableCell>
                  <TableCell className="tabular-nums">{ex.total_processos}</TableCell>
                  <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                    {formatDate(ex.data_criacao)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button asChild size="sm" variant="outline">
                        <a href={api.extracoes.downloadUrl(ex.id)} download>
                          <Download className="h-4 w-4" />
                          Download
                        </a>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => deleteMutation.mutate(ex.id)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
