import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/hooks/useAuth'
import { DataWebJobProvider } from '@/hooks/useDataWebJob'
import { ProtectedRoute } from '@/routes/ProtectedRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/pages/LoginPage'
import { ScraperPage } from '@/pages/ScraperPage'
import { ExtracoesPage } from '@/pages/ExtracoesPage'
import { AdminPage } from '@/pages/AdminPage'
import { DashboardEscritorioPage } from '@/pages/DashboardEscritorioPage'
import { BASE_PATH } from '@/lib/paths'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <DataWebJobProvider>
        <BrowserRouter basename={BASE_PATH || undefined}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<ScraperPage />} />
              <Route path="extracoes" element={<ExtracoesPage />} />
              <Route
                path="admin/dashboard"
                element={
                  <ProtectedRoute adminOnly>
                    <DashboardEscritorioPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="admin"
                element={
                  <ProtectedRoute adminOnly>
                    <AdminPage />
                  </ProtectedRoute>
                }
              />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster richColors position="top-right" />
        </DataWebJobProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
