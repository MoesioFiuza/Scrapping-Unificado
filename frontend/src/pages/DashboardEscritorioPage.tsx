import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  ArrowLeft,
  BarChart3,
  Building2,
  CheckCircle2,
  FileStack,
  Loader2,
  TrendingUp,
  Users,
  XCircle,
} from 'lucide-react'
import { api } from '@/lib/api'
import { TopBar } from '@/components/layout/TopBar'
import { DarkStatCard } from '@/components/layout/DarkStatCard'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'

function fmtDate(iso: string | null | undefined) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function taxaBadgeClass(pct: number) {
  if (pct >= 90) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
  if (pct >= 70) return 'bg-amber-500/15 text-amber-400 border-amber-500/30'
  return 'bg-red-500/15 text-red-400 border-red-500/30'
}

function PeriodBars({
  hoje,
  semana,
  mes,
}: {
  hoje: number
  semana: number
  mes: number
}) {
  const max = Math.max(hoje, semana, mes, 1)
  const bars = [
    { label: 'Hoje', value: hoje, className: 'bg-indigo-500' },
    { label: '7 dias', value: semana, className: 'bg-violet-500' },
    { label: '30 dias', value: mes, className: 'bg-fuchsia-500' },
  ]
  return (
    <div className="space-y-4">
      {bars.map((b) => (
        <div key={b.label}>
          <div className="mb-1.5 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{b.label}</span>
            <span className="font-semibold tabular-nums">{b.value}</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-muted/40">
            <div
              className={cn('h-full rounded-full transition-all duration-500', b.className)}
              style={{ width: `${Math.max(4, (b.value / max) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

export function DashboardEscritorioPage() {
  const { data, isLoading, isFetching, dataUpdatedAt } = useQuery({
    queryKey: ['admin-dashboard-escritorio'],
    queryFn: () => api.admin.dashboardEscritorio(30),
    refetchInterval: 12_000,
  })

  const maxTribunalExtracoes = useMemo(
    () => Math.max(...(data?.top_tribunais.map((t) => t.extracoes) ?? [1]), 1),
    [data?.top_tribunais],
  )

  if (isLoading || !data) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
      </div>
    )
  }

  const { periodos, taxa_sucesso_global: taxaGlobal } = data

  return (
    <div className="space-y-6">
      <TopBar
        title="Dashboard Escritório"
        subtitle="Visão de gestão — extrações, tribunais e actividade da equipa."
        actions={
          <div className="flex items-center gap-2">
            {isFetching && (
              <span className="text-xs text-muted-foreground">A actualizar…</span>
            )}
            <Button variant="outline" size="sm" asChild>
              <Link to="/admin">
                <ArrowLeft className="h-4 w-4" />
                Administração
              </Link>
            </Button>
          </div>
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <DarkStatCard
          label="Extrações hoje"
          value={periodos.hoje.extracoes}
          icon={FileStack}
          hint={`${periodos.hoje.processos} processos`}
        />
        <DarkStatCard
          label="Extrações (7 dias)"
          value={periodos.semana.extracoes}
          icon={BarChart3}
          hint={`${periodos.semana.processos} processos`}
        />
        <DarkStatCard
          label="Taxa de sucesso (30d)"
          value={taxaGlobal.taxa_pct != null ? `${taxaGlobal.taxa_pct}%` : '—'}
          icon={TrendingUp}
          iconClass={
            taxaGlobal.taxa_pct != null && taxaGlobal.taxa_pct >= 90
              ? 'bg-emerald-500/15 text-emerald-400'
              : 'bg-amber-500/15 text-amber-400'
          }
          hint={
            taxaGlobal.sucesso + taxaGlobal.erro > 0
              ? `${taxaGlobal.sucesso} ok · ${taxaGlobal.erro} erros`
              : 'Sem jobs com parciais'
          }
        />
        <DarkStatCard
          label="Jobs activos agora"
          value={data.total_jobs_ativos}
          icon={Activity}
          iconClass={
            data.total_jobs_ativos > 0
              ? 'bg-amber-500/15 text-amber-400'
              : 'bg-indigo-500/15 text-indigo-400'
          }
          hint={data.total_jobs_ativos > 0 ? 'Scraper ou CLI em curso' : 'Nenhuma extração activa'}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="surface-card p-5">
          <h3 className="flex items-center gap-2 font-semibold">
            <BarChart3 className="h-4 w-4 text-indigo-400" />
            Extrações por período
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Ficheiros registados na base de dados
          </p>
          <div className="mt-5">
            <PeriodBars
              hoje={periodos.hoje.extracoes}
              semana={periodos.semana.extracoes}
              mes={periodos.mes.extracoes}
            />
          </div>
          <div className="mt-5 grid grid-cols-3 gap-2 border-t border-border-subtle pt-4 text-center text-xs">
            <div>
              <p className="font-semibold tabular-nums">{periodos.hoje.jobs_concluidos}</p>
              <p className="text-muted-foreground">Jobs hoje</p>
            </div>
            <div>
              <p className="font-semibold tabular-nums">{periodos.semana.jobs_concluidos}</p>
              <p className="text-muted-foreground">Jobs 7d</p>
            </div>
            <div>
              <p className="font-semibold tabular-nums">{periodos.mes.jobs_concluidos}</p>
              <p className="text-muted-foreground">Jobs 30d</p>
            </div>
          </div>
        </div>

        <div className="surface-card p-5">
          <h3 className="flex items-center gap-2 font-semibold">
            <Building2 className="h-4 w-4 text-violet-400" />
            Top tribunais (30 dias)
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">Por volume de extrações</p>
          {data.top_tribunais.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">Sem dados ainda</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {data.top_tribunais.map((t, i) => (
                <li key={t.codigo}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <span className="flex h-5 w-5 items-center justify-center rounded bg-muted/50 text-[10px] font-bold text-muted-foreground">
                        {i + 1}
                      </span>
                      <span className="font-medium">{t.nome}</span>
                    </span>
                    <span className="tabular-nums text-muted-foreground">
                      {t.extracoes} · {t.processos} proc.
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted/40">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
                      style={{ width: `${(t.extracoes / maxTribunalExtracoes) * 100}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <div className="surface-card overflow-hidden">
          <div className="border-b border-border-subtle px-5 py-4">
            <h3 className="flex items-center gap-2 font-semibold">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              Taxa de sucesso por tribunal
            </h3>
            <p className="text-sm text-muted-foreground">
              Últimos {data.dias_taxa_sucesso} dias · jobs concluídos com parciais
            </p>
          </div>
          {data.taxa_sucesso_por_tribunal.length === 0 ? (
            <p className="px-5 py-8 text-center text-sm text-muted-foreground">
              Ainda não há jobs concluídos com resultados parciais registados.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tribunal</TableHead>
                  <TableHead className="text-right">Sucesso</TableHead>
                  <TableHead className="text-right">Erros</TableHead>
                  <TableHead className="text-right">Taxa</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.taxa_sucesso_por_tribunal.map((t) => (
                  <TableRow key={t.codigo}>
                    <TableCell className="font-medium">{t.nome}</TableCell>
                    <TableCell className="text-right tabular-nums text-emerald-400">
                      {t.sucesso}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-red-400">{t.erro}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className={taxaBadgeClass(t.taxa_pct)}>
                        {t.taxa_pct}%
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        <div className="surface-card overflow-hidden">
          <div className="border-b border-border-subtle px-5 py-4">
            <h3 className="flex items-center gap-2 font-semibold">
              <Users className="h-4 w-4 text-indigo-400" />
              Utilizadores mais activos
            </h3>
            <p className="text-sm text-muted-foreground">Últimos 30 dias</p>
          </div>
          {data.utilizadores_ativos.length === 0 ? (
            <p className="px-5 py-8 text-center text-sm text-muted-foreground">
              Nenhuma extração registada neste período.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Utilizador</TableHead>
                  <TableHead className="text-right">Extrações</TableHead>
                  <TableHead className="text-right">Processos</TableHead>
                  <TableHead className="hidden sm:table-cell">Última</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.utilizadores_ativos.map((u) => (
                  <TableRow key={u.username}>
                    <TableCell className="max-w-[180px] truncate font-medium">
                      {u.username}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{u.extracoes_mes}</TableCell>
                    <TableCell className="text-right tabular-nums">{u.processos_mes}</TableCell>
                    <TableCell className="hidden text-xs text-muted-foreground sm:table-cell">
                      {fmtDate(u.ultima_extracao)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </div>

      <div className="surface-card overflow-hidden">
        <div className="border-b border-border-subtle px-5 py-4">
          <h3 className="flex items-center gap-2 font-semibold">
            <Activity className="h-4 w-4 text-amber-400" />
            Jobs em curso
          </h3>
          <p className="text-sm text-muted-foreground">
            Scraper normal e extrações CLI · actualização automática
          </p>
        </div>
        {data.total_jobs_ativos === 0 ? (
          <div className="flex flex-col items-center gap-2 px-5 py-10 text-center">
            <CheckCircle2 className="h-8 w-8 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">Nenhum job activo neste momento.</p>
          </div>
        ) : (
          <div className="divide-y divide-border-subtle">
            {data.jobs_em_curso.scraping.map((j) => (
              <div
                key={j.session_id}
                className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="border-indigo-500/40 text-indigo-300">
                      Scraper
                    </Badge>
                    <span className="text-sm font-medium">{j.username}</span>
                  </div>
                  <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                    {j.session_id.slice(0, 8)}…
                  </p>
                </div>
                <div className="text-right text-sm">
                  <p className="font-semibold tabular-nums">
                    {j.processos_concluidos}/{j.total_processos}
                  </p>
                  <p className="text-xs text-muted-foreground capitalize">{j.status}</p>
                </div>
              </div>
            ))}
            {data.jobs_em_curso.cli.map((j) => (
              <div
                key={j.job_id}
                className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="border-violet-500/40 text-violet-300">
                      CLI · {j.tribunal_key}
                    </Badge>
                    <span className="text-sm font-medium">{j.username}</span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {j.job_mode} · {j.total_processos} processos
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {j.status === 'running' && (
                    <Loader2 className="h-4 w-4 animate-spin text-amber-400" />
                  )}
                  {j.status === 'error' && <XCircle className="h-4 w-4 text-red-400" />}
                  <span className="text-sm capitalize text-muted-foreground">{j.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <p className="text-center text-[11px] text-muted-foreground">
        Dados gerados em {fmtDate(data.gerado_em)}
        {dataUpdatedAt ? ` · última actualização ${fmtDate(new Date(dataUpdatedAt).toISOString())}` : ''}
      </p>
    </div>
  )
}
