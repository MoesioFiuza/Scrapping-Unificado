import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  Building2,
  Download,
  FileStack,
  FolderOpen,
  Loader2,
  Play,
  RefreshCw,
  Square,
  TrendingUp,
} from 'lucide-react'
import { api } from '@/lib/api'
import { formatDuration, processoCompativelComTribunal } from '@/lib/utils'
import { formatNumero, labelCliFilename } from '@/lib/extracoes'
import {
  clearScraperSession,
  defaultCliConfig,
  initialScraperState,
  saveScraperSession,
} from '@/lib/scraperSessionStorage'
import type { Processo, ScraperModo } from '@/types'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { TopBar } from '@/components/layout/TopBar'
import { DarkStatCard } from '@/components/layout/DarkStatCard'
import { TribunaisSidebar } from '@/components/scraper/TribunaisSidebar'
import { UploadZone } from '@/components/scraper/UploadZone'
import { ProcessosList } from '@/components/scraper/ProcessosList'
import { CliPanel, type CliConfig } from '@/components/scraper/CliPanel'
import { DataWebPanel } from '@/components/scraper/DataWebPanel'
import type { DataWebResult } from '@/types'
import { WorkflowStepper, type WorkflowStep } from '@/components/scraper/WorkflowStepper'
import { RecentExtractionsTable } from '@/components/scraper/RecentExtractionsTable'
import { ActivityFeed } from '@/components/scraper/ActivityFeed'
import {
  ExtractionResultPanel,
} from '@/components/scraper/ExtractionResultPanel'
import type { CliDownloadItem } from '@/types'

function applyParciais(processos: Processo[], parciais: Processo[]): Processo[] {
  const map = new Map(parciais.map((r) => [String(r.numero_processo).trim(), r]))
  return processos.map((p) => {
    const hit = map.get(String(p.numero_processo).trim())
    return hit ? { ...p, ...hit } : p
  })
}

function downloadBlob(res: Response, defaultName: string) {
  const cd = res.headers.get('content-disposition')
  const match = cd?.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
  const name = match?.[1]?.replace(/['"]/g, '') || defaultName
  return res.blob().then((blob) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = name
    a.click()
    URL.revokeObjectURL(url)
  })
}

export function ScraperPage() {
  const queryClient = useQueryClient()
  const initial = initialScraperState()
  const [processos, setProcessos] = useState<Processo[]>(initial.processos)
  const [uploadFilename, setUploadFilename] = useState<string | null>(initial.uploadFilename)
  const [modo, setModo] = useState<ScraperModo>(initial.modo)
  const [busy, setBusy] = useState(
    !!(initial.sessionId || initial.cliJobId) && initial.completedModo === null,
  )
  const [sessionId, setSessionId] = useState<string | null>(initial.sessionId ?? null)
  const [cliJobId, setCliJobId] = useState<string | null>(initial.cliJobId ?? null)
  const [cliDownloads, setCliDownloads] = useState<CliDownloadItem[]>(initial.cliDownloads)
  const [completedModo, setCompletedModo] = useState<ScraperModo | null>(initial.completedModo)
  const [finishedDuration, setFinishedDuration] = useState<string | null>(initial.finishedDuration)
  const [startedAt, setStartedAt] = useState<number | null>(initial.startedAt)
  const [cliConfig, setCliConfig] = useState<CliConfig>(initial.cliConfig)
  const [refreshing, setRefreshing] = useState(false)
  const [datawebBusy, setDatawebBusy] = useState(false)
  const [datawebResult, setDatawebResult] = useState<DataWebResult | null>(initial.datawebResult ?? null)

  const anyBusy = busy || datawebBusy

  const { data: tribData } = useQuery({
    queryKey: ['tribunais'],
    queryFn: () => api.tribunais.list(),
  })

  const { data: resumoData, refetch: refetchResumo, isFetching: resumoFetching } = useQuery({
    queryKey: ['extracoes', 'resumo'],
    queryFn: () => api.extracoes.resumo(),
  })

  const resumo = resumoData?.resumo

  const tribunaisMap = Object.fromEntries(
    (tribData?.tribunais ?? []).map((t) => [t.codigo, t.nome]),
  )
  const tribCount = tribData?.tribunais?.length ?? 0

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startedAtRef = useRef<number | null>(null)

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  useEffect(() => () => stopPolling(), [stopPolling])

  useEffect(() => {
    if (initial.startedAt) {
      startedAtRef.current = initial.startedAt
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    saveScraperSession({
      processos,
      uploadFilename,
      modo,
      cliConfig,
      cliDownloads,
      completedModo,
      finishedDuration,
      startedAt,
      datawebResult,
      sessionId,
      cliJobId,
    })
  }, [
    processos,
    uploadFilename,
    modo,
    cliConfig,
    cliDownloads,
    completedModo,
    finishedDuration,
    startedAt,
    datawebResult,
    sessionId,
    cliJobId,
  ])

  const stats = {
    total: processos.length,
    sucesso: processos.filter((p) => p.status === 'sucesso').length,
    erro: processos.filter((p) => p.status === 'erro').length,
    processando: processos.filter((p) => p.status === 'processando').length,
  }

  const doneCount = stats.sucesso + stats.erro
  const progressPct = processos.length ? Math.round((doneCount / processos.length) * 100) : 0
  const successRate =
    doneCount > 0 ? `${((stats.sucesso / doneCount) * 100).toFixed(1).replace('.', ',')}%` : '—'

  const etaText = (() => {
    if (!startedAt || !processos.length) return null
    const elapsed = Date.now() - startedAt
    if (doneCount === 0) {
      return `Aguardando 1.º resultado · ${formatDuration(elapsed)}`
    }
    const avg = elapsed / doneCount
    const remaining = (processos.length - doneCount) * avg
    return `${doneCount}/${processos.length} · ~${formatDuration(remaining)} restante`
  })()

  const workflowStep: WorkflowStep = useMemo(() => {
    if (processos.length === 0) return 1
    if (busy) return 3
    if (completedModo !== null) return 4
    if (doneCount === processos.length && doneCount > 0) return 4
    return 2
  }, [processos.length, busy, doneCount, completedModo])

  const activityExtra = useMemo(() => {
    const items: { title: string; desc: string; time: string }[] = []
    if (uploadFilename && processos.length > 0) {
      items.push({
        title: 'Planilha carregada',
        desc: `${processos.length} processos em ${uploadFilename}`,
        time: 'Agora',
      })
    }
    if (busy) {
      items.unshift({
        title: modo === 'cli' ? 'Extração CLI em curso' : 'Scraping em curso',
        desc: `${doneCount}/${processos.length} concluídos (${progressPct}%)`,
        time: 'Em progresso',
      })
    } else if (workflowStep === 4) {
      items.unshift({
        title: 'Extração concluída',
        desc: `${stats.sucesso} sucesso · ${stats.erro} erro(s)`,
        time: 'Concluído',
      })
    }
    return items
  }, [
    uploadFilename,
    processos.length,
    busy,
    modo,
    doneCount,
    progressPct,
    workflowStep,
    stats.sucesso,
    stats.erro,
  ])

  const startScrapingPolling = useCallback(
    (sid: string) => {
      stopPolling()
      pollingRef.current = setInterval(async () => {
        try {
          const st = await api.processos.scrapingStatus(sid)
          if (st.resultados_parciais?.length) {
            setProcessos((prev) => applyParciais(prev, st.resultados_parciais!))
          }
          if (st.status === 'completed') {
            stopPolling()
            if (st.resultados?.length) {
              setProcessos((prev) => applyParciais(prev, st.resultados!))
            }
            setBusy(false)
            setSessionId(null)
            setCompletedModo('normal')
            if (startedAtRef.current) {
              setFinishedDuration(formatDuration(Date.now() - startedAtRef.current))
            }
            toast.success('Raspagem concluída!')
            void queryClient.invalidateQueries({ queryKey: ['extracoes'] })
          } else if (st.status === 'error' || st.status === 'aborted' || st.status === 'interrupted') {
            stopPolling()
            setBusy(false)
            setSessionId(null)
            toast.error(st.error || 'Scraping interrompido')
          }
        } catch {
          /* retry */
        }
      }, 1500)
    },
    [queryClient, stopPolling],
  )

  const startCliPolling = useCallback(
    (jid: string) => {
      stopPolling()
      pollingRef.current = setInterval(async () => {
        try {
          const j = await api.processos.cliStatus(jid)
          if (j.resultados_parciais?.length) {
            setProcessos((prev) => applyParciais(prev, j.resultados_parciais!))
          }
          if (j.status === 'completed') {
            stopPolling()
            setBusy(false)
            setCliJobId(null)
            setCompletedModo('cli')
            if (startedAtRef.current) {
              setFinishedDuration(formatDuration(Date.now() - startedAtRef.current))
            }
            const ids = j.extracao_ids ?? []
            const names = j.filenames ?? []
            setCliDownloads(
              ids.map((id, i) => ({
                id,
                filename: names[i] ?? `extracao-${id}.xlsx`,
              })),
            )
            toast.success('Extração CLI concluída!')
            void queryClient.invalidateQueries({ queryKey: ['extracoes'] })
          } else if (j.status === 'error' || j.status === 'interrupted') {
            stopPolling()
            setBusy(false)
            setCliJobId(null)
            toast.error(j.error || 'Erro na extração CLI')
          } else if (j.status === 'aborted') {
            stopPolling()
            setBusy(false)
            setCliJobId(null)
            toast.info('Extração CLI cancelada')
          }
        } catch {
          /* retry */
        }
      }, 2000)
    },
    [queryClient, stopPolling],
  )

  useEffect(() => {
    if (initial.completedModo !== null) return
    if (initial.sessionId && initial.modo === 'normal') {
      startScrapingPolling(initial.sessionId)
    } else if (initial.cliJobId && initial.modo === 'cli') {
      startCliPolling(initial.cliJobId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const startNormalScraping = async () => {
    if (!processos.length) {
      toast.error('Faça upload de uma planilha primeiro')
      return
    }
    setBusy(true)
    setCompletedModo(null)
    setCliDownloads([])
    setFinishedDuration(null)
    const updated = processos.map((p) =>
      p.status === 'pendente' ? { ...p, status: 'processando' as const } : p,
    )
    setProcessos(updated)
    const now = Date.now()
    startedAtRef.current = now
    setStartedAt(now)

    try {
      const res = await api.processos.startScraper(updated)
      if (!res.success || !res.session_id) {
        toast.error(res.error || 'Erro ao iniciar scraping')
        setBusy(false)
        return
      }
      setSessionId(res.session_id)
      startScrapingPolling(res.session_id)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Erro')
      setBusy(false)
    }
  }

  const startCli = async () => {
    if (!processos.length) {
      toast.error('Faça upload de uma planilha primeiro')
      return
    }
    if (!cliConfig.tribunalKey) {
      toast.error('Selecione o tribunal CLI')
      return
    }
    const mism = processos.filter(
      (p) => !processoCompativelComTribunal(p.tribunal, cliConfig.tribunalKey),
    )
    if (mism.length) {
      toast.error(`${mism.length} processo(s) de outro tribunal`)
      return
    }

    setBusy(true)
    setCompletedModo(null)
    setCliDownloads([])
    setFinishedDuration(null)
    setProcessos((prev) =>
      prev.map((p) => (p.status === 'pendente' ? { ...p, status: 'processando' as const } : p)),
    )
    const now = Date.now()
    startedAtRef.current = now
    setStartedAt(now)

    try {
      const res = await api.processos.startCli({
        tribunal_key: cliConfig.tribunalKey,
        browser: cliConfig.browser,
        job_mode: cliConfig.jobMode,
        workers: cliConfig.workers,
        processos,
      })
      if (!res.success || !res.job_id) {
        toast.error(res.error || 'Erro ao iniciar CLI')
        setBusy(false)
        return
      }
      setCliJobId(res.job_id)
      startCliPolling(res.job_id)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Erro')
      setBusy(false)
    }
  }

  const abortScraping = async () => {
    if (sessionId) {
      await api.processos.abortScraping(sessionId)
      stopPolling()
      setBusy(false)
      setSessionId(null)
      toast.info('Scraping abortado')
    }
  }

  const abortCli = async () => {
    if (!cliJobId) return
    try {
      await api.processos.abortCli(cliJobId)
      stopPolling()
      setBusy(false)
      setCliJobId(null)
      setCompletedModo(null)
      toast.info('Extração CLI cancelada')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Erro ao cancelar')
    }
  }

  const handleAction = () => {
    if (modo === 'cli') void startCli()
    else void startNormalScraping()
  }

  const resetForNewExtraction = useCallback(() => {
    stopPolling()
    clearScraperSession()
    setProcessos([])
    setUploadFilename(null)
    setModo('normal')
    setBusy(false)
    setSessionId(null)
    setCliJobId(null)
    setCliDownloads([])
    setCompletedModo(null)
    setFinishedDuration(null)
    setStartedAt(null)
    startedAtRef.current = null
    setCliConfig(defaultCliConfig)
    setDatawebResult(null)
  }, [stopPolling])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      resetForNewExtraction()
      await Promise.all([
        refetchResumo(),
        queryClient.invalidateQueries({ queryKey: ['extracoes', 'recent'] }),
        queryClient.invalidateQueries({ queryKey: ['extracoes'] }),
      ])
      toast.success('Pronto para nova extração')
    } catch {
      toast.error('Erro ao atualizar')
    } finally {
      setRefreshing(false)
    }
  }

  const isRefreshing = refreshing || resumoFetching

  const exportar = async (tipo: 'raspado' | 'tratado') => {
    const ok = processos.filter((p) => p.status === 'sucesso')
    if (!ok.length) {
      toast.error('Nenhum processo com sucesso para exportar')
      return
    }
    const fn = tipo === 'raspado' ? api.resultados.exportarRaspado : api.resultados.exportarTratado
    try {
      const res = await fn(ok)
      if (!res.ok) throw new Error('Falha na exportação')
      await downloadBlob(res, `${tipo}.xlsx`)
      toast.success(`Planilha ${tipo} baixada`)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Erro na exportação')
    }
  }

  const showResult = completedModo !== null && !busy
  const sessionSuccessRate =
    doneCount > 0 ? `${((stats.sucesso / doneCount) * 100).toFixed(1).replace('.', ',')}%` : '—'
  const avgTime =
    startedAt && doneCount > 0
      ? formatDuration((Date.now() - startedAt) / doneCount)
      : '—'

  return (
    <div>
      <TopBar
        title="Nova Extração"
        subtitle="Carregue uma planilha, configure o modo de raspagem e acompanhe o progresso em tempo real."
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => void handleRefresh()}
            disabled={isRefreshing || anyBusy}
            className="h-10"
          >
            {isRefreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Atualizar
          </Button>
        }
      />

      <WorkflowStepper current={workflowStep} />

      <div className="grid gap-6 xl:grid-cols-[1fr_300px]">
        <div className="min-w-0 space-y-6">
          <div className="surface-card overflow-hidden">
            <div className="border-b border-border-subtle px-6 py-5">
              <h2 className="text-lg font-semibold">Upload da planilha</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                O sistema identifica automaticamente tribunal e número de cada processo.
              </p>
            </div>
            <div className="p-6">
              <UploadZone
                disabled={anyBusy}
                filename={uploadFilename}
                onClear={() => {
                  setProcessos([])
                  setUploadFilename(null)
                  setStartedAt(null)
                  startedAtRef.current = null
                  setCliDownloads([])
                  setCompletedModo(null)
                  setFinishedDuration(null)
                  setDatawebResult(null)
                }}
                onUploaded={(list, filename) => {
                  setProcessos(list)
                  setUploadFilename(filename)
                  setStartedAt(null)
                  startedAtRef.current = null
                  setCliDownloads([])
                  setCompletedModo(null)
                  setFinishedDuration(null)
                }}
              />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <DarkStatCard
              label="Tribunais disponíveis"
              value={tribCount}
              icon={Building2}
              iconClass="bg-indigo-500/15 text-indigo-400"
            />
            <DarkStatCard
              label="Processos extraídos (total)"
              value={resumo ? formatNumero(resumo.total_processos_extraidos) : '—'}
              icon={FileStack}
              iconClass="bg-violet-500/15 text-violet-400"
              hint={
                processos.length > 0
                  ? `Planilha atual: ${formatNumero(stats.total)}`
                  : undefined
              }
            />
            <DarkStatCard
              label="Taxa de sucesso (sessão)"
              value={processos.length > 0 ? sessionSuccessRate : '—'}
              icon={TrendingUp}
              iconClass="bg-emerald-500/15 text-emerald-400"
              hint={
                resumo && resumo.media_processos_por_ficheiro > 0
                  ? `Média global: ${formatNumero(Math.round(resumo.media_processos_por_ficheiro))} proc./ficheiro`
                  : undefined
              }
            />
            <DarkStatCard
              label="Ficheiros gerados"
              value={resumo ? formatNumero(resumo.total_ficheiros) : '—'}
              icon={FolderOpen}
              iconClass="bg-amber-500/15 text-amber-400"
              hint={
                resumo && resumo.extracoes_ultimos_30_dias > 0
                  ? `${formatNumero(resumo.extracoes_ultimos_30_dias)} nos últimos 30 dias`
                  : busy && avgTime !== '—'
                    ? `Tempo médio: ${avgTime}/proc.`
                    : undefined
              }
            />
          </div>

          {processos.length > 0 && (
            <>
              <div className="surface-card overflow-hidden">
                <div className="border-b border-border-subtle px-6 py-5">
                  <h2 className="text-lg font-semibold">Modo de extração</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Scraper normal processa na aplicação; CLI gera ficheiros para download.
                  </p>
                </div>
                <div className="space-y-6 p-6">
                  <Tabs value={modo} onValueChange={(v) => setModo(v as ScraperModo)}>
                    <TabsList className="w-full sm:w-auto flex-wrap h-auto">
                      <TabsTrigger value="normal" className="flex-1 sm:flex-none">
                        Scraper normal
                      </TabsTrigger>
                      <TabsTrigger value="cli" className="flex-1 sm:flex-none">
                        Extração CLI
                      </TabsTrigger>
                      <TabsTrigger value="dataweb" className="flex-1 sm:flex-none">
                        DataWeb
                      </TabsTrigger>
                    </TabsList>
                    <TabsContent value="normal" className="mt-4">
                      <p className="rounded-xl border border-border-subtle bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
                        Raspagem integrada com exportação imediata de planilhas raspada e tratada
                        após a conclusão.
                      </p>
                    </TabsContent>
                    <TabsContent value="cli" className="mt-4">
                      <CliPanel config={cliConfig} onChange={setCliConfig} tribunaisMap={tribunaisMap} />
                    </TabsContent>
                    <TabsContent value="dataweb" className="mt-4">
                      <DataWebPanel
                        processos={processos}
                        disabled={datawebBusy}
                        onBusyChange={setDatawebBusy}
                        result={datawebResult}
                        onResult={(r) => {
                          setDatawebResult(r)
                          if (r) {
                            setCompletedModo('dataweb')
                            void queryClient.invalidateQueries({ queryKey: ['extracoes'] })
                          }
                        }}
                      />
                    </TabsContent>
                  </Tabs>

                  {anyBusy && etaText && modo !== 'dataweb' && (
                    <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4">
                      <div className="mb-2 flex items-center justify-between text-sm">
                        <span className="font-semibold text-indigo-200">
                          {modo === 'cli' ? 'Extração CLI' : 'Scraping'} em curso
                        </span>
                        <span className="text-indigo-300/80">{etaText}</span>
                      </div>
                      <Progress value={progressPct} className="h-2" />
                    </div>
                  )}

                  {modo !== 'dataweb' && (
                  <div className="flex flex-wrap gap-3 border-t border-border-subtle pt-4">
                    <Button onClick={handleAction} disabled={busy} size="lg" className="min-w-[180px]">
                      {busy ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          A processar...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" />
                          {modo === 'cli' ? 'Iniciar extração CLI' : 'Iniciar scraping'}
                        </>
                      )}
                    </Button>

                    {busy && sessionId && modo === 'normal' && (
                      <Button variant="outline" onClick={() => void abortScraping()}>
                        <Square className="h-4 w-4" />
                        Abortar
                      </Button>
                    )}

                    {busy && cliJobId && modo === 'cli' && (
                      <Button variant="outline" onClick={() => void abortCli()}>
                        <Square className="h-4 w-4" />
                        Abortar CLI
                      </Button>
                    )}

                    {showResult && completedModo === 'normal' && stats.sucesso > 0 && (
                      <>
                        <Button variant="outline" onClick={() => void exportar('raspado')}>
                          <Download className="h-4 w-4" />
                          Exportar raspado
                        </Button>
                        <Button variant="outline" onClick={() => void exportar('tratado')}>
                          <Download className="h-4 w-4" />
                          Exportar tratado
                        </Button>
                      </>
                    )}

                    {showResult && completedModo === 'cli' && cliDownloads.length > 0 && (
                      <>
                        {cliDownloads.map((item) => (
                          <Button key={item.id} asChild variant="outline">
                            <a href={api.extracoes.downloadUrl(item.id)} download>
                              <Download className="h-4 w-4" />
                              {labelCliFilename(item.filename)}
                            </a>
                          </Button>
                        ))}
                      </>
                    )}
                  </div>
                  )}
                </div>
              </div>

              {showResult && completedModo !== 'dataweb' && (
                <ExtractionResultPanel
                  modo={completedModo}
                  stats={stats}
                  successRate={successRate}
                  durationLabel={finishedDuration}
                  cliDownloads={cliDownloads}
                  onExportRaspado={() => void exportar('raspado')}
                  onExportTratado={() => void exportar('tratado')}
                />
              )}

              <div className="surface-card overflow-hidden">
                <div className="border-b border-border-subtle px-6 py-5">
                  <h2 className="text-lg font-semibold">Processos</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Lista completa com filtros e pesquisa.
                  </p>
                </div>
                <div className="p-6">
                  <ProcessosList processos={processos} tribunaisMap={tribunaisMap} />
                </div>
              </div>
            </>
          )}

          <RecentExtractionsTable />
        </div>

        <div className="space-y-4">
          <div className="xl:sticky xl:top-6 xl:max-h-[calc(100vh-3rem)] xl:overflow-y-auto">
            <TribunaisSidebar processos={processos} />
            <div className="mt-4">
              <ActivityFeed extra={activityExtra} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
