import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Download, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import {
  labelTipo,
  processosCount,
  tribunalResumo,
  TIPO_VARIANT,
} from '@/lib/extracoes'
import { Badge } from '@/components/ui/badge'
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
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export function RecentExtractionsTable() {
  const { data: tribData } = useQuery({
    queryKey: ['tribunais'],
    queryFn: () => api.tribunais.list(),
  })

  const tribunaisMap = Object.fromEntries(
    (tribData?.tribunais ?? []).map((t) => [t.codigo, t.nome]),
  )

  const { data, isLoading } = useQuery({
    queryKey: ['extracoes', 'recent'],
    queryFn: () => api.extracoes.list(),
  })

  const recent = (data?.extracoes ?? []).slice(0, 5)

  return (
    <div className="surface-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-border-subtle px-5 py-4">
        <h3 className="font-semibold text-foreground">Extrações recentes</h3>
        <Link to="/extracoes" className="text-sm font-medium text-indigo-400 hover:text-indigo-300">
          Ver todas
        </Link>
      </div>
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : recent.length === 0 ? (
        <p className="px-5 py-10 text-center text-sm text-muted-foreground">
          Nenhuma extração registada ainda.
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow className="border-border-subtle hover:bg-transparent">
              <TableHead>Arquivo</TableHead>
              <TableHead className="hidden md:table-cell">Tipo</TableHead>
              <TableHead className="hidden lg:table-cell">Tribunal</TableHead>
              <TableHead className="hidden sm:table-cell">Processos</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="hidden sm:table-cell">Data</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {recent.map((ex) => (
              <TableRow key={ex.id} className="border-border-subtle">
                <TableCell>
                  <p className="max-w-[200px] truncate font-mono text-xs font-medium">{ex.filename}</p>
                  {ex.username && (
                    <p className="mt-0.5 max-w-[200px] truncate text-[10px] text-muted-foreground">
                      {ex.username}
                    </p>
                  )}
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <Badge variant={TIPO_VARIANT[ex.tipo] ?? 'secondary'} className="text-[10px]">
                    {labelTipo(ex.tipo)}
                  </Badge>
                </TableCell>
                <TableCell className="hidden max-w-[140px] truncate text-sm text-muted-foreground lg:table-cell">
                  {tribunalResumo(ex, tribunaisMap)}
                </TableCell>
                <TableCell className="hidden tabular-nums text-sm sm:table-cell">
                  {processosCount(ex)}
                </TableCell>
                <TableCell>
                  <Badge variant="success" className="text-[10px]">
                    Concluído
                  </Badge>
                </TableCell>
                <TableCell className="hidden whitespace-nowrap text-xs text-muted-foreground sm:table-cell">
                  {formatDate(ex.data_criacao)}
                </TableCell>
                <TableCell>
                  <a
                    href={api.extracoes.downloadUrl(ex.id)}
                    download
                    title="Download"
                    className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-indigo-400"
                  >
                    <Download className="h-4 w-4" />
                  </a>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
