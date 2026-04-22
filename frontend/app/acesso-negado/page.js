'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function AcessoNegado() {
  const router = useRouter()
  const [countdown, setCountdown] = useState(5)

  useEffect(() => {
    // Redirecionar para login após 5 segundos
    const timer = setTimeout(() => {
      router.push('/login')
    }, 5000)

    // Contador regressivo
    const countdownTimer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(countdownTimer)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => {
      clearTimeout(timer)
      clearInterval(countdownTimer)
    }
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 text-center">
        {/* Ícone de acesso negado */}
        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-10 h-10 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        </div>

        {/* Título */}
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Acesso Negado
        </h1>

        {/* Mensagem principal */}
        <p className="text-gray-600 mb-6">
          Você não tem permissão para acessar essa página.
        </p>

        {/* Informação sobre roles */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-amber-800 font-medium mb-2">
            Somente roles permitidas podem acessar o sistema:
          </p>
          <div className="text-xs text-amber-700 space-y-1">
            <p>• <span className="font-semibold">ADMIN</span> - Acesso completo ao sistema</p>
            <p>• <span className="font-semibold">GERENTE</span> - Gestão administrativa</p>
            <p>• <span className="font-semibold">RECEPCAO</span> - Operações de recepção</p>
            <p>• <span className="font-semibold">FUNCIONARIO</span> - Acesso básico</p>
          </div>
        </div>

        {/* Ações */}
        <div className="space-y-3">
          <button
            onClick={() => router.push('/login')}
            className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Ir para Login
          </button>
          
          <button
            onClick={() => router.back()}
            className="w-full bg-gray-200 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors font-medium"
          >
            Voltar
          </button>
        </div>

        {/* Contador regressivo */}
        <div className="mt-6 text-xs text-gray-500">
          Redirecionando para login em <span className="font-semibold">{countdown}</span> segundos...
        </div>
      </div>
    </div>
  )
}
