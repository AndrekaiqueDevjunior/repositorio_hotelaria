'use client'
import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'

export default function Antifraude() {
  const [activeTab, setActiveTab] = useState('antifraude')
  const [operacoes, setOperacoes] = useState([])
  const [pagamentos, setPagamentos] = useState([])
  const [transacoes, setTransacoes] = useState([])
  const [stats, setStats] = useState({
    pendentes: 0,
    aprovadas: 0,
    recusadas: 0
  })
  const [pagamentoStats, setPagamentoStats] = useState({
    pendentes: 0,
    aprovados: 0,
    rejeitados: 0,
    total: 0
  })

  // Estados para Cielo Real
  const [cieloTransacoes, setCieloTransacoes] = useState([])
  const [cieloLoading, setCieloLoading] = useState(false)
  const [cieloError, setCieloError] = useState(null)
  const [cieloStatus, setCieloStatus] = useState(null)
  const [cieloFilters, setCieloFilters] = useState({
    page: 1,
    pageSize: 20,
    dataInicio: '',
    dataFim: ''
  })
  const [cieloPagination, setCieloPagination] = useState(null)
  const [selectedPayment, setSelectedPayment] = useState(null)
  const [showDetails, setShowDetails] = useState(false)
  const [showOperacaoDetails, setShowOperacaoDetails] = useState(false)
  const [selectedOperacao, setSelectedOperacao] = useState(null)
  
  // Estados para registro manual de pagamento
  const [showManualModal, setShowManualModal] = useState(false)
  const [manualLoading, setManualLoading] = useState(false)
  const [manualComprovante, setManualComprovante] = useState(null)
  const [manualPayment, setManualPayment] = useState({
    codigo: '',
    valor: '',
    reserva_id: '',
    metodo: 'credit_card'
  })
  
  // Estados para proteção por senha
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [adminPassword, setAdminPassword] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [passwordLoading, setPasswordLoading] = useState(false)

  useEffect(() => {
    loadOperacoes()
    loadPagamentos()
    loadTransacoes()
  }, [])

  const loadOperacoes = async () => {
    try {
      const res = await api.get('/antifraude/operacoes')
      const ops = res.data.operacoes || []
      setOperacoes(ops)
      
      // Calcular estatísticas
      setStats({
        pendentes: res.data.pendentes || 0,
        aprovadas: ops.filter(o => o.status === 'AUTO_APROVADO' || o.status === 'MANUAL_APROVADO').length,
        recusadas: ops.filter(o => o.status === 'RECUSADO').length
      })
    } catch (error) {
      console.error('Erro ao carregar operações:', error)
    }
  }

  const loadPagamentos = async () => {
    try {
      const res = await api.get('/pagamentos')
      const pags = res.data.pagamentos || []
      setPagamentos(pags)
      
      // Calcular estatísticas
      setPagamentoStats({
        total: pags.length,
        pendentes: pags.filter(p => p.status === 'PENDING').length,
        aprovados: pags.filter(p => p.status === 'APPROVED').length,
        rejeitados: pags.filter(p => p.status === 'REJECTED' || p.status === 'CHARGEBACK').length
      })
    } catch (error) {
      console.error('Erro ao carregar pagamentos:', error)
    }
  }

  const loadTransacoes = async () => {
    try {
      // Agrupar transações por cliente com dados de merchant
      const res = await api.get('/pagamentos')
      const pags = res.data.pagamentos || []
      
      // Agrupar por cliente e calcular totais
      const transacoesAgrupadas = {}
      pags.forEach(pag => {
        const clienteKey = pag.cliente_nome || `Cliente #${pag.clienteId}`
        if (!transacoesAgrupadas[clienteKey]) {
          transacoesAgrupadas[clienteKey] = {
            cliente: clienteKey,
            clienteId: pag.clienteId,
            totalTransacoes: 0,
            valorTotal: 0,
            aprovadas: 0,
            rejeitadas: 0,
            pendentes: 0,
            riscoMedio: 0,
            merchant: 'Cielo', // Merchant padrão
            ultimaTransacao: null
          }
        }
        
        const trans = transacoesAgrupadas[clienteKey]
        trans.totalTransacoes++
        trans.valorTotal += pag.valor || 0
        
        if (pag.status === 'APPROVED') trans.aprovadas++
        else if (pag.status === 'REJECTED' || pag.status === 'CHARGEBACK') trans.rejeitadas++
        else if (pag.status === 'PENDING') trans.pendentes++
        
        trans.riscoMedio += pag.risk_score || 0
        
        if (!trans.ultimaTransacao || new Date(pag.dataCriacao) > new Date(trans.ultimaTransacao)) {
          trans.ultimaTransacao = pag.dataCriacao
        }
      })
      
      // Calcular médias e ordenar
      const resultado = Object.values(transacoesAgrupadas).map(trans => ({
        ...trans,
        riscoMedio: Math.round(trans.riscoMedio / trans.totalTransacoes),
        taxaAprovacao: Math.round((trans.aprovadas / trans.totalTransacoes) * 100)
      })).sort((a, b) => b.valorTotal - a.valorTotal)
      
      setTransacoes(resultado)
    } catch (error) {
      console.error('Erro ao carregar transações:', error)
    }
  }

  const handleAprovar = async (id) => {
    try {
      await api.post(`/antifraude/${id}/aprovar`)
      loadOperacoes()
    } catch (error) {
      console.error('Erro ao aprovar operação:', error)
      alert('Erro ao aprovar operação')
    }
  }

  const handleRecusar = async (id) => {
    try {
      await api.post(`/antifraude/${id}/recusar`)
      loadOperacoes()
    } catch (error) {
      console.error('Erro ao recusar operação:', error)
      alert('Erro ao recusar operação')
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      'PENDENTE': 'text-yellow-600 bg-yellow-100',
      'AUTO_APROVADO': 'text-green-600 bg-green-100',
      'MANUAL_APROVADO': 'text-blue-600 bg-blue-100',
      'RECUSADO': 'text-red-600 bg-red-100'
    }
    return colors[status] || 'text-gray-600 bg-gray-100'
  }

  const getRiskColor = (score) => {
    if (score >= 80) return 'text-red-600'
    if (score >= 50) return 'text-yellow-600'
    return 'text-green-600'
  }

  // Funções para autenticação de administrador
  const handleTabChange = (tab) => {
    if (tab === 'cielo-real' && !isAdminAuthenticated) {
      setShowPasswordModal(true)
      return
    }
    setActiveTab(tab)
  }

  const verifyAdminPassword = async () => {
    if (!adminPassword.trim()) {
      setPasswordError('Por favor, digite a senha')
      return
    }

    setPasswordLoading(true)
    setPasswordError('')

    try {
      const response = await api.post('/auth/admin/verify', {
        password: adminPassword
      })

      if (response.data.success) {
        setIsAdminAuthenticated(true)
        setShowPasswordModal(false)
        setActiveTab('cielo-real')
        setAdminPassword('')
        // Carregar dados da Cielo após autenticação bem-sucedida
        loadCieloStatus()
        loadCieloTransacoes()
      } else {
        setPasswordError('Senha de administrador incorreta')
      }
    } catch (error) {
      console.error('Erro ao verificar senha:', error)
      setPasswordError('Erro ao verificar senha. Tente novamente.')
    } finally {
      setPasswordLoading(false)
    }
  }

  const handlePasswordModalClose = () => {
    setShowPasswordModal(false)
    setAdminPassword('')
    setPasswordError('')
    // Voltar para aba anterior se não estiver autenticado
    if (!isAdminAuthenticated) {
      setActiveTab('antifraude')
    }
  }

  const handlePasswordSubmit = (e) => {
    e.preventDefault()
    verifyAdminPassword()
  }

  // Funções para Cielo
  const loadCieloStatus = async () => {
    try {
      const res = await api.get('/cielo/status')
      setCieloStatus(res.data)
    } catch (error) {
      console.error('Erro ao carregar status Cielo:', error)
      setCieloError('Erro ao conectar com API Cielo')
    }
  }

  const loadCieloTransacoes = async () => {
    setCieloLoading(true)
    setCieloError(null)
    
    try {
      const res = await api.get('/cielo/historico', {
        params: cieloFilters
      })
      
      if (res.data.success) {
        setCieloTransacoes(res.data.data || [])
        setCieloPagination(res.data.pagination || null)
      } else {
        setCieloError(res.data.error || 'Erro ao carregar transações')
      }
    } catch (error) {
      console.error('Erro ao carregar transações Cielo:', error)
      setCieloError('Erro ao carregar transações da Cielo')
    } finally {
      setCieloLoading(false)
    }
  }

  const handleCieloFilter = () => {
    setCieloFilters({ ...cieloFilters, page: 1 })
    loadCieloTransacoes()
  }

  const handleCieloPageChange = (newPage) => {
    setCieloFilters({ ...cieloFilters, page: newPage })
    loadCieloTransacoes()
  }

  const consultarPagamentoCielo = async (paymentId) => {
    try {
      const res = await api.get(`/cielo/pagamento/${paymentId}`)
      
      if (res.data.success) {
        setSelectedPayment(res.data.data)
        setShowDetails(true)
      } else {
        alert('Pagamento não encontrado')
      }
    } catch (error) {
      console.error('Erro ao consultar pagamento:', error)
      alert('Erro ao consultar pagamento')
    }
  }

  // Funções para registro manual de pagamento
  const consultarComprovante = async () => {
    if (!manualPayment.codigo.trim()) {
      alert('Digite o código do comprovante')
      return
    }

    setManualLoading(true)
    try {
      // Determinar se é PaymentId ou TID
      const isPaymentId = manualPayment.codigo.includes('-')
      const endpoint = isPaymentId ? 'payment_id' : 'tid'
      
      const res = await api.post('/pagamentos/consultar-comprovante', {
        [endpoint]: manualPayment.codigo
      })

      if (res.data.found) {
        setManualComprovante(res.data)
        alert(' Comprovante validado com sucesso!')
      } else {
        setManualComprovante(null)
        alert(' Comprovante não encontrado ou inválido')
      }
    } catch (error) {
      console.error('Erro ao consultar comprovante:', error)
      setManualComprovante(null)
      alert(' Erro ao consultar comprovante')
    } finally {
      setManualLoading(false)
    }
  }

  const registrarPagamento = async () => {
    if (!manualComprovante) {
      alert('Consulte o comprovante primeiro')
      return
    }

    if (!manualPayment.reserva_id || !manualPayment.valor) {
      alert('Preencha todos os campos')
      return
    }

    setManualLoading(true)
    try {
      const res = await api.post('/pagamentos/registrar-manual-maquininha', {
        reserva_id: parseInt(manualPayment.reserva_id),
        codigo_autorizacao: manualPayment.codigo,
        valor: parseFloat(manualPayment.valor),
        metodo: manualPayment.metodo
      })

      if (res.data.success) {
        alert(' Pagamento registrado com sucesso!')
        
        // Limpar formulário
        setManualPayment({
          codigo: '',
          valor: '',
          reserva_id: '',
          metodo: 'credit_card'
        })
        setManualComprovante(null)
        setShowManualModal(false)
        
        // Recarregar lista de pagamentos
        loadPagamentos()
        
        // Mostrar voucher se houver
        if (res.data.voucher) {
          alert(` Voucher gerado: ${res.data.voucher.codigo}`)
        }
      } else {
        alert(' Erro ao registrar pagamento')
      }
    } catch (error) {
      console.error('Erro ao registrar pagamento:', error)
      alert(' Erro ao registrar pagamento')
    } finally {
      setManualLoading(false)
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(amount / 100)
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('pt-BR')
  }

  const getCieloStatusColor = (status) => {
    const colors = {
      1: 'bg-yellow-100 text-yellow-800',
      2: 'bg-green-100 text-green-800',
      3: 'bg-red-100 text-red-800',
      10: 'bg-gray-100 text-gray-800',
      12: 'bg-purple-100 text-purple-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getCieloStatusText = (status) => {
    const texts = {
      1: 'Autorizado',
      2: 'Capturado',
      3: 'Negado',
      10: 'Cancelado',
      12: 'Em análise'
    }
    return texts[status] || 'Desconhecido'
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-real-blue mb-6">Sistema Antifraude</h1>
      
      {/* Navegação por Abas */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="flex border-b">
          <button
            onClick={() => handleTabChange('antifraude')}
            className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'antifraude'
                ? 'border-real-blue text-real-blue'
                : 'border-transparent text-gray-600 hover:text-real-blue'
            }`}
          >
            🛡️ Operações Antifraude
          </button>
          <button
            onClick={() => handleTabChange('pagamentos')}
            className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'pagamentos'
                ? 'border-real-blue text-real-blue'
                : 'border-transparent text-gray-600 hover:text-real-blue'
            }`}
          >
            💳 Todos os Pagamentos
          </button>
          <button
            onClick={() => handleTabChange('transacoes')}
            className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'transacoes'
                ? 'border-real-blue text-real-blue'
                : 'border-transparent text-gray-600 hover:text-real-blue'
            }`}
          >
            📊 Histórico de Transações
          </button>
          <button
            onClick={() => handleTabChange('cielo-real')}
            className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'cielo-real'
                ? 'border-real-blue text-real-blue'
                : 'border-transparent text-gray-600 hover:text-real-blue'
            }`}
          >
            🔒 {isAdminAuthenticated ? '🌐' : '🔒'} Histórico Cielo Real
          </button>
        </div>
      </div>

      {/* Conteúdo da Aba Ativa */}
      {activeTab === 'antifraude' && (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm">Operações Pendentes</h3>
              <p className="text-3xl font-bold text-yellow-600">{stats.pendentes}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm">Aprovadas</h3>
              <p className="text-3xl font-bold text-green-600">{stats.aprovadas}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm">Recusadas</h3>
              <p className="text-3xl font-bold text-red-600">{stats.recusadas}</p>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-real-blue text-white">
                <tr>
                  <th className="p-3 text-left">ID</th>
                  <th className="p-3 text-left">Cliente</th>
                  <th className="p-3 text-left">Reserva</th>
                  <th className="p-3 text-left">Pagamento</th>
                  <th className="p-3 text-left">Score Risco</th>
                  <th className="p-3 text-left">Status</th>
                  <th className="p-3 text-left">Motivo</th>
                  <th className="p-3 text-left">Ações</th>
                </tr>
              </thead>
              <tbody>
                {operacoes.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="p-6 text-center text-gray-500">
                      Nenhuma operação encontrada
                    </td>
                  </tr>
                ) : (
                  operacoes.map((op) => (
                    <tr key={op.id} className="border-b hover:bg-gray-50">
                      <td className="p-3">#{op.id}</td>
                      <td className="p-3">{op.cliente_nome}</td>
                      <td className="p-3">{op.reserva_codigo}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          op.payment_status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                          op.payment_status === 'REJECTED' ? 'bg-red-100 text-red-800' :
                          op.payment_status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {op.payment_status || 'N/A'}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className={`font-bold ${getRiskColor(op.risk_score)}`}>
                          {op.risk_score}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(op.status)}`}>
                          {op.status}
                        </span>
                      </td>
                      <td className="p-3 text-sm text-gray-600">
                        {op.motivo_risco || '-'}
                      </td>
                      <td className="p-3">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => {
                              setSelectedOperacao(op)
                              setShowOperacaoDetails(true)
                            }}
                            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                          >
                            📊 Detalhes
                          </button>
                          {op.status === 'PENDENTE' && (
                            <>
                              <button
                                onClick={() => handleAprovar(op.id)}
                                className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                              >
                                Aprovar
                              </button>
                              <button
                                onClick={() => handleRecusar(op.id)}
                                className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                              >
                                Recusar
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'pagamentos' && (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm">Total</h3>
              <p className="text-3xl font-bold text-blue-600">{pagamentoStats.total}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm">Pendentes</h3>
              <p className="text-3xl font-bold text-yellow-600">{pagamentoStats.pendentes}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm">Aprovados</h3>
              <p className="text-3xl font-bold text-green-600">{pagamentoStats.aprovados}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm">Rejeitados</h3>
              <p className="text-3xl font-bold text-red-600">{pagamentoStats.rejeitados}</p>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-real-blue text-white">
                <tr>
                  <th className="p-3 text-left">ID</th>
                  <th className="p-3 text-left">ID Cielo</th>
                  <th className="p-3 text-left">Cliente</th>
                  <th className="p-3 text-left">Reserva</th>
                  <th className="p-3 text-left">Valor</th>
                  <th className="p-3 text-left">Método</th>
                  <th className="p-3 text-left">Status</th>
                  <th className="p-3 text-left">Score</th>
                  <th className="p-3 text-left">Data</th>
                </tr>
              </thead>
              <tbody>
                {pagamentos.length === 0 ? (
                  <tr>
                    <td colSpan="9" className="p-6 text-center text-gray-500">
                      Nenhum pagamento encontrado
                    </td>
                  </tr>
                ) : (
                  pagamentos.map((pag) => (
                    <tr key={pag.id} className="border-b hover:bg-gray-50">
                      <td className="p-3">#{pag.id}</td>
                      <td className="p-3 text-xs text-gray-600">{pag.cieloPaymentId}</td>
                      <td className="p-3">{pag.cliente_nome}</td>
                      <td className="p-3">{pag.reserva_codigo}</td>
                      <td className="p-3 font-semibold">R$ {pag.valor?.toFixed(2)}</td>
                      <td className="p-3">
                        <span className="text-xs px-2 py-1 bg-gray-100 rounded">
                          {pag.metodo}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          pag.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                          pag.status === 'REJECTED' || pag.status === 'CHARGEBACK' ? 'bg-red-100 text-red-800' :
                          pag.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {pag.status}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className={`font-bold ${getRiskColor(pag.risk_score)}`}>
                          {pag.risk_score || '-'}
                        </span>
                      </td>
                      <td className="p-3 text-sm text-gray-600">
                        {new Date(pag.dataCriacao).toLocaleDateString('pt-BR')}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'transacoes' && (
        <div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h3 className="text-blue-800 font-semibold mb-2">📊 Histórico de Transações por Cliente</h3>
            <p className="text-blue-600 text-sm">Visualização agrupada por cliente com dados do merchant e métricas de risco</p>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-real-blue text-white">
                <tr>
                  <th className="p-3 text-left">Cliente</th>
                  <th className="p-3 text-left">Merchant</th>
                  <th className="p-3 text-left">Total Transações</th>
                  <th className="p-3 text-left">Valor Total</th>
                  <th className="p-3 text-left">Taxa Aprovação</th>
                  <th className="p-3 text-left">Risco Médio</th>
                  <th className="p-3 text-left">Status</th>
                  <th className="p-3 text-left">Última Transação</th>
                </tr>
              </thead>
              <tbody>
                {transacoes.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="p-6 text-center text-gray-500">
                      Nenhuma transação encontrada
                    </td>
                  </tr>
                ) : (
                  transacoes.map((trans, index) => (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="p-3 font-medium">{trans.cliente}</td>
                      <td className="p-3">
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">
                          {trans.merchant}
                        </span>
                      </td>
                      <td className="p-3">
                        <div className="text-center">
                          <div className="font-semibold">{trans.totalTransacoes}</div>
                          <div className="text-xs text-gray-500">
                            {trans.aprovadas}✓ {trans.rejeitadas}✗ {trans.pendentes}⏳
                          </div>
                        </div>
                      </td>
                      <td className="p-3 font-semibold text-green-600">
                        R$ {trans.valorTotal.toFixed(2)}
                      </td>
                      <td className="p-3">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className={`h-2 rounded-full ${
                                trans.taxaAprovacao >= 80 ? 'bg-green-500' :
                                trans.taxaAprovacao >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{width: `${trans.taxaAprovacao}%`}}
                            />
                          </div>
                          <span className="text-sm font-medium">{trans.taxaAprovacao}%</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <span className={`font-bold ${getRiskColor(trans.riscoMedio)}`}>
                          {trans.riscoMedio}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          trans.riscoMedio >= 70 ? 'bg-red-100 text-red-800' :
                          trans.riscoMedio >= 40 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {trans.riscoMedio >= 70 ? 'Alto Risco' :
                           trans.riscoMedio >= 40 ? 'Médio Risco' : 'Baixo Risco'}
                        </span>
                      </td>
                      <td className="p-3 text-sm text-gray-600">
                        {trans.ultimaTransacao ? new Date(trans.ultimaTransacao).toLocaleDateString('pt-BR') : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Aba Histórico Cielo Real */}
      {activeTab === 'cielo-real' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-real-blue">Histórico Cielo Real</h2>
              <p className="text-gray-600 mt-1">Consulte transações reais da Cielo E-commerce</p>
            </div>
            <div className="flex items-center space-x-4">
              {cieloStatus && (
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${cieloStatus.success ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className="text-sm text-gray-600">
                    {cieloStatus.mode?.toUpperCase()} - {cieloStatus.status}
                  </span>
                </div>
              )}
              <button
                onClick={loadCieloTransacoes}
                disabled={cieloLoading}
                className="bg-real-blue text-white px-4 py-2 rounded hover:bg-blue-800 disabled:opacity-50"
              >
                {cieloLoading ? 'Atualizando...' : 'Atualizar'}
              </button>
            </div>
          </div>

          {/* Status Card */}
          {cieloStatus && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Status da Conexão</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Ambiente</p>
                  <p className="font-semibold capitalize">{cieloStatus.mode}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Merchant ID</p>
                  <p className="font-mono text-sm">{cieloStatus.merchant_id}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">API Base URL</p>
                  <p className="font-mono text-xs truncate">{cieloStatus.api_base_url}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Timeout</p>
                  <p className="font-semibold">{cieloStatus.timeout}</p>
                </div>
              </div>
            </div>
          )}

          {/* Registro Manual de Pagamento */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-lg font-semibold">📳 Registrar Pagamento Manual</h3>
                <p className="text-gray-600 mt-1">Registre pagamentos feitos na maquininha fora do sistema</p>
              </div>
              <button
                onClick={() => setShowManualModal(true)}
                className="bg-real-gold text-real-blue px-4 py-2 rounded hover:bg-yellow-500"
              >
                Novo Registro
              </button>
            </div>
            
            {/* Formulário de Registro */}
            {showManualModal && (
              <div className="border-t pt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Código do Comprovante (PaymentId ou TID)
                    </label>
                    <input
                      type="text"
                      value={manualPayment.codigo}
                      onChange={(e) => setManualPayment({...manualPayment, codigo: e.target.value})}
                      placeholder="Ex: 8a8f7d5a-1b2c-3d4e-5f6g-7h8i9j0k1l2m"
                      className="w-full p-2 border rounded focus:ring-2 focus:ring-real-blue focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Valor (R$)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={manualPayment.valor}
                      onChange={(e) => setManualPayment({...manualPayment, valor: e.target.value})}
                      placeholder="150.00"
                      className="w-full p-2 border rounded focus:ring-2 focus:ring-real-blue focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ID da Reserva
                    </label>
                    <input
                      type="number"
                      value={manualPayment.reserva_id}
                      onChange={(e) => setManualPayment({...manualPayment, reserva_id: e.target.value})}
                      placeholder="123"
                      className="w-full p-2 border rounded focus:ring-2 focus:ring-real-blue focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Método
                    </label>
                    <select
                      value={manualPayment.metodo}
                      onChange={(e) => setManualPayment({...manualPayment, metodo: e.target.value})}
                      className="w-full p-2 border rounded focus:ring-2 focus:ring-real-blue focus:border-transparent"
                    >
                      <option value="credit_card">Cartão Crédito</option>
                      <option value="debit_card">Cartão Débito</option>
                    </select>
                  </div>
                </div>
                
                <div className="flex space-x-4 mt-4">
                  <button
                    onClick={consultarComprovante}
                    disabled={manualLoading}
                    className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
                  >
                    {manualLoading ? 'Consultando...' : '🔍 Consultar Comprovante'}
                  </button>
                  <button
                    onClick={registrarPagamento}
                    disabled={manualLoading || !manualComprovante}
                    className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50"
                  >
                    {manualLoading ? 'Registrando...' : '✅ Registrar Pagamento'}
                  </button>
                  <button
                    onClick={() => setShowManualModal(false)}
                    className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                  >
                    Cancelar
                  </button>
                </div>
                
                {/* Resultado da Consulta */}
                {manualComprovante && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded">
                    <h4 className="font-semibold text-blue-800 mb-2">✅ Comprovante Validado</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div><strong>PaymentId:</strong> {manualComprovante.payment_id}</div>
                      <div><strong>Status:</strong> {manualComprovante.status_text}</div>
                      <div><strong>Valor:</strong> {formatCurrency(manualComprovante.amount)}</div>
                      <div><strong>Data:</strong> {formatDate(manualComprovante.captured_date)}</div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Filters */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Filtros</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Início
                </label>
                <input
                  type="datetime-local"
                  value={cieloFilters.dataInicio}
                  onChange={(e) => setCieloFilters({ ...cieloFilters, dataInicio: e.target.value })}
                  className="w-full p-2 border rounded focus:ring-2 focus:ring-real-blue focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Fim
                </label>
                <input
                  type="datetime-local"
                  value={cieloFilters.dataFim}
                  onChange={(e) => setCieloFilters({ ...cieloFilters, dataFim: e.target.value })}
                  className="w-full p-2 border rounded focus:ring-2 focus:ring-real-blue focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Resultados por página
                </label>
                <select
                  value={cieloFilters.pageSize}
                  onChange={(e) => setCieloFilters({ ...cieloFilters, pageSize: parseInt(e.target.value), page: 1 })}
                  className="w-full p-2 border rounded focus:ring-2 focus:ring-real-blue focus:border-transparent"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleCieloFilter}
                  className="w-full bg-real-gold text-real-blue px-4 py-2 rounded hover:bg-yellow-500"
                >
                  Aplicar Filtros
                </button>
              </div>
            </div>
          </div>

          {/* Transactions Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Transações</h3>
              {cieloPagination && (
                <p className="text-sm text-gray-600 mt-1">
                  Mostrando {cieloTransacoes.length} de {cieloPagination.total} transações
                </p>
              )}
            </div>
            
            {cieloError && (
              <div className="px-6 py-4 bg-red-50 border-l-4 border-red-400">
                <p className="text-red-700">{cieloError}</p>
              </div>
            )}

            {cieloLoading ? (
              <div className="px-6 py-8 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-real-blue"></div>
                <p className="mt-2 text-gray-600">Carregando transações...</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Payment ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Order ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cliente
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Valor
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cartão
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Parcelas
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Data
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ações
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {cieloTransacoes.length === 0 ? (
                      <tr>
                        <td colSpan="8" className="px-6 py-8 text-center text-gray-500">
                          Nenhuma transação encontrada
                        </td>
                      </tr>
                    ) : (
                      cieloTransacoes.map((transacao) => (
                        <tr key={transacao.PaymentId} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                            {transacao.PaymentId}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                            {transacao.MerchantOrderId}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div className="font-medium text-gray-900">
                              {transacao.Customer?.Name || '-'}
                            </div>
                            {transacao.Customer?.Identity && (
                              <div className="text-xs text-gray-500">
                                CPF: {transacao.Customer.Identity}
                              </div>
                            )}
                            {transacao.Customer?.Email && (
                              <div className="text-xs text-gray-500">
                                {transacao.Customer.Email}
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">
                            {formatCurrency(transacao.Amount)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getCieloStatusColor(transacao.Status)}`}>
                              {getCieloStatusText(transacao.Status)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div>
                              <div className="text-gray-900">{transacao.CreditCard?.Brand}</div>
                              <div className="text-gray-500 text-xs">{transacao.CreditCard?.CardNumber}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            {transacao.Installments}x
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(transacao.CaptureDate)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <button
                              onClick={() => consultarPagamentoCielo(transacao.PaymentId)}
                              className="text-real-blue hover:text-blue-800 font-medium"
                            >
                              Detalhes
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {cieloPagination && cieloPagination.total_pages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    Página {cieloPagination.page} de {cieloPagination.total_pages}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleCieloPageChange(cieloPagination.page - 1)}
                      disabled={cieloPagination.page <= 1}
                      className="px-3 py-1 border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Anterior
                    </button>
                    <button
                      onClick={() => handleCieloPageChange(cieloPagination.page + 1)}
                      disabled={cieloPagination.page >= cieloPagination.total_pages}
                      className="px-3 py-1 border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Próxima
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Payment Details Modal */}
      {showDetails && selectedPayment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Detalhes do Pagamento</h3>
            </div>
            <div className="px-6 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Payment ID</p>
                  <p className="font-mono text-sm">{selectedPayment.PaymentId}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Order ID</p>
                  <p className="font-mono text-sm">{selectedPayment.MerchantOrderId}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Cliente</p>
                  <p className="font-medium">{selectedPayment.Customer?.Name || '-'}</p>
                  {selectedPayment.Customer?.Identity && (
                    <p className="text-sm text-gray-500">CPF: {selectedPayment.Customer.Identity}</p>
                  )}
                  {selectedPayment.Customer?.Email && (
                    <p className="text-sm text-gray-500">{selectedPayment.Customer.Email}</p>
                  )}
                </div>
                <div>
                  <p className="text-sm text-gray-500">Valor</p>
                  <p className="font-semibold">{formatCurrency(selectedPayment.Amount)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getCieloStatusColor(selectedPayment.Status)}`}>
                    {getCieloStatusText(selectedPayment.Status)}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Código Autorização</p>
                  <p className="font-mono">{selectedPayment.AuthorizationCode || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Return Code</p>
                  <p className="font-mono">{selectedPayment.ReturnCode}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Return Message</p>
                  <p className="text-sm">{selectedPayment.ReturnMessage}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Data Captura</p>
                  <p className="text-sm">{formatDate(selectedPayment.CapturedDate)}</p>
                </div>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200">
              <button
                onClick={() => setShowDetails(false)}
                className="w-full bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============= MODAL DE DETALHES DA OPERAÇÃO ANTIFRAUDE ============= */}
      {showOperacaoDetails && selectedOperacao && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="bg-gradient-to-r from-red-600 to-red-800 text-white p-6 rounded-t-lg">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    🛡️ Análise Antifraude #{selectedOperacao.id}
                  </h2>
                  <p className="text-sm opacity-80 mt-1">
                    {selectedOperacao.cliente_nome} • Reserva {selectedOperacao.reserva_codigo}
                  </p>
                </div>
                <span className={`px-4 py-2 rounded-lg font-bold ${getStatusColor(selectedOperacao.status)}`}>
                  {selectedOperacao.status}
                </span>
              </div>
            </div>

            {/* Score e Status */}
            <div className="grid grid-cols-3 gap-4 p-6 bg-gray-50 border-b">
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Score de Risco</p>
                <p className={`text-4xl font-bold ${getRiskColor(selectedOperacao.risk_score)}`}>
                  {selectedOperacao.risk_score}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {selectedOperacao.risk_score < 30 ? 'Baixo Risco' :
                   selectedOperacao.risk_score < 70 ? 'Médio Risco' : 'Alto Risco'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Status Pagamento</p>
                <span className={`inline-block px-4 py-2 rounded-lg font-bold ${
                  selectedOperacao.payment_status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                  selectedOperacao.payment_status === 'REJECTED' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {selectedOperacao.payment_status || 'PENDING'}
                </span>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Valor</p>
                <p className="text-3xl font-bold text-green-600">
                  R$ {Number(selectedOperacao.amount || 0).toFixed(2)}
                </p>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Fatores de Risco */}
              <div className="bg-red-50 p-5 rounded-lg border border-red-200">
                <h3 className="text-lg font-bold text-red-800 mb-4 flex items-center gap-2">
                  ⚠️ Fatores de Risco Identificados
                </h3>
                
                <div className="space-y-2">
                  <p className="text-sm text-gray-700">
                    <strong>Motivo:</strong> {selectedOperacao.motivo_risco || 'N/A'}
                  </p>
                  {selectedOperacao.fatores_risco && (
                    <div className="mt-3 bg-white p-3 rounded border border-red-100">
                      <p className="text-xs text-gray-500 mb-1">Detalhes técnicos:</p>
                      <pre className="text-xs text-gray-700 overflow-x-auto">
                        {JSON.stringify(JSON.parse(selectedOperacao.fatores_risco), null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>

              {/* Informações do Pagamento */}
              <div className="bg-blue-50 p-5 rounded-lg border border-blue-200">
                <h3 className="text-lg font-bold text-blue-800 mb-3">💳 Informações do Pagamento</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">ID do Pagamento</p>
                    <p className="font-medium text-gray-900">#{selectedOperacao.pagamento_id || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Método</p>
                    <p className="font-medium text-gray-900">{selectedOperacao.metodo || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Cartão Final</p>
                    <p className="font-medium text-gray-900 font-mono">
                      {selectedOperacao.cartao_final ? `•••• ${selectedOperacao.cartao_final}` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Cielo Payment ID</p>
                    <p className="font-medium text-gray-900 text-xs break-all">
                      {selectedOperacao.cielo_payment_id || 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Timeline de Análise */}
              <div className="bg-purple-50 p-5 rounded-lg border border-purple-200">
                <h3 className="text-lg font-bold text-purple-800 mb-4">⏱️ Timeline de Análise</h3>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-3 h-3 bg-purple-500 rounded-full mt-1.5"></div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">Análise Criada</p>
                      <p className="text-sm text-gray-600">
                        {selectedOperacao.created_at ? 
                          new Date(selectedOperacao.created_at).toLocaleString('pt-BR') : 
                          'Data não disponível'}
                      </p>
                    </div>
                  </div>

                  {selectedOperacao.analiseEm && (
                    <div className="flex items-start gap-3">
                      <div className="w-3 h-3 bg-blue-500 rounded-full mt-1.5"></div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">Em Análise</p>
                        <p className="text-sm text-gray-600">
                          {new Date(selectedOperacao.analiseEm).toLocaleString('pt-BR')}
                        </p>
                      </div>
                    </div>
                  )}

                  {selectedOperacao.status !== 'PENDENTE' && (
                    <div className="flex items-start gap-3">
                      <div className={`w-3 h-3 rounded-full mt-1.5 ${
                        selectedOperacao.status.includes('APROVADO') ? 'bg-green-500' : 'bg-red-500'
                      }`}></div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">
                          {selectedOperacao.status.includes('APROVADO') ? 'Aprovada' : 'Recusada'}
                        </p>
                        <p className="text-sm text-gray-600">
                          {selectedOperacao.updated_at ? 
                            new Date(selectedOperacao.updated_at).toLocaleString('pt-BR') : 
                            'Data não disponível'}
                        </p>
                        {selectedOperacao.analisadoPor && (
                          <p className="text-xs text-gray-500 mt-1">
                            Por: {selectedOperacao.analisadoPor}
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Cliente e Reserva */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-bold text-gray-800 mb-2">👤 Cliente</h4>
                  <p className="text-sm text-gray-600">Nome</p>
                  <p className="font-medium text-gray-900">{selectedOperacao.cliente_nome}</p>
                  <p className="text-sm text-gray-600 mt-2">ID</p>
                  <p className="font-medium text-gray-900">#{selectedOperacao.cliente_id}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-bold text-gray-800 mb-2">🏨 Reserva</h4>
                  <p className="text-sm text-gray-600">Código</p>
                  <p className="font-medium text-gray-900">{selectedOperacao.reserva_codigo}</p>
                  <p className="text-sm text-gray-600 mt-2">ID</p>
                  <p className="font-medium text-gray-900">#{selectedOperacao.reserva_id}</p>
                </div>
              </div>

              {/* Ações (se pendente) */}
              {selectedOperacao.status === 'PENDENTE' && (
                <div className="bg-yellow-50 p-5 rounded-lg border-2 border-yellow-300">
                  <h3 className="text-lg font-bold text-yellow-800 mb-3">⚡ Ações Necessárias</h3>
                  <p className="text-sm text-gray-700 mb-4">
                    Esta operação requer análise manual. Revise os fatores de risco e tome uma decisão.
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={async () => {
                        await handleAprovar(selectedOperacao.id)
                        setShowOperacaoDetails(false)
                      }}
                      className="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 font-bold"
                    >
                      ✅ Aprovar Operação
                    </button>
                    <button
                      onClick={async () => {
                        await handleRecusar(selectedOperacao.id)
                        setShowOperacaoDetails(false)
                      }}
                      className="flex-1 bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 font-bold"
                    >
                      ❌ Recusar Operação
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-4 rounded-b-lg flex justify-end border-t">
              <button
                onClick={() => setShowOperacaoDetails(false)}
                className="px-6 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 font-medium"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Senha de Administrador */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-red-600">
                🔒 Acesso Restrito - Administrador
              </h3>
            </div>
            <form onSubmit={handlePasswordSubmit}>
              <div className="px-6 py-4">
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Senha de Administrador
                  </label>
                  <input
                    type="password"
                    value={adminPassword}
                    onChange={(e) => {
                      setAdminPassword(e.target.value)
                      setPasswordError('')
                    }}
                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    placeholder="Digite a senha de administrador"
                    autoFocus
                  />
                  {passwordError && (
                    <p className="mt-2 text-sm text-red-600">{passwordError}</p>
                  )}
                </div>
                <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                  <p className="text-sm text-yellow-800">
                    <strong>⚠️ Aviso:</strong> Esta aba contém dados sensíveis de transações reais da Cielo.
                    Apenas administradores autorizados devem acessar esta funcionalidade.
                  </p>
                </div>
              </div>
              <div className="px-6 py-4 border-t border-gray-200 flex space-x-3">
                <button
                  type="button"
                  onClick={handlePasswordModalClose}
                  className="flex-1 bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={passwordLoading}
                  className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  {passwordLoading ? 'Verificando...' : 'Acessar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}