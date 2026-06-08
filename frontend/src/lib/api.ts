import type {
  AuthUser,
  CliJobMode,
  CliJobStatus,
  CliOpcoes,
  DashboardEscritorio,
  DashboardResumo,
  DataWebProcessarResponse,
  Extracao,
  Processo,
  ScrapingStatus,
  Tribunal,
  AdminUser,
  AuditLogEntry,
} from '@/types'
import { withBase } from '@/lib/paths'

class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(withBase(path), {
    credentials: 'include',
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    },
  })

  const isJson = res.headers.get('content-type')?.includes('application/json')
  const data = isJson ? await res.json() : null

  if (!res.ok) {
    const msg = data?.error || data?.message || `Erro HTTP ${res.status}`
    throw new ApiError(msg, res.status)
  }
  return data as T
}

export const api = {
  auth: {
    check: () =>
      fetch(withBase('/api/auth/check'), { credentials: 'include' }).then(async (res) => {
        if (res.status === 401) return { authenticated: false } as AuthUser
        return res.json() as Promise<AuthUser>
      }),
    login: (username: string, password: string) =>
      request<{ success: boolean; role?: string; error?: string }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
    logout: () =>
      request<{ success: boolean }>('/api/auth/logout', { method: 'POST' }),
  },

  tribunais: {
    list: () =>
      request<{ success: boolean; tribunais: Tribunal[] }>('/api/tribunais'),
  },

  upload: {
    file: (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return request<{
        success: boolean
        filename: string
        total_processos: number
        processos: Processo[]
        error?: string
      }>('/api/upload', { method: 'POST', body: fd })
    },
  },

  processos: {
    startScraper: (processos: Processo[]) =>
      request<{ success: boolean; session_id?: string; error?: string }>(
        '/api/processos/scraper',
        { method: 'POST', body: JSON.stringify({ processos }) },
      ),
    scrapingStatus: (sessionId: string) =>
      request<ScrapingStatus>(`/api/processos/status/${sessionId}`),
    abortScraping: (sessionId: string) =>
      request<{ success: boolean }>(`/api/processos/abort/${sessionId}`, {
        method: 'POST',
      }),
    cliOpcoes: () =>
      request<{ success: boolean; opcoes: CliOpcoes }>('/api/processos/cli-opcoes'),
    startCli: (body: {
      tribunal_key: string
      browser: string
      job_mode: CliJobMode
      workers: number
      processos: Processo[]
    }) =>
      request<{ success: boolean; job_id?: string; error?: string }>(
        '/api/processos/cli-extracao',
        { method: 'POST', body: JSON.stringify(body) },
      ),
    cliStatus: (jobId: string) =>
      request<CliJobStatus>(`/api/processos/cli-extracao/${jobId}`),
    abortCli: (jobId: string) =>
      request<{ success: boolean; message?: string }>(
        `/api/processos/cli-extracao/${jobId}/abort`,
        { method: 'POST' },
      ),
  },

  resultados: {
    exportarRaspado: (resultados: Processo[]) =>
      fetch(withBase('/api/resultados/exportar'), {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resultados }),
      }),
    exportarTratado: (resultados: Processo[]) =>
      fetch(withBase('/api/resultados/exportar-tratado'), {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resultados }),
      }),
  },

  dataweb: {
    health: () =>
      request<{ success: boolean; healthy: boolean }>('/api/dataweb/health'),
    processar: (cnjs: string[]) =>
      request<DataWebProcessarResponse>('/api/dataweb/processar', {
        method: 'POST',
        body: JSON.stringify({ cnjs }),
      }),
  },

  extracoes: {
    list: () =>
      request<{ success: boolean; extracoes: Extracao[]; total: number }>(
        '/api/extracoes/listar',
      ),
    resumo: () =>
      request<{ success: boolean; resumo: DashboardResumo }>('/api/extracoes/resumo'),
    downloadUrl: (id: string) => withBase(`/api/extracoes/download/${id}`),
    delete: (id: string) =>
      request<{ success: boolean }>(`/api/extracoes/deletar/${id}`, {
        method: 'DELETE',
      }),
  },

  admin: {
    users: () =>
      request<{ success: boolean; users: AdminUser[]; is_super_admin: boolean }>(
        '/api/admin/users',
      ),
    addUser: (username: string, password: string, role: string) =>
      request<{ success: boolean; message?: string; error?: string }>(
        '/api/admin/users',
        { method: 'POST', body: JSON.stringify({ username, password, role }) },
      ),
    deleteUser: (username: string) =>
      request<{ success: boolean }>(`/api/admin/users/${encodeURIComponent(username)}`, {
        method: 'DELETE',
      }),
    updateRole: (username: string, role: string) =>
      request<{ success: boolean }>(
        `/api/admin/users/${encodeURIComponent(username)}/role`,
        { method: 'PUT', body: JSON.stringify({ role }) },
      ),
    scrapingStatus: () =>
      request<{
        success: boolean
        tem_extracao_ativa: boolean
        total_sessoes_ativas: number
        resumo: Record<string, number>
        jobs_cli_ativos?: { job_id: string; username: string; status: string }[]
      }>('/api/admin/scraping-status'),
    auditLogs: (limit = 50, offset = 0) =>
      request<{ success: boolean; logs: AuditLogEntry[]; total: number }>(
        `/api/admin/audit-logs?limit=${limit}&offset=${offset}`,
      ),
    dashboardEscritorio: (diasTaxa = 30) =>
      request<DashboardEscritorio>(
        `/api/admin/dashboard-escritorio?dias_taxa=${diasTaxa}`,
      ),
  },
}

export { ApiError }
