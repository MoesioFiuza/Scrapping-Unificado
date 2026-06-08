# Frontend React — Scraper Unificado

Stack: **React 19 + Vite + TypeScript + Tailwind CSS 4 + shadcn/ui + TanStack Query**

Flask continua como API (`/api/*`). O React consome os mesmos endpoints com cookies de sessão.

## Desenvolvimento (recomendado)

Dois terminais:

**Terminal 1 — API Flask**
```powershell
cd "c:\Users\Moésio\Desktop\Scrapper Unificado"
python run.py
```

**Terminal 2 — Frontend Vite (hot reload)**
```powershell
cd "c:\Users\Moésio\Desktop\Scrapper Unificado\frontend"
npm install
npm run dev
```

Abra **http://localhost:5173** — o Vite faz proxy de `/api` para `http://127.0.0.1:5000`.

## Produção (build + Flask)

```powershell
cd frontend
npm install
npm run build
```

Com `frontend/dist/index.html` presente, o Flask serve automaticamente a SPA em `/`, `/login`, `/extracoes`, `/admin`.

```powershell
cd ..
python run.py
```

Abra **http://localhost:5000**

## Estrutura

```
frontend/src/
├── components/
│   ├── ui/          # shadcn (Button, Card, Select…)
│   ├── layout/      # AppLayout
│   └── scraper/     # Upload, processos, CLI
├── hooks/           # useAuth
├── lib/             # api.ts, utils.ts
├── pages/           # Login, Scraper, Extrações, Admin
└── types/           # TypeScript interfaces
```

## Rotas

| Rota | Página |
|------|--------|
| `/login` | Login |
| `/` | Scraper (upload + normal + CLI) |
| `/extracoes` | Minhas extrações |
| `/admin` | Painel admin (só role admin) |

## Fallback legado

Se `frontend/dist` não existir, Flask usa os templates antigos (`templates/index.html`, etc.).
