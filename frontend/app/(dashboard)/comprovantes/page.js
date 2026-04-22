/**
 * Dashboard de Validação de Comprovantes
 * 
 * Interface para administradores validarem comprovantes de pagamento.
 */

'use client'
import { useState, useEffect } from 'react'
import { api } from '../../../lib/api'
import { StatusValidacao } from '../../../lib/constants/enums'

const DashboardValidacao = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({})
  const [pendentes, setPendentes] = useState([])
  const [emAnalise, setEmAnalise] = useState([])
  const [selectedTab, setSelectedTab] = useState('pendentes')
  const [selectedComprovante, setSelectedComprovante] = useState(null)
  
  // Estados para feedback no modal
  const [processandoAcao, setProcessandoAcao] = useState(false)
  const [acaoAtual, setAcaoAtual] = useState('')
  const [motivoRecusa, setMotivoRecusa] = useState('')
  const [mostrarCampoRecusa, setMostrarCampoRecusa] = useState(false)
  const [feedbackAcao, setFeedbackAcao] = useState(null)

  useEffect(() => {
    carregarDashboard()
  }, [])

  const mostrarFeedback = (tipo, titulo, mensagem) => {
    setFeedbackAcao({
      tipo,
      titulo,
      mensagem,
      timestamp: new Date().toISOString()
    })
  }

  const limparFeedback = () => {
    setFeedbackAcao(null)
  }

  const formatarHorarioFeedback = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const atualizarComprovanteNaTela = (pagamentoId, statusAtual, novoStatus) => {
    setPendentes(prev => prev.filter(item => item.pagamento_id !== pagamentoId))
    setEmAnalise(prev => prev.filter(item => item.pagamento_id !== pagamentoId))

    setStats(prev => ({
      ...prev,
      aguardando_comprovante: statusAtual === 'AGUARDANDO_COMPROVANTE'
        ? Math.max(0, (prev.aguardando_comprovante || 0) - 1)
        : prev.aguardando_comprovante || 0,
      em_analise: statusAtual === 'EM_ANALISE'
        ? Math.max(0, (prev.em_analise || 0) - 1)
        : prev.em_analise || 0,
      aprovados_hoje: novoStatus === 'APROVADO'
        ? (prev.aprovados_hoje || 0) + 1
        : prev.aprovados_hoje || 0,
      recusados_hoje: novoStatus === 'RECUSADO'
        ? (prev.recusados_hoje || 0) + 1
        : prev.recusados_hoje || 0,
    }))
  }

  const carregarDashboard = async () => {
    try {
      setLoading(true)
      const response = await api.get('/comprovantes/dashboard')
      
      console.log('[COMPROVANTES] Response completa:', response.data)
      console.log('[COMPROVANTES] estatisticas:', response.data.estatisticas)
      console.log('[COMPROVANTES] aguardando_comprovante:', response.data.aguardando_comprovante)
      console.log('[COMPROVANTES] em_analise:', response.data.em_analise)
      
      setStats(response.data.estatisticas || {})
      setPendentes(response.data.aguardando_comprovante || [])
      setEmAnalise(response.data.em_analise || [])
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error)
      mostrarFeedback('erro', 'Falha ao carregar comprovantes', error.response?.data?.detail || 'Não foi possível carregar o dashboard de comprovantes.')
    } finally {
      setLoading(false)
    }
  }

  const handleAprovar = async (pagamentoId, motivo = 'Comprovante validado e aprovado') => {
    try {
      setProcessandoAcao(true)
      setAcaoAtual('aprovando')
      
      await api.post('/comprovantes/validar', {
        pagamento_id: pagamentoId,
        status: StatusValidacao.APROVADO,
        motivo: motivo,
        usuario_validador_id: 1 // TODO: Pegar do contexto de autenticação
      })

      atualizarComprovanteNaTela(pagamentoId, selectedComprovante?.status_validacao, 'APROVADO')
      mostrarFeedback('sucesso', 'Comprovante aprovado', `Pagamento #${pagamentoId} aprovado com sucesso.`)
      carregarDashboard()
      setSelectedComprovante(null)
      setMostrarCampoRecusa(false)
      setMotivoRecusa('')
    } catch (error) {
      console.error('Erro ao aprovar:', error)
      mostrarFeedback('erro', 'Falha na aprovação', error.response?.data?.detail || 'Erro ao aprovar pagamento.')
    } finally {
      setProcessandoAcao(false)
      setAcaoAtual('')
    }
  }

  const handleRecusar = async (pagamentoId, motivo) => {
    if (!motivo.trim()) {
      mostrarFeedback('aviso', 'Motivo obrigatório', 'Informe o motivo da recusa antes de continuar.')
      return
    }

    try {
      setProcessandoAcao(true)
      setAcaoAtual('recusando')
      
      await api.post('/comprovantes/validar', {
        pagamento_id: pagamentoId,
        status: StatusValidacao.RECUSADO,
        motivo: motivo,
        usuario_validador_id: 1 // TODO: Pegar do contexto de autenticação
      })

      atualizarComprovanteNaTela(pagamentoId, selectedComprovante?.status_validacao, 'RECUSADO')
      mostrarFeedback('recusado', 'Comprovante recusado', `Pagamento #${pagamentoId} recusado com sucesso.`)
      carregarDashboard()
      setSelectedComprovante(null)
      setMostrarCampoRecusa(false)
      setMotivoRecusa('')
    } catch (error) {
      console.error('Erro ao recusar:', error)
      mostrarFeedback('erro', 'Falha na recusa', error.response?.data?.detail || 'Erro ao recusar pagamento.')
    } finally {
      setProcessandoAcao(false)
      setAcaoAtual('')
    }
  }

  const handleAprovarRapido = async (pagamentoId) => {
    try {
      await api.post(`/comprovantes/${pagamentoId}/aprovar-rapido`)
      const comprovante = pendentes.find(item => item.pagamento_id === pagamentoId) || emAnalise.find(item => item.pagamento_id === pagamentoId)
      atualizarComprovanteNaTela(pagamentoId, comprovante?.status_validacao, 'APROVADO')
      mostrarFeedback('sucesso', 'Aprovação rápida concluída', `Pagamento #${pagamentoId} aprovado rapidamente.`)
      carregarDashboard()
    } catch (error) {
      console.error('Erro ao aprovar rapidamente:', error)
      mostrarFeedback('erro', 'Falha na aprovação rápida', error.response?.data?.detail || 'Erro ao aprovar pagamento.')
    }
  }

  const formatarData = (dataString) => {
    return new Date(dataString).toLocaleString('pt-BR')
  }

  const formatarValor = (valor) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'AGUARDANDO_COMPROVANTE':
        return 'bg-yellow-100 text-yellow-800'
      case 'EM_ANALISE':
        return 'bg-blue-100 text-blue-800'
      case 'APROVADO':
        return 'bg-green-100 text-green-800'
      case 'RECUSADO':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getFeedbackStyle = (tipo) => {
    switch (tipo) {
      case 'sucesso':
        return {
          container: 'border-green-200 bg-green-50 text-green-900',
          badge: 'bg-green-600 text-white',
          icon: 'Aprovado'
        }
      case 'erro':
        return {
          container: 'border-red-200 bg-red-50 text-red-900',
          badge: 'bg-red-600 text-white',
          icon: 'Erro'
        }
      case 'recusado':
        return {
          container: 'border-rose-200 bg-rose-50 text-rose-900',
          badge: 'bg-rose-600 text-white',
          icon: 'Recusado'
        }
      case 'aviso':
      default:
        return {
          container: 'border-yellow-200 bg-yellow-50 text-yellow-900',
          badge: 'bg-yellow-500 text-white',
          icon: 'Aviso'
        }
    }
  }

  const ComprovanteCard = ({ comprovante }) => (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="font-semibold text-lg">
            Reserva #{comprovante.reserva?.id ?? comprovante.pagamento_id}
          </h4>
          <p className="text-gray-600">
            Cliente: {comprovante.cliente?.nome_completo || '—'}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(comprovante.status_validacao)}`}>
          {(comprovante.status_validacao || '').replace('_', ' ')}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-500">Valor</p>
          <p className="font-semibold">{formatarValor(comprovante.pagamento?.valor)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Tipo</p>
          <p className="font-semibold">{comprovante.tipo_comprovante}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Upload</p>
          <p className="font-semibold">{formatarData(comprovante.data_upload)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Arquivo</p>
          <a 
            href={`${(() => {
              const base = api?.defaults?.baseURL || ''
              if (typeof base === 'string' && base.startsWith('http')) return base
              const envBase = process.env.NEXT_PUBLIC_API_URL || ''
              if (envBase && envBase.startsWith('http')) return envBase.replace(/\/+$/, '')
              return 'http://localhost:8000/api/v1'
            })()}/comprovantes/arquivo/${comprovante.nome_arquivo}`}
            target="_blank"
            className="text-blue-600 hover:underline font-semibold"
          >
            Visualizar
          </a>
        </div>
      </div>

      {comprovante.observacoes && (
        <div className="mb-4">
          <p className="text-sm text-gray-500">Observações</p>
          <p className="text-gray-700">{comprovante.observacoes}</p>
        </div>
      )}

      <div className="flex gap-2">
        {comprovante.status_validacao === 'AGUARDANDO_COMPROVANTE' && (
          <>
            <button
              onClick={() => setSelectedComprovante(comprovante)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Analisar
            </button>
            <button
              onClick={() => handleAprovarRapido(comprovante.pagamento_id)}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            >
              Aprovar Rápido
            </button>
          </>
        )}
        
        {comprovante.status_validacao === 'EM_ANALISE' && (
          <>
            <button
              onClick={() => handleAprovar(comprovante.pagamento_id)}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            >
              Aprovar
            </button>
            <button
              onClick={() => setSelectedComprovante(comprovante)}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Recusar
            </button>
          </>
        )}
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Validação de Comprovantes</h1>
          <p className="mt-2 text-sm text-gray-500">
            Aprove ou recuse comprovantes com retorno visual imediato na tela.
          </p>
        </div>
        {feedbackAcao && (
          <button
            onClick={limparFeedback}
            className="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            Limpar aviso
          </button>
        )}
      </div>

      {feedbackAcao && (
        <div className={`mb-6 rounded-2xl border p-4 shadow-sm ${getFeedbackStyle(feedbackAcao.tipo).container}`}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${getFeedbackStyle(feedbackAcao.tipo).badge}`}>
                  {getFeedbackStyle(feedbackAcao.tipo).icon}
                </span>
                <p className="text-sm text-current/70">
                  {formatarHorarioFeedback(feedbackAcao.timestamp)}
                </p>
              </div>
              <h2 className="mt-3 text-lg font-semibold">{feedbackAcao.titulo}</h2>
              <p className="mt-1 text-sm">{feedbackAcao.mensagem}</p>
            </div>
          </div>
        </div>
      )}

      {/* Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-yellow-600">Aguardando</h3>
          <p className="text-3xl font-bold">{stats.aguardando_comprovante || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-blue-600">Em Análise</h3>
          <p className="text-3xl font-bold">{stats.em_analise || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-green-600">Aprovados Hoje</h3>
          <p className="text-3xl font-bold">{stats.aprovados_hoje || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-red-600">Recusados Hoje</h3>
          <p className="text-3xl font-bold">{stats.recusados_hoje || 0}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setSelectedTab('pendentes')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 'pendentes'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Aguardando Comprovante ({pendentes.length})
            </button>
            <button
              onClick={() => setSelectedTab('em_analise')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 'em_analise'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Em Análise ({emAnalise.length})
            </button>
          </nav>
        </div>

        <div className="p-6">
          {selectedTab === 'pendentes' && (
            <div>
              {pendentes.length === 0 ? (
                <p className="text-center text-gray-500 py-8">
                  Nenhum comprovante aguardando validação
                </p>
              ) : (
                pendentes.map(comprovante => (
                  <ComprovanteCard key={comprovante.id} comprovante={comprovante} />
                ))
              )}
            </div>
          )}

          {selectedTab === 'em_analise' && (
            <div>
              {emAnalise.length === 0 ? (
                <p className="text-center text-gray-500 py-8">
                  Nenhum comprovante em análise
                </p>
              ) : (
                emAnalise.map(comprovante => (
                  <ComprovanteCard key={comprovante.id} comprovante={comprovante} />
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modal de Análise */}
      {selectedComprovante && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto">
            {/* Header com feedback */}
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold">
                  {processandoAcao ? (
                    <span className="flex items-center gap-2">
                      {acaoAtual === 'aprovando' && '🔄 Aprovando...'}
                      {acaoAtual === 'recusando' && '🔄 Recusando...'}
                    </span>
                  ) : (
                    '📋 Analisar Comprovante'
                  )}
                </h2>
                <button
                  onClick={() => {
                    if (!processandoAcao) {
                      setSelectedComprovante(null)
                      setMostrarCampoRecusa(false)
                      setMotivoRecusa('')
                    }
                  }}
                  className="text-gray-400 hover:text-gray-600 text-2xl disabled:opacity-50"
                  disabled={processandoAcao}
                >
                  ×
                </button>
              </div>
              
              {/* Feedback de processamento */}
              {processandoAcao && (
                <div className="mt-4">
                  <div className="flex items-center gap-2 text-sm text-blue-600">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span>
                      {acaoAtual === 'aprovando' && 'Processando aprovação...'}
                      {acaoAtual === 'recusando' && 'Processando recusa...'}
                    </span>
                  </div>
                  <div className="mt-2 bg-blue-50 rounded-lg p-3">
                    <p className="text-xs text-blue-700">
                      ⏳ Aguarde enquanto validamos o comprovante e atualizamos o status...
                    </p>
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-6">
              <div className="mb-6">
                <h3 className="font-semibold mb-2">💰 Informações do Pagamento</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Reserva:</span> #{selectedComprovante.reserva?.id ?? selectedComprovante.pagamento_id}
                  </div>
                  <div>
                    <span className="text-gray-500">Cliente:</span> {selectedComprovante.cliente?.nome_completo || '—'}
                  </div>
                  <div>
                    <span className="text-gray-500">Valor:</span> {formatarValor(selectedComprovante.pagamento?.valor)}
                  </div>
                  <div>
                    <span className="text-gray-500">Tipo:</span> {selectedComprovante.tipo_comprovante}
                  </div>
                </div>
              </div>

              <div className="mb-6">
                <h3 className="font-semibold mb-2">📄 Comprovante</h3>
                <a 
                  href={`/api/v1/comprovantes/arquivo/${selectedComprovante.nome_arquivo}`}
                  target="_blank"
                  className="text-blue-600 hover:underline inline-flex items-center gap-1"
                >
                  🔍 Abrir comprovante em nova aba
                </a>
              </div>

              {/* Campo de recusa melhorado */}
              {mostrarCampoRecusa && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <h3 className="font-semibold text-red-800 mb-2">❌ Motivo da Recusa</h3>
                  <textarea
                    value={motivoRecusa}
                    onChange={(e) => setMotivoRecusa(e.target.value)}
                    className="w-full px-3 py-2 border border-red-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    rows={3}
                    placeholder="Descreva o motivo da recusa..."
                    disabled={processandoAcao}
                  />
                  <div className="mt-2 flex gap-2">
                    <button
                      onClick={() => {
                        setMostrarCampoRecusa(false)
                        setMotivoRecusa('')
                      }}
                      className="px-3 py-1 text-sm bg-gray-300 text-gray-700 rounded hover:bg-gray-400 disabled:opacity-50"
                      disabled={processandoAcao}
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={() => handleRecusar(selectedComprovante.pagamento_id, motivoRecusa)}
                      className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                      disabled={processandoAcao || !motivoRecusa.trim()}
                    >
                      Confirmar Recusa
                    </button>
                  </div>
                </div>
              )}

              {/* Botões de Ação */}
              <div className="flex gap-4">
                {!mostrarCampoRecusa ? (
                  <>
                    <button
                      onClick={() => {
                        handleAprovar(selectedComprovante.pagamento_id)
                      }}
                      className="flex-1 bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center justify-center gap-2"
                      disabled={processandoAcao}
                    >
                      {processandoAcao && acaoAtual === 'aprovando' ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          Aprovando...
                        </>
                      ) : (
                        <>
                          ✅ Aprovar
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => setMostrarCampoRecusa(true)}
                      className="flex-1 bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                      disabled={processandoAcao}
                    >
                      ❌ Recusar
                    </button>
                  </>
                ) : null}
                
                <button
                  onClick={() => {
                    setSelectedComprovante(null)
                    setMostrarCampoRecusa(false)
                    setMotivoRecusa('')
                  }}
                  className="flex-1 bg-gray-600 text-white py-3 px-4 rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  disabled={processandoAcao}
                >
                  {processandoAcao ? '⏳ Processando...' : '🚪 Cancelar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DashboardValidacao
