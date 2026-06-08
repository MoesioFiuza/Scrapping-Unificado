import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Scale, Loader2, ShieldCheck } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/'

  const loginMutation = useMutation({
    mutationFn: () => api.auth.login(username.trim(), password),
    onSuccess: async (data) => {
      if (data.success) {
        await queryClient.invalidateQueries({ queryKey: ['auth'] })
        toast.success('Sessão iniciada')
        navigate(from, { replace: true })
      } else {
        toast.error(data.error || 'Credenciais inválidas')
      }
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password) {
      toast.error('Preencha usuário e senha')
      return
    }
    loginMutation.mutate()
  }

  return (
    <div className="flex min-h-screen">
      {/* Brand panel */}
      <div className="relative hidden w-[45%] overflow-hidden bg-sidebar lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgb(99_102_241/0.25),transparent_55%)]" />
        <div className="relative flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-lg shadow-indigo-900/40">
            <Scale className="h-5 w-5" />
          </div>
          <div>
            <p className="text-lg font-semibold text-white">Scraper Unificado</p>
            <p className="text-sm text-sidebar-muted">Plataforma de extração processual</p>
          </div>
        </div>

        <div className="relative space-y-6">
          <h2 className="text-3xl font-semibold leading-tight text-white">
            Consulta e extração de processos judiciais num só lugar.
          </h2>
          <ul className="space-y-3 text-sm text-sidebar-muted">
            <li className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 shrink-0 text-indigo-400" />
              Acesso restrito à equipa autorizada
            </li>
            <li className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 shrink-0 text-indigo-400" />
              Múltiplos tribunais e modos de extração
            </li>
            <li className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 shrink-0 text-indigo-400" />
              Histórico de planilhas geradas
            </li>
          </ul>
        </div>

        <p className="relative text-xs text-sidebar-muted">
          Ferramenta interna · Uso exclusivo autorizado
        </p>
      </div>

      {/* Form */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
        <div className="w-full max-w-[400px]">
          <div className="mb-8 lg:hidden">
            <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white">
              <Scale className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-semibold">Scraper Unificado</h1>
            <p className="mt-1 text-sm text-muted-foreground">Inicie sessão para continuar</p>
          </div>

          <div className="hidden lg:block mb-8">
            <h1 className="text-2xl font-semibold tracking-tight">Bem-vindo de volta</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Introduza as suas credenciais para aceder à plataforma.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="username">E-mail</Label>
              <Input
                id="username"
                type="email"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="nome@empresa.com"
                className="h-11"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Palavra-passe</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11"
              />
            </div>
            <Button type="submit" className="h-11 w-full" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  A autenticar...
                </>
              ) : (
                'Entrar'
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
