'use client'
import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

// Helper para formatar erros de validação
const formatErrorMessage = (error) => {
  const detail = error.response?.data?.detail
  
  // Se detail é um array (erros de validação do Pydantic)
  if (Array.isArray(detail)) {
    return detail.map(err => {
      if (typeof err === 'string') return err
      if (err.msg) return String(err.msg)
      return JSON.stringify(err)
    }).join(', ')
  }
  
  // Se detail é uma string
  if (typeof detail === 'string') {
    return detail
  }
  
  // Se detail é um objeto, tentar extrair mensagem
  if (detail && typeof detail === 'object') {
    return JSON.stringify(detail)
  }
  
  // Fallback para outras mensagens
  return error.response?.data?.message || error.message || 'Erro desconhecido'
}

export default function Clientes() {
  const [clientes, setClientes] = useState([])
  const [funcionarios, setFuncionarios] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [showFuncionarioForm, setShowFuncionarioForm] = useState(false)
  const [activeTab, setActiveTab] = useState('admin-pontos')
  const [editingFuncionario, setEditingFuncionario] = useState(null)
  const [showClienteDetailsModal, setShowClienteDetailsModal] = useState(false)
  const [clienteDetalhes, setClienteDetalhes] = useState(null)
  const [showClienteEditModal, setShowClienteEditModal] = useState(false)
  const [editingCliente, setEditingCliente] = useState(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [clienteToDelete, setClienteToDelete] = useState(null)
  const [editForm, setEditForm] = useState({
    nome_completo: '',
    documento: '',
    telefone: '',
    email: '',
    data_nascimento: '',
    nacionalidade: '',
    endereco_completo: '',
    cidade: '',
    estado: '',
    pais: '',
    observacoes: ''
  })

  // Estados para Admin Pontos
  const [clientesPontos, setClientesPontos] = useState([])
  const [historicoAntifraude, setHistoricoAntifraude] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showAjusteModal, setShowAjusteModal] = useState(false)
  const [selectedCliente, setSelectedCliente] = useState(null)

  // Form de ajuste manual
  const [ajusteForm, setAjusteForm] = useState({
    cliente_id: '',
    pontos: '',
    motivo: ''
  })

  // Estados para filtros e busca
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    limit: 20,
    offset: 0
  })
  const [totalRecords, setTotalRecords] = useState(0)

  // Paginação
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0
  })
  const [form, setForm] = useState({
    nome_completo: '',
    documento: '',
    telefone: '',
    email: '',
    data_nascimento: '',
    nacionalidade: 'Brasil',
    endereco_completo: '',
    cidade: '',
    estado: '',
    pais: 'Brasil',
    observacoes: ''
  })
  const [formFuncionario, setFormFuncionario] = useState({
    nome: '',
    email: '',
    perfil: 'ADMIN',
    status: 'ATIVO',
    senha: ''
  })

  useEffect(() => {
    if (activeTab === 'clientes') {
      loadClientes()
    } else if (activeTab === 'funcionarios') {
      loadFuncionarios()
    } else if (activeTab === 'admin-pontos') {
      loadClientesPontos()
    } else if (activeTab === 'antifraude') {
      loadHistoricoAntifraude()
    }
  }, [activeTab, pagination.page, filters])

  const loadClientesPontos = async () => {
    try {
      setLoading(true)
      const res = await api.get('/clientes')
      // Buscar clientes e seus pontos
      const clientes = res.data.clientes || []
      setClientesPontos(clientes)
      setError('')
    } catch (error) {
      console.error('Erro ao carregar clientes:', error)
      setError('Erro ao conectar com o servidor')
      setClientesPontos([]) // Garantir array vazio
    } finally {
      setLoading(false)
    }
  }

  const loadHistoricoAntifraude = async () => {
    try {
      setLoading(true)
      const res = await api.get('/antifraude/transacoes-suspeitas?limit=50')
      
      if (res.data.success) {
        const transacoes = res.data.transacoes || []
        // Transformar para formato esperado
        const operacoes = transacoes.map(t => ({
          id: t.cliente_id,
          operacao_id: `OP-${t.cliente_id}`,
          reserva_codigo: '-',
          cliente_nome: `Cliente #${t.cliente_id}`,
          cpf_hospede: t.documento || '-',
          pontos_calculados: 0,
          status: t.risco === 'ALTO' ? 'RECUSADO' : 'SUCESSO',
          motivo_recusa: t.alertas?.join(', ') || '-',
          created_at: new Date().toISOString(),
          ...t
        }))
        setHistoricoAntifraude(operacoes)
        setPagination(prev => ({
          ...prev,
          total: operacoes.length
        }))
        setError('')
      } else {
        setError(res.data.message || 'Erro ao carregar histórico antifraude')
        setHistoricoAntifraude([])
      }
    } catch (error) {
      console.error('Erro ao carregar histórico antifraude:', error)
      setError('Erro ao conectar com o servidor')
      setHistoricoAntifraude([]) // Garantir array vazio
    } finally {
      setLoading(false)
    }
  }

  const handleAjusteManual = async (e) => {
    e.preventDefault()

    // Validar limite de ±4 pontos
    const pontos = parseInt(ajusteForm.pontos)
    if (Math.abs(pontos) > 4) {
      setError('Ajuste manual limitado a ±4 pontos')
      return
    }

    try {
      setLoading(true)
      const res = await api.post('/pontos/ajustar', {
        cliente_id: parseInt(ajusteForm.cliente_id),
        pontos: pontos,
        motivo: ajusteForm.motivo,
        usuario_id: 1 // ID do usuário admin (simulado)
      })

      if (res.data.success) {
        alert('Ajuste realizado com sucesso!')
        setShowAjusteModal(false)
        setAjusteForm({ cliente_id: '', pontos: '', motivo: '' })
        loadClientesPontos() // Recarregar para atualizar saldos
      } else {
        setError(res.data.error || 'Erro ao realizar ajuste')
      }
    } catch (error) {
      console.error('Erro ao realizar ajuste:', error)
      setError('Erro ao conectar com o servidor')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'SUCESSO': return 'bg-green-100 text-green-800'
      case 'RECUSADO': return 'bg-red-100 text-red-800'
      case 'DUPLICADO': return 'bg-yellow-100 text-yellow-800'
      case 'ERRO_API': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getSaldoColor = (saldo) => {
    if (saldo >= 100) return 'text-purple-600 font-bold'
    if (saldo >= 20) return 'text-green-600 font-bold'
    if (saldo >= 5) return 'text-blue-600'
    return 'text-gray-600'
  }

  const getTotalStats = () => {
    const totalClientes = clientesPontos.length || 0
    const totalPontos = clientesPontos.reduce((acc, c) => acc + (c.saldo_pontos || 0), 0)
    const clientesComPontos = clientesPontos.filter(c => (c.saldo_pontos || 0) > 0).length
    const clientesAltos = clientesPontos.filter(c => (c.saldo_pontos || 0) >= 50).length

    return { totalClientes, totalPontos, clientesComPontos, clientesAltos }
  }

  const stats = getTotalStats()

  const loadClientes = async () => {
    console.log('🔄 [DEBUG] Carregando clientes com filtros:', filters)
    
    try {
      setLoading(true)
      
      // Construir query params com filtros
      const params = new URLSearchParams()
      if (filters.search) params.append('search', filters.search)
      if (filters.status) params.append('status', filters.status)
      params.append('limit', filters.limit)
      params.append('offset', filters.offset)
      params.append('_t', new Date().getTime())
      
      const url = `/clientes?${params.toString()}`
      
      console.log('📡 [DEBUG] URL:', url)
      
      const res = await api.get(url)
      
      console.log('📦 [DEBUG] Resposta completa:', res)
      
      const clientes = res.data.clientes || []
      const total = res.data.total || 0
      
      setClientes(clientes)
      setTotalRecords(total)
      
      console.log('✅ [DEBUG] Estado atualizado com', clientes.length, 'clientes de', total, 'total')
      
      if (clientes.length > 0) {
        toast.success(`✅ ${clientes.length} clientes carregados (${total} total)`)
      } else {
        toast.warning('⚠️ Nenhum cliente encontrado')
      }
      
      setError('')
    } catch (error) {
      console.error('❌ [DEBUG] Erro completo:', error)
      
      const errorMsg = formatErrorMessage(error)
      
      setClientes([])
      setError(errorMsg)
      toast.error(`Erro: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
      offset: 0 // Reset offset quando mudar filtro
    }))
  }

  const handleSearch = () => {
    loadClientes()
  }

  const handleClearFilters = () => {
    setFilters({
      search: '',
      status: '',
      limit: 20,
      offset: 0
    })
  }

  const handleExportCSV = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.search) params.append('search', filters.search)
      if (filters.status) params.append('status', filters.status)
      
      const url = `/clientes/export/csv?${params.toString()}`
      window.open(url, '_blank')
      toast.success('📥 Exportando CSV...')
    } catch (error) {
      console.error('Erro ao exportar CSV:', error)
      const errorMsg = formatErrorMessage(error)
      toast.error(`Erro: ${errorMsg}`)
    }
  }

  const handleExportPDF = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.search) params.append('search', filters.search)
      if (filters.status) params.append('status', filters.status)
      
      const url = `/clientes/export/pdf?${params.toString()}`
      window.open(url, '_blank')
      toast.success('📥 Exportando PDF...')
    } catch (error) {
      console.error('Erro ao exportar PDF:', error)
      const errorMsg = formatErrorMessage(error)
      toast.error(`Erro: ${errorMsg}`)
    }
  }

  const handlePreviousPage = () => {
    if (filters.offset > 0) {
      setFilters(prev => ({
        ...prev,
        offset: Math.max(0, prev.offset - prev.limit)
      }))
    }
  }

  const handleNextPage = () => {
    if (filters.offset + filters.limit < totalRecords) {
      setFilters(prev => ({
        ...prev,
        offset: prev.offset + prev.limit
      }))
    }
  }

  const loadFuncionarios = async () => {
    console.log('🔄 [DEBUG] Carregando funcionários...')
    
    try {
      setLoading(true)
      const res = await api.get('/funcionarios')
      
      console.log('📦 [DEBUG] Resposta funcionários:', res.data)
      
      const funcionarios = res.data.funcionarios || res.data || []
      setFuncionarios(funcionarios)
      
      console.log('✅ [DEBUG] Estado atualizado com', funcionarios.length, 'funcionários')
      
      if (funcionarios.length > 0) {
        toast.success(`✅ ${funcionarios.length} funcionários carregados`)
      } else {
        toast.warning('⚠️ Nenhum funcionário encontrado')
      }
      
      setError('')
    } catch (error) {
      console.error('❌ [DEBUG] Erro ao carregar funcionários:', error)
      console.error('❌ [DEBUG] error.response:', error.response)
      const errorMsg = formatErrorMessage(error)
      setError(errorMsg)
      toast.error(`Erro: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validação: campos obrigatórios
    if (!form.nome_completo || !form.documento) {
      toast.warning('⚠️ Nome e documento são obrigatórios')
      return
    }
    
    setLoading(true)
    
    console.log('📤 [DEBUG] Criando cliente:', form)
    
    try {
      const res = await api.post('/clientes', form)
      
      console.log('✅ [DEBUG] Cliente criado:', res.data)
      
      if (res.data) {
        toast.success('Cliente criado com sucesso! ✅')
        await loadClientes()
        setShowForm(false)
        setForm({ 
          nome_completo: '', 
          documento: '', 
          telefone: '', 
          email: '',
          data_nascimento: '',
          nacionalidade: 'Brasil',
          endereco_completo: '',
          cidade: '',
          estado: '',
          pais: 'Brasil',
          observacoes: ''
        })
        setError('')
      }
    } catch (error) {
      console.error('❌ [DEBUG] Erro ao criar cliente:', error)
      console.error('❌ [DEBUG] error.response:', error.response)
      const errorMsg = formatErrorMessage(error)
      toast.error(`Erro: ${errorMsg}`)
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteCliente = (cliente) => {
    setClienteToDelete(cliente)
    setShowDeleteModal(true)
  }

  const confirmDeleteCliente = async () => {
    if (!clienteToDelete) return

    setLoading(true)

    try {
      const res = await api.delete(`/clientes/${clienteToDelete.id}`)
      
      toast.success('Cliente excluído com sucesso! ✅')
      await loadClientes()
      await loadClientesPontos()
      setShowDeleteModal(false)
      setClienteToDelete(null)
    } catch (error) {
      console.error('❌ Erro ao deletar cliente:', error)
      const errorMsg = formatErrorMessage(error)
      toast.error(`Erro: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteFuncionario = async (funcionario) => {
    if (!confirm(`Tem certeza que deseja inativar o funcionário ${funcionario.nome}?`)) {
      return
    }

    setLoading(true)

    try {
      await api.delete(`/funcionarios/${funcionario.id}`)
      
      toast.success('Funcionário inativado com sucesso! ✅')
      await loadFuncionarios()
    } catch (error) {
      console.error('❌ Erro ao deletar funcionário:', error)
      const errorMsg = formatErrorMessage(error)
      toast.error(`Erro: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleViewClienteDetails = async (cliente) => {
    setLoading(true)
    try {
      // Carregar detalhes completos do cliente
      const res = await api.get(`/clientes/${cliente.id}`)
      
      // Carregar reservas do cliente
      const reservasRes = await api.get(`/reservas/cliente/${cliente.id}`)
      
      setClienteDetalhes({
        ...res.data,
        reservas: reservasRes.data || []
      })
      setShowClienteDetailsModal(true)
    } catch (error) {
      console.error('❌ Erro ao carregar detalhes:', error)
      const errorMsg = formatErrorMessage(error)
      toast.error(`Erro: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleEditCliente = (cliente) => {
    setEditingCliente(cliente)
    setEditForm({
      nome_completo: cliente.nome_completo || '',
      documento: cliente.documento || '',
      telefone: cliente.telefone || '',
      email: cliente.email || '',
      data_nascimento: cliente.data_nascimento || '',
      nacionalidade: cliente.nacionalidade || '',
      endereco_completo: cliente.endereco_completo || '',
      cidade: cliente.cidade || '',
      estado: cliente.estado || '',
      pais: cliente.pais || '',
      observacoes: cliente.observacoes || ''
    })
    setShowClienteEditModal(true)
  }

  const handleUpdateCliente = async (e) => {
    e.preventDefault()
    
    if (!editForm.nome_completo || !editForm.documento) {
      toast.warning('⚠️ Nome e documento são obrigatórios')
      return
    }

    setLoading(true)

    try {
      const res = await api.put(`/clientes/${editingCliente.id}`, editForm)
      
      if (res.data) {
        toast.success('Cliente atualizado com sucesso! ✅')
        await loadClientes()
        await loadClientesPontos()
        setShowClienteEditModal(false)
        setEditingCliente(null)
        setEditForm({ nome_completo: '', documento: '', telefone: '', email: '' })
      }
    } catch (error) {
      console.error('❌ Erro ao atualizar cliente:', error)
      const errorMsg = formatErrorMessage(error)
      toast.error(`Erro: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitFuncionario = async (e) => {
    e.preventDefault()
    
    // Validação: senha obrigatória na criação
    if (!editingFuncionario && !formFuncionario.senha) {
      toast.warning('⚠️ Senha é obrigatória para criar funcionário')
      return
    }
    
    // Validação: campos obrigatórios
    if (!formFuncionario.nome || !formFuncionario.email) {
      toast.warning('⚠️ Nome e email são obrigatórios')
      return
    }
    
    setLoading(true)
    
    const payload = {
      nome: formFuncionario.nome,
      email: formFuncionario.email,
      perfil: formFuncionario.perfil,
      status: formFuncionario.status,
    }
    
    // Só envia senha se foi preenchida
    if (formFuncionario.senha) {
      payload.senha = formFuncionario.senha
    }
    
    console.log('📤 [DEBUG] Enviando funcionário:', payload)
    console.log('📤 [DEBUG] Editando?', editingFuncionario ? `ID ${editingFuncionario.id}` : 'Novo')

    try {
      let res
      if (editingFuncionario) {
        res = await api.put(`/funcionarios/${editingFuncionario.id}`, payload)
        console.log('✅ [DEBUG] Funcionário atualizado:', res.data)
        toast.success('Funcionário atualizado com sucesso! ✅')
      } else {
        res = await api.post('/funcionarios', payload)
        console.log('✅ [DEBUG] Funcionário criado:', res.data)
        toast.success('Funcionário criado com sucesso! ✅')
      }

      await loadFuncionarios()
      setShowFuncionarioForm(false)
      setEditingFuncionario(null)
      setFormFuncionario({ nome: '', email: '', perfil: 'ADMIN', status: 'ATIVO', senha: '' })
      setError('')
    } catch (error) {
      console.error('❌ [DEBUG] Erro ao salvar funcionário:', error)
      console.error('❌ [DEBUG] error.response:', error.response)
      const errorMsg = formatErrorMessage(error)
      toast.error(`Erro: ${errorMsg}`)
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const startCreateFuncionario = () => {
    setEditingFuncionario(null)
    setFormFuncionario({ nome: '', email: '', perfil: 'ADMIN', status: 'ATIVO', senha: '' })
    setShowFuncionarioForm(true)
  }

  const startEditFuncionario = (func) => {
    setEditingFuncionario(func)
    setFormFuncionario({
      nome: func.nome,
      email: func.email,
      perfil: func.perfil,
      status: func.status || 'ATIVO',
      senha: ''
    })
    setShowFuncionarioForm(true)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white flex items-center gap-3">
            <span className="text-4xl">👥</span>
            Usuários
          </h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            Gerencie funcionários e clientes do Hotel Real Cabo Frio
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-ghost">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Exportar
          </button>
        </div>
      </div>

      {/* Premium Tabs */}
      <div className="glass-card p-1">
        <nav className="flex flex-col sm:flex-row gap-1" role="tablist">
          {[
            { id: 'funcionarios', label: 'Funcionários', icon: '👔', count: funcionarios.length },
            { id: 'clientes', label: 'Clientes', icon: '🧳', count: clientes.length },
            { id: 'admin-pontos', label: 'Admin Pontos', icon: '🎯', count: clientesPontos.length },
            { id: 'antifraude', label: 'Antifraude', icon: '🛡️', count: historicoAntifraude.length },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center justify-center sm:justify-start px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-primary-600 text-white shadow-medium'
                  : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-neutral-100 dark:hover:bg-neutral-800'
              }`}
            >
              <span className="text-lg mr-2">{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.count > 0 && (
                <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                  activeTab === tab.id
                    ? 'bg-white/20 text-white'
                    : 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Alert */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <span className="block sm:inline">{error}</span>
          <button
            onClick={() => setError('')}
            className="float-right text-red-500 hover:text-red-700"
          >
            ×
          </button>
        </div>
      )}

      {activeTab === 'admin-pontos' && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-gradient-to-r from-red-600 to-red-800 text-white p-6 rounded-lg">
            <h2 className="text-2xl font-bold mb-2">🔧 Admin Real Points</h2>
            <p className="text-red-100">Painel administrativo do sistema de fidelidade</p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm mb-1">Total de Clientes</h3>
              <p className="text-3xl font-bold text-blue-600">{stats.totalClientes}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm mb-1">Pontos Distribuídos</h3>
              <p className="text-3xl font-bold text-green-600">{stats.totalPontos.toLocaleString('pt-BR')}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm mb-1">Clientes com Pontos</h3>
              <p className="text-3xl font-bold text-yellow-600">{stats.clientesComPontos}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-600 text-sm mb-1">Clientes Premium</h3>
              <p className="text-3xl font-bold text-purple-600">{stats.clientesAltos}</p>
            </div>
          </div>

          {/* Actions Bar */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Lista de Clientes</h3>
              <button
                onClick={() => setShowAjusteModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                ⚙️ Ajuste Manual
              </button>
            </div>
          </div>

          {/* Clients Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Documento
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Saldo RP
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {clientesPontos.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                        {loading ? 'Carregando...' : 'Nenhum cliente encontrado'}
                      </td>
                    </tr>
                  ) : (
                    clientesPontos.map((cliente) => (
                      <tr key={cliente.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {cliente.nomeCompleto || cliente.nome || `Cliente #${cliente.id}`}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {cliente.documento || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {cliente.email || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-lg ${getSaldoColor(cliente.saldo_pontos || 0)}`}>
                            {(cliente.saldo_pontos || 0).toLocaleString('pt-BR')} RP
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            ATIVO
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => {
                              setSelectedCliente(cliente)
                              setAjusteForm({
                                cliente_id: cliente.id,
                                pontos: '',
                                motivo: ''
                              })
                              setShowAjusteModal(true)
                            }}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            Ajustar
                          </button>
                          <button
                            onClick={() => {
                              alert('Funcionalidade em desenvolvimento')
                            }}
                            className="text-gray-600 hover:text-gray-900"
                          >
                            Histórico
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'antifraude' && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-gradient-to-r from-red-600 to-red-800 text-white p-6 rounded-lg">
            <h2 className="text-2xl font-bold mb-2">🛡️ Histórico Antifraude</h2>
            <p className="text-red-100">Operações de validação de pontos</p>
          </div>

          {/* Operations Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold">Operações Antifraude</h3>
              <p className="text-sm text-gray-500 mt-1">
                Total: {pagination.total} operações
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ID Operação
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Reserva
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      CPF
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Pontos
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Motivo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Data
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {historicoAntifraude.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="px-6 py-8 text-center text-gray-500">
                        {loading ? 'Carregando...' : 'Nenhuma operação encontrada'}
                      </td>
                    </tr>
                  ) : (
                    historicoAntifraude.map((operacao) => (
                      <tr key={operacao.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {operacao.operacao_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {operacao.reserva_codigo || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {operacao.cliente_nome || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {operacao.cpf_hospede}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className="font-medium text-blue-600">
                            {operacao.pontos_calculados} RP
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(operacao.status)}`}>
                            {operacao.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {operacao.motivo_recusa || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(operacao.created_at).toLocaleDateString('pt-BR')}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination.total > pagination.pageSize && (
              <div className="px-6 py-4 border-t flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Mostrando {((pagination.page - 1) * pagination.pageSize) + 1} a{' '}
                  {Math.min(pagination.page * pagination.pageSize, pagination.total)} de{' '}
                  {pagination.total} resultados
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
                    disabled={pagination.page === 1}
                    className="px-3 py-1 border rounded text-sm disabled:opacity-50"
                  >
                    Anterior
                  </button>
                  <span className="px-3 py-1 text-sm">
                    Página {pagination.page}
                  </span>
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                    disabled={pagination.page * pagination.pageSize >= pagination.total}
                    className="px-3 py-1 border rounded text-sm disabled:opacity-50"
                  >
                    Próxima
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'clientes' && (
        <>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-real-blue">Clientes</h2>
            <div className="flex gap-2">
              <button
                onClick={handleExportCSV}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 flex items-center gap-2"
                title="Exportar para CSV"
              >
                📊 CSV
              </button>
              <button
                onClick={handleExportPDF}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 flex items-center gap-2"
                title="Exportar para PDF"
              >
                📄 PDF
              </button>
              <button
                onClick={() => setShowForm(!showForm)}
                className="bg-real-blue text-white px-4 py-2 rounded hover:bg-blue-800"
              >
                Novo Cliente
              </button>
            </div>
          </div>

          {/* Filtros e Busca */}
          <div className="bg-white p-4 rounded-lg shadow mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  🔍 Buscar
                </label>
                <input
                  type="text"
                  placeholder="Nome, documento ou email..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  <option value="ATIVO">Ativo</option>
                  <option value="INATIVO">Inativo</option>
                </select>
              </div>

              <div className="flex items-end gap-2">
                <button
                  onClick={handleSearch}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                  Buscar
                </button>
                <button
                  onClick={handleClearFilters}
                  className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300"
                  title="Limpar filtros"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Paginação Info */}
            <div className="mt-4 text-sm text-gray-600 flex justify-between items-center">
              <span>
                Mostrando {filters.offset + 1} até {Math.min(filters.offset + filters.limit, totalRecords)} de {totalRecords} registros
              </span>
              <div className="flex gap-2">
                <button
                  onClick={handlePreviousPage}
                  disabled={filters.offset === 0}
                  className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ← Anterior
                </button>
                <button
                  onClick={handleNextPage}
                  disabled={filters.offset + filters.limit >= totalRecords}
                  className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Próximo →
                </button>
              </div>
            </div>
          </div>

          {showForm && (
            <div className="bg-white p-6 rounded-lg shadow mb-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">📝 Novo Cliente</h3>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Seção: Dados Pessoais */}
                <div>
                  <h4 className="font-medium text-gray-700 mb-3 pb-2 border-b">👤 Dados Pessoais</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Nome Completo *
                      </label>
                      <input
                        placeholder="João Silva"
                        value={form.nome_completo}
                        onChange={(e) => setForm({ ...form, nome_completo: e.target.value })}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Documento (CPF/RG) *
                      </label>
                      <input
                        placeholder="000.000.000-00"
                        value={form.documento}
                        onChange={(e) => setForm({ ...form, documento: e.target.value })}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Data de Nascimento
                      </label>
                      <input
                        type="date"
                        value={form.data_nascimento}
                        onChange={(e) => setForm({ ...form, data_nascimento: e.target.value })}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Nacionalidade
                      </label>
                      <select
                        value={form.nacionalidade}
                        onChange={(e) => setForm({ ...form, nacionalidade: e.target.value })}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="Brasil">Brasil</option>
                        <option value="Portugal">Portugal</option>
                        <option value="Argentina">Argentina</option>
                        <option value="Estados Unidos">Estados Unidos</option>
                        <option value="Outro">Outro</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Seção: Contato */}
                <div>
                  <h4 className="font-medium text-gray-700 mb-3 pb-2 border-b">📞 Contato</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Telefone
                      </label>
                      <input
                        placeholder="(22) 99999-9999"
                        value={form.telefone}
                        onChange={(e) => setForm({ ...form, telefone: e.target.value })}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email
                      </label>
                      <input
                        type="email"
                        placeholder="joao@email.com"
                        value={form.email}
                        onChange={(e) => setForm({ ...form, email: e.target.value })}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>

                {/* Seção: Endereço */}
                <div>
                  <h4 className="font-medium text-gray-700 mb-3 pb-2 border-b">🏠 Endereço</h4>
                  <div className="grid grid-cols-1 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Endereço Completo
                      </label>
                      <input
                        placeholder="Rua Exemplo, 123 - Centro"
                        value={form.endereco_completo}
                        onChange={(e) => setForm({ ...form, endereco_completo: e.target.value })}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Cidade
                        </label>
                        <input
                          placeholder="Cabo Frio"
                          value={form.cidade}
                          onChange={(e) => setForm({ ...form, cidade: e.target.value })}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Estado
                        </label>
                        <select
                          value={form.estado}
                          onChange={(e) => setForm({ ...form, estado: e.target.value })}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value="">Selecione...</option>
                          <option value="AC">AC</option>
                          <option value="AL">AL</option>
                          <option value="AP">AP</option>
                          <option value="AM">AM</option>
                          <option value="BA">BA</option>
                          <option value="CE">CE</option>
                          <option value="DF">DF</option>
                          <option value="ES">ES</option>
                          <option value="GO">GO</option>
                          <option value="MA">MA</option>
                          <option value="MT">MT</option>
                          <option value="MS">MS</option>
                          <option value="MG">MG</option>
                          <option value="PA">PA</option>
                          <option value="PB">PB</option>
                          <option value="PR">PR</option>
                          <option value="PE">PE</option>
                          <option value="PI">PI</option>
                          <option value="RJ">RJ</option>
                          <option value="RN">RN</option>
                          <option value="RS">RS</option>
                          <option value="RO">RO</option>
                          <option value="RR">RR</option>
                          <option value="SC">SC</option>
                          <option value="SP">SP</option>
                          <option value="SE">SE</option>
                          <option value="TO">TO</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          País
                        </label>
                        <select
                          value={form.pais}
                          onChange={(e) => setForm({ ...form, pais: e.target.value })}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value="Brasil">Brasil</option>
                          <option value="Portugal">Portugal</option>
                          <option value="Argentina">Argentina</option>
                          <option value="Estados Unidos">Estados Unidos</option>
                          <option value="Outro">Outro</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Seção: Observações */}
                <div>
                  <h4 className="font-medium text-gray-700 mb-3 pb-2 border-b">📋 Observações</h4>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Observações Adicionais
                    </label>
                    <textarea
                      placeholder="Informações adicionais sobre o cliente..."
                      value={form.observacoes}
                      onChange={(e) => setForm({ ...form, observacoes: e.target.value })}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      rows="3"
                    />
                  </div>
                </div>

                {/* Botões */}
                <div className="flex gap-3 pt-4 border-t">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
                  >
                    {loading ? '⏳ Cadastrando...' : '✅ Cadastrar Cliente'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="bg-white rounded-lg shadow">
            <table className="w-full">
              <thead className="bg-real-blue text-white">
                <tr>
                  <th className="p-3 text-left">Nome</th>
                  <th className="p-3 text-left">Documento</th>
                  <th className="p-3 text-left">Telefone</th>
                  <th className="p-3 text-left">Email</th>
                  <th className="p-3 text-left">Ações</th>
                </tr>
              </thead>
              <tbody>
                {clientes.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="p-6 text-center text-gray-500">
                      {loading ? 'Carregando...' : 'Nenhum cliente encontrado'}
                    </td>
                  </tr>
                ) : (
                  clientes.map((cliente) => (
                    <tr key={cliente.id} className="border-b hover:bg-gray-50">
                      <td className="p-3">{cliente.nome_completo}</td>
                      <td className="p-3">{cliente.documento}</td>
                      <td className="p-3">{cliente.telefone}</td>
                      <td className="p-3">{cliente.email}</td>
                      <td className="p-3">
                        <button
                          onClick={() => handleViewClienteDetails(cliente)}
                          disabled={loading}
                          className="text-blue-600 hover:text-blue-800 font-medium disabled:opacity-50 mr-3"
                          title="Ver detalhes completos"
                        >
                          👁️ Detalhes
                        </button>
                        <button
                          onClick={() => handleEditCliente(cliente)}
                          disabled={loading}
                          className="text-green-600 hover:text-green-800 font-medium disabled:opacity-50 mr-3"
                          title="Editar cliente"
                        >
                          ✏️ Editar
                        </button>
                        <button
                          onClick={() => handleDeleteCliente(cliente)}
                          disabled={loading}
                          className="text-red-600 hover:text-red-800 font-medium disabled:opacity-50"
                          title="Excluir cliente"
                        >
                          🗑️ Excluir
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {activeTab === 'funcionarios' && (
        <>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-real-blue">Funcionários</h2>
            <button
              onClick={startCreateFuncionario}
              className="bg-real-blue text-white px-4 py-2 rounded hover:bg-blue-800"
            >
              Novo Funcionário
            </button>
          </div>

          {showFuncionarioForm && (
            <div className="bg-white p-6 rounded-lg shadow mb-6">
              <form onSubmit={handleSubmitFuncionario} className="grid grid-cols-2 gap-4">
                <input
                  placeholder="Nome"
                  value={formFuncionario.nome}
                  onChange={(e) => setFormFuncionario({ ...formFuncionario, nome: e.target.value })}
                  className="p-2 border rounded"
                  required
                />
                <input
                  type="email"
                  placeholder="Email"
                  value={formFuncionario.email}
                  onChange={(e) => setFormFuncionario({ ...formFuncionario, email: e.target.value })}
                  className="p-2 border rounded"
                  required
                />
                <select
                  value={formFuncionario.perfil}
                  onChange={(e) => setFormFuncionario({ ...formFuncionario, perfil: e.target.value })}
                  className="p-2 border rounded"
                >
                  <option value="ADMIN">Admin</option>
                  <option value="RECEPCIONISTA">Recepcionista</option>
                  <option value="GERENTE">Gerente</option>
                </select>
                <select
                  value={formFuncionario.status}
                  onChange={(e) => setFormFuncionario({ ...formFuncionario, status: e.target.value })}
                  className="p-2 border rounded"
                >
                  <option value="ATIVO">Ativo</option>
                  <option value="INATIVO">Inativo</option>
                </select>
                <input
                  type="password"
                  placeholder="Senha (deixe em branco para não alterar)"
                  value={formFuncionario.senha}
                  onChange={(e) => setFormFuncionario({ ...formFuncionario, senha: e.target.value })}
                  className="p-2 border rounded col-span-2"
                />
                <button
                  type="submit"
                  className="col-span-2 bg-real-gold text-real-blue p-2 rounded hover:bg-yellow-500"
                >
                  {editingFuncionario ? 'Salvar alterações' : 'Criar Funcionário'}
                </button>
              </form>
            </div>
          )}

          <div className="bg-white rounded-lg shadow">
            <table className="w-full">
              <thead className="bg-real-blue text-white">
                <tr>
                  <th className="p-3 text-left">Nome</th>
                  <th className="p-3 text-left">Email</th>
                  <th className="p-3 text-left">Perfil</th>
                  <th className="p-3 text-left">Status</th>
                  <th className="p-3 text-left">Ações</th>
                </tr>
              </thead>
              <tbody>
                {funcionarios.map((func) => (
                  <tr key={func.id} className="border-b hover:bg-gray-50">
                    <td className="p-3">{func.nome}</td>
                    <td className="p-3">{func.email}</td>
                    <td className="p-3">{func.perfil}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${func.status === 'ATIVO' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {func.status}
                      </span>
                    </td>
                    <td className="p-3 space-x-2">
                      <button
                        onClick={() => startEditFuncionario(func)}
                        className="text-sm px-3 py-1 rounded bg-real-blue text-white hover:bg-blue-800"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleDeleteFuncionario(func)}
                        disabled={loading || func.status === 'INATIVO'}
                        className="text-sm px-3 py-1 rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        title={func.status === 'INATIVO' ? 'Funcionário já está inativo' : 'Inativar funcionário'}
                      >
                        Inativar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      
      {/* Modal de Edição do Cliente */}
      {showClienteEditModal && editingCliente && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
            {/* Header */}
            <div className="bg-gradient-to-r from-green-600 to-green-800 text-white p-6 rounded-t-lg">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold mb-2">✏️ Editar Cliente</h2>
                  <p className="text-green-100">ID: #{editingCliente.id}</p>
                </div>
                <button
                  onClick={() => {
                    setShowClienteEditModal(false)
                    setEditingCliente(null)
                  }}
                  className="text-white hover:text-gray-200 text-2xl"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleUpdateCliente} className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome Completo *
                  </label>
                  <input
                    type="text"
                    value={editForm.nome_completo}
                    onChange={(e) => setEditForm({ ...editForm, nome_completo: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Documento (CPF/CNPJ) *
                  </label>
                  <input
                    type="text"
                    value={editForm.documento}
                    onChange={(e) => setEditForm({ ...editForm, documento: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Telefone
                  </label>
                  <input
                    type="text"
                    value={editForm.telefone}
                    onChange={(e) => setEditForm({ ...editForm, telefone: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="(00) 00000-0000"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="cliente@email.com"
                  />
                </div>
              </div>

              {/* Footer */}
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowClienteEditModal(false)
                    setEditingCliente(null)
                  }}
                  className="px-6 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 font-medium"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 font-medium disabled:opacity-50"
                >
                  {loading ? 'Salvando...' : 'Salvar Alterações'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* Modal de Detalhes do Cliente */}
      {showClienteDetailsModal && clienteDetalhes && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-t-lg">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold mb-2">👤 Detalhes do Cliente</h2>
                  <p className="text-blue-100">Informações completas e histórico</p>
                </div>
                <button
                  onClick={() => setShowClienteDetailsModal(false)}
                  className="text-white hover:text-gray-200 text-2xl"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Conteúdo */}
            <div className="p-6 space-y-6">
              {/* Informações Básicas */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-bold text-gray-800 mb-3">📋 Informações Básicas</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Nome Completo</p>
                    <p className="font-medium text-gray-900">{clienteDetalhes.nome_completo}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Documento</p>
                    <p className="font-medium text-gray-900">{clienteDetalhes.documento}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <p className="font-medium text-gray-900">{clienteDetalhes.email || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Telefone</p>
                    <p className="font-medium text-gray-900">{clienteDetalhes.telefone || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Status</p>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${clienteDetalhes.status === 'ATIVO' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {clienteDetalhes.status}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Cliente desde</p>
                    <p className="font-medium text-gray-900">
                      {clienteDetalhes.created_at ? new Date(clienteDetalhes.created_at).toLocaleDateString('pt-BR') : '-'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Histórico de Reservas */}
              <div>
                <h3 className="text-lg font-bold text-gray-800 mb-3">📅 Histórico de Reservas</h3>
                {clienteDetalhes.reservas && clienteDetalhes.reservas.length > 0 ? (
                  <div className="space-y-2">
                    {clienteDetalhes.reservas.map((reserva) => (
                      <div key={reserva.id} className="bg-gray-50 p-3 rounded-lg border border-gray-200">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-semibold text-gray-900">Reserva #{reserva.codigo_reserva || reserva.id}</p>
                            <p className="text-sm text-gray-600">
                              Quarto {reserva.quarto_numero} - {reserva.tipo_suite}
                            </p>
                            <p className="text-sm text-gray-600">
                              {new Date(reserva.checkin_previsto).toLocaleDateString('pt-BR')} até {new Date(reserva.checkout_previsto).toLocaleDateString('pt-BR')}
                            </p>
                          </div>
                          <div className="text-right">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${
                              reserva.status === 'HOSPEDADO' ? 'bg-blue-100 text-blue-800' :
                              reserva.status === 'CHECKED_OUT' ? 'bg-green-100 text-green-800' :
                              reserva.status === 'CANCELADO' ? 'bg-red-100 text-red-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {reserva.status}
                            </span>
                            <p className="text-sm font-medium text-gray-900 mt-2">
                              R$ {Number(reserva.valor_total || 0).toFixed(2)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-4">Nenhuma reserva encontrada</p>
                )}
              </div>

              {/* Estatísticas */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg">
                <h3 className="text-lg font-bold text-gray-800 mb-3">📊 Estatísticas</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {clienteDetalhes.reservas ? clienteDetalhes.reservas.length : 0}
                    </p>
                    <p className="text-sm text-gray-600">Total de Reservas</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">
                      {clienteDetalhes.reservas ? clienteDetalhes.reservas.filter(r => r.status === 'CHECKED_OUT').length : 0}
                    </p>
                    <p className="text-sm text-gray-600">Concluídas</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-600">
                      {clienteDetalhes.saldo_pontos || 0} RP
                    </p>
                    <p className="text-sm text-gray-600">Saldo de Pontos</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-4 rounded-b-lg flex justify-end">
              <button
                onClick={() => setShowClienteDetailsModal(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Modal de Confirmação de Exclusão */}
      {showDeleteModal && clienteToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="p-6">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
                Confirmar Exclusão
              </h3>
              
              <p className="text-gray-600 text-center mb-6">
                Tem certeza que deseja excluir o cliente <strong>{clienteToDelete.nome_completo}</strong>?
                <br />
                <span className="text-sm text-red-600 mt-2 block">Esta ação não pode ser desfeita.</span>
              </p>
              
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowDeleteModal(false)
                    setClienteToDelete(null)
                  }}
                  disabled={loading}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={confirmDeleteCliente}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  {loading ? 'Excluindo...' : 'Excluir'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Toast Container para notificações */}
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="colored"
      />
    </div>
  )
}