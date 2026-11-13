import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Eye, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import { TopBar } from '@/components/layout/TopBar'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
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

type OrigemFiltro = 'tudo' | 'site' | 'aplicativo'

const FILTROS: { id: OrigemFiltro; label: string }[] = [
  { id: 'tudo', label: 'Tudo' },
  { id: 'site', label: 'Site' },
  { id: 'aplicativo', label: 'Aplicativo' },
]

export function AcompanhamentoPage() {
  const [origem, setOrigem] = useState<OrigemFiltro>('tudo')
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin-acompanhamento'],
    queryFn: () => api.admin.acompanhamento(),
    refetchInterval: 30_000,
  })

  const linhas = useMemo(() => {
    const todas = data?.linhas ?? []
    if (origem === 'site') return todas.filter((item) => item.origem === 'Site')
    if (origem === 'aplicativo') return todas.filter((item) => item.origem === 'Valença Suite')
    return todas
  }, [data, origem])

  const resumo = useMemo(() => {
    const porUsuario = new Map<
      string,
      {
        usuario: string
        ultimo_login: string | null
        total: number
        sucesso: number
        erro: number
        vezes: number
      }
    >()
    for (const item of linhas) {
      if (item.servico === 'Login') continue
      const atual = porUsuario.get(item.usuario) ?? {
        usuario: item.usuario || '—',
        ultimo_login: item.ultimo_login,
        total: 0,
        sucesso: 0,
        erro: 0,
        vezes: 0,
      }
      atual.total += item.total
      atual.sucesso += item.sucesso
      atual.erro += item.erro
      atual.vezes += 1
      if (item.ultimo_login && (!atual.ultimo_login || item.ultimo_login > atual.ultimo_login)) {
        atual.ultimo_login = item.ultimo_login
      }
      porUsuario.set(item.usuario, atual)
    }
    return [...porUsuario.values()].sort((a, b) => b.vezes - a.vezes)
  }, [linhas])

  return (
    <div className="mx-auto max-w-6xl">
      <TopBar
        title="Acompanhamento"
        subtitle="Quem entrou, qual serviço usou e quantos processos deram certo ou errado."
        actions={
          <div className="flex rounded-xl border border-border bg-card p-1">
            {FILTROS.map((item) => (
              <Button
                key={item.id}
                type="button"
                size="sm"
                variant="ghost"
                className={cn(
                  'rounded-lg px-3',
                  origem === item.id && 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground',
                )}
                onClick={() => setOrigem(item.id)}
              >
                {item.label}
              </Button>
            ))}
          </div>
        }
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
                {resumo.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-muted-foreground">
                      Ainda não há uso registrado neste filtro.
                    </TableCell>
                  </TableRow>
                )}
                {resumo.map((item) => (
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
                {linhas.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} className="text-muted-foreground">
                      Nenhuma atividade neste filtro.
                    </TableCell>
                  </TableRow>
                )}
                {linhas.map((item, index) => (
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
