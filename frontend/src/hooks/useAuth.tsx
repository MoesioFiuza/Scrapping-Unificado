import { createContext, useContext, useCallback, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { UserRole } from '@/types'

interface AuthContextValue {
  username: string | undefined
  role: UserRole | undefined
  isAdmin: boolean
  isLoading: boolean
  isAuthenticated: boolean
  logout: () => Promise<void>
  refresh: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['auth'],
    queryFn: () => api.auth.check(),
    retry: false,
    staleTime: 60_000,
  })

  const logout = useCallback(async () => {
    await api.auth.logout()
    queryClient.setQueryData(['auth'], { authenticated: false })
    queryClient.clear()
  }, [queryClient])

  const value: AuthContextValue = {
    username: data?.username,
    role: data?.role as UserRole | undefined,
    isAdmin: data?.role === 'admin',
    isLoading,
    isAuthenticated: !!data?.authenticated,
    logout,
    refresh: () => void refetch(),
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
