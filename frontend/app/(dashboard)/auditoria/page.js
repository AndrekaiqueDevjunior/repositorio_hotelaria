'use client'

import { useEffect, useMemo, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../contexts/AuthContext'
import { useToast } from '../../../contexts/ToastContext'
import { api } from '../../../lib/api'

export default function AuditoriaPage() {
  const router = useRouter()
  const { user, loading, isAuthenticated } = useAuth()
  const { addToast } = useToast()

  const [filters, setFilters] = useState({
    funcionario_id: '',
    entidade: '',
    acao: '',
    data_inicio: '',
    data_fim: '',
    ip_address: '',
  })

  const [funcionarios, setFuncionarios] = useState([])
  const [loadingFuncionarios, setLoadingFuncionarios] = useState(true)

  const [page, setPage] = useState(1)
  const [limit, setLimit] = useState(50)

  const [logs, setLogs] = useState([])
  const [meta, setMeta] = useState({
    total: 0,
    total_paginas: 0,
    pagina: 1,
    limite: 50,
  })

  const [resumoDias, setResumoDias] = useState(7)
  const [resumo, setResumo] = useState(null)

  const [loadingLogs, setLoadingLogs] = useState(true)
  const [loadingResumo, setLoadingResumo] = useState(true)

  const entidadesOpcoes = [
    { value: '', label: 'Todas as áreas' },
    { value: 'RESERVA', label: 'Reservas' },
    { value: 'PAGAMENTO', label: 'Pagamentos' },
    { value: 'PONTOS', label: 'Pontos' },
    { value: 'RESGATE', label: 'Resgates' },
    { value: 'CHECKIN', label: 'Check-in' },
    { value: 'CHECKOUT', label: 'Check-out' },
    { value: 'FUNCIONARIO', label: 'Funcionários' },
  ]

  const acoesOpcoes = [
    { value: '', label: 'Todas as ações' },
    { value: 'CREATE', label: 'Criação' },
    { value: 'UPDATE', label: 'Atualização' },
    { value: 'DELETE', label: 'Exclusão' },
    { value: 'LOGIN', label: 'Login' },
    { value: 'LOGOUT', label: 'Logout' },
    { value: 'CONFIRM', label: 'Confirmação' },
    { value: 'CREDITO', label: 'Crédito de pontos' },
    { value: 'DEBITO', label: 'Débito de pontos' },
  ]

  const [showDetails, setShowDetails] = useState(false)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [selectedLog, setSelectedLog] = useState(null)
  const [selectedDetails, setSelectedDetails] = useState(null)

  const authenticated = useMemo(() => isAuthenticated(), [isAuthenticated])

  // Guard de auth + permissão
  useEffect(() => {
    if (loading) return

    if (!authenticated) {
      router.push('/login')
      return
    }

    const perfil = (user?.perfil || '').toUpperCase()
    if (!['ADMIN', 'GERENTE'].includes(perfil)) {
      addToast({
        titulo: 'Acesso negado',
        mensagem: 'Apenas ADMIN e GERENTE.',
        tipo: 'critical',
        categoria: 'seguranca',
      })
      router.push('/dashboard')
    }
  }, [loading, authenticated, user, router, addToast])

  const buildParams = useCallback(() => {
    const params = {
      page,
      limit,
    }

    if (filters.funcionario_id) params.funcionario_id = Number(filters.funcionario_id)
    if (filters.entidade) params.entidade = filters.entidade
    if (filters.acao) params.acao = filters.acao
    if (filters.data_inicio) params.data_inicio = filters.data_inicio
    if (filters.data_fim) params.data_fim = filters.data_fim
    if (filters.ip_address) params.ip_address = filters.ip_address

    return params
  }, [page, limit, filters])

  const buildMetaParams = useCallback(() => {
    // Para buscar apenas o "detalhes" (total/paginas) quando page != 1
    const params = {
      page: 1,
      limit: 1,
    }

    if (filters.funcionario_id) params.funcionario_id = Number(filters.funcionario_id)
    if (filters.entidade) params.entidade = filters.entidade
    if (filters.acao) params.acao = filters.acao
    if (filters.data_inicio) params.data_inicio = filters.data_inicio
    if (filters.data_fim) params.data_fim = filters.data_fim
    if (filters.ip_address) params.ip_address = filters.ip_address

    return params
  }, [filters])

  const fetchLogs = useCallback(async () => {
    try {
      setLoadingLogs(true)

      const reqLogs = api.get('/auditoria/logs', { params: buildParams() })

      // Se não for página 1, o backend não envia "detalhes"; então buscamos meta na page 1.
      const reqMeta = page === 1 ? null : api.get('/auditoria/logs', { params: buildMetaParams() })

      const [respLogs, respMeta] = await Promise.all([reqLogs, reqMeta])

      const dataLogs = Array.isArray(respLogs.data) ? respLogs.data : []
      setLogs(dataLogs)

      const metaSource = page === 1 ? dataLogs : (Array.isArray(respMeta?.data) ? respMeta.data : [])
      const metaFromApi = metaSource?.[0]?.detalhes

      if (metaFromApi && typeof metaFromApi.total === 'number') {
        setMeta({
          total: metaFromApi.total,
          total_paginas: metaFromApi.total_paginas,
          pagina: page,
          limite: limit,
        })
      } else if (page === 1) {
        // fallback (quando não tem detalhes)
        setMeta({
          total: dataLogs.length,
          total_paginas: 1,
          pagina: page,
          limite: limit,
        })
      } else {
        setMeta((prev) => ({ ...prev, pagina: page, limite: limit }))
      }
    } catch (error) {
      addToast({
        titulo: 'Erro na auditoria',
        mensagem: error?.response?.data?.detail || 'Erro ao buscar logs de auditoria',
        tipo: 'critical',
        categoria: 'auditoria',
      })
      setLogs([])
    } finally {
      setLoadingLogs(false)
    }
  }, [page, limit, buildParams, buildMetaParams, addToast])

  const fetchResumo = useCallback(async () => {
    try {
      setLoadingResumo(true)
      const resp = await api.get('/auditoria/resumo', { params: { dias: resumoDias } })
      setResumo(resp.data || null)
    } catch (error) {
      setResumo(null)
    } finally {
      setLoadingResumo(false)
    }
  }, [resumoDias])

  const fetchFuncionarios = useCallback(async () => {
    try {
      setLoadingFuncionarios(true)
      const resp = await api.get('/auditoria/funcionarios')
      setFuncionarios(resp.data || [])
    } catch (error) {
      setFuncionarios([])
    } finally {
      setLoadingFuncionarios(false)
    }
  }, [])

  useEffect(() => {
    if (!authenticated) return
    fetchLogs()
  }, [authenticated, page, limit, fetchLogs])

  useEffect(() => {
    if (!authenticated) return
    setPage(1)
  }, [authenticated, filters])

  useEffect(() => {
    if (!authenticated) return
    fetchResumo()
  }, [authenticated, resumoDias, fetchResumo])

  useEffect(() => {
    if (!authenticated) return
    fetchFuncionarios()
  }, [authenticated, fetchFuncionarios])

  const openDetails = async (log) => {
    setSelectedLog(log)
    setSelectedDetails(null)
    setShowDetails(true)

    try {
      setDetailsLoading(true)
      const resp = await api.get(`/auditoria/detalhes/${log.id}`)
      setSelectedDetails(resp.data || null)
    } catch (error) {
      addToast({
        titulo: 'Erro',
        mensagem: 'Erro ao carregar detalhes do log',
        tipo: 'critical',
        categoria: 'auditoria',
      })
      setSelectedDetails(null)
    } finally {
      setDetailsLoading(false)
    }
  }

  const closeDetails = () => {
    setShowDetails(false)
    setSelectedLog(null)
    setSelectedDetails(null)
    setDetailsLoading(false)
  }

  const formatDateTime = (iso) => {
    try {
      return new Date(iso).toLocaleString('pt-BR')
    } catch {
      return iso
    }
  }

  const canPrev = page > 1
  const canNext = meta.total_paginas ? page < meta.total_paginas : logs.length === limit

  return (
    <div className="p-6">
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📊 Auditoria do Sistema</h1>
          <p className="text-gray-600">Acompanhe todas as ações realizadas pelos funcionários</p>
        </div>
        <button
          onClick={() => { fetchLogs(); fetchResumo(); fetchFuncionarios(); }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          🔄 Atualizar
        </button>
      </div>

      {/* Resumo */}
      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between gap-4 mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Resumo</h2>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Dias:</label>
            <select
              value={resumoDias}
              onChange={(e) => setResumoDias(Number(e.target.value))}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              <option value={7}>7</option>
              <option value={15}>15</option>
              <option value={30}>30</option>
              <option value={60}>60</option>
            </select>
          </div>
        </div>

        {loadingResumo ? (
          <div className="text-gray-500">Carregando resumo...</div>
        ) : resumo ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-gray-50 rounded">
              <div className="text-xs text-gray-500">Período</div>
              <div className="font-semibold text-gray-900">{resumo.periodo_analise}</div>
            </div>
            <div className="p-4 bg-gray-50 rounded">
              <div className="text-xs text-gray-500">Total de ações</div>
              <div className="font-semibold text-gray-900">{resumo.total_acoes}</div>
            </div>
            <div className="p-4 bg-gray-50 rounded">
              <div className="text-xs text-gray-500">Top IPs (qtde)</div>
              <div className="font-semibold text-gray-900">{Object.keys(resumo.top_ips || {}).length}</div>
            </div>
            <div className="p-4 bg-gray-50 rounded">
              <div className="text-xs text-gray-500">Ações por tipo (qtde)</div>
              <div className="font-semibold text-gray-900">{Object.keys(resumo.acoes_por_tipo || {}).length}</div>
            </div>
          </div>
        ) : (
          <div className="text-gray-500">Sem dados de resumo.</div>
        )}
      </div>

      {/* Filtros */}
      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🔍 Filtrar Registros</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Funcionário
            </label>
            <select
              value={filters.funcionario_id}
              onChange={(e) => setFilters((p) => ({ ...p, funcionario_id: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={loadingFuncionarios}
            >
              <option value="">Todos os funcionários</option>
              {funcionarios.map((func) => (
                <option key={func.id} value={func.id}>
                  {func.nome} ({func.perfil})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Área do Sistema
            </label>
            <select
              value={filters.entidade}
              onChange={(e) => setFilters((p) => ({ ...p, entidade: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {entidadesOpcoes.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de Ação
            </label>
            <select
              value={filters.acao}
              onChange={(e) => setFilters((p) => ({ ...p, acao: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {acoesOpcoes.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Inicial
            </label>
            <input
              type="date"
              value={filters.data_inicio}
              onChange={(e) => setFilters((p) => ({ ...p, data_inicio: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Final
            </label>
            <input
              type="date"
              value={filters.data_fim}
              onChange={(e) => setFilters((p) => ({ ...p, data_fim: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Endereço IP
            </label>
            <input
              type="text"
              placeholder="Ex: 192.168.1.1"
              value={filters.ip_address}
              onChange={(e) => setFilters((p) => ({ ...p, ip_address: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-between mt-4 gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Registros por página:</label>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <button
            onClick={() => setFilters({ funcionario_id: '', entidade: '', acao: '', data_inicio: '', data_fim: '', ip_address: '' })}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            ✖ Limpar Filtros
          </button>
        </div>
      </div>

      {/* Tabela */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Logs</h2>
            <div className="text-sm text-gray-600">
              {meta.total ? `${meta.total} registros` : `${logs.length} registros`}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              disabled={!canPrev}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className={`px-3 py-2 text-sm rounded border ${canPrev ? 'hover:bg-gray-50' : 'opacity-50 cursor-not-allowed'}`}
            >
              Anterior
            </button>
            <div className="text-sm text-gray-600">
              Página {page}{meta.total_paginas ? ` de ${meta.total_paginas}` : ''}
            </div>
            <button
              disabled={!canNext}
              onClick={() => setPage((p) => p + 1)}
              className={`px-3 py-2 text-sm rounded border ${canNext ? 'hover:bg-gray-50' : 'opacity-50 cursor-not-allowed'}`}
            >
              Próxima
            </button>
          </div>
        </div>

        {loadingLogs ? (
          <div className="p-6 text-gray-500">Carregando logs...</div>
        ) : logs.length === 0 ? (
          <div className="p-6 text-gray-500">Nenhum log encontrado para os filtros atuais.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quando</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quem</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Área</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">O que fez</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descrição</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Ações</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
                      <div className="font-medium">{formatDateTime(log.created_at).split(' ')[0]}</div>
                      <div className="text-xs text-gray-500">{formatDateTime(log.created_at).split(' ')[1]}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <div className="font-medium">{log.funcionario_nome || 'Sistema'}</div>
                      <div className="text-xs text-gray-500">{log.funcionario_perfil || '-'}</div>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {log.entidade}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <span className="font-medium">{log.acao_descricao || log.acao}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 max-w-[300px]">
                      <div className="truncate" title={log.payload_resumo}>
                        {log.payload_resumo || '-'}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                      <code className="text-xs">{log.ip_address || '-'}</code>
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      <button
                        onClick={() => openDetails(log)}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                      >
                        🔍 Ver detalhes
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal detalhes */}
      {showDetails && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white w-full max-w-2xl rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Detalhes do Log</h3>
              <button onClick={closeDetails} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>

            {detailsLoading ? (
              <div className="text-gray-500">Carregando detalhes...</div>
            ) : selectedDetails ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-xs text-gray-500">Data/Hora</div>
                    <div className="text-sm text-gray-900">{formatDateTime(selectedDetails.created_at)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Ação</div>
                    <div className="text-sm text-gray-900">{selectedDetails.acao}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Entidade</div>
                    <div className="text-sm text-gray-900">{selectedDetails.entidade}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Entidade ID</div>
                    <div className="text-sm text-gray-900">{selectedDetails.entidade_id}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Funcionário</div>
                    <div className="text-sm text-gray-900">{selectedDetails.funcionario_nome || '-'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">IP</div>
                    <div className="text-sm text-gray-900">{selectedDetails.ip_address || '-'}</div>
                  </div>
                </div>

                <div>
                  <div className="text-xs text-gray-500 mb-1">Resumo</div>
                  <div className="text-sm text-gray-900 bg-gray-50 rounded p-3">{selectedDetails.payload_resumo || '-'}</div>
                </div>

                <div>
                  <div className="text-xs text-gray-500 mb-1">Detalhes</div>
                  <pre className="text-xs bg-gray-50 rounded p-3 overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(selectedDetails.detalhes || {}, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="text-gray-500">Sem detalhes para exibir.</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
