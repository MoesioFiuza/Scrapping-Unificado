import { useQuery } from '@tanstack/react-query'
import { Eye, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import { TopBar } from '@/components/layout/TopBar'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

function fmtDate(iso: string | null | undefined) {
  if (!iso) return '—'
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

export function AcompanhamentoPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin-acompanhamento'],
    queryFn: () => api.admin.acompanhamento(),
    refetchInterval: 30_000,
  })

  return (
    <div className="mx-auto max-w-6xl">
      <TopBar
        title="Acompanhamento"
        subtitle="Quem entrou, qual serviço usou e quantos processos deram certo ou errado."
      />

      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Carregando
        </div>
      )}
      {isError && <p className="text-sm text-destructive">Não foi possível carregar o acompanhamento.</p>}

      {data && (
        <div className="space-y-8">
          <section className="rounded-2xl border border-border bg-card">
            <div className="flex items-center gap-2 border-b border-border px-4 py-3">
              <Eye className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold">Por usuário</h2>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Usuário</TableHead>
                  <TableHead>Último login</TableHead>
                  <TableHead>Vezes</TableHead>
                  <TableHead>Processos</TableHead>
                  <TableHead>Sucesso</TableHead>
                  <TableHead>Erro</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.resumo.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-muted-foreground">
                      Ainda não há uso registrado.
                    </TableCell>
                  </TableRow>
                )}
                {data.resumo.map((item) => (
                  <TableRow key={item.usuario}>
                    <TableCell>{item.usuario}</TableCell>
                    <TableCell>{fmtDate(item.ultimo_login)}</TableCell>
                    <TableCell>{item.vezes}</TableCell>
                    <TableCell>{item.total}</TableCell>
                    <TableCell>{item.sucesso}</TableCell>
                    <TableCell>{item.erro}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </section>

          <section className="rounded-2xl border border-border bg-card">
            <div className="border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold">Atividade</h2>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Quando</TableHead>
                  <TableHead>Usuário</TableHead>
                  <TableHead>Login</TableHead>
                  <TableHead>Origem</TableHead>
                  <TableHead>Serviço</TableHead>
                  <TableHead>Processos</TableHead>
                  <TableHead>Sucesso</TableHead>
                  <TableHead>Erro</TableHead>
                  <TableHead>Computador</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.linhas.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} className="text-muted-foreground">
                      Nenhuma atividade.
                    </TableCell>
                  </TableRow>
                )}
                {data.linhas.map((item, index) => (
                  <TableRow key={`${item.quando}-${item.usuario}-${item.servico}-${index}`}>
                    <TableCell>{fmtDate(item.quando)}</TableCell>
                    <TableCell>{item.usuario}</TableCell>
                    <TableCell>{fmtDate(item.ultimo_login)}</TableCell>
                    <TableCell>{item.origem}</TableCell>
                    <TableCell>{item.servico}</TableCell>
                    <TableCell>{item.servico === 'Login' ? '—' : item.total}</TableCell>
                    <TableCell>{item.servico === 'Login' ? '—' : item.sucesso}</TableCell>
                    <TableCell>{item.servico === 'Login' ? '—' : item.erro}</TableCell>
                    <TableCell className="max-w-[180px] truncate">{item.maquina || '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </section>
        </div>
      )}
    </div>
  )
}
