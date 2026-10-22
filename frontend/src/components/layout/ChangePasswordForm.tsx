import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { KeyRound, Loader2, X } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function ChangePasswordForm() {
  const [open, setOpen] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const mutation = useMutation({
    mutationFn: () => api.auth.changePassword(currentPassword, newPassword, confirmPassword),
    onSuccess: (res) => {
      toast.success(res.message || 'Senha alterada')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setOpen(false)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  if (!open) {
    return (
      <Button
        variant="ghost"
        size="sm"
        className="w-full justify-start text-sidebar-muted hover:bg-white/[0.04] hover:text-white"
        onClick={() => setOpen(true)}
      >
        <KeyRound className="h-4 w-4" />
        Alterar senha
      </Button>
    )
  }

  return (
    <form
      className="mb-2 space-y-2 rounded-xl border border-sidebar-border bg-white/[0.03] p-3"
      onSubmit={(e) => {
        e.preventDefault()
        mutation.mutate()
      }}
    >
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-sidebar-muted">
          Nova senha
        </p>
        <button
          type="button"
          className="text-sidebar-muted hover:text-white"
          onClick={() => setOpen(false)}
          aria-label="Fechar"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
      <div className="space-y-1">
        <Label htmlFor="current-password" className="text-[11px] text-sidebar-muted">
          Actual
        </Label>
        <Input
          id="current-password"
          type="password"
          autoComplete="current-password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          className="h-8 bg-background/60"
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="new-password" className="text-[11px] text-sidebar-muted">
          Nova (mín. 8)
        </Label>
        <Input
          id="new-password"
          type="password"
          autoComplete="new-password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          className="h-8 bg-background/60"
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="confirm-password" className="text-[11px] text-sidebar-muted">
          Confirmar
        </Label>
        <Input
          id="confirm-password"
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="h-8 bg-background/60"
        />
      </div>
      <Button
        type="submit"
        size="sm"
        className="w-full"
        disabled={
          mutation.isPending || !currentPassword || !newPassword || !confirmPassword
        }
      >
        {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
        Guardar senha
      </Button>
    </form>
  )
}
