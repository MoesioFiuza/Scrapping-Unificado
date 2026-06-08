import type { Extracao } from '@/types'

export const TIPO_LABELS: Record<string, string> = {
  raspado: 'Raspado',
  tratado: 'Tratado',
  movimentacoes_cli: 'Movimentações CLI',
  polos_cli: 'Polos CLI',
  raspado_cli: 'Raspado CLI',
  tratado_cli: 'Tratado CLI',
  dataweb: 'DataWeb',
}

export const TIPO_VARIANT: Record<string, 'default' | 'secondary' | 'success' | 'outline'> = {
  raspado: 'secondary',
  tratado: 'success',
  movimentacoes_cli: 'outline',
  polos_cli: 'outline',
  raspado_cli: 'secondary',
  tratado_cli: 'success',
  dataweb: 'outline',
}

export function labelTipo(tipo: string): string {
  return TIPO_LABELS[tipo] ?? tipo
}

export function tribunalResumo(
  extracao: Extracao,
  tribunaisMap: Record<string, string> = {},
): string {
  const stats = extracao.estatisticas
  const maior = stats?.maior_tribunal?.codigo
  if (maior) {
    const nome = tribunaisMap[maior] ?? maior
    const totalT = stats?.total_tribunais ?? 1
    return totalT > 1 ? `${nome} (+${totalT - 1})` : nome
  }

  const fn = extracao.filename.replace(/\.xlsx$/i, '')
  for (const [codigo, nome] of Object.entries(tribunaisMap)) {
    const slug = nome.replace(/\s+/g, '_')
    if (fn.includes(slug) || fn.toUpperCase().includes(codigo.toUpperCase())) {
      return nome
    }
  }

  const m = fn.match(/^([A-Za-z0-9_]+?)_(?:chrome|edge)_/i)
  if (m?.[1]) return m[1].replace(/_/g, ' ')

  if (extracao.tipo.includes('cli')) return 'CLI'
  return '—'
}

export function formatNumero(n: number): string {
  return new Intl.NumberFormat('pt-BR').format(n)
}

export function labelCliFilename(filename: string): string {
  const lower = filename.toLowerCase()
  if (lower.includes('raspado') || lower.includes('raspados')) return 'Planilha raspada (raw)'
  if (lower.includes('tratado') || lower.includes('tratados')) return 'Planilha tratada'
  if (lower.includes('moviment')) return 'Movimentações'
  if (lower.includes('polos')) return 'Polos e advogados'
  return filename
}

export function processosCount(extracao: Extracao): number {
  return extracao.estatisticas?.total_processos ?? extracao.total_processos ?? 0
}
