'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function AreaRestritaFuncionarios() {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  // Senha codificada ofuscada
  const correctPassword = atob('Q09NQlVTVElWRUxFVEFOT0xKVU5UQVFVRUlNQURB')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // Simular processamento
    await new Promise(resolve => setTimeout(resolve, 1000))

    if (password === correctPassword) {
      // Redirecionar para a página de login normal
      router.push('/login')
    } else {
      setError('🔒 Senha incorreta. Acesso negado.')
      setPassword('')
    }
    
    setLoading(false)
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-6"
      style={{
        backgroundImage: 'linear-gradient(135deg, #0f2c4d 0%, #1e4fa1 100%)',
      }}
    >
      <div className="bg-white/95 p-10 rounded-2xl shadow-2xl w-full max-w-[420px] backdrop-blur">
        <div className="flex flex-col items-center mb-8">
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-3xl">🔒</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-800 text-center">Área Restrita Funcionários</h1>
          <p className="text-sm text-slate-600 mt-2 text-center">Acesso exclusivo e autorizado</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div 
              className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded"
              role="alert"
              aria-live="assertive"
            >
              {error}
            </div>
          )}

          <div className="mb-6">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              🔒 Senha de Acesso
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Digite a senha de acesso"
              required
              disabled={loading}
              autoComplete="off"
              className="w-full px-4 py-3 border border-gray-200 rounded-lg shadow-inner transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-red-500/40 focus:border-red-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !password}
            className="w-full h-12 bg-red-600 text-white rounded-lg font-semibold transition-all duration-200 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed hover:-translate-y-0.5 hover:shadow-xl"
          >
            {loading ? 'Verificando...' : 'Acessar Área Restrita'}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-gray-500">
          <p>🔐 Acesso monitorado e protegido</p>
          <p className="mt-1">Área exclusiva para funcionários autorizados</p>
        </div>
      </div>
    </div>
  )
}
