import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Link } from 'react-router-dom'
import { Loader2, UserPlus, Trash2, Activity, Users, CheckCircle2, ListOrdered, ScrollText, BarChart3 } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { TopBar } from '@/components/layout/TopBar'
import { DarkStatCard } from '@/components/layout/DarkStatCard'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export function AdminPage() {
  const queryClient = useQueryClient()
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'user' })

  const { data, isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => api.admin.users(),
  })

  const { data: scrapingData } = useQuery({
    queryKey: ['admin-scraping'],
    queryFn: () => api.admin.scrapingStatus(),
    refetchInterval: 5000,
  })

  const { data: auditData, isLoading: auditLoading } = useQuery({
    queryKey: ['admin-audit'],
    queryFn: () => api.admin.auditLogs(40),
  })

  const addMutation = useMutation({
    mutationFn: () => api.admin.addUser(newUser.username, newUser.password, newUser.role),
    onSuccess: (res) => {
      if (res.success) {
        toast.success(res.message || 'Utilizador adicionado')
        setNewUser({ username: '', password: '', role: 'user' })
        void queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      } else {
        toast.error(res.error || 'Erro')
      }
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const deleteMutation = useMutation({
    mutationFn: (username: string) => api.admin.deleteUser(username),
    onSuccess: () => {
      toast.success('Utilizador removido')
      void queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const roleMutation = useMutation({
    mutationFn: ({ username, role }: { username: string; role: string }) =>
      api.admin.updateRole(username, role),
    onSuccess: () => {
      toast.success('Permissão actualizada')
      void queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const users = data?.users ?? []
  const isSuperAdmin = data?.is_super_admin ?? false
  const resumo = scrapingData?.resumo

  return (
    <div className="space-y-6">
      <TopBar
        title="Administração"
        subtitle="Gestão de utilizadores e monitorização de extrações activas."
        actions={
          <Button variant="outline" size="sm" asChild>
            <Link to="/admin/dashboard">
              <BarChart3 className="h-4 w-4" />
              Dashboard Escritório
            </Link>
          </Button>
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <DarkStatCard label="Utilizadores" value={users.length} icon={Users} />
        <DarkStatCard
          label="Sessões activas"
          value={scrapingData?.total_sessoes_ativas ?? 0}
          icon={Activity}
          iconClass={
            scrapingData?.tem_extracao_ativa
              ? 'bg-amber-500/15 text-amber-400'
              : 'bg-indigo-500/15 text-indigo-400'
          }
        />
        <DarkStatCard label="Em fila" value={resumo?.total_processos_em_fila ?? 0} icon={ListOrdered} iconClass="bg-violet-500/15 text-violet-400" />
        <DarkStatCard label="Concluídos" value={resumo?.total_processos_concluidos ?? 0} icon={CheckCircle2} iconClass="bg-emerald-500/15 text-emerald-400" />
      </div>

      {scrapingData?.tem_extracao_ativa && (
        <div className="surface-card border-amber-500/30 bg-amber-500/5 p-5">
          <div className="flex items-center gap-2 text-base font-semibold text-amber-200">
            <Activity className="h-4 w-4" />
            Extrações em curso
          </div>
          <p className="mt-1 text-sm text-amber-200/70">
            {scrapingData.total_sessoes_ativas} sessão(ões) activa(s) neste momento.
          </p>
        </div>
      )}

      <div className="surface-card overflow-hidden">
        <div className="border-b border-border-subtle px-6 py-4">
          <h3 className="flex items-center gap-2 font-semibold">
            <ScrollText className="h-4 w-4 text-indigo-400" />
            Registo de auditoria
          </h3>
          <p className="text-sm text-muted-foreground">Últimas acções na aplicação</p>
        </div>
        {auditLoading ? (
          <div className="flex justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>Utilizador</TableHead>
                <TableHead>Acção</TableHead>
                <TableHead>Detalhes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(auditData?.logs ?? []).map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                    {new Date(log.created_at).toLocaleString('pt-BR')}
                  </TableCell>
                  <TableCell className="text-sm">{log.username ?? '—'}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="font-mono text-[10px]">
                      {log.action}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-xs truncate font-mono text-[10px] text-muted-foreground">
                    {JSON.stringify(log.details)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <div className="surface-card overflow-hidden">
        <div className="border-b border-border-subtle px-6 py-4">
          <h3 className="flex items-center gap-2 font-semibold">
            <UserPlus className="h-4 w-4 text-indigo-400" />
            Novo utilizador
          </h3>
        </div>
        <div className="p-6">
          <div className="grid gap-4 lg:grid-cols-4">
            <div className="space-y-2 lg:col-span-2">
              <Label>E-mail</Label>
              <Input
                value={newUser.username}
                onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                placeholder="email@empresa.com"
              />
            </div>
            <div className="space-y-2">
              <Label>Palavra-passe</Label>
              <Input
                type="password"
                value={newUser.password}
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Perfil</Label>
              <Select value={newUser.role} onValueChange={(v) => setNewUser({ ...newUser, role: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">Utilizador</SelectItem>
                  {(isSuperAdmin || newUser.role === 'admin') && (
                    <SelectItem value="admin">Administrador</SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button
            className="mt-4"
            onClick={() => addMutation.mutate()}
            disabled={addMutation.isPending || !newUser.username || !newUser.password}
          >
            {addMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Adicionar utilizador
          </Button>
        </div>
      </div>

      <div className="surface-card overflow-hidden">
        <div className="border-b border-border-subtle px-6 py-4">
          <h3 className="font-semibold">Utilizadores registados</h3>
          <p className="text-sm text-muted-foreground">{users.length} conta(s)</p>
        </div>
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>E-mail</TableHead>
                <TableHead>Perfil</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((u) => (
                <TableRow key={u.username}>
                  <TableCell className="font-medium">{u.username}</TableCell>
                  <TableCell>
                    <Badge variant={u.role === 'admin' ? 'default' : 'secondary'}>
                      {u.role === 'admin' ? 'Administrador' : 'Utilizador'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      {isSuperAdmin && (
                        <Select
                          value={u.role}
                          onValueChange={(role) =>
                            roleMutation.mutate({ username: u.username, role })
                          }
                        >
                          <SelectTrigger className="h-9 w-36">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="user">Utilizador</SelectItem>
                            <SelectItem value="admin">Administrador</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => deleteMutation.mutate(u.username)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}
