import { Link } from 'react-router-dom'
import { Database, Loader2 } from 'lucide-react'
import { useDataWebJob } from '@/hooks/useDataWebJob'
import { Progress } from '@/components/ui/progress'

export function DataWebProgressBanner() {
  const { busy, loteAtual, totalLotes, totalCnjs } = useDataWebJob()

  if (!busy) return null

  const pct =
    totalLotes > 0 ? Math.round((Math.max(loteAtual, 1) / totalLotes) * 100) : undefined

  return (
    <div className="mb-4 rounded-xl border border-indigo-500/30 bg-indigo-500/10 px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-medium text-indigo-200">
          <Loader2 className="h-4 w-4 animate-spin" />
          <Database className="h-4 w-4" />
          DataWeb a processar
          {totalCnjs > 0 ? ` · ${totalCnjs} CNJ(s)` : ''}
          {totalLotes > 1 ? ` · lote ${loteAtual || 1}/${totalLotes}` : ''}
        </div>
        <Link
          to="/"
          className="text-xs font-medium text-indigo-300 hover:text-indigo-200"
        >
          Ver na extração
        </Link>
      </div>
      {pct !== undefined && totalLotes > 1 && (
        <Progress value={pct} className="mt-2 h-1.5" />
      )}
      <p className="mt-1 text-xs text-indigo-300/70">
        Pode navegar para outras abas — o processamento continua em segundo plano.
      </p>
    </div>
  )
}
