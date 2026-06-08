/** Prefixo público da app (ex.: /scraper). Vite define BASE_URL com barra final. */
const raw = import.meta.env.BASE_URL || '/'
export const BASE_PATH = raw.endsWith('/') && raw.length > 1 ? raw.slice(0, -1) : raw === '/' ? '' : raw

/** Monta URL absoluta dentro do subpath (ex.: /scraper/api/foo). */
export function withBase(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  return `${BASE_PATH}${p}`
}
