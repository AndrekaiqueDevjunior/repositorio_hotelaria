'use client'
import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'
import ProtectedRoute from '../../../components/ProtectedRoute'

export default function Notificacoes() {
  const [notificacoes, setNotificacoes] = useState([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    tipo: '',
    categoria: '',
    lida: '',
    limit: 50,
    offset: 0
  })
  const [stats, setStats] = useState({
    total: 0,
    total_nao_lidas: 0
  })

  useEffect(() => {
    loadNotificacoes()
  }, [filters])

  const loadNotificacoes = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      
      if (filters.tipo) params.append('tipo', filters.tipo)
      if (filters.categoria) params.append('categoria', filters.categoria)
      if (filters.lida) params.append('lida', filters.lida)
      params.append('limit', filters.limit.toString())
      params.append('offset', filters.offset.toString())

      const res = await api.get(`/notificacoes?${params}`)
      
      // API pode retornar array direto ou objeto
      let notifData = []
      let totalData = 0
      let naoLidasData = 0
      
      if (Array.isArray(res.data)) {
        notifData = res.data
        totalData = res.data.length
        naoLidasData = res.data.filter(n => !n.lida).length
      } else if (res.data.success || res.data.notificacoes) {
        notifData = res.data.notificacoes || []
        totalData = res.data.total || notifData.length
        naoLidasData = res.data.total_nao_lidas || notifData.filter(n => !n.lida).length
      }
      
      setNotificacoes(notifData)
      setStats({
        total: totalData,
        total_nao_lidas: naoLidasData
      })
    } catch (error) {
      console.error('Erro ao carregar notificações:', error)
      alert('Erro ao carregar notificações')
    } finally {
      setLoading(false)
    }
  }

  const marcarComoLida = async (id) => {
    try {
      await api.post(`/notificacoes/${id}/marcar-lida`)
      loadNotificacoes()
    } catch (error) {
      console.error('Erro ao marcar notificação:', error)
      alert('Erro ao marcar notificação como lida')
    }
  }

  const marcarTodasLidas = async () => {
    try {
      await api.post('/notificacoes/marcar-todas-lidas')
      alert('Todas as notificações foram marcadas como lidas')
      loadNotificacoes()
    } catch (error) {
      console.error('Erro ao marcar todas:', error)
      alert('Erro ao marcar todas as notificações')
    }
  }

  const deletarNotificacao = async (id) => {
    if (!confirm('Deseja realmente deletar esta notificação?')) return

    try {
      await api.delete(`/notificacoes/${id}`)
      loadNotificacoes()
    } catch (error) {
      console.error('Erro ao deletar notificação:', error)
      alert('Erro ao deletar notificação')
    }
  }

  const limparAntigas = async () => {
    if (!confirm('Deseja limpar notificações antigas (lidas com mais de 30 dias)?')) return

    try {
      await api.delete('/notificacoes/limpar-antigas?dias=30')
      alert('Notificações antigas removidas')
      loadNotificacoes()
    } catch (error) {
      console.error('Erro ao limpar notificações:', error)
      alert('Erro ao limpar notificações antigas')
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

  const getTipoColor = (tipo) => {
    switch (tipo) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200'
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'success': return 'bg-green-100 text-green-800 border-green-200'
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getCategoriaLabel = (categoria) => {
    switch (categoria) {
      case 'reserva': return 'Reserva'
      case 'pagamento': return 'Pagamento'
      case 'antifraude': return 'Antifraude'
      case 'sistema': return 'Sistema'
      default: return categoria
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleAcao = (notificacao) => {
    // Marcar como lida
    if (!notificacao.lida) {
      marcarComoLida(notificacao.id)
    }

    // Navegar para URL se existir
    if (notificacao.url_acao) {
      window.location.href = notificacao.url_acao
    } else if (notificacao.reserva_id) {
      window.location.href = `/reservas?id=${notificacao.reserva_id}`
    } else if (notificacao.pagamento_id) {
      window.location.href = `/pagamentos?id=${notificacao.pagamento_id}`
    }
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-6">

      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">🔔 Notificações</h1>
            <p className="text-gray-600 text-sm">
              Gerenciar alertas e avisos do sistema
            </p>
          </div>
          <div className="flex gap-2">
            {stats.total_nao_lidas > 0 && (
              <button
                onClick={marcarTodasLidas}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
              >
                Marcar Todas como Lidas
              </button>
            )}
            <button
              onClick={limparAntigas}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm"
            >
              Limpar Antigas
            </button>
          </div>
        </div>

        {/* Estatísticas */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">Total de Notificações</div>
            <div className="text-2xl font-bold text-gray-800">{stats.total}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">Não Lidas</div>
            <div className="text-2xl font-bold text-blue-600">{stats.total_nao_lidas}</div>
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-white p-4 rounded-lg shadow mb-4">
          <div className="grid grid-cols-3 gap-4">
            {/* Filtro Tipo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo
              </label>
              <select
                value={filters.tipo}
                onChange={(e) => setFilters({ ...filters, tipo: e.target.value, offset: 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                <option value="info">ℹ️ Info</option>
                <option value="warning">⚠️ Aviso</option>
                <option value="critical">🔴 Crítico</option>
                <option value="success">✅ Sucesso</option>
              </select>
            </div>

            {/* Filtro Categoria */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Categoria
              </label>
              <select
                value={filters.categoria}
                onChange={(e) => setFilters({ ...filters, categoria: e.target.value, offset: 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todas</option>
                <option value="reserva">Reserva</option>
                <option value="pagamento">Pagamento</option>
                <option value="antifraude">Antifraude</option>
                <option value="sistema">Sistema</option>
              </select>
            </div>

            {/* Filtro Lida */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={filters.lida}
                onChange={(e) => setFilters({ ...filters, lida: e.target.value, offset: 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todas</option>
                <option value="false">Não Lidas</option>
                <option value="true">Lidas</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de Notificações */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-8 text-gray-500">
            Carregando notificações...
          </div>
        ) : notificacoes.length === 0 ? (
          <div className="bg-white p-8 rounded-lg shadow text-center text-gray-500">
            Nenhuma notificação encontrada
          </div>
        ) : (
          notificacoes.map((notif) => (
            <div
              key={notif.id}
              className={`bg-white p-4 rounded-lg shadow border-l-4 ${
                !notif.lida ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
              } hover:shadow-md transition-shadow`}
            >
              <div className="flex items-start justify-between">
                {/* Conteúdo */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{getTipoIcon(notif.tipo)}</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getTipoColor(notif.tipo)}`}>
                      {notif.tipo.toUpperCase()}
                    </span>
                    <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
                      {getCategoriaLabel(notif.categoria)}
                    </span>
                    {!notif.lida && (
                      <span className="px-2 py-1 rounded text-xs font-medium bg-blue-500 text-white">
                        NOVA
                      </span>
                    )}
                  </div>

                  <h3 className="font-semibold text-gray-800 mb-1">{notif.titulo}</h3>
                  <p className="text-gray-600 text-sm mb-2">{notif.mensagem}</p>

                  {/* Informações adicionais */}
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>📅 {formatDate(notif.data_criacao)}</span>
                    {notif.reserva_codigo && (
                      <span>🏨 Reserva: {notif.reserva_codigo}</span>
                    )}
                    {notif.cliente_nome && (
                      <span>👤 {notif.cliente_nome}</span>
                    )}
                  </div>
                </div>

                {/* Ações */}
                <div className="flex flex-col gap-2 ml-4">
                  {(notif.url_acao || notif.reserva_id || notif.pagamento_id) && (
                    <button
                      onClick={() => handleAcao(notif)}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                    >
                      Ver Detalhes
                    </button>
                  )}
                  {!notif.lida && (
                    <button
                      onClick={() => marcarComoLida(notif.id)}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                    >
                      Marcar Lida
                    </button>
                  )}
                  <button
                    onClick={() => deletarNotificacao(notif.id)}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                  >
                    Deletar
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Paginação */}
      {stats.total > filters.limit && (
        <div className="mt-6 flex justify-center gap-2">
          <button
            onClick={() => setFilters({ ...filters, offset: Math.max(0, filters.offset - filters.limit) })}
            disabled={filters.offset === 0}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Anterior
          </button>
          <span className="px-4 py-2 text-gray-700">
            {filters.offset + 1} - {Math.min(filters.offset + filters.limit, stats.total)} de {stats.total}
          </span>
          <button
            onClick={() => setFilters({ ...filters, offset: filters.offset + filters.limit })}
            disabled={filters.offset + filters.limit >= stats.total}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Próxima
          </button>
        </div>
      )}
      </div>
    </ProtectedRoute>
  )
}

