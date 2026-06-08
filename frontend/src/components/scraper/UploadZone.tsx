import { useCallback, useRef, useState } from 'react'
import { Upload, FileSpreadsheet, X, Loader2, CloudUpload } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import type { Processo } from '@/types'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface UploadZoneProps {
  onUploaded: (processos: Processo[], filename: string) => void
  disabled?: boolean
  filename?: string | null
  onClear?: () => void
}

export function UploadZone({ onUploaded, disabled, filename: filenameProp, onClear }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [localFilename, setLocalFilename] = useState<string | null>(null)

  const filename = filenameProp !== undefined ? filenameProp : localFilename

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.match(/\.(xlsx|xls|csv)$/i)) {
        toast.error('Formato inválido. Use .xlsx, .xls ou .csv')
        return
      }
      setUploading(true)
      try {
        const data = await api.upload.file(file)
        if (data.success) {
          if (filenameProp === undefined) setLocalFilename(data.filename)
          onUploaded(data.processos, data.filename)
          toast.success(`${data.total_processos} processos identificados`)
        }
      } catch (err) {
        toast.error(err instanceof Error ? err.message : 'Erro no upload')
      } finally {
        setUploading(false)
      }
    },
    [onUploaded, filenameProp],
  )

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (disabled || uploading) return
    const file = e.dataTransfer.files[0]
    if (file) void handleFile(file)
  }

  const clear = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (filenameProp === undefined) setLocalFilename(null)
    onClear?.()
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          'relative flex min-h-[220px] flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 transition-all',
          dragging
            ? 'border-indigo-500 bg-indigo-500/10'
            : 'border-border-subtle bg-background/50 hover:border-indigo-500/40 hover:bg-indigo-500/[0.04]',
          (disabled || uploading) && 'pointer-events-none opacity-50',
        )}
      >
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/15 ring-1 ring-indigo-500/20">
          {uploading ? (
            <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
          ) : (
            <CloudUpload className="h-8 w-8 text-indigo-400" />
          )}
        </div>
        <p className="text-base font-medium text-foreground">
          {uploading ? 'A processar ficheiro...' : 'Arraste sua planilha aqui'}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">ou clique para selecionar</p>
        <Button
          type="button"
          className="mt-6 min-w-[160px] shadow-lg shadow-indigo-950/30"
          disabled={disabled || uploading}
          onClick={(e) => {
            e.stopPropagation()
            inputRef.current?.click()
          }}
        >
          <Upload className="h-4 w-4" />
          Selecionar arquivo
        </Button>
        <p className="mt-4 text-xs text-muted-foreground">
          Formatos: .xlsx, .xls, .csv · Máx. 16 MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) void handleFile(file)
          }}
        />
      </div>

      {filename && (
        <div className="flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400">
              <FileSpreadsheet className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-emerald-100">{filename}</p>
              <p className="text-xs text-emerald-400/80">Carregado com sucesso</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={clear}
            disabled={disabled}
            className="shrink-0 text-emerald-400 hover:text-emerald-300"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
