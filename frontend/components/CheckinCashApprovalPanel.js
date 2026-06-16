'use client'

import { useEffect, useMemo, useState } from 'react'
import { Banknote, CheckCircle, Clock, RefreshCw } from 'lucide-react'
import { toast } from 'react-toastify'
import { api } from '../lib/api'

const ACTIVE_RESERVATION_STATUSES = new Set([
  'PENDENTE',
  'PENDENTE_PAGAMENTO',
  'AGUARDANDO_COMPROVANTE',
  'EM_ANALISE',
  'PAGA_REJEITADA',
  'CONFIRMADA',
  'PAGA_APROVADA',
  'CHECKIN_LIBERADO',
])

const STATUS_LABELS = {
  pending: 'Pendente',
  approved: 'Aprovado',
  expired: 'Expirado',
  cancelled: 'Cancelado',
}

function formatCurrency(value) {
  return Number(value || 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getStatusClass(status) {
  if (status === 'approved') return 'bg-green-100 text-green-700'
  if (status === 'expired') return 'bg-red-100 text-red-700'
  if (status === 'cancelled') return 'bg-gray-100 text-gray-700'
  return 'bg-yellow-100 text-yellow-800'
}

export default function CheckinCashApprovalPanel({ reservas = [], onRefreshReservas }) {
  const [approvals, setApprovals] = useState([])
  const [selectedReservationId, setSelectedReservationId] = useState('')
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [approvingCode, setApprovingCode] = useState('')
  const [lastUpdatedAt, setLastUpdatedAt] = useState('')

  const activeReservations = useMemo(() => {
    return reservas
      .filter((reserva) => ACTIVE_RESERVATION_STATUSES.has(String(reserva.status || '').toUpperCase()))
      .sort((a, b) => String(a.codigo_reserva || '').localeCompare(String(b.codigo_reserva || '')))
  }, [reservas])

  const pendingApprovals = approvals.filter((approval) => approval.status === 'pending')
  const historyApprovals = approvals.filter((approval) => approval.status !== 'pending').slice(0, 8)

  useEffect(() => {
    loadApprovals({ silent: true })
    const intervalId = setInterval(() => loadApprovals({ silent: true }), 30000)
    return () => clearInterval(intervalId)
  }, [])

  useEffect(() => {
    if (!selectedReservationId) {
      setAmount('')
      return
    }

    const reserva = activeReservations.find((item) => Number(item.id) === Number(selectedReservationId))
    const total = reserva?.valor_total_com_desconto || reserva?.valor_total || 0
    setAmount(Number(total || 0).toFixed(2))
  }, [selectedReservationId, activeReservations])

  const loadApprovals = async ({ silent = false } = {}) => {
    if (!silent) setLoading(true)
    try {
      const response = await api.get('/checkins/cash-approvals', {
        params: { status: 'all', limit: 80 },
      })
      setApprovals(response.data?.approvals || [])
      setLastUpdatedAt(new Date().toISOString())
    } catch (error) {
      if (!silent) {
        toast.error(error.response?.data?.detail || 'Erro ao carregar aprovacoes CHK')
      }
    } finally {
      if (!silent) setLoading(false)
    }
  }

  const handleCreateApproval = async () => {
    if (!selectedReservationId) {
      toast.warning('Selecione uma reserva')
      return
    }

    const parsedAmount = Number(amount)
    if (!parsedAmount || parsedAmount <= 0) {
      toast.warning('Informe um valor valido')
      return
    }

    setCreating(true)
    try {
      const response = await api.post('/checkins/request-cash-approval', {
        reservation_id: Number(selectedReservationId),
        amount: parsedAmount,
        payment_method: 'cash',
      })
      toast.success(`Codigo ${response.data.approval_code} enviado ao admin`)
      setSelectedReservationId('')
      setAmount('')
      await loadApprovals({ silent: true })
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao solicitar aprovacao CHK')
    } finally {
      setCreating(false)
    }
  }

  const handleApprove = async (approval) => {
    const code = approval.approval_code || approval.code
    if (!code) return

    const confirmed = window.confirm(`Aprovar check-in em dinheiro do codigo ${code}?`)
    if (!confirmed) return

    setApprovingCode(code)
    try {
      await api.post(`/checkins/${code}/approve`)
      toast.success(`Codigo ${code} aprovado`)
      await loadApprovals({ silent: true })
      if (onRefreshReservas) {
        await onRefreshReservas()
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao aprovar codigo CHK')
    } finally {
      setApprovingCode('')
    }
  }

  return (
    <section className="bg-white rounded-lg shadow p-4 mb-6 border border-gray-100">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded bg-green-100 text-green-700">
            <Banknote className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Check-in em dinheiro</h2>
            <p className="text-sm text-gray-500">
              {pendingApprovals.length} pendente(s)
              {lastUpdatedAt ? ` | Atualizado ${formatDateTime(lastUpdatedAt)}` : ''}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => loadApprovals({ silent: false })}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
          Atualizar
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(280px,360px)_1fr] gap-4">
        <div className="rounded border border-gray-200 p-3">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Solicitar CHK</h3>
          <div className="space-y-3">
            <select
              value={selectedReservationId}
              onChange={(event) => setSelectedReservationId(event.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">Selecione a reserva</option>
              {activeReservations.map((reserva) => (
                <option key={reserva.id} value={reserva.id}>
                  {reserva.codigo_reserva} | {reserva.cliente_nome} | Q{reserva.quarto_numero}
                </option>
              ))}
            </select>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
              placeholder="Valor"
            />
            <button
              type="button"
              onClick={handleCreateApproval}
              disabled={creating || !selectedReservationId}
              className="inline-flex w-full items-center justify-center gap-2 rounded bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
            >
              <Clock className="h-4 w-4" aria-hidden="true" />
              {creating ? 'Enviando...' : 'Gerar codigo CHK'}
            </button>
          </div>
        </div>

        <div className="min-w-0">
          <div className="overflow-x-auto rounded border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold text-gray-600">Codigo</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-600">Reserva</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-600">Cliente</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-600">Quarto</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-600">Valor</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-600">Expira</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-600">Status</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-600">Acao</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {pendingApprovals.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-3 py-6 text-center text-gray-500">
                      Nenhum CHK pendente
                    </td>
                  </tr>
                ) : (
                  pendingApprovals.map((approval) => {
                    const code = approval.approval_code || approval.code
                    return (
                      <tr key={approval.id}>
                        <td className="px-3 py-2 font-mono text-gray-900">{code}</td>
                        <td className="px-3 py-2 text-gray-700">{approval.codigo_reserva}</td>
                        <td className="px-3 py-2 text-gray-700">{approval.guest_name || approval.cliente_nome}</td>
                        <td className="px-3 py-2 text-gray-700">{approval.room_number || approval.room}</td>
                        <td className="px-3 py-2 text-gray-900">{formatCurrency(approval.amount || approval.valor)}</td>
                        <td className="px-3 py-2 text-gray-700">{formatDateTime(approval.expires_at)}</td>
                        <td className="px-3 py-2">
                          <span className={`rounded px-2 py-1 text-xs font-medium ${getStatusClass(approval.status)}`}>
                            {STATUS_LABELS[approval.status] || approval.status}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <button
                            type="button"
                            onClick={() => handleApprove(approval)}
                            disabled={!approval.can_approve || approvingCode === code}
                            className="inline-flex items-center gap-1 rounded bg-blue-600 px-2 py-1 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
                          >
                            <CheckCircle className="h-3.5 w-3.5" aria-hidden="true" />
                            {approvingCode === code ? 'Aprovando...' : 'Aprovar'}
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          {historyApprovals.length > 0 && (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-2">
              {historyApprovals.map((approval) => (
                <div key={approval.id} className="rounded border border-gray-200 p-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs text-gray-800">{approval.approval_code || approval.code}</span>
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${getStatusClass(approval.status)}`}>
                      {STATUS_LABELS[approval.status] || approval.status}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-600">{approval.codigo_reserva} | Q{approval.room_number}</p>
                  <p className="text-xs text-gray-600">{formatCurrency(approval.amount || approval.valor)}</p>
                  {approval.approved_at && (
                    <p className="text-xs text-gray-500">{formatDateTime(approval.approved_at)}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
