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

export interface DashboardPeriodoStats {
  extracoes: number
  processos: number
  jobs_concluidos: number
}

export interface DashboardTribunalRank {
  codigo: string
  nome: string
  extracoes: number
  processos: number
}

export interface DashboardTaxaTribunal {
  codigo: string
  nome: string
  sucesso: number
  erro: number
  taxa_pct: number
}

export interface DashboardUsuarioAtivo {
  username: string
  extracoes_mes: number
  processos_mes: number
  ultima_extracao: string | null
  ultimo_login: string | null
}

export interface DashboardEscritorio {
  success: boolean
  gerado_em: string
  dias_taxa_sucesso: number
  periodos: {
    hoje: DashboardPeriodoStats
    semana: DashboardPeriodoStats
    mes: DashboardPeriodoStats
  }
  taxa_sucesso_global: {
    sucesso: number
    erro: number
    taxa_pct: number | null
  }
  top_tribunais: DashboardTribunalRank[]
  taxa_sucesso_por_tribunal: DashboardTaxaTribunal[]
  utilizadores_ativos: DashboardUsuarioAtivo[]
  jobs_em_curso: {
    scraping: {
      session_id: string
      username: string
      status: string
      processos_em_fila: number
      processos_processando: number
      processos_concluidos: number
      total_processos: number
    }[]
    cli: {
      job_id: string
      username: string
      status: string
      tribunal_key: string
      job_mode: string
      total_processos: number
    }[]
  }
  total_jobs_ativos: number
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
