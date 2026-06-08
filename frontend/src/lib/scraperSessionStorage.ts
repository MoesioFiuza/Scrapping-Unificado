import type { CliDownloadItem } from '@/types'
import type { CliConfig } from '@/components/scraper/CliPanel'
import type { Processo, ScraperModo } from '@/types'
import type { DataWebResult } from '@/types'

const STORAGE_KEY = 'scraper-unificado:session'

export interface ScraperPersistedState {
  processos: Processo[]
  uploadFilename: string | null
  modo: ScraperModo
  cliConfig: CliConfig
  cliDownloads: CliDownloadItem[]
  completedModo: ScraperModo | null
  finishedDuration: string | null
  startedAt: number | null
  datawebResult: DataWebResult | null
  sessionId: string | null
  cliJobId: string | null
}

export function loadScraperSession(): ScraperPersistedState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const data = JSON.parse(raw) as ScraperPersistedState
    if (!Array.isArray(data.processos)) return null
    return data
  } catch {
    return null
  }
}

export function saveScraperSession(state: ScraperPersistedState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    /* quota / private mode */
  }
}

export function clearScraperSession(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}

export const defaultCliConfig: CliConfig = {
  tribunalKey: '',
  browser: 'chrome',
  jobMode: 'planilhas',
  workers: 3,
}

export function initialScraperState(): ScraperPersistedState {
  const saved = loadScraperSession()
  if (saved) {
    return {
      ...saved,
      cliConfig: { ...defaultCliConfig, ...saved.cliConfig },
      datawebResult: saved.datawebResult ?? null,
      sessionId: saved.sessionId ?? null,
      cliJobId: saved.cliJobId ?? null,
    }
  }
  return {
    processos: [],
    uploadFilename: null,
    modo: 'normal',
    cliConfig: defaultCliConfig,
    cliDownloads: [],
    completedModo: null,
    finishedDuration: null,
    startedAt: null,
    datawebResult: null,
    sessionId: null,
    cliJobId: null,
  }
}
