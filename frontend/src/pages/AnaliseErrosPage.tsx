import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Loader2, ScrollText } from 'lucide-react'
import { api } from '@/lib/api'
import { TopBar } from '@/components/layout/TopBar'
import { Button } from '@/components/ui/button'
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

export function AnaliseErrosPage() {
  const [usuario, setUsuario] = useState('')
  const [servico, setServico] = useState('')
  const [logAberto, setLogAberto] = useState<number | null>(null)
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin-analise-erros'],
    queryFn: () => api.admin.analiseErros(),
    refetchInterval: 30_000,
  })
  const logsQuery = useQuery({
    queryKey: ['admin-logs'],
    queryFn: () => api.admin.logs(),
    refetchInterval: 30_000,
  })
  const logDetalhe = useQuery({
    queryKey: ['admin-log', logAberto],
    queryFn: () => api.admin.log(logAberto as number),
    enabled: logAberto != null,
  })

  const usuarios = useMemo(() => {
    const nomes = new Set<string>()
    for (const item of data?.linhas ?? []) if (item.usuario) nomes.add(item.usuario)
    for (const item of logsQuery.data?.logs ?? []) if (item.usuario) nomes.add(item.usuario)
    return [...nomes].sort()
  }, [data, logsQuery.data])

  const servicos = useMemo(() => {
    const nomes = new Set<string>()
    for (const item of data?.linhas ?? []) if (item.servico) nomes.add(item.servico)
    for (const item of logsQuery.data?.logs ?? []) if (item.servico) nomes.add(item.servico)
    return [...nomes].sort()
  }, [data, logsQuery.data])

  const linhas = useMemo(() => {
    return (data?.linhas ?? []).filter((item) => {
      if (usuario && item.usuario !== usuario) return false
      if (servico && item.servico !== servico) return false
      return true
    })
  }, [data, usuario, servico])

  const logs = useMemo(() => {
    return (logsQuery.data?.logs ?? []).filter((item) => {
      if (usuario && item.usuario !== usuario) return false
      if (servico && item.servico !== servico) return false
      return true
    })
  }, [logsQuery.data, usuario, servico])

  return (
    <div className="mx-auto max-w-6xl">
      <TopBar
        title="Análise de erros"
        subtitle="Qual processo falhou, para quem, e a mensagem do erro."
        actions={
          <div className="flex gap-2">
            <select
              className="h-9 rounded-lg border border-border bg-card px-3 text-sm"
              value={usuario}
              onChange={(evento) => setUsuario(evento.target.value)}
            >
              <option value="">Todos os usuários</option>
              {usuarios.map((nome) => (
                <option key={nome} value={nome}>
                  {nome}
                </option>
              ))}
            </select>
            <select
              className="h-9 rounded-lg border border-border bg-card px-3 text-sm"
              value={servico}
              onChange={(evento) => setServico(evento.target.value)}
            >
              <option value="">Todos os fluxos</option>
              {servicos.map((nome) => (
                <option key={nome} value={nome}>
                  {nome}
                </option>
              ))}
            </select>
          </div>
        }
      />

      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Carregando
        </div>
      )}
      {isError && <p className="text-sm text-destructive">Não foi possível carregar a análise de erros.</p>}

      {data && (
        <section className="rounded-2xl border border-border bg-card">
          <div className="flex items-center gap-2 border-b border-border px-4 py-3">
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold">Falhas</h2>
            <span className="text-sm text-muted-foreground">{linhas.length}</span>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Quando</TableHead>
                <TableHead>Usuário</TableHead>
                <TableHead>Fluxo</TableHead>
                <TableHead>CNJ</TableHead>
                <TableHead>Erro</TableHead>
                <TableHead>Versão</TableHead>
                <TableHead>Computador</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {linhas.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-muted-foreground">
                    Nenhuma falha neste filtro.
                  </TableCell>
                </TableRow>
              )}
              {linhas.map((item, indice) => (
                <TableRow key={`${item.quando}-${item.cnj}-${indice}`}>
                  <TableCell className="whitespace-nowrap">{fmtDate(item.quando)}</TableCell>
                  <TableCell>{item.usuario || '—'}</TableCell>
                  <TableCell>{item.servico}</TableCell>
                  <TableCell className="whitespace-nowrap font-medium">{item.cnj || '—'}</TableCell>
                  <TableCell className="max-w-md whitespace-normal">{item.erro}</TableCell>
                  <TableCell>{item.versao || '—'}</TableCell>
                  <TableCell>{item.maquina || '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>
      )}

      {logsQuery.data && (
        <section className="mt-8 rounded-2xl border border-border bg-card">
          <div className="flex items-center gap-2 border-b border-border px-4 py-3">
            <ScrollText className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold">Logs das execuções</h2>
            <span className="text-sm text-muted-foreground">{logs.length}</span>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Quando</TableHead>
                <TableHead>Usuário</TableHead>
                <TableHead>Fluxo</TableHead>
                <TableHead>Versão</TableHead>
                <TableHead>Computador</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-muted-foreground">
                    Nenhum log neste filtro.
                  </TableCell>
                </TableRow>
              )}
              {logs.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="whitespace-nowrap">{fmtDate(item.quando)}</TableCell>
                  <TableCell>{item.usuario || '—'}</TableCell>
                  <TableCell>{item.servico}</TableCell>
                  <TableCell>{item.versao || '—'}</TableCell>
                  <TableCell>{item.maquina || '—'}</TableCell>
                  <TableCell>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => setLogAberto(logAberto === item.id ? null : item.id)}
                    >
                      {logAberto === item.id ? 'Fechar' : 'Ver log'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {logAberto != null && (
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap border-t border-border px-4 py-3 font-mono text-xs text-muted-foreground">
              {logDetalhe.isLoading ? 'Carregando…' : logDetalhe.data?.texto || 'Log vazio.'}
            </pre>
          )}
        </section>
      )}
    </div>
  )
}
