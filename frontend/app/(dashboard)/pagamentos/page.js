'use client'

import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'
import { 
  StatusPagamento,
  STATUS_PAGAMENTO_COLORS,
  METODO_PAGAMENTO_LABELS,
  isPagamentoAprovado,
  isPagamentoNegado
} from '../../../lib/constants/enums'

const formatCurrency = (value) => {
  const numero = Number(value || 0)
  return numero.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('pt-BR')
}

export default function PagamentosPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [pagamentos, setPagamentos] = useState([])
  const [showPagamentoDetailsModal, setShowPagamentoDetailsModal] = useState(false)
  const [pagamentoDetalhes, setPagamentoDetalhes] = useState(null)
  const [stats, setStats] = useState({
    total: 0,
    pendentes: 0,
    aprovados: 0,
    rejeitados: 0,
    processando: 0,
  })

  const loadPagamentos = async () => {
    try {
      setLoading(true)
      setError('')
      const res = await api.get('/pagamentos')
      const lista = res.data?.pagamentos || []
      setPagamentos(lista)
      setStats({
        total: res.data?.total || lista.length,
        pendentes: lista.filter((p) => p.status === StatusPagamento.PENDENTE).length,
        aprovados: lista.filter((p) => isPagamentoAprovado(p.status)).length,
        rejeitados: lista.filter((p) => isPagamentoNegado(p.status)).length,
        processando: lista.filter((p) => p.status === StatusPagamento.PROCESSANDO).length,
      })
    } catch (err) {
      console.error('Erro ao carregar pagamentos:', err)
      setError(err.response?.data?.detail || err.message || 'Falha ao carregar pagamentos')
    } finally {
      setLoading(false)
    }
  }

  const handleViewPagamentoDetails = async (pagamento) => {
    setLoading(true)
    try {
      // Carregar detalhes completos do pagamento
      const res = await api.get(`/pagamentos/${pagamento.id}`)
      
      // Carregar reserva associada
      let reserva = null
      if (res.data.reserva_id) {
        try {
          const resRes = await api.get(`/reservas/${res.data.reserva_id}`)
          reserva = resRes.data
        } catch (err) {
          console.log('Reserva não encontrada')
        }
      }
      
      setPagamentoDetalhes({
        ...res.data,
        reserva: reserva
      })
      setShowPagamentoDetailsModal(true)
    } catch (error) {
      console.error('❌ Erro ao carregar detalhes:', error)
      setError('Erro ao carregar detalhes do pagamento')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPagamentos()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-real-blue">Pagamentos</h1>
          <p className="text-gray-600">
            Acompanhe a liquidação diária e o status das cobranças provenientes das reservas.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={loadPagamentos}
            className="bg-real-blue text-white px-4 py-2 rounded shadow hover:bg-blue-800 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Atualizando...' : 'Atualizar'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Total" value={stats.total} color="text-real-blue" />
        <StatCard label="Pendentes" value={stats.pendentes} color="text-yellow-600" />
        <StatCard label="Processando" value={stats.processando} color="text-blue-600" />
        <StatCard label="Aprovados" value={stats.aprovados} color="text-green-600" />
        <StatCard label="Rejeitados" value={stats.rejeitados} color="text-red-600" />
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Histórico de pagamentos</h2>
            <p className="text-sm text-gray-500">
              Últimas movimentações sincronizadas com reservas e antifraude
            </p>
          </div>
          <span className="text-sm text-gray-500">Total exibido: {pagamentos.length}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase text-gray-500">
              <tr>
                <th className="px-6 py-3">Pagamento</th>
                <th className="px-6 py-3">Cliente</th>
                <th className="px-6 py-3">Reserva</th>
                <th className="px-6 py-3">Valor</th>
                <th className="px-6 py-3">Método</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Score</th>
                <th className="px-6 py-3">Data</th>
                <th className="px-6 py-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-6 py-8 text-center text-gray-500">
                    Carregando dados...
                  </td>
                </tr>
              ) : pagamentos.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-6 py-8 text-center text-gray-500">
                    Nenhum pagamento encontrado.
                  </td>
                </tr>
              ) : (
                pagamentos.map((pagamento) => (
                  <tr key={pagamento.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-gray-900">#{pagamento.id}</div>
                      <div className="text-xs text-gray-500">
                        {pagamento.cielo_payment_id || 'sem Cielo'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">
                        {pagamento.cliente_nome || `Cliente #${pagamento.cliente_id}`}
                      </div>
                      <div className="text-xs text-gray-500">{pagamento.cliente_email || '-'}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">
                        {pagamento.reserva_codigo || `#${pagamento.reserva_id}`}
                      </div>
                      <div className="text-xs text-gray-500">Quarto {pagamento.quarto_numero || '-'}</div>
                    </td>
                    <td className="px-6 py-4 font-semibold text-gray-900">
                      {formatCurrency(pagamento.valor)}
                    </td>
                    <td className="px-6 py-4 text-xs">
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-gray-100 text-gray-700">
                        {METODO_PAGAMENTO_LABELS[pagamento.metodo] || pagamento.metodo}
                        {pagamento.cartao_final && (
                          <span className="font-mono text-gray-500">•••• {pagamento.cartao_final}</span>
                        )}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${
                          STATUS_PAGAMENTO_COLORS[pagamento.status] || 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {pagamento.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {pagamento.risk_score != null ? (
                        <span className="font-semibold text-gray-900">{pagamento.risk_score}</span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-500">
                      {formatDate(pagamento.dataCriacao || pagamento.data_criacao)}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleViewPagamentoDetails(pagamento)}
                        className="text-sm px-3 py-1 rounded bg-blue-500 text-white hover:bg-blue-600"
                        title="Ver detalhes completos"
                      >
                        👁️ Detalhes
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de Detalhes do Pagamento */}
      {showPagamentoDetailsModal && pagamentoDetalhes && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="bg-gradient-to-r from-green-600 to-green-800 text-white p-6 rounded-t-lg">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold mb-2">💳 Detalhes do Pagamento</h2>
                  <p className="text-green-100">ID: #{pagamentoDetalhes.id}</p>
                </div>
                <button
                  onClick={() => setShowPagamentoDetailsModal(false)}
                  className="text-white hover:text-gray-200 text-2xl"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Conteúdo */}
            <div className="p-6 space-y-6">
              {/* Status Badge Grande */}
              <div className="text-center">
                <span className={`inline-block px-6 py-3 rounded-lg text-lg font-bold ${
                  STATUS_PAGAMENTO_COLORS[pagamentoDetalhes.status] || 'bg-gray-100 text-gray-800'
                }`}>
                  {pagamentoDetalhes.status}
                </span>
              </div>

              {/* Valor */}
              <div className="bg-green-50 p-4 rounded-lg text-center border-2 border-green-200">
                <p className="text-sm text-gray-600 mb-1">Valor do Pagamento</p>
                <p className="text-4xl font-bold text-green-600">
                  {formatCurrency(pagamentoDetalhes.valor)}
                </p>
              </div>

              {/* Informações do Pagamento */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-bold text-gray-800 mb-3">💳 Dados do Pagamento</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Método</p>
                    <p className="font-medium text-gray-900">
                      {METODO_PAGAMENTO_LABELS[pagamentoDetalhes.metodo] || pagamentoDetalhes.metodo || '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Cartão Final</p>
                    <p className="font-medium text-gray-900 font-mono">
                      {pagamentoDetalhes.cartao_final ? `•••• ${pagamentoDetalhes.cartao_final}` : '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">ID Cielo</p>
                    <p className="font-medium text-gray-900 text-xs break-all">
                      {pagamentoDetalhes.cielo_payment_id || '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Data de Criação</p>
                    <p className="font-medium text-gray-900">
                      {formatDate(pagamentoDetalhes.dataCriacao || pagamentoDetalhes.data_criacao)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Cliente */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="text-lg font-bold text-gray-800 mb-3">👤 Cliente</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Nome</p>
                    <p className="font-medium text-gray-900">
                      {pagamentoDetalhes.cliente_nome || `Cliente #${pagamentoDetalhes.cliente_id}`}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <p className="font-medium text-gray-900">
                      {pagamentoDetalhes.cliente_email || '-'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Reserva Associada */}
              {pagamentoDetalhes.reserva && (
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="text-lg font-bold text-gray-800 mb-3">📅 Reserva Associada</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Código</p>
                      <p className="font-medium text-gray-900">
                        {pagamentoDetalhes.reserva.codigo_reserva}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Quarto</p>
                      <p className="font-medium text-gray-900">
                        {pagamentoDetalhes.reserva.quarto_numero}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Status Reserva</p>
                      <span className={`text-xs px-2 py-1 rounded font-semibold ${
                        pagamentoDetalhes.reserva.status === 'HOSPEDADO' ? 'bg-blue-100 text-blue-800' :
                        pagamentoDetalhes.reserva.status === 'CHECKED_OUT' ? 'bg-green-100 text-green-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {pagamentoDetalhes.reserva.status}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Antifraude */}
              <div className="bg-red-50 p-4 rounded-lg">
                <h3 className="text-lg font-bold text-gray-800 mb-3">🛡️ Análise de Risco</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Risk Score</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {pagamentoDetalhes.risk_score != null ? pagamentoDetalhes.risk_score : '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Avaliação</p>
                    <span className={`inline-block px-3 py-1 rounded font-semibold ${
                      (pagamentoDetalhes.risk_score || 0) < 30 ? 'bg-green-100 text-green-800' :
                      (pagamentoDetalhes.risk_score || 0) < 70 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {(pagamentoDetalhes.risk_score || 0) < 30 ? 'BAIXO RISCO' :
                       (pagamentoDetalhes.risk_score || 0) < 70 ? 'MÉDIO RISCO' : 'ALTO RISCO'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Informações Adicionais */}
              {(pagamentoDetalhes.tid || pagamentoDetalhes.nsu || pagamentoDetalhes.authorization_code) && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-bold text-gray-800 mb-3">ℹ️ Informações Técnicas</h3>
                  <div className="grid grid-cols-3 gap-4">
                    {pagamentoDetalhes.tid && (
                      <div>
                        <p className="text-sm text-gray-500">TID</p>
                        <p className="font-medium text-gray-900 text-xs font-mono">{pagamentoDetalhes.tid}</p>
                      </div>
                    )}
                    {pagamentoDetalhes.nsu && (
                      <div>
                        <p className="text-sm text-gray-500">NSU</p>
                        <p className="font-medium text-gray-900 text-xs font-mono">{pagamentoDetalhes.nsu}</p>
                      </div>
                    )}
                    {pagamentoDetalhes.authorization_code && (
                      <div>
                        <p className="text-sm text-gray-500">Código Autorização</p>
                        <p className="font-medium text-gray-900 text-xs font-mono">{pagamentoDetalhes.authorization_code}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-4 rounded-b-lg flex justify-end">
              <button
                onClick={() => setShowPagamentoDetailsModal(false)}
                className="px-6 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 font-medium"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div className="bg-white rounded-xl shadow p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-3xl font-semibold mt-2 ${color}`}>{value}</p>
    </div>
  )
}

