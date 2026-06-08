import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(ms: number): string {
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  const h = Math.floor(m / 60)
  if (h > 0) return `${h}h ${m % 60}m`
  if (m > 0) return `${m}m ${s % 60}s`
  return `${s}s`
}

export function processoCompativelComTribunal(tribunalProcesso: string | null, tribunalEscolhido: string): boolean {
  if (tribunalProcesso === tribunalEscolhido) return true
  if (tribunalEscolhido === '8.06_esaj' && tribunalProcesso === '8.06') return true
  return false
}
