export type UserRole = 'admin' | 'user'

export interface AuthUser {
  authenticated: boolean
  username?: string
  role?: UserRole
}

export type ProcessoStatus = 'pendente' | 'processando' | 'sucesso' | 'erro'

export interface Processo {
  id?: number
  numero_processo: string
  tribunal: string | null
  status: ProcessoStatus
  dados?: unknown
  erro?: string | null
}

export interface Tribunal {
  codigo: string
  nome: string
  ramo_justica: string
  tribunal_cnj: string
}

export interface CliOpcoes {
  [tribunalKey: string]: {
    chrome?: Record<string, boolean>
    edge?: Record<string, boolean>
  }
}

export type ScraperModo = 'normal' | 'cli' | 'dataweb'
export type CliJobMode = 'movimentacoes' | 'planilhas' | 'polos'

export interface ScrapingStatus {
  status: 'starting' | 'processing' | 'completed' | 'error' | 'aborted' | 'interrupted' | 'aborting'
  total_processos?: number
  resultados_parciais?: Processo[]
  resultados?: Processo[]
  error?: string
}

export interface CliJobStatus {
  status: 'queued' | 'running' | 'completed' | 'error' | 'aborted' | 'aborting' | 'interrupted'
  error?: string | null
  extracao_ids?: string[]
  filenames?: string[]
  total_processos?: number
  resultados_parciais?: Processo[]
}

export interface AuditLogEntry {
  id: number
  username: string | null
  action: string
  details: Record<string, unknown>
  ip_address: string | null
  created_at: string
}

export interface Extracao {
  id: string
  username: string
  filename: string
  tipo: string
  data_criacao: string
  total_processos: number
  filepath: string
  estatisticas?: {
    total_processos: number
    tribunais: Record<string, { count: number; percent: number }>
    total_tribunais?: number
    maior_tribunal?: { codigo: string | null; count: number } | null
  }
}

export interface CliDownloadItem {
  id: string
  filename: string
}

export interface AdminUser {
  username: string
  role: UserRole
}

export interface DashboardResumo {
  total_ficheiros: number
  total_processos_extraidos: number
  media_processos_por_ficheiro: number
  extracoes_ultimos_30_dias: number
  extracoes_cli: number
  extracoes_app: number
}

export interface DataWebProcessarResponse {
  success: boolean
  extracao_id?: string
  filename?: string
  total_cnjs?: number
  error?: string
  title?: string
}

export interface DataWebResult {
  extracaoId: string
  filename: string
  totalCnjs: number
}
