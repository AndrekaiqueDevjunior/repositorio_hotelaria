'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'

// Mapeamento de permissões por página
export const PAGE_PERMISSIONS = {
  '/dashboard': ['ADMIN', 'GERENTE', 'RECEPCAO', 'FUNCIONARIO'],
  '/reservas': ['ADMIN', 'GERENTE', 'RECEPCAO', 'FUNCIONARIO'],
  '/clientes': ['ADMIN', 'GERENTE', 'RECEPCAO'],
  '/pagamentos': ['ADMIN', 'GERENTE', 'RECEPCAO'],
  '/pontos': ['ADMIN', 'GERENTE'],
  '/tarifas': ['ADMIN', 'GERENTE'],
  '/antifraude': ['ADMIN', 'GERENTE'],
  '/notificacoes': ['ADMIN', 'GERENTE', 'RECEPCAO', 'FUNCIONARIO'],
}

// Hook para verificar permissão
export function useHasPermission(requiredRoles) {
  const { user } = useAuth()
  if (!requiredRoles || requiredRoles.length === 0) return true
  return requiredRoles.includes(user?.perfil)
}

export default function ProtectedRoute({ children, requiredRoles = null }) {
  const { user, loading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated()) {
        router.push('/login')
        return
      }

      if (requiredRoles && !requiredRoles.includes(user?.perfil)) {
        router.push('/acesso-negado')
      }
    }
  }, [loading, user, router, requiredRoles])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated()) {
    return null
  }

  if (requiredRoles && !requiredRoles.includes(user?.perfil)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-8 rounded-lg shadow-lg text-center max-w-md">
          <div className="text-6xl mb-4">🚫</div>
          <h1 className="text-2xl font-bold text-red-600 mb-2">Acesso Negado</h1>
          <p className="text-gray-600 mb-4">
            Você não tem permissão para acessar esta página.
          </p>
          <p className="text-sm text-gray-500 mb-4">
            Seu perfil: <span className="font-semibold">{user?.perfil}</span>
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Perfis permitidos: <span className="font-semibold">{requiredRoles?.join(', ')}</span>
          </p>
          <button
            onClick={() => router.push('/dashboard')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Voltar ao Dashboard
          </button>
        </div>
      </div>
    )
  }

  return children
}
