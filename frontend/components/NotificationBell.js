'use client'
import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { useRouter } from 'next/navigation'

export default function NotificationBell() {
  const [count, setCount] = useState(0)
  const [notificacoes, setNotificacoes] = useState([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  useEffect(() => {
    // Carregar contagem inicial
    loadCount()

    // Polling: atualizar a cada 30 segundos
    const interval = setInterval(() => {
      loadCount()
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const loadCount = async () => {
    try {
      const res = await api.get('/notificacoes/nao-lidas')
      if (res.data.success) {
        setCount(res.data.count)
      }
    } catch (error) {
      console.error('Erro ao carregar contagem:', error)
    }
  }

  const loadRecentNotifications = async () => {
    try {
      setLoading(true)
      console.log('[NotificationBell] Carregando notificações...')
      
      const res = await api.get('/notificacoes', {
        params: {
          lida: false,
          limit: 10
        }
      })
      
      console.log('[NotificationBell] Resposta da API:', res.data)
      
      // Backend pode retornar:
      // 1. { success: true, notificacoes: [...] } - formato esperado
      // 2. [...] - array direto
      let notificacoesData = []
      
      if (Array.isArray(res.data)) {
        // Resposta é um array direto
        console.log('[NotificationBell] Array direto recebido')
        notificacoesData = res.data
      } else if (res.data && res.data.notificacoes) {
        // Resposta é objeto com propriedade notificacoes
        console.log('[NotificationBell] Objeto com notificacoes recebido')
        notificacoesData = res.data.notificacoes
      } else {
        console.warn('[NotificationBell] Formato de resposta inesperado:', res.data)
      }
      
      console.log('[NotificationBell] Notificações encontradas:', notificacoesData.length)
      setNotificacoes(notificacoesData)
    } catch (error) {
      console.error('[NotificationBell] Erro ao carregar notificações:', error)
      console.error('[NotificationBell] Detalhes do erro:', error.response?.data)
      setNotificacoes([])
    } finally {
      setLoading(false)
    }
  }

  const handleBellClick = () => {
    console.log('[NotificationBell] Sino clicado. Dropdown atual:', showDropdown)
    const newState = !showDropdown
    setShowDropdown(newState)
    
    if (newState) {
      console.log('[NotificationBell] Abrindo dropdown, carregando notificações...')
      loadRecentNotifications()
    }
  }

  const handleNotificationClick = async (notif) => {
    // Marcar como lida
    try {
      await api.post(`/notificacoes/${notif.id}/marcar-lida`)
      loadCount()
    } catch (error) {
      console.error('Erro ao marcar como lida:', error)
    }

    // Fechar dropdown
    setShowDropdown(false)

    // Navegar
    if (notif.url_acao) {
      router.push(notif.url_acao)
    } else if (notif.reserva_id) {
      router.push(`/reservas?id=${notif.reserva_id}`)
    } else if (notif.pagamento_id) {
      router.push(`/pagamentos?id=${notif.pagamento_id}`)
    }
  }

  const getTipoIcon = (tipo) => {
    switch (tipo) {
      case 'critical': return '🔴'
      case 'warning': return '⚠️'
      case 'success': return '✅'
      case 'info': return 'ℹ️'
      default: return '📌'
    }
  }

  const formatTimeAgo = (dateString) => {
    if (!dateString) return ''
    
    const now = new Date()
    const date = new Date(dateString)
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Agora'
    if (diffMins < 60) return `${diffMins}m atrás`
    if (diffHours < 24) return `${diffHours}h atrás`
    if (diffDays < 7) return `${diffDays}d atrás`
    
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
  }

  return (
    <div className="relative">
      {/* Bell Icon */}
      <button
        onClick={handleBellClick}
        className="relative p-2 rounded-full hover:bg-gray-100 transition-colors"
        title="Notificações"
      >
        <svg
          className="w-6 h-6 text-gray-700"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>

        {/* Badge de Contagem */}
        {count > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {count > 99 ? '99+' : count}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {showDropdown && (
        <>
          {/* Overlay para fechar ao clicar fora */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowDropdown(false)}
          />

          {/* Dropdown Content */}
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-[600px] flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="font-semibold text-gray-800">
                🔔 Notificações {count > 0 && `(${count})`}
              </h3>
              <button
                onClick={() => {
                  setShowDropdown(false)
                  router.push('/notificacoes')
                }}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Ver todas
              </button>
            </div>

            {/* Lista */}
            <div className="overflow-y-auto flex-1">
              {loading ? (
                <div className="p-4 text-center text-gray-500">
                  Carregando...
                </div>
              ) : notificacoes.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <div className="text-4xl mb-2">✅</div>
                  <p>Nenhuma notificação nova</p>
                  <p className="text-xs mt-2 text-gray-400">Total no estado: {notificacoes.length}</p>
                </div>
              ) : (
                notificacoes.map((notif) => (
                  <button
                    key={notif.id}
                    onClick={() => handleNotificationClick(notif)}
                    className="w-full p-4 hover:bg-gray-50 border-b border-gray-100 text-left transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-xl flex-shrink-0">
                        {getTipoIcon(notif.tipo)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-800 text-sm truncate">
                          {notif.titulo}
                        </h4>
                        <p className="text-gray-600 text-xs mt-1 line-clamp-2">
                          {notif.mensagem}
                        </p>
                        <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                          <span>{formatTimeAgo(notif.data_criacao)}</span>
                          {notif.categoria && (
                            <>
                              <span>•</span>
                              <span className="capitalize">{notif.categoria}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>

            {/* Footer */}
            {count > 0 && (
              <div className="p-3 border-t border-gray-200 bg-gray-50">
                <button
                  onClick={async () => {
                    try {
                      await api.post('/notificacoes/marcar-todas-lidas')
                      loadCount()
                      setNotificacoes([])
                      setShowDropdown(false)
                    } catch (error) {
                      console.error('Erro ao marcar todas:', error)
                    }
                  }}
                  className="w-full text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  Marcar todas como lidas
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

