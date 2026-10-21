import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Download, FileText, Loader2, Plus, RefreshCw, Send, Undo2, Upload } from 'lucide-react'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { DocumentoEquipe, DocumentoItem } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { TopBar } from '@/components/layout/TopBar'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const COMPRESSAO: Record<string, string> = {
  comprimido: 'comprimido',
  original_menor: 'já estava otimizado',
  assinado: 'assinado digitalmente — mantido original',
  desativada: 'sem compressão',
  sem_ghostscript: 'compressão indisponível no servidor',
  falhou: 'compressão falhou — mantido original',
  paginas_divergentes: 'compressão alterou páginas — mantido original',
}

function mb(bytes?: number | null) {
  if (!bytes) return '—'
  return `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} MB`
}

function dataHora(iso?: string | null) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function useInvalidar() {
  const qc = useQueryClient()
  return () => void qc.invalidateQueries({ queryKey: ['documentos-admin'] })
}

function LinhaDocumento({
  equipe,
  doc,
  comprimir,
}: {
  equipe: DocumentoEquipe
  doc: DocumentoItem
  comprimir: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const invalidar = useInvalidar()
  const rascunho = doc.rascunho
  const tipoAtual = rascunho?.tipo || doc.tipo || ''

  const upload = useMutation({
    mutationFn: (file: File) => api.documentos.upload(equipe.id, doc.slot, file, { comprimir }),
    onSuccess: () => {
      toast.success(`"${doc.titulo}" enviado. Publique para os aplicativos receberem.`)
      invalidar()
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const tipo = useMutation({
    mutationFn: (novo: string) => api.documentos.definirTipo(equipe.id, doc.slot, novo),
    onSuccess: invalidar,
    onError: (err: Error) => toast.error(err.message),
  })

  const descartar = useMutation({
    mutationFn: () => api.documentos.descartar(equipe.id, doc.slot),
    onSuccess: invalidar,
    onError: (err: Error) => toast.error(err.message),
  })

  const shaPublicado = doc.publicado?.sha256

  return (
    <div
      className={cn(
        'grid gap-4 rounded-xl border p-4 md:grid-cols-[minmax(0,1fr)_220px_auto] md:items-center',
        rascunho ? 'border-amber-500/40 bg-amber-500/[0.04]' : 'border-border-subtle',
      )}
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-muted text-xs font-semibold">
            {doc.ordem}
          </span>
          <p className="truncate font-medium">{rascunho?.titulo || doc.titulo}</p>
          {rascunho && <Badge variant="warning">Pendente</Badge>}
        </div>
        <p className="mt-1 truncate font-mono text-[11px] text-muted-foreground" title={doc.nome_arquivo}>
          {doc.nome_arquivo}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {doc.publicado
            ? doc.publicado.origem === 'servidor'
              ? `Em uso: ${mb(doc.publicado.tamanho)} · ${doc.publicado.paginas ?? '?'} pág.`
              : 'Em uso: PDF que veio no instalador'
            : 'Documento novo'}
        </p>
        {rascunho?.sha256 && (
          <p className="mt-1 text-xs text-amber-300">
            Novo arquivo: {mb(rascunho.tamanho_original)} → {mb(rascunho.tamanho)} ·{' '}
            {rascunho.paginas} pág. · {COMPRESSAO[rascunho.compressao || ''] || rascunho.compressao} · por{' '}
            {rascunho.enviado_por}
          </p>
        )}
      </div>

      <div>
        {equipe.tipo_editavel ? (
          <Select value={tipoAtual} onValueChange={(v) => tipo.mutate(v)} disabled={tipo.isPending}>
            <SelectTrigger>
              <SelectValue placeholder="Tipo no PJe" />
            </SelectTrigger>
            <SelectContent>
              {equipe.tipos.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Badge variant="outline" title="No EPROC/eSAJ o tipo segue a posição do documento">
            {tipoAtual || '—'}
          </Badge>
        )}
      </div>

      <div className="flex flex-wrap justify-end gap-2">
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            e.target.value = ''
            if (file) upload.mutate(file)
          }}
        />
        <Button size="sm" onClick={() => inputRef.current?.click()} disabled={upload.isPending}>
          {upload.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
          {upload.isPending ? 'Comprimindo…' : 'Substituir'}
        </Button>
        {(rascunho?.sha256 || shaPublicado) && (
          <Button size="sm" variant="outline" asChild>
            <a href={api.documentos.arquivoUrl((rascunho?.sha256 || shaPublicado) as string, doc.nome_arquivo)}>
              <Download className="h-4 w-4" />
              Baixar
            </a>
          </Button>
        )}
        {rascunho && (
          <Button size="sm" variant="ghost" onClick={() => descartar.mutate()} disabled={descartar.isPending}>
            <Undo2 className="h-4 w-4" />
            Descartar
          </Button>
        )}
      </div>
    </div>
  )
}

function AdicionarDocumento({ equipe, comprimir }: { equipe: DocumentoEquipe; comprimir: boolean }) {
  const [titulo, setTitulo] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const invalidar = useInvalidar()

  const add = useMutation({
    mutationFn: (file: File) => api.documentos.upload(equipe.id, 'novo', file, { titulo, comprimir }),
    onSuccess: () => {
      toast.success('Documento adicionado. Publique para os aplicativos receberem.')
      setTitulo('')
      invalidar()
    },
    onError: (err: Error) => toast.error(err.message),
  })

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-dashed border-border-subtle p-4 sm:flex-row sm:items-center">
      <Input
        placeholder="Nome do documento novo (ex.: AGE 2026 - eleição diretoria)"
        value={titulo}
        onChange={(e) => setTitulo(e.target.value)}
        className="sm:flex-1"
      />
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          e.target.value = ''
          if (file) add.mutate(file)
        }}
      />
      <Button
        variant="outline"
        onClick={() => inputRef.current?.click()}
        disabled={!titulo.trim() || add.isPending}
      >
        {add.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
        Adicionar documento
      </Button>
    </div>
  )
}

function PainelEquipe({ equipe }: { equipe: DocumentoEquipe }) {
  const [comprimir, setComprimir] = useState(true)
  const invalidar = useInvalidar()

  const publicar = useMutation({
    mutationFn: () => api.documentos.publicar(equipe.id),
    onSuccess: (res) => {
      toast.success(`Versão ${res.versao} publicada. Os aplicativos baixam na próxima abertura.`)
      invalidar()
    },
    onError: (err: Error) => toast.error(err.message),
  })

  return (
    <div className="surface-card overflow-hidden">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border-subtle px-6 py-4">
        <div>
          <h3 className="flex items-center gap-2 font-semibold">
            <FileText className="h-4 w-4 text-indigo-400" />
            {equipe.nome}
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {equipe.versao
              ? `Versão ${equipe.versao} · publicada ${dataHora(equipe.publicado_em)} por ${equipe.publicado_por}`
              : 'Nenhuma versão publicada — os aplicativos usam os PDFs do instalador.'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={comprimir}
              onChange={(e) => setComprimir(e.target.checked)}
              className="h-4 w-4 accent-indigo-500"
            />
            Comprimir PDFs enviados
          </label>
          <Button onClick={() => publicar.mutate()} disabled={!equipe.pendentes || publicar.isPending}>
            {publicar.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Publicar {equipe.pendentes ? `(${equipe.pendentes})` : ''}
          </Button>
        </div>
      </div>
      <div className="space-y-3 p-6">
        {equipe.documentos.map((doc) => (
          <LinhaDocumento key={doc.slot} equipe={equipe} doc={doc} comprimir={comprimir} />
        ))}
        {equipe.pode_adicionar && <AdicionarDocumento equipe={equipe} comprimir={comprimir} />}
        <p className="pt-1 text-xs text-muted-foreground">
          O arquivo enviado é renomeado automaticamente para o nome que o robô espera. PDFs
          assinados digitalmente não são recomprimidos para não invalidar a assinatura.
        </p>
      </div>
    </div>
  )
}

export function DocumentosPage() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['documentos-admin'],
    queryFn: () => api.documentos.estado(),
  })
  const equipes = data?.equipes ?? []
  const [ativa, setAtiva] = useState<string | null>(null)
  const equipe = equipes.find((e) => e.id === ativa) ?? equipes[0]

  return (
    <div className="space-y-6">
      <TopBar
        title="Documentos de habilitação"
        subtitle="PDFs anexados pela Valença Suite. Ao publicar, os aplicativos baixam na próxima abertura."
        actions={
          <Button variant="outline" onClick={() => void refetch()} disabled={isFetching}>
            {isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Atualizar
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2">
            {equipes.map((e) => (
              <button
                key={e.id}
                type="button"
                onClick={() => setAtiva(e.id)}
                className={cn(
                  'flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition-colors',
                  equipe?.id === e.id
                    ? 'border-indigo-500 bg-indigo-600/90 text-white'
                    : 'border-border-subtle bg-card text-muted-foreground hover:text-foreground',
                )}
              >
                {e.nome.split(' — ')[0]}
                {e.pendentes > 0 && (
                  <span className="rounded-full bg-amber-500 px-1.5 text-[11px] font-bold text-black">
                    {e.pendentes}
                  </span>
                )}
              </button>
            ))}
          </div>
          {equipe && <PainelEquipe key={equipe.id} equipe={equipe} />}
        </>
      )}
    </div>
  )
}
