'use client'
import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { api } from '../../../lib/api'
import ProtectedRoute from '../../../components/ProtectedRoute'

export default function CheckinPage() {
  const params = useParams()
  const router = useRouter()
  const [reserva, setReserva] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [processando, setProcessando] = useState(false)

  useEffect(() => {
    if (params.id) {
      loadReserva(params.id)
    }
  }, [params.id])

  const loadReserva = async (reservaId) => {
    try {
      setLoading(true)
      const res = await api.get(`/reservas/${reservaId}`)
      
      if (res.data.success) {
        setReserva(res.data.data)
      } else {
        setError(res.data.message || 'Reserva não encontrada')
      }
    } catch (error) {
      console.error('Erro ao carregar reserva:', error)
      setError('Erro ao carregar reserva. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  const realizarCheckin = async () => {
    if (!reserva) return
    
    try {
      setProcessando(true)
      const res = await api.post(`/reservas/${reserva.id}/checkin`)
      
      if (res.data.success) {
        // Atualizar status da reserva
        setReserva(prev => ({
          ...prev,
          status_reserva: 'CHECKIN_REALIZADO'
        }))
        
        // Redirecionar para dashboard após sucesso
        setTimeout(() => {
          router.push('/dashboard')
        }, 2000)
      } else {
        setError(res.data.message || 'Erro ao realizar check-in')
      }
    } catch (error) {
      console.error('Erro ao realizar check-in:', error)
      setError('Erro ao realizar check-in. Tente novamente.')
    } finally {
      setProcessando(false)
    }
  }

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Carregando reserva...</p>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  if (error) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center p-8">
            <div className="text-red-500 text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Erro</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Voltar ao Dashboard
            </button>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  if (!reserva) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center p-8">
            <div className="text-gray-400 text-6xl mb-4">📋</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Reserva não encontrada</h2>
            <p className="text-gray-600 mb-6">A reserva solicitada não foi encontrada.</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Voltar ao Dashboard
            </button>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  const podeRealizarCheckin = reserva.status_reserva === 'CONFIRMADA' || reserva.status_reserva === 'PAGA_APROVADA'

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          {/* Header */}
          <div className="mb-8">
            <button
              onClick={() => router.push('/dashboard')}
              className="text-blue-600 hover:text-blue-800 flex items-center gap-2 mb-4"
            >
              ← Voltar ao Dashboard
            </button>
            <h1 className="text-3xl font-bold text-gray-800">Check-in da Reserva</h1>
          </div>

          {/* Card da Reserva */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Reserva #{reserva.id}
                </h2>
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    reserva.status_reserva === 'CHECKIN_REALIZADO' 
                      ? 'bg-green-100 text-green-800'
                      : podeRealizarCheckin
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {reserva.status_reserva === 'CHECKIN_REALIZADO' 
                      ? '✅ Check-in Realizado'
                      : podeRealizarCheckin
                      ? '🏨 Aguardando Check-in'
                      : reserva.status_reserva
                    }
                  </span>
                </div>
              </div>
            </div>

            {/* Informações da Reserva */}
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-gray-700 mb-3">Informações da Estadia</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Check-in:</span>
                    <span className="font-medium">
                      {new Date(reserva.checkin_previsto).toLocaleDateString('pt-BR')}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Check-out:</span>
                    <span className="font-medium">
                      {new Date(reserva.checkout_previsto).toLocaleDateString('pt-BR')}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Quarto:</span>
                    <span className="font-medium">{reserva.quarto_numero}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tipo:</span>
                    <span className="font-medium">{reserva.tipo_suite}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Hóspedes:</span>
                    <span className="font-medium">{reserva.num_hospedes}</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-gray-700 mb-3">Informações do Hóspede</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Nome:</span>
                    <span className="font-medium">{reserva.cliente?.nome_completo || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Documento:</span>
                    <span className="font-medium">{reserva.cliente?.documento || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Telefone:</span>
                    <span className="font-medium">{reserva.cliente?.telefone || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Email:</span>
                    <span className="font-medium text-sm">{reserva.cliente?.email || 'N/A'}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Valores */}
            <div className="mt-6 pt-6 border-t">
              <div className="flex justify-between items-center">
                <div>
                  <span className="text-gray-600">Valor Total:</span>
                  <span className="ml-2 text-2xl font-bold text-green-600">
                    R$ {parseFloat(reserva.valor_total).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Ações */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            {reserva.status_reserva === 'CHECKIN_REALIZADO' ? (
              <div className="text-center py-8">
                <div className="text-green-500 text-6xl mb-4">✅</div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Check-in já realizado!</h3>
                <p className="text-gray-600 mb-4">O check-in desta reserva já foi realizado.</p>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Voltar ao Dashboard
                </button>
              </div>
            ) : podeRealizarCheckin ? (
              <div className="text-center">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Confirmar Check-in</h3>
                <p className="text-gray-600 mb-6">
                  Confirme o check-in do hóspede para liberar o acesso ao quarto.
                </p>
                <button
                  onClick={realizarCheckin}
                  disabled={processando}
                  className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {processando ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white inline-block mr-2"></div>
                      Processando...
                    </>
                  ) : (
                    '🏨 Realizar Check-in'
                  )}
                </button>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-yellow-500 text-6xl mb-4">⚠️</div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Check-in não disponível</h3>
                <p className="text-gray-600 mb-4">
                  Esta reserva não está em status adequado para check-in.
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  Status atual: {reserva.status_reserva}
                </p>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Voltar ao Dashboard
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
