'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../contexts/AuthContext'
import { api } from '../../lib/api'

export default function PrimeiroAcessoPage() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const router = useRouter()
  const { user } = useAuth()

  // Validação de senha forte
  const validatePassword = (password) => {
    const validations = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      digit: /\d/.test(password),
      special: /[!@#$%&*()_+\-=\[\]{}|;:,.<>?]/.test(password)
    }

    const isValid = Object.values(validations).every(Boolean)
    return { isValid, validations }
  }

  const getPasswordStrength = (password) => {
    if (!password) return { strength: 0, text: '', color: '' }
    
    const { validations } = validatePassword(password)
    const score = Object.values(validations).filter(Boolean).length
    
    if (score <= 2) return { strength: 25, text: 'Fraca', color: 'bg-red-500' }
    if (score <= 3) return { strength: 50, text: 'Média', color: 'bg-yellow-500' }
    if (score <= 4) return { strength: 75, text: 'Forte', color: 'bg-blue-500' }
    return { strength: 100, text: 'Muito Forte', color: 'bg-green-500' }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    console.log('🔐 [PrimeiroAcesso] Iniciando troca de senha...')

    // Validações
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('Todos os campos são obrigatórios')
      setLoading(false)
      return
    }

    if (newPassword !== confirmPassword) {
      setError('A nova senha e a confirmação não coincidem')
      setLoading(false)
      return
    }

    const { isValid, validations } = validatePassword(newPassword)
    if (!isValid) {
      setError('A nova senha não atende aos requisitos de segurança')
      setLoading(false)
      return
    }

    try {
      console.log('📞 [PrimeiroAcesso] Enviando requisição de troca de senha...')
      
      const response = await api.post('/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      })

      console.log('✅ [PrimeiroAcesso] Senha alterada com sucesso!')

      // Redirecionar para dashboard
      router.push('/dashboard')
    } catch (err) {
      console.error('❌ [PrimeiroAcesso] Erro ao alterar senha:', err)
      
      let message = 'Erro ao alterar senha'
      if (err.response?.data?.detail) {
        message = err.response.data.detail
      } else if (err.response?.data?.message) {
        message = err.response.data.message
      }
      
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const { validations } = validatePassword(newPassword)
  const { strength, text, color } = getPasswordStrength(newPassword)

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-500 to-red-600">
      <div className="bg-white p-8 rounded-lg shadow-2xl w-full max-w-md">
        <div className="text-center mb-8">
          <div className="mx-auto w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center mb-4">
            <svg className="w-10 h-10 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-800">🔐 Primeiro Acesso</h1>
          <p className="text-gray-600 mt-2">Olá, {user?.nome}!</p>
          <p className="text-sm text-gray-500 mt-1">Por segurança, altere sua senha</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-2">
              Senha Atual
            </label>
            <div className="relative">
              <input
                id="currentPassword"
                type={showPassword ? 'text' : 'password'}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder="Digite sua senha atual"
                required
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-2">
              Nova Senha
            </label>
            <div className="relative">
              <input
                id="newPassword"
                type={showNewPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder="Digite sua nova senha"
                required
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {showNewPassword ? '🙈' : '👁️'}
              </button>
            </div>
            
            {/* Indicador de força da senha */}
            {newPassword && (
              <div className="mt-2">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-gray-600">Força da senha:</span>
                  <span className={`text-xs font-medium ${color.replace('bg-', 'text-')}`}>{text}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`${color} h-2 rounded-full transition-all duration-300`}
                    style={{ width: `${strength}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
              Confirmar Nova Senha
            </label>
            <div className="relative">
              <input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder="Confirme sua nova senha"
                required
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {showConfirmPassword ? '🙈' : '👁️'}
              </button>
            </div>
            
            {/* Validação de senhas coincidindo */}
            {confirmPassword && (
              <div className="mt-1">
                {newPassword === confirmPassword ? (
                  <span className="text-xs text-green-600">✅ Senhas coincidem</span>
                ) : (
                  <span className="text-xs text-red-600">❌ Senhas não coincidem</span>
                )}
              </div>
            )}
          </div>

          {/* Requisitos de senha */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Requisitos da senha:</h3>
            <div className="space-y-1">
              <div className={`text-xs flex items-center ${validations.length ? 'text-green-600' : 'text-gray-400'}`}>
                {validations.length ? '✅' : '○'} Mínimo 8 caracteres
              </div>
              <div className={`text-xs flex items-center ${validations.uppercase ? 'text-green-600' : 'text-gray-400'}`}>
                {validations.uppercase ? '✅' : '○'} Letra maiúscula (A-Z)
              </div>
              <div className={`text-xs flex items-center ${validations.lowercase ? 'text-green-600' : 'text-gray-400'}`}>
                {validations.lowercase ? '✅' : '○'} Letra minúscula (a-z)
              </div>
              <div className={`text-xs flex items-center ${validations.digit ? 'text-green-600' : 'text-gray-400'}`}>
                {validations.digit ? '✅' : '○'} Número (0-9)
              </div>
              <div className={`text-xs flex items-center ${validations.special ? 'text-green-600' : 'text-gray-400'}`}>
                {validations.special ? '✅' : '○'} Símbolo (!@#$%&*...)
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !validatePassword(newPassword).isValid || newPassword !== confirmPassword}
            className="w-full bg-orange-600 text-white py-3 px-4 rounded-lg hover:bg-orange-700 focus:ring-4 focus:ring-orange-300 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Alterando senha...
              </span>
            ) : (
              'Alterar Senha e Acessar Sistema'
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>🔒 Sua senha será armazenada com segurança</p>
        </div>
      </div>
    </div>
  )
}
