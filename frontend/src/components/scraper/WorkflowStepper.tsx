import { cn } from '@/lib/utils'
import { Check } from 'lucide-react'

export type WorkflowStep = 1 | 2 | 3 | 4

const steps = [
  { n: 1 as const, label: 'Upload' },
  { n: 2 as const, label: 'Configuração' },
  { n: 3 as const, label: 'Processamento' },
  { n: 4 as const, label: 'Resultado' },
]

interface WorkflowStepperProps {
  current: WorkflowStep
}

export function WorkflowStepper({ current }: WorkflowStepperProps) {
  return (
    <div className="mb-6 flex items-center gap-0 overflow-x-auto pb-1">
      {steps.map(({ n, label }, i) => {
        const done = n < current
        const active = n === current
        return (
          <div key={n} className="flex items-center">
            {i > 0 && (
              <div
                className={cn(
                  'mx-2 h-px w-8 sm:w-16',
                  done || active ? 'bg-indigo-500/60' : 'bg-border-subtle',
                )}
              />
            )}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <div
                className={cn(
                  'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-all',
                  done && 'bg-indigo-600 text-white',
                  active && 'bg-indigo-600 text-white ring-4 ring-indigo-600/25',
                  !done && !active && 'border border-border-subtle bg-card text-muted-foreground',
                )}
              >
                {done ? <Check className="h-3.5 w-3.5" /> : n}
              </div>
              <span
                className={cn(
                  'hidden text-sm font-medium sm:inline',
                  active ? 'text-white' : done ? 'text-indigo-300' : 'text-muted-foreground',
                )}
              >
                {label}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
