'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch('/api/v1/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (response.ok) {
        // Login bem-sucedido
        if (data.requirePasswordChange) {
          router.push('/primeiro-acesso')
        } else {
          router.push('/dashboard')
        }
      } else {
        setError(data.detail || 'Credenciais inválidas')
      }
    } catch (err) {
      setError('Erro ao conectar com o servidor')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-6"
      style={{
        backgroundImage: 'linear-gradient(135deg, #0f2c4d 0%, #1e4fa1 100%)',
      }}
    >
      <div className="bg-white/95 p-10 rounded-2xl shadow-2xl w-full max-w-[520px] backdrop-blur">
        <div className="flex flex-col items-center mb-8">
          <div className="relative w-[360px] h-[360px] -mt-6">
            <img
              src="/images/hotel real cabo frio PNG.png"
              alt="Hotel Real Cabo Frio"
              className="w-full h-full object-contain"
            />
          </div>
          <p className="text-sm uppercase tracking-[0.4em] text-slate-500 mt-2">Portal Oficial</p>
          <h2 className="text-xl font-semibold text-slate-700 mt-2">
            Bem-vindo ao sistema do Hotel Real
          </h2>
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

          <div className="mb-4">
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              required
              disabled={loading}
              autoComplete="email"
              className="w-full px-4 py-3 border border-gray-200 rounded-lg shadow-inner transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500"
            />
          </div>

          <div className="mb-6">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Senha
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="•••••••••"
              required
              disabled={loading}
              autoComplete="current-password"
              className="w-full px-4 py-3 border border-gray-200 rounded-lg shadow-inner transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full h-12 bg-blue-600 text-white rounded-lg font-semibold transition-all duration-200 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed hover:-translate-y-0.5 hover:shadow-xl"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-500">
          <p className="text-xs">Acesso restrito a funcionários</p>
          <p className="text-xs text-slate-500 mt-2">🔒 Ambiente seguro</p>
        </div>
      </div>
    </div>
  )
}
