import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Info } from 'lucide-react'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { api } from '@/lib/api'
import type { CliJobMode } from '@/types'

export interface CliConfig {
  tribunalKey: string
  browser: 'chrome' | 'edge'
  jobMode: CliJobMode
  workers: number
}

interface CliPanelProps {
  config: CliConfig
  onChange: (config: CliConfig) => void
  tribunaisMap: Record<string, string>
}

export function CliPanel({ config, onChange, tribunaisMap }: CliPanelProps) {
  const { data } = useQuery({
    queryKey: ['cli-opcoes'],
    queryFn: () => api.processos.cliOpcoes(),
  })

  const opcoes = data?.opcoes ?? {}
  const tribunalKeys = Object.keys(opcoes).filter((k) => tribunaisMap[k])
  const caps = opcoes[config.tribunalKey]?.[config.browser] ?? {}

  const modes: { value: CliJobMode; label: string; key: string }[] = [
    { value: 'movimentacoes', label: 'Só movimentações', key: 'movimentacoes' },
    { value: 'planilhas', label: 'Planilha completa (raspada + tratada)', key: 'planilhas' },
    { value: 'polos', label: 'Polos (partes e advogados)', key: 'polos' },
  ]

  useEffect(() => {
    if (tribunalKeys.length && !config.tribunalKey) {
      onChange({ ...config, tribunalKey: tribunalKeys[0]! })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tribunalKeys.length, config.tribunalKey])

  const set = (partial: Partial<CliConfig>) => onChange({ ...config, ...partial })

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="space-y-2">
          <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Tribunal
          </Label>
          <Select value={config.tribunalKey} onValueChange={(v) => set({ tribunalKey: v })}>
            <SelectTrigger className="h-10">
              <SelectValue placeholder="Selecione" />
            </SelectTrigger>
            <SelectContent>
              {tribunalKeys.map((k) => (
                <SelectItem key={k} value={k}>
                  {tribunaisMap[k] || k}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Navegador
          </Label>
          <Select value={config.browser} onValueChange={(v) => set({ browser: v as 'chrome' | 'edge' })}>
            <SelectTrigger className="h-10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {opcoes[config.tribunalKey]?.chrome && <SelectItem value="chrome">Chrome</SelectItem>}
              {opcoes[config.tribunalKey]?.edge && <SelectItem value="edge">Edge</SelectItem>}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Tipo de extração
          </Label>
          <Select value={config.jobMode} onValueChange={(v) => set({ jobMode: v as CliJobMode })}>
            <SelectTrigger className="h-10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {modes
                .filter((m) => caps[m.key] !== false)
                .map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Workers paralelos
          </Label>
          <Input
            type="number"
            min={1}
            max={8}
            className="h-10"
            value={config.workers}
            onChange={(e) =>
              set({ workers: Math.min(8, Math.max(1, parseInt(e.target.value, 10) || 1)) })
            }
          />
        </div>
      </div>

      <Alert variant="info">
        <Info className="h-4 w-4" />
        <AlertDescription>
          Todos os processos da planilha devem pertencer ao tribunal selecionado. A extração CLI
          pode demorar vários minutos — acompanhe o progresso abaixo e descarregue o ficheiro em{' '}
          <strong>Extrações</strong> quando concluir.
        </AlertDescription>
      </Alert>
    </div>
  )
}
