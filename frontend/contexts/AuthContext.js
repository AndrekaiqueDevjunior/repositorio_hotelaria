'use client'
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '../lib/api'

const AuthContext = createContext({})

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      // Verificar autenticação via cookie (não há localStorage)
      // O cookie é enviado automaticamente pelo axios (withCredentials: true)
      const response = await api.get('/me')
      
      if (response.data) {
        setUser(response.data)
      }
    } catch (error) {
      // Erro 401 significa não autenticado (normal na primeira visita)
      if (error.response?.status !== 401) {
        console.error('Erro ao verificar autenticação:', error)
      }
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const refreshUser = async () => {
    const response = await api.get('/me')
    if (response.data) {
      setUser(response.data)
    }
    return response.data
  }

  const login = async (email, password) => {
    try {
      console.log('🔐 [AuthContext] Iniciando login...', { email })
      
      const response = await api.post('/login', { 
        email, 
        password
      })
      
      console.log('✅ [AuthContext] Resposta recebida:', {
        status: response.status,
        success: response.data.success,
        hasUser: !!response.data.user || !!response.data.funcionario,
        tokenType: response.data.token_type
      })
      
      const returnedUser = response.data.user || response.data.funcionario

      if (response.data.success && returnedUser) {
        const { requirePasswordChange } = response.data
        
        console.log('🍪 [AuthContext] JWT armazenado em cookie HttpOnly')
        console.log('✅ [AuthContext] Atualizando state do usuário...')
        console.log('🔐 [AuthContext] Primeiro acesso obrigatório:', requirePasswordChange)
        
        setUser(returnedUser)
        
        console.log('🎉 [AuthContext] Login bem-sucedido!', { user: returnedUser, requirePasswordChange })
        return { success: true, user: returnedUser, requirePasswordChange }
      }
      
      console.error('❌ [AuthContext] Resposta inválida')
      return { success: false, error: 'Resposta inválida do servidor' }
    } catch (error) {
      console.error('❌ [AuthContext] Erro no login:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      })
      
      let message = 'Erro ao fazer login'
      
      if (error.response?.data) {
        const data = error.response.data
        
        if (typeof data === 'string') {
          message = data
        } else if (data.detail) {
          if (typeof data.detail === 'string') {
            message = data.detail
          } else if (Array.isArray(data.detail)) {
            message = data.detail.map(err => err.msg || JSON.stringify(err)).join(', ')
          }
        } else if (Array.isArray(data)) {
          message = data.map(err => err.msg || JSON.stringify(err)).join(', ')
        } else if (data.message) {
          message = data.message
        }
      } else if (error.message) {
        message = error.message
      }
      
      return { success: false, error: message }
    }
  }

  const logout = async () => {
    try {
      // Chamar endpoint de logout para remover cookie no servidor
      await api.post('/logout')
      console.log('✅ [AuthContext] Logout realizado, cookie removido')
    } catch (error) {
      console.error('⚠️ [AuthContext] Erro ao fazer logout:', error)
    } finally {
      setUser(null)
      router.push('/login')
    }
  }

  const isAuthenticated = useCallback(() => {
    return !!user
  }, [user])

  const hasRole = useCallback((roles) => {
    if (!user) return false
    if (typeof roles === 'string') return user.perfil === roles
    return roles.includes(user.perfil)
  }, [user])

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      logout,
      refreshUser,
      isAuthenticated,
      hasRole
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider')
  }
  return context
}

export default AuthContext
