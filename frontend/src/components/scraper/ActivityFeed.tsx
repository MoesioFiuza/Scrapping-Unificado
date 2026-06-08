import { Activity } from 'lucide-react'

const activities = [
  { title: 'Sistema iniciado', desc: 'Plataforma pronta para extrações', time: 'Agora' },
  { title: 'Tribunais carregados', desc: '10 sistemas disponíveis', time: 'Agora' },
]

interface ActivityFeedProps {
  extra?: { title: string; desc: string; time: string }[]
}

export function ActivityFeed({ extra = [] }: ActivityFeedProps) {
  const items = [...extra, ...activities].slice(0, 5)

  return (
    <div className="surface-card p-4">
      <div className="mb-4 flex items-center gap-2">
        <Activity className="h-4 w-4 text-indigo-400" />
        <h3 className="text-sm font-semibold">Atividade recente</h3>
      </div>
      <ul className="space-y-4">
        {items.map((item, i) => (
          <li key={i} className="relative pl-4">
            <span className="absolute left-0 top-1.5 h-2 w-2 rounded-full bg-emerald-500 ring-4 ring-emerald-500/15" />
            {i < items.length - 1 && (
              <span className="absolute bottom-[-14px] left-[3px] top-4 w-px bg-border-subtle" />
            )}
            <p className="text-sm font-medium leading-tight">{item.title}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">{item.desc}</p>
            <p className="mt-1 text-[10px] text-muted-foreground/70">{item.time}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}
