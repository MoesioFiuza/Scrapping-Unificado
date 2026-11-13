import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Loader2 } from 'lucide-react'

export function ProtectedRoute({
  children,
  adminOnly = false,
  superOnly = false,
}: {
  children: React.ReactNode
  adminOnly?: boolean
  superOnly?: boolean
}) {
  const { isAuthenticated, isAdmin, isSuperAdmin, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/" replace />
  }

  if (superOnly && !isSuperAdmin) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
