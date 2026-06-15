import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import {
  loadScraperSession,
  saveScraperSession,
  type ScraperPersistedState,
} from '@/lib/scraperSessionStorage'
import type { DataWebResult } from '@/types'

interface DataWebJobContextValue {
  jobId: string | null
  busy: boolean
  loteAtual: number
  totalLotes: number
  totalCnjs: number
  result: DataWebResult | null
  error: string | null
  startJob: (cnjs: string[]) => Promise<void>
  clearResult: () => void
}

const DataWebJobContext = createContext<DataWebJobContextValue | null>(null)

function patchSession(patch: Partial<ScraperPersistedState>) {
  const current = loadScraperSession()
  if (!current) {
    saveScraperSession({
      processos: [],
      uploadFilename: null,
      modo: 'dataweb',
      cliConfig: {
        tribunalKey: '',
        browser: 'chrome',
        jobMode: 'planilhas',
        workers: 3,
      },
      cliDownloads: [],
      completedModo: null,
      finishedDuration: null,
      startedAt: null,
      datawebResult: null,
      datawebJobId: null,
      sessionId: null,
      cliJobId: null,
      ...patch,
    })
    return
  }
  saveScraperSession({ ...current, ...patch })
}

export function DataWebJobProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const saved = loadScraperSession()
  const [jobId, setJobId] = useState<string | null>(saved?.datawebJobId ?? null)
  const [busy, setBusy] = useState(!!saved?.datawebJobId && !saved?.datawebResult)
  const [loteAtual, setLoteAtual] = useState(0)
  const [totalLotes, setTotalLotes] = useState(0)
  const [totalCnjs, setTotalCnjs] = useState(0)
  const [result, setResult] = useState<DataWebResult | null>(saved?.datawebResult ?? null)
  const [error, setError] = useState<string | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const completedRef = useRef(false)

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const applyCompleted = useCallback(
    (item: DataWebResult) => {
      if (completedRef.current) return
      completedRef.current = true
      setResult(item)
      setBusy(false)
      setJobId(null)
      patchSession({ datawebJobId: null, datawebResult: item })
      toast.success('Planilha DataWeb gerada com sucesso!')
      void queryClient.invalidateQueries({ queryKey: ['extracoes'] })
    },
    [queryClient],
  )

  const applyError = useCallback((msg: string) => {
    if (completedRef.current) return
    completedRef.current = true
    setError(msg)
    setBusy(false)
    setJobId(null)
    patchSession({ datawebJobId: null })
    toast.error(msg)
  }, [])

  const startPolling = useCallback(
    (id: string) => {
      stopPolling()
      completedRef.current = false
      pollingRef.current = setInterval(async () => {
        try {
          const st = await api.dataweb.status(id)
          setLoteAtual(st.lote_atual ?? 0)
          setTotalLotes(st.total_lotes ?? 0)
          setTotalCnjs(st.total_cnjs ?? 0)

          if (st.status === 'completed' && st.extracao_id && st.filename) {
            stopPolling()
            applyCompleted({
              extracaoId: st.extracao_id,
              filename: st.filename,
              totalCnjs: st.total_cnjs ?? 0,
            })
          } else if (st.status === 'error' || st.status === 'interrupted') {
            stopPolling()
            applyError(st.error || 'Erro ao processar no DataWeb')
          }
        } catch {
          /* retry */
        }
      }, 2000)
    },
    [applyCompleted, applyError, stopPolling],
  )

  const startJob = useCallback(
    async (cnjs: string[]) => {
      setError(null)
      setResult(null)
      setBusy(true)
      completedRef.current = false
      patchSession({ datawebResult: null })

      try {
        const res = await api.dataweb.processar(cnjs)
        if (!res.success || !res.job_id) {
          const msg = res.error || 'Erro ao iniciar processamento DataWeb'
          setBusy(false)
          toast.error(msg)
          return
        }
        setJobId(res.job_id)
        setTotalCnjs(res.total_cnjs ?? cnjs.length)
        setTotalLotes(res.total_lotes ?? 1)
        patchSession({ datawebJobId: res.job_id, datawebResult: null })
        startPolling(res.job_id)
      } catch (err) {
        setBusy(false)
        toast.error(err instanceof Error ? err.message : 'Erro ao contactar DataWeb')
      }
    },
    [startPolling],
  )

  const clearResult = useCallback(() => {
    setResult(null)
    setError(null)
    patchSession({ datawebResult: null })
  }, [])

  useEffect(() => {
    if (jobId && busy && !result) {
      startPolling(jobId)
    }
    return () => stopPolling()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const value = useMemo(
    () => ({
      jobId,
      busy,
      loteAtual,
      totalLotes,
      totalCnjs,
      result,
      error,
      startJob,
      clearResult,
    }),
    [jobId, busy, loteAtual, totalLotes, totalCnjs, result, error, startJob, clearResult],
  )

  return <DataWebJobContext.Provider value={value}>{children}</DataWebJobContext.Provider>
}

export function useDataWebJob(): DataWebJobContextValue {
  const ctx = useContext(DataWebJobContext)
  if (!ctx) {
    throw new Error('useDataWebJob deve ser usado dentro de DataWebJobProvider')
  }
  return ctx
}
