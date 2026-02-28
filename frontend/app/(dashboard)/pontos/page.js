'use client'
import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'
import { formatErrorMessage } from '../../../lib/errorHandler'
import ProtectedRoute from '../../../components/ProtectedRoute'
import { useAuth } from '../../../contexts/AuthContext'

function PontosContent() {
  const { hasRole } = useAuth()
  const canManageRegras = hasRole(['ADMIN', 'GERENTE'])
  const canManagePremios = hasRole(['ADMIN', 'GERENTE'])
  const canManageCupons = hasRole(['ADMIN', 'GERENTE'])

  const [activeTab, setActiveTab] = useState('dashboard')
  const [saldo, setSaldo] = useState(0)
  const [historico, setHistorico] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [clientes, setClientes] = useState([])
  const [clienteNome, setClienteNome] = useState('')
  const [totalGanhos, setTotalGanhos] = useState(0)
  const [diariasPendentes, setDiariasPendentes] = useState(0)
  const [reservasCliente, setReservasCliente] = useState([])
  const [estatisticas, setEstatisticas] = useState(null)

  const [regras, setRegras] = useState([])
  const [regrasLoading, setRegrasLoading] = useState(false)
  const [regrasError, setRegrasError] = useState('')
  const [editRegraId, setEditRegraId] = useState(null)
  const [regraForm, setRegraForm] = useState({
    suite_tipo: '',
    temporada: '',
    diarias_base: 2,
    rp_por_base: 0,
    data_inicio: '',
    data_fim: '',
    ativo: true
  })

  const [premios, setPremios] = useState([])
  const [premiosLoading, setPremiosLoading] = useState(false)
  const [premiosError, setPremiosError] = useState('')
  const [editPremioId, setEditPremioId] = useState(null)
  const [premioForm, setPremioForm] = useState({
    nome: '',
    descricao: '',
    preco_em_pontos: 0,
    preco_em_rp: '',
    categoria: 'GERAL',
    estoque: '',
    imagem_url: '',
    ativo: true
  })
  const [precoEdits, setPrecoEdits] = useState({})
  const [cupons, setCupons] = useState([])
  const [cuponsLoading, setCuponsLoading] = useState(false)
  const [cuponsError, setCuponsError] = useState('')
  const [editCupomId, setEditCupomId] = useState(null)
  const [cupomForm, setCupomForm] = useState({
    codigo: '',
    descricao: '',
    tipo_desconto: 'PERCENTUAL',
    valor_desconto: '',
    pontos_bonus: '',
    min_diarias: '',
    suites_permitidas: '',
    data_inicio: '',
    data_fim: '',
    limite_total_usos: '',
    limite_por_cliente: '',
    ativo: true
  })
  
  // Cliente selecionado
  const [clienteId, setClienteId] = useState(null)

  // Estados para validação de resgates
  const [codigoResgate, setCodigoResgate] = useState('')
  const [validacaoResult, setValidacaoResult] = useState(null)
  const [validandoCodigo, setValidandoCodigo] = useState(false)
  const [confirmandoEntrega, setConfirmandoEntrega] = useState(false)
  const [resgatesPendentes, setResgatesPendentes] = useState([])
  const [loadingPendentes, setLoadingPendentes] = useState(false)

  // Carregar lista de clientes ao iniciar
  useEffect(() => {
    loadClientes()
  }, [])

  useEffect(() => {
    if (clienteId) {
      if (activeTab === 'dashboard' || activeTab === 'historico') {
        loadSaldo()
        loadHistorico()
      }
      if (activeTab === 'reservas') {
        loadReservasCliente()
      }
      if (activeTab === 'estatisticas') {
        loadEstatisticas()
      }
    }

    if (activeTab === 'regras') {
      loadRegras()
    }

    if (activeTab === 'premios' || activeTab === 'precos') {
      loadPremios()
    }

    if (activeTab === 'cupons') {
      loadCupons()
    }

    if (activeTab === 'validar-resgate') {
      loadResgatesPendentes()
    }

    setError('')
  }, [activeTab, clienteId, canManageRegras, canManagePremios, canManageCupons])

  const resetRegraForm = () => {
    setEditRegraId(null)
    setRegraForm({
      suite_tipo: '',
      temporada: '',
      diarias_base: 2,
      rp_por_base: 0,
      data_inicio: '',
      data_fim: '',
      ativo: true
    })
  }

  const resetCupomForm = () => {
    setEditCupomId(null)
    setCupomForm({
      codigo: '',
      descricao: '',
      tipo_desconto: 'PERCENTUAL',
      valor_desconto: '',
      pontos_bonus: '',
      min_diarias: '',
      suites_permitidas: '',
      data_inicio: '',
      data_fim: '',
      limite_total_usos: '',
      limite_por_cliente: '',
      ativo: true
    })
  }

  const normalizarSuitesCupom = (value) =>
    value
      .split(',')
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean)

  const loadCupons = async () => {
    if (!canManageCupons) return

    try {
      setCuponsLoading(true)
      setCuponsError('')
      const res = await api.get('/cupons')
      setCupons(Array.isArray(res.data) ? res.data : [])
    } catch (err) {
      setCuponsError(formatErrorMessage(err))
    } finally {
      setCuponsLoading(false)
    }
  }

  const loadRegras = async () => {
    if (!canManageRegras) return

    try {
      setRegrasLoading(true)
      setRegrasError('')

      const res = await api.get('/pontos/regras')
      const regrasData = Array.isArray(res.data) ? res.data : []
      setRegras(regrasData)
    } catch (err) {
      setRegrasError(formatErrorMessage(err))
    } finally {
      setRegrasLoading(false)
    }
  }

  const resetPremioForm = () => {
    setEditPremioId(null)
    setPremioForm({
      nome: '',
      descricao: '',
      preco_em_pontos: 0,
      preco_em_rp: '',
      categoria: 'GERAL',
      estoque: '',
      imagem_url: '',
      ativo: true
    })
  }

  const loadPremios = async () => {
    try {
      setPremiosLoading(true)
      setPremiosError('')
      const res = await api.get('/premios')
      const premiosData = Array.isArray(res.data) ? res.data : []
      setPremios(premiosData)
    } catch (err) {
      setPremiosError(formatErrorMessage(err))
    } finally {
      setPremiosLoading(false)
    }
  }

  const startEditPremio = (premio) => {
    setEditPremioId(premio.id)
    setPremioForm({
      nome: premio.nome || '',
      descricao: premio.descricao || '',
      preco_em_pontos: premio.preco_em_pontos ?? 0,
      preco_em_rp: premio.preco_em_rp ?? '',
      categoria: premio.categoria || 'GERAL',
      estoque: premio.estoque ?? '',
      imagem_url: premio.imagem_url || '',
      ativo: !!premio.ativo
    })
  }

  const submitPremio = async (e) => {
    e.preventDefault()
    if (!canManagePremios) return

    if (!premioForm.nome) {
      setPremiosError('Informe o nome do premio')
      return
    }
    if (!premioForm.preco_em_pontos || Number(premioForm.preco_em_pontos) <= 0) {
      setPremiosError('Informe um preco em pontos valido')
      return
    }

    try {
      setPremiosLoading(true)
      setPremiosError('')

      const payload = {
        nome: premioForm.nome.trim(),
        descricao: premioForm.descricao || null,
        preco_em_pontos: Number(premioForm.preco_em_pontos),
        categoria: premioForm.categoria || 'GERAL',
        ativo: !!premioForm.ativo
      }

      if (premioForm.preco_em_rp !== '' && premioForm.preco_em_rp !== null) {
        const rpValue = Number(premioForm.preco_em_rp)
        if (rpValue <= 0) {
          setPremiosError('Preco em RP deve ser maior que 0')
          return
        }
        payload.preco_em_rp = rpValue
      }

      if (premioForm.estoque !== '' && premioForm.estoque !== null) {
        payload.estoque = Number(premioForm.estoque)
      }

      if (premioForm.imagem_url) {
        payload.imagem_url = premioForm.imagem_url
      }

      if (editPremioId) {
        await api.put(`/premios/${editPremioId}`, payload)
      } else {
        await api.post('/premios', payload)
      }

      resetPremioForm()
      await loadPremios()
    } catch (err) {
      setPremiosError(formatErrorMessage(err))
    } finally {
      setPremiosLoading(false)
    }
  }

  const desativarPremio = async (id) => {
    if (!canManagePremios) return
    if (!window.confirm('Deseja desativar este premio?')) return

    try {
      setPremiosLoading(true)
      setPremiosError('')
      await api.delete(`/premios/${id}`)
      await loadPremios()
    } catch (err) {
      setPremiosError(formatErrorMessage(err))
    } finally {
      setPremiosLoading(false)
    }
  }

  const updatePrecoEdit = (premioId, field, value) => {
    setPrecoEdits((prev) => ({
      ...prev,
      [premioId]: {
        ...(prev[premioId] || {}),
        [field]: value
      }
    }))
  }

  const clearPrecoEdit = (premioId) => {
    setPrecoEdits((prev) => {
      const next = { ...prev }
      delete next[premioId]
      return next
    })
  }

  const savePreco = async (premioId) => {
    if (!canManagePremios) return
    const edit = precoEdits[premioId]
    if (!edit) return

    const payload = {}

    if (edit.preco_em_pontos !== undefined && edit.preco_em_pontos !== '') {
      const valor = Number(edit.preco_em_pontos)
      if (valor <= 0) {
        setPremiosError('Preco em pontos deve ser maior que 0')
        return
      }
      payload.preco_em_pontos = valor
    }

    if (edit.preco_em_rp !== undefined && edit.preco_em_rp !== '') {
      const valor = Number(edit.preco_em_rp)
      if (valor <= 0) {
        setPremiosError('Preco em RP deve ser maior que 0')
        return
      }
      payload.preco_em_rp = valor
    }

    if (!Object.keys(payload).length) {
      setPremiosError('Informe ao menos um preco para salvar')
      return
    }

    try {
      setPremiosLoading(true)
      setPremiosError('')
      await api.put(`/premios/${premioId}`, payload)
      clearPrecoEdit(premioId)
      await loadPremios()
    } catch (err) {
      setPremiosError(formatErrorMessage(err))
    } finally {
      setPremiosLoading(false)
    }
  }

  const startEditCupom = (cupom) => {
    setEditCupomId(cupom.id)
    setCupomForm({
      codigo: cupom.codigo || '',
      descricao: cupom.descricao || '',
      tipo_desconto: cupom.tipo_desconto || 'PERCENTUAL',
      valor_desconto: cupom.valor_desconto ?? '',
      pontos_bonus: cupom.pontos_bonus ?? '',
      min_diarias: cupom.min_diarias ?? '',
      suites_permitidas: Array.isArray(cupom.suites_permitidas) ? cupom.suites_permitidas.join(', ') : '',
      data_inicio: (cupom.data_inicio || '').toString().slice(0, 10),
      data_fim: (cupom.data_fim || '').toString().slice(0, 10),
      limite_total_usos: cupom.limite_total_usos ?? '',
      limite_por_cliente: cupom.limite_por_cliente ?? '',
      ativo: !!cupom.ativo
    })
  }

  const submitCupom = async (e) => {
    e.preventDefault()
    if (!canManageCupons) return

    if (!editCupomId && !cupomForm.codigo.trim()) {
      setCuponsError('Informe o código do cupom')
      return
    }
    if (!cupomForm.valor_desconto || Number(cupomForm.valor_desconto) <= 0) {
      setCuponsError('Informe um valor de desconto válido')
      return
    }
    if (!cupomForm.data_inicio || !cupomForm.data_fim) {
      setCuponsError('Informe o período de vigência do cupom')
      return
    }

    try {
      setCuponsLoading(true)
      setCuponsError('')

      const payload = {
        descricao: cupomForm.descricao || null,
        tipo_desconto: cupomForm.tipo_desconto,
        valor_desconto: Number(cupomForm.valor_desconto),
        data_inicio: `${cupomForm.data_inicio}T00:00:00`,
        data_fim: `${cupomForm.data_fim}T23:59:59`,
        ativo: !!cupomForm.ativo
      }

      if (!editCupomId) {
        payload.codigo = cupomForm.codigo.trim().toUpperCase()
      }

      if (cupomForm.pontos_bonus !== '') {
        payload.pontos_bonus = Number(cupomForm.pontos_bonus)
      }
      if (cupomForm.min_diarias !== '') {
        payload.min_diarias = Number(cupomForm.min_diarias)
      }
      if (cupomForm.limite_total_usos !== '') {
        payload.limite_total_usos = Number(cupomForm.limite_total_usos)
      }
      if (cupomForm.limite_por_cliente !== '') {
        payload.limite_por_cliente = Number(cupomForm.limite_por_cliente)
      }

      const suites = normalizarSuitesCupom(cupomForm.suites_permitidas)
      if (suites.length) {
        payload.suites_permitidas = suites
      }

      if (editCupomId) {
        await api.put(`/cupons/${editCupomId}`, payload)
      } else {
        await api.post('/cupons', payload)
      }

      resetCupomForm()
      await loadCupons()
    } catch (err) {
      setCuponsError(formatErrorMessage(err))
    } finally {
      setCuponsLoading(false)
    }
  }

  const toggleCupomStatus = async (cupom) => {
    if (!canManageCupons) return

    try {
      setCuponsLoading(true)
      setCuponsError('')
      await api.patch(`/cupons/${cupom.id}/ativar`, { ativo: !cupom.ativo })
      await loadCupons()
    } catch (err) {
      setCuponsError(formatErrorMessage(err))
    } finally {
      setCuponsLoading(false)
    }
  }

  const excluirCupom = async (cupomId) => {
    if (!canManageCupons) return
    if (!window.confirm('Deseja desativar este cupom?')) return

    try {
      setCuponsLoading(true)
      setCuponsError('')
      await api.delete(`/cupons/${cupomId}`)
      await loadCupons()
    } catch (err) {
      setCuponsError(formatErrorMessage(err))
    } finally {
      setCuponsLoading(false)
    }
  }

  const startEditRegra = (regra) => {
    setEditRegraId(regra.id)
    setRegraForm({
      suite_tipo: regra.suite_tipo || '',
      temporada: regra.temporada || '',
      diarias_base: regra.diarias_base ?? 2,
      rp_por_base: regra.rp_por_base ?? 0,
      data_inicio: (regra.data_inicio || '').toString().slice(0, 10),
      data_fim: (regra.data_fim || '').toString().slice(0, 10),
      ativo: !!regra.ativo
    })
  }

  const duplicateRegra = (regra) => {
    setEditRegraId(null)
    setRegraForm({
      suite_tipo: regra.suite_tipo || '',
      temporada: regra.temporada || '',
      diarias_base: regra.diarias_base ?? 2,
      rp_por_base: regra.rp_por_base ?? 0,
      data_inicio: (regra.data_inicio || '').toString().slice(0, 10),
      data_fim: (regra.data_fim || '').toString().slice(0, 10),
      ativo: true
    })
  }

  const submitRegra = async (e) => {
    e.preventDefault()
    if (!canManageRegras) return

    if (!regraForm.suite_tipo) {
      setRegrasError('Informe o tipo de suíte')
      return
    }
    if (!regraForm.rp_por_base || regraForm.rp_por_base <= 0) {
      setRegrasError('Informe RP por base (maior que 0)')
      return
    }
    if (!regraForm.data_inicio || !regraForm.data_fim) {
      setRegrasError('Informe data início e data fim')
      return
    }

    try {
      setRegrasLoading(true)
      setRegrasError('')

      const payload = {
        suite_tipo: regraForm.suite_tipo,
        diarias_base: Number(regraForm.diarias_base || 2),
        rp_por_base: Number(regraForm.rp_por_base || 0),
        temporada: regraForm.temporada || null,
        data_inicio: regraForm.data_inicio,
        data_fim: regraForm.data_fim,
        ativo: !!regraForm.ativo
      }

      if (editRegraId) {
        await api.put(`/pontos/regras/${editRegraId}`, payload)
      } else {
        await api.post('/pontos/regras', payload)
      }

      resetRegraForm()
      await loadRegras()
    } catch (err) {
      setRegrasError(formatErrorMessage(err))
    } finally {
      setRegrasLoading(false)
    }
  }

  const desativarRegra = async (id) => {
    if (!canManageRegras) return

    try {
      setRegrasLoading(true)
      setRegrasError('')
      await api.delete(`/pontos/regras/${id}`)
      await loadRegras()
    } catch (err) {
      setRegrasError(formatErrorMessage(err))
    } finally {
      setRegrasLoading(false)
    }
  }

  const validarCodigoResgate = async () => {
    if (!codigoResgate.trim()) {
      setError('Digite um código de resgate')
      return
    }

    try {
      setValidandoCodigo(true)
      setError('')
      const res = await api.post('/validacao-resgates/validar', {
        codigo_resgate: codigoResgate.trim()
      })
      setValidacaoResult(res.data)
    } catch (err) {
      setError(formatErrorMessage(err))
      setValidacaoResult(null)
    } finally {
      setValidandoCodigo(false)
    }
  }

  const confirmarEntrega = async () => {
    if (!validacaoResult || !codigoResgate) return

    if (!window.confirm('Confirmar entrega deste prêmio?')) return

    try {
      setConfirmandoEntrega(true)
      setError('')
      await api.post('/validacao-resgates/confirmar-entrega', {
        codigo_resgate: codigoResgate.trim()
      })
      alert('✅ Entrega confirmada com sucesso!')
      setCodigoResgate('')
      setValidacaoResult(null)
      loadResgatesPendentes()
    } catch (err) {
      setError(formatErrorMessage(err))
    } finally {
      setConfirmandoEntrega(false)
    }
  }

  const loadResgatesPendentes = async () => {
    try {
      setLoadingPendentes(true)
      const res = await api.get('/validacao-resgates/historico?status=PENDENTE')
      setResgatesPendentes(res.data.resgates || [])
    } catch (err) {
      console.error('Erro ao carregar resgates pendentes:', err)
    } finally {
      setLoadingPendentes(false)
    }
  }

  const loadClientes = async () => {
    try {
      setLoading(true)
      const res = await api.get('/clientes')
      const clientesData = res.data.clientes || res.data
      if (clientesData && clientesData.length > 0) {
        setClientes(clientesData)
        // Selecionar primeiro cliente por padrão
        setClienteId(clientesData[0].id)
        setClienteNome(clientesData[0].nome_completo)
      } else {
        setError('Nenhum cliente encontrado. Cadastre clientes primeiro.')
      }
    } catch (error) {
      console.error('Erro ao carregar clientes:', error)
      setError('Erro ao carregar clientes. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  const loadSaldo = async () => {
    try {
      setLoading(true)
      const res = await api.get(`/pontos/saldo/${clienteId}`)
      if (res.data.success || res.data.saldo !== undefined) {
        setSaldo(res.data.saldo || 0)
        setError('')
      } else {
        setError(res.data.error || 'Erro ao carregar saldo')
      }
    } catch (error) {
      console.error('Erro ao carregar saldo:', error)
      const errorMsg = formatErrorMessage(error)
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const loadHistorico = async () => {
    try {
      setLoading(true)
      const res = await api.get(`/pontos/historico/${clienteId}?limit=100`)
      if (res.data.success || res.data.transacoes) {
        const transacoes = res.data.transacoes || []
        setHistorico(transacoes)
        
        // Calcular total de ganhos (apenas créditos)
        const ganhos = transacoes
          .filter(t => ['CREDITO', 'GANHO'].includes(t.tipo) && t.pontos > 0)
          .reduce((sum, t) => sum + t.pontos, 0)
        setTotalGanhos(ganhos)
        
        // Calcular diárias pendentes (reservas CHECKED_OUT sem pontos)
        const reservasComPontos = new Set(transacoes.filter(t => t.reserva_id).map(t => t.reserva_id))
        // Buscar reservas do cliente para calcular pendentes
        loadReservasCliente().then(reservas => {
          const pendentes = reservas.filter(r => 
            r.status === 'CHECKED_OUT' && !reservasComPontos.has(r.id)
          ).length
          setDiariasPendentes(pendentes)
        })
        
        setError('')
      } else {
        setError(res.data.error || 'Erro ao carregar histórico')
      }
    } catch (error) {
      console.error('Erro ao carregar histórico:', error)
      const errorMsg = formatErrorMessage(error)
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const loadReservasCliente = async () => {
    if (!clienteId) return []
    
    try {
      const res = await api.get(`/reservas?cliente_id=${clienteId}&limit=100`)
      const reservas = res.data.reservas || []
      setReservasCliente(reservas)
      return reservas
    } catch (error) {
      console.error('Erro ao carregar reservas:', error)
      return []
    }
  }

  const loadEstatisticas = async () => {
    try {
      const res = await api.get('/pontos/estatisticas')
      setEstatisticas(res.data)
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error)
    }
  }

  const getTipoTransacaoColor = (tipo) => {
    switch (tipo) {
      case 'CREDITO':
      case 'GANHO':
        return 'text-green-600 font-bold'
      case 'DEBITO':
      case 'RESGATE':
        return 'text-red-600 font-bold'
      case 'AJUSTE':
      case 'AJUSTE_MANUAL':
        return 'text-blue-600 font-bold'
      case 'ESTORNO':
        return 'text-orange-600 font-bold'
      default:
        return 'text-gray-600'
    }
  }

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Saldo */}
      <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-6 rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold mb-4">💎 Seus Pontos RP</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold">{saldo}</div>
            <div className="text-sm opacity-75">Saldo RP</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold">{diariasPendentes}</div>
            <div className="text-sm opacity-75">Diárias Pendentes</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold">{totalGanhos}</div>
            <div className="text-sm opacity-75">Total Ganhos</div>
          </div>
        </div>
      </div>

      {/* Histórico */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">📈 Histórico de Pontos</h3>
        {historico.length > 0 ? (
          <div className="space-y-3">
            {historico.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                  <div className="font-medium">{item.reserva_codigo || `Transação #${item.id}`}</div>
                  <div className="text-sm text-gray-500">{new Date(item.created_at).toLocaleDateString()}</div>
                </div>
                <div className="text-right">
                  <span className={getTipoTransacaoColor(item.tipo)}>
                    {item.pontos > 0 ? '+' : ''}{item.pontos} pts
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            <div className="text-6xl mb-2">📊</div>
            <p>Nenhum histórico encontrado</p>
          </div>
        )}
      </div>
    </div>
  )

  const renderHistorico = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">📈 Histórico Detalhado</h3>
      {historico.length > 0 ? (
        <div className="space-y-3">
          {historico.map((item, index) => (
            <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {item.reserva_codigo || `Transação #${item.id}`}
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(item.created_at).toLocaleDateString()}
                  </div>
                  <div className="text-sm text-gray-400">
                    {item.origem} • {item.tipo}
                  </div>
                  {item.motivo && (
                    <div className="text-sm text-gray-600 mt-1">{item.motivo}</div>
                  )}
                </div>
                <div className="text-right">
                  <span className={getTipoTransacaoColor(item.tipo)}>
                    {item.pontos > 0 ? '+' : ''}{item.pontos} pts
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center text-gray-500 py-8">
          <div className="text-6xl mb-2">📈</div>
          <p>Nenhum histórico encontrado</p>
        </div>
      )}
    </div>
  )

  const renderReservas = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">🏨 Reservas e Pontos</h3>
      {reservasCliente.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {reservasCliente.map((reserva) => {
            const pontosGanhos = historico.find(h => h.reserva_id === reserva.id)?.pontos || 0
            const podeGanharPontos = reserva.status === 'CHECKED_OUT' && pontosGanhos === 0
            
            return (
              <div key={reserva.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold text-gray-900 dark:text-white">
                      Reserva #{reserva.codigo_reserva}
                    </div>
                    <div className="text-sm text-gray-500">
                      Quarto {reserva.quarto_numero} • {reserva.tipo_suite}
                    </div>
                    <div className="text-sm text-gray-500">
                      {new Date(reserva.checkin_previsto).toLocaleDateString()} - {new Date(reserva.checkout_previsto).toLocaleDateString()}
                    </div>
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mt-1">
                      Valor: R$ {Number(reserva.valor_total || 0).toFixed(2)}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      reserva.status === 'CHECKED_OUT' ? 'bg-green-100 text-green-800' :
                      reserva.status === 'HOSPEDADO' ? 'bg-blue-100 text-blue-800' :
                      reserva.status === 'CONFIRMADA' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {reserva.status}
                    </span>
                    {pontosGanhos > 0 && (
                      <div className="text-green-600 font-bold mt-2">
                        +{pontosGanhos} pts ✓
                      </div>
                    )}
                    {podeGanharPontos && (
                      <div className="text-orange-600 font-medium text-xs mt-2">
                        ⏳ Pontos pendentes
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center text-gray-500 py-8">
          <div className="text-6xl mb-2">🏨</div>
          <p>Nenhuma reserva encontrada</p>
        </div>
      )}
    </div>
  )

  const renderEstatisticas = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">📊 Estatísticas do Programa</h3>
      {estatisticas ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Seus Dados</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Saldo Atual:</span>
                <span className="font-bold text-purple-600">{saldo} pts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Ganho:</span>
                <span className="font-bold text-green-600">+{totalGanhos} pts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Gasto:</span>
                <span className="font-bold text-red-600">-{totalGanhos - saldo} pts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Reservas:</span>
                <span className="font-bold">{reservasCliente.length}</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Programa Geral</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Clientes:</span>
                <span className="font-bold">{estatisticas.total_usuarios || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Pontos em Circulação:</span>
                <span className="font-bold text-purple-600">{estatisticas.total_pontos_circulacao || 0} pts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Transações Hoje:</span>
                <span className="font-bold">{estatisticas.transacoes_hoje || 0}</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center text-gray-500 py-8">
          <div className="text-6xl mb-2">📊</div>
          <p>Carregando estatísticas...</p>
        </div>
      )}
    </div>
  )

  const renderPremios = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">Gestao de Premios</h3>

      {!canManagePremios ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <p className="text-gray-600 dark:text-gray-300">Acesso restrito a ADMIN e GERENTE.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold text-gray-900 dark:text-white">Cadastrar / Editar premio</h4>
              {editPremioId ? (
                <button
                  type="button"
                  onClick={resetPremioForm}
                  className="px-3 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-900"
                >
                  Cancelar edicao
                </button>
              ) : null}
            </div>

            {premiosError ? (
              <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 border border-red-200">
                {premiosError}
              </div>
            ) : null}

            <form onSubmit={submitPremio} className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome</label>
                <input
                  value={premioForm.nome}
                  onChange={(e) => setPremioForm(prev => ({ ...prev, nome: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="Ex: Cafe da Manha"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label>
                <input
                  value={premioForm.categoria}
                  onChange={(e) => setPremioForm(prev => ({ ...prev, categoria: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="HOSPEDAGEM, LAZER..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preco em pontos</label>
                <input
                  type="number"
                  min="1"
                  value={premioForm.preco_em_pontos}
                  onChange={(e) => setPremioForm(prev => ({ ...prev, preco_em_pontos: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preco em RP (opcional)</label>
                <input
                  type="number"
                  min="1"
                  value={premioForm.preco_em_rp}
                  onChange={(e) => setPremioForm(prev => ({ ...prev, preco_em_rp: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="Se diferente do preco em pontos"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Estoque (opcional)</label>
                <input
                  type="number"
                  min="0"
                  value={premioForm.estoque}
                  onChange={(e) => setPremioForm(prev => ({ ...prev, estoque: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div className="md:col-span-3">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descricao</label>
                <textarea
                  value={premioForm.descricao}
                  onChange={(e) => setPremioForm(prev => ({ ...prev, descricao: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  rows="3"
                  placeholder="Descreva o prêmio..."
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  🖼️ URL da Imagem do Prêmio
                </label>
                <input
                  type="url"
                  value={premioForm.imagem_url}
                  onChange={(e) => setPremioForm(prev => ({ ...prev, imagem_url: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="https://exemplo.com/imagem.jpg"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  💡 Dica: Use serviços como Imgur, Cloudinary ou hospede a imagem em seu servidor
                </p>
              </div>

              <div className="md:col-span-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preview</label>
                {premioForm.imagem_url ? (
                  <div className="border-2 border-gray-300 dark:border-gray-600 rounded-lg p-2 bg-gray-50 dark:bg-gray-700">
                    <img
                      src={premioForm.imagem_url}
                      alt="Preview"
                      className="w-full h-24 object-cover rounded"
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3E❌ Erro%3C/text%3E%3C/svg%3E'
                      }}
                    />
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-2 h-24 flex items-center justify-center bg-gray-50 dark:bg-gray-700">
                    <span className="text-gray-400 text-sm">Sem imagem</span>
                  </div>
                )}
              </div>

              <div className="md:col-span-3 flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={!!premioForm.ativo}
                    onChange={(e) => setPremioForm(prev => ({ ...prev, ativo: e.target.checked }))}
                  />
                  Ativo
                </label>

                <button
                  type="submit"
                  disabled={premiosLoading}
                  className="px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-60"
                >
                  {editPremioId ? 'Salvar' : 'Criar'}
                </button>
              </div>
            </form>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold text-gray-900 dark:text-white">Premios cadastrados</h4>
              <button
                type="button"
                onClick={loadPremios}
                disabled={premiosLoading}
                className="px-3 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-900 disabled:opacity-60"
              >
                Atualizar
              </button>
            </div>

            {premiosLoading ? (
              <div className="text-gray-600 dark:text-gray-300">Carregando premios...</div>
            ) : premios.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left border-b">
                      <th className="py-2 pr-4">Imagem</th>
                      <th className="py-2 pr-4">Nome</th>
                      <th className="py-2 pr-4">Categoria</th>
                      <th className="py-2 pr-4">Pontos</th>
                      <th className="py-2 pr-4">RP</th>
                      <th className="py-2 pr-4">Estoque</th>
                      <th className="py-2 pr-4">Ativo</th>
                      <th className="py-2 pr-4">Acoes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {premios.map((p) => (
                      <tr key={p.id} className="border-b">
                        <td className="py-2 pr-4">
                          {p.imagem_url ? (
                            <img
                              src={p.imagem_url}
                              alt={p.nome}
                              className="w-12 h-12 object-cover rounded border border-gray-300"
                              onError={(e) => {
                                e.target.src = 'data:image/svg+xml,%3Csvg xmlns=\"http://www.w3.org/2000/svg\" width=\"48\" height=\"48\"%3E%3Crect fill=\"%23e5e7eb\" width=\"48\" height=\"48\"/%3E%3Ctext fill=\"%239ca3af\" x=\"50%25\" y=\"50%25\" text-anchor=\"middle\" dy=\".3em\" font-size=\"20\"%3E🎁%3C/text%3E%3C/svg%3E'
                              }}
                            />
                          ) : (
                            <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600 flex items-center justify-center text-2xl">
                              🎁
                            </div>
                          )}
                        </td>
                        <td className="py-2 pr-4 font-medium">{p.nome}</td>
                        <td className="py-2 pr-4">{p.categoria || '-'}</td>
                        <td className="py-2 pr-4">{p.preco_em_pontos}</td>
                        <td className="py-2 pr-4">{p.preco_em_rp ?? '-'}</td>
                        <td className="py-2 pr-4">{p.estoque ?? '-'}</td>
                        <td className="py-2 pr-4">{p.ativo ? 'Sim' : 'Nao'}</td>
                        <td className="py-2 pr-4">
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => startEditPremio(p)}
                              className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
                            >
                              Editar
                            </button>
                            {p.ativo ? (
                              <button
                                type="button"
                                onClick={() => desativarPremio(p.id)}
                                className="px-3 py-1 rounded bg-red-600 text-white hover:bg-red-700"
                              >
                                Desativar
                              </button>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-gray-600 dark:text-gray-300">Nenhum premio cadastrado.</div>
            )}
          </div>
        </div>
      )}
    </div>
  )

  const renderPrecos = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">Atualizar precos por temporada</h3>

      {!canManagePremios ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <p className="text-gray-600 dark:text-gray-300">Acesso restrito a ADMIN e GERENTE.</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          {premiosError ? (
            <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 border border-red-200">
              {premiosError}
            </div>
          ) : null}

          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Atualize os precos dos premios para a temporada atual. As alteracoes sao salvas imediatamente.
            </p>
            <button
              type="button"
              onClick={loadPremios}
              disabled={premiosLoading}
              className="px-3 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-900 disabled:opacity-60"
            >
              Atualizar
            </button>
          </div>

          {premiosLoading ? (
            <div className="text-gray-600 dark:text-gray-300">Carregando premios...</div>
          ) : premios.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left border-b">
                    <th className="py-2 pr-4">Premio</th>
                    <th className="py-2 pr-4">Categoria</th>
                    <th className="py-2 pr-4">Preco atual</th>
                    <th className="py-2 pr-4">Novo preco (pontos)</th>
                    <th className="py-2 pr-4">Novo preco (RP)</th>
                    <th className="py-2 pr-4">Acoes</th>
                  </tr>
                </thead>
                <tbody>
                  {premios.map((p) => {
                    const edit = precoEdits[p.id] || {}
                    return (
                      <tr key={p.id} className="border-b">
                        <td className="py-2 pr-4 font-medium">{p.nome}</td>
                        <td className="py-2 pr-4">{p.categoria || '-'}</td>
                        <td className="py-2 pr-4">
                          {p.preco_em_pontos} pts {p.preco_em_rp ? `| ${p.preco_em_rp} RP` : ''}
                        </td>
                        <td className="py-2 pr-4">
                          <input
                            type="number"
                            min="1"
                            value={edit.preco_em_pontos ?? p.preco_em_pontos}
                            onChange={(e) => updatePrecoEdit(p.id, 'preco_em_pontos', e.target.value)}
                            className="w-28 p-2 border border-gray-300 rounded-lg"
                          />
                        </td>
                        <td className="py-2 pr-4">
                          <input
                            type="number"
                            min="1"
                            value={edit.preco_em_rp ?? (p.preco_em_rp ?? '')}
                            onChange={(e) => updatePrecoEdit(p.id, 'preco_em_rp', e.target.value)}
                            className="w-28 p-2 border border-gray-300 rounded-lg"
                          />
                        </td>
                        <td className="py-2 pr-4">
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => savePreco(p.id)}
                              className="px-3 py-1 rounded bg-green-600 text-white hover:bg-green-700"
                            >
                              Salvar
                            </button>
                            <button
                              type="button"
                              onClick={() => clearPrecoEdit(p.id)}
                              className="px-3 py-1 rounded bg-gray-600 text-white hover:bg-gray-700"
                            >
                              Limpar
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-gray-600 dark:text-gray-300">Nenhum premio cadastrado.</div>
          )}
        </div>
      )}
    </div>
  )

  const renderCupons = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">Cupons Promocionais</h3>

      {!canManageCupons ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <p className="text-gray-600 dark:text-gray-300">Acesso restrito a ADMIN e GERENTE.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white">Cadastrar / Editar cupom</h4>
                <p className="text-sm text-gray-500 mt-1">Gerencie cupons de desconto e bônus de RP diretamente no módulo de pontos.</p>
              </div>
              {editCupomId ? (
                <button
                  type="button"
                  onClick={resetCupomForm}
                  className="px-3 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-900"
                >
                  Cancelar edição
                </button>
              ) : null}
            </div>

            {cuponsError ? (
              <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 border border-red-200">
                {cuponsError}
              </div>
            ) : null}

            <form onSubmit={submitCupom} className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Código</label>
                <input
                  value={cupomForm.codigo}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, codigo: e.target.value.toUpperCase() }))}
                  disabled={!!editCupomId}
                  className="w-full p-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                  placeholder="CARNAVAL10"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo de desconto</label>
                <select
                  value={cupomForm.tipo_desconto}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, tipo_desconto: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                >
                  <option value="PERCENTUAL">Percentual</option>
                  <option value="FIXO">Fixo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor do desconto</label>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={cupomForm.valor_desconto}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, valor_desconto: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Pontos bônus</label>
                <input
                  type="number"
                  min="0"
                  value={cupomForm.pontos_bonus}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, pontos_bonus: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="Opcional"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mínimo de diárias</label>
                <input
                  type="number"
                  min="1"
                  value={cupomForm.min_diarias}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, min_diarias: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="Opcional"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Suítes permitidas</label>
                <input
                  value={cupomForm.suites_permitidas}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, suites_permitidas: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="MASTER, DUPLA, REAL"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data início</label>
                <input
                  type="date"
                  value={cupomForm.data_inicio}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, data_inicio: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data fim</label>
                <input
                  type="date"
                  value={cupomForm.data_fim}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, data_fim: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Limite total de usos</label>
                <input
                  type="number"
                  min="1"
                  value={cupomForm.limite_total_usos}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, limite_total_usos: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="Opcional"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Limite por cliente</label>
                <input
                  type="number"
                  min="1"
                  value={cupomForm.limite_por_cliente}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, limite_por_cliente: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="Opcional"
                />
              </div>

              <div className="md:col-span-3">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descrição</label>
                <textarea
                  value={cupomForm.descricao}
                  onChange={(e) => setCupomForm(prev => ({ ...prev, descricao: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  rows="3"
                  placeholder="Ex: Desconto de carnaval com bônus de fidelidade"
                />
              </div>

              <div className="md:col-span-3 flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={!!cupomForm.ativo}
                    onChange={(e) => setCupomForm(prev => ({ ...prev, ativo: e.target.checked }))}
                  />
                  Ativo
                </label>

                <button
                  type="submit"
                  disabled={cuponsLoading}
                  className="px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-60"
                >
                  {editCupomId ? 'Salvar' : 'Criar'}
                </button>
              </div>
            </form>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold text-gray-900 dark:text-white">Cupons cadastrados</h4>
              <button
                type="button"
                onClick={loadCupons}
                disabled={cuponsLoading}
                className="px-3 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-900 disabled:opacity-60"
              >
                Atualizar
              </button>
            </div>

            {cuponsLoading ? (
              <div className="text-gray-600 dark:text-gray-300">Carregando cupons...</div>
            ) : cupons.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left border-b">
                      <th className="py-2 pr-4">Código</th>
                      <th className="py-2 pr-4">Tipo</th>
                      <th className="py-2 pr-4">Desconto</th>
                      <th className="py-2 pr-4">Bônus</th>
                      <th className="py-2 pr-4">Vigência</th>
                      <th className="py-2 pr-4">Uso</th>
                      <th className="py-2 pr-4">Status</th>
                      <th className="py-2 pr-4">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cupons.map((cupom) => (
                      <tr key={cupom.id} className="border-b">
                        <td className="py-2 pr-4 font-semibold">{cupom.codigo}</td>
                        <td className="py-2 pr-4">{cupom.tipo_desconto}</td>
                        <td className="py-2 pr-4">
                          {cupom.tipo_desconto === 'PERCENTUAL'
                            ? `${Number(cupom.valor_desconto || 0).toFixed(2)}%`
                            : `R$ ${Number(cupom.valor_desconto || 0).toFixed(2)}`}
                        </td>
                        <td className="py-2 pr-4">{cupom.pontos_bonus || 0} RP</td>
                        <td className="py-2 pr-4">
                          {(cupom.data_inicio || '').toString().slice(0, 10)} até {(cupom.data_fim || '').toString().slice(0, 10)}
                        </td>
                        <td className="py-2 pr-4">
                          {cupom.total_usos || 0}
                          {cupom.limite_total_usos ? ` / ${cupom.limite_total_usos}` : ''}
                        </td>
                        <td className="py-2 pr-4">{cupom.ativo ? 'Ativo' : 'Inativo'}</td>
                        <td className="py-2 pr-4">
                          <div className="flex flex-wrap gap-2">
                            <button
                              type="button"
                              onClick={() => startEditCupom(cupom)}
                              className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              onClick={() => toggleCupomStatus(cupom)}
                              className={`px-3 py-1 rounded text-white ${cupom.ativo ? 'bg-amber-600 hover:bg-amber-700' : 'bg-green-600 hover:bg-green-700'}`}
                            >
                              {cupom.ativo ? 'Inativar' : 'Ativar'}
                            </button>
                            <button
                              type="button"
                              onClick={() => excluirCupom(cupom.id)}
                              className="px-3 py-1 rounded bg-red-600 text-white hover:bg-red-700"
                            >
                              Excluir
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-gray-600 dark:text-gray-300">Nenhum cupom cadastrado.</div>
            )}
          </div>
        </div>
      )}
    </div>
  )

  const renderRegras = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">Regras de Pontuacao</h3>

      {!canManageRegras ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <p className="text-gray-600 dark:text-gray-300">Acesso restrito a ADMIN e GERENTE.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold text-gray-900 dark:text-white">Cadastrar / Editar regra</h4>
              {editRegraId ? (
                <button
                  type="button"
                  onClick={resetRegraForm}
                  className="px-3 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-900"
                >
                  Cancelar edicao
                </button>
              ) : null}
            </div>

            {regrasError ? (
              <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 border border-red-200">
                {regrasError}
              </div>
            ) : null}

            <form onSubmit={submitRegra} className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo de suite</label>
                <input
                  value={regraForm.suite_tipo}
                  onChange={(e) => setRegraForm(prev => ({ ...prev, suite_tipo: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="LUXO, MASTER, REAL..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Temporada (opcional)</label>
                <input
                  value={regraForm.temporada}
                  onChange={(e) => setRegraForm(prev => ({ ...prev, temporada: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="ALTA, BAIXA..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Diarias base</label>
                <input
                  type="number"
                  min="1"
                  value={regraForm.diarias_base}
                  onChange={(e) => setRegraForm(prev => ({ ...prev, diarias_base: Number(e.target.value) }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">RP por base</label>
                <input
                  type="number"
                  min="1"
                  value={regraForm.rp_por_base}
                  onChange={(e) => setRegraForm(prev => ({ ...prev, rp_por_base: Number(e.target.value) }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data inicio</label>
                <input
                  type="date"
                  value={regraForm.data_inicio}
                  onChange={(e) => setRegraForm(prev => ({ ...prev, data_inicio: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data fim</label>
                <input
                  type="date"
                  value={regraForm.data_fim}
                  onChange={(e) => setRegraForm(prev => ({ ...prev, data_fim: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div className="md:col-span-3 flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={!!regraForm.ativo}
                    onChange={(e) => setRegraForm(prev => ({ ...prev, ativo: e.target.checked }))}
                  />
                  Ativo
                </label>

                <button
                  type="submit"
                  disabled={regrasLoading}
                  className="px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-60"
                >
                  {editRegraId ? 'Salvar' : 'Criar'}
                </button>
              </div>
            </form>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold text-gray-900 dark:text-white">Regras cadastradas</h4>
              <button
                type="button"
                onClick={loadRegras}
                disabled={regrasLoading}
                className="px-3 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-900 disabled:opacity-60"
              >
                Atualizar
              </button>
            </div>

            {regrasLoading ? (
              <div className="text-gray-600 dark:text-gray-300">Carregando regras...</div>
            ) : regras.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left border-b">
                      <th className="py-2 pr-4">Suite</th>
                      <th className="py-2 pr-4">Temporada</th>
                      <th className="py-2 pr-4">Base</th>
                      <th className="py-2 pr-4">RP</th>
                      <th className="py-2 pr-4">Vigencia</th>
                      <th className="py-2 pr-4">Ativo</th>
                      <th className="py-2 pr-4">Acoes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {regras.map((r) => (
                      <tr key={r.id} className="border-b">
                        <td className="py-2 pr-4 font-medium">{r.suite_tipo}</td>
                        <td className="py-2 pr-4">{r.temporada || '-'}</td>
                        <td className="py-2 pr-4">{r.diarias_base}</td>
                        <td className="py-2 pr-4">{r.rp_por_base}</td>
                        <td className="py-2 pr-4">
                          {(r.data_inicio || '').toString().slice(0, 10)} - {(r.data_fim || '').toString().slice(0, 10)}
                        </td>
                        <td className="py-2 pr-4">{r.ativo ? 'Sim' : 'Nao'}</td>
                        <td className="py-2 pr-4">
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => startEditRegra(r)}
                              className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              onClick={() => duplicateRegra(r)}
                              className="px-3 py-1 rounded bg-gray-600 text-white hover:bg-gray-700"
                            >
                              Duplicar
                            </button>
                            {r.ativo ? (
                              <button
                                type="button"
                                onClick={() => desativarRegra(r.id)}
                                className="px-3 py-1 rounded bg-red-600 text-white hover:bg-red-700"
                              >
                                Desativar
                              </button>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-gray-600 dark:text-gray-300">Nenhuma regra cadastrada.</div>
            )}
          </div>
        </div>
      )}
    </div>
  )

  const renderValidarResgate = () => (
    <div className="space-y-6">
      {/* Formulário de Validação */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          🔍 Validar Código de Resgate
        </h3>
        
        <div className="flex gap-3 mb-4">
          <input
            type="text"
            value={codigoResgate}
            onChange={(e) => setCodigoResgate(e.target.value.toUpperCase())}
            placeholder="Digite o código (ex: RES-000001)"
            className="flex-1 p-3 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
            onKeyPress={(e) => e.key === 'Enter' && validarCodigoResgate()}
          />
          <button
            onClick={validarCodigoResgate}
            disabled={validandoCodigo}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-semibold"
          >
            {validandoCodigo ? 'Validando...' : 'Validar'}
          </button>
        </div>

        {/* Resultado da Validação */}
        {validacaoResult && (
          <div className={`p-6 rounded-lg border-2 ${
            validacaoResult.valido && !validacaoResult.ja_entregue
              ? 'bg-green-50 dark:bg-green-900/20 border-green-500'
              : validacaoResult.ja_entregue
              ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500'
              : 'bg-red-50 dark:bg-red-900/20 border-red-500'
          }`}>
            <div className="text-center mb-4">
              <div className="text-4xl mb-2">
                {validacaoResult.valido && !validacaoResult.ja_entregue ? '✅' : validacaoResult.ja_entregue ? '⚠️' : '❌'}
              </div>
              <p className="text-lg font-bold">
                {validacaoResult.mensagem}
              </p>
            </div>

            {validacaoResult.valido && (
              <div className="space-y-3 text-sm">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="font-semibold">Cliente:</span>
                    <p className="text-gray-700 dark:text-gray-300">{validacaoResult.cliente_nome}</p>
                  </div>
                  <div>
                    <span className="font-semibold">Documento:</span>
                    <p className="text-gray-700 dark:text-gray-300">{validacaoResult.cliente_documento}</p>
                  </div>
                  <div>
                    <span className="font-semibold">Prêmio:</span>
                    <p className="text-gray-700 dark:text-gray-300">{validacaoResult.premio_nome}</p>
                  </div>
                  <div>
                    <span className="font-semibold">Pontos:</span>
                    <p className="text-gray-700 dark:text-gray-300">{validacaoResult.pontos_usados} pontos</p>
                  </div>
                  <div>
                    <span className="font-semibold">Status:</span>
                    <p className="text-gray-700 dark:text-gray-300">{validacaoResult.status}</p>
                  </div>
                  <div>
                    <span className="font-semibold">Data Resgate:</span>
                    <p className="text-gray-700 dark:text-gray-300">
                      {validacaoResult.data_resgate ? new Date(validacaoResult.data_resgate).toLocaleString('pt-BR') : '-'}
                    </p>
                  </div>
                </div>

                {validacaoResult.ja_entregue && (
                  <div className="mt-4 p-3 bg-yellow-100 dark:bg-yellow-900/30 rounded">
                    <p className="font-semibold">⚠️ Prêmio já foi entregue!</p>
                    <p className="text-sm">Entregue por: {validacaoResult.funcionario_entrega || 'N/A'}</p>
                  </div>
                )}

                {!validacaoResult.ja_entregue && (
                  <button
                    onClick={confirmarEntrega}
                    disabled={confirmandoEntrega}
                    className="w-full mt-4 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-semibold"
                  >
                    {confirmandoEntrega ? 'Confirmando...' : '✅ Confirmar Entrega'}
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Lista de Resgates Pendentes */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold flex items-center gap-2">
            📋 Resgates Pendentes
          </h3>
          <button
            onClick={loadResgatesPendentes}
            disabled={loadingPendentes}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
          >
            🔄 Atualizar
          </button>
        </div>

        {loadingPendentes ? (
          <div className="text-center py-8 text-gray-500">Carregando...</div>
        ) : resgatesPendentes.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-6xl mb-4">🎉</div>
            <p>Nenhum resgate pendente</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left border-b dark:border-gray-700">
                  <th className="py-2 pr-4">Código</th>
                  <th className="py-2 pr-4">Cliente</th>
                  <th className="py-2 pr-4">Prêmio</th>
                  <th className="py-2 pr-4">Pontos</th>
                  <th className="py-2 pr-4">Data</th>
                  <th className="py-2 pr-4">Ação</th>
                </tr>
              </thead>
              <tbody>
                {resgatesPendentes.map((resgate) => (
                  <tr key={resgate.resgate_id} className="border-b dark:border-gray-700">
                    <td className="py-2 pr-4 font-mono font-bold text-purple-600 dark:text-purple-400">
                      {resgate.codigo}
                    </td>
                    <td className="py-2 pr-4">{resgate.cliente_nome}</td>
                    <td className="py-2 pr-4">{resgate.premio_nome}</td>
                    <td className="py-2 pr-4">{resgate.pontos_usados}</td>
                    <td className="py-2 pr-4">
                      {resgate.data_resgate ? new Date(resgate.data_resgate).toLocaleDateString('pt-BR') : '-'}
                    </td>
                    <td className="py-2 pr-4">
                      <button
                        onClick={() => {
                          setCodigoResgate(resgate.codigo)
                          validarCodigoResgate()
                        }}
                        className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-xs"
                      >
                        Validar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )

  const renderContent = () => {
    const isRegrasTab = activeTab === 'regras'
    const isPremiosTab = activeTab === 'premios'
    const isPrecosTab = activeTab === 'precos'
    const isCuponsTab = activeTab === 'cupons'
    const isValidarResgateTab = activeTab === 'validar-resgate'
    const needsCliente = !isRegrasTab && !isPremiosTab && !isPrecosTab && !isCuponsTab && !isValidarResgateTab

    return (
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">💎 Sistema de Pontos RP</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Programa de fidelidade do Hotel Cabo Frio
          </p>
        </div>

        {/* Cliente Selector */}
        {needsCliente ? (
          clientes.length ? (
            <div className="mb-6">
              <label htmlFor="cliente-select" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Selecione o Cliente
              </label>
              <select
                id="cliente-select"
                value={clienteId || ''}
                onChange={(e) => {
                  const selectedId = parseInt(e.target.value)
                  const cliente = clientes.find(c => c.id === selectedId)
                  setClienteId(selectedId)
                  setClienteNome(cliente?.nome_completo || '')
                  setError('')
                }}
                className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:ring-blue-500 focus:ring-opacity-50"
              >
                <option value="">Selecione um cliente...</option>
                {clientes.map(cliente => (
                  <option key={cliente.id} value={cliente.id}>
                    {cliente.nome_completo}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="mb-6">
              <div className="text-sm text-gray-600 dark:text-gray-300">
                Nenhum cliente carregado.
              </div>
            </div>
          )
        ) : null}

        {needsCliente && loading ? (
          <div className="mb-4 p-3 rounded-lg bg-gray-50 text-gray-700 border border-gray-200">
            Carregando...
          </div>
        ) : null}

        {needsCliente && error ? (
          <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 border border-red-200">
            {error}
          </div>
        ) : null}

        {/* Tabs */}
        <div className="mb-6">
          <div className="flex space-x-1 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                activeTab === 'dashboard' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📊 Dashboard
            </button>
            <button
              onClick={() => setActiveTab('historico')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                activeTab === 'historico' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📈 Histórico
            </button>
            <button
              onClick={() => setActiveTab('reservas')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                activeTab === 'reservas' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              🏨 Reservas
            </button>
            <button
              onClick={() => setActiveTab('estatisticas')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                activeTab === 'estatisticas' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📊 Estatísticas
            </button>
            {canManageRegras ? (
              <button
                onClick={() => setActiveTab('regras')}
                className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                  activeTab === 'regras' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Regras
              </button>
            ) : null}
            {canManagePremios ? (
              <button
                onClick={() => setActiveTab('premios')}
                className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                  activeTab === 'premios' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Premios
              </button>
            ) : null}
            {canManagePremios ? (
              <button
                onClick={() => setActiveTab('precos')}
                className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                  activeTab === 'precos' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Precos
              </button>
            ) : null}
            {canManageCupons ? (
              <button
                onClick={() => setActiveTab('cupons')}
                className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                  activeTab === 'cupons' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Cupons
              </button>
            ) : null}
            <button
              onClick={() => setActiveTab('validar-resgate')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
                activeTab === 'validar-resgate' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              🔍 Validar Resgate
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'regras' ? (
          renderRegras()
        ) : activeTab === 'premios' ? (
          renderPremios()
        ) : activeTab === 'precos' ? (
          renderPrecos()
        ) : activeTab === 'cupons' ? (
          renderCupons()
        ) : activeTab === 'validar-resgate' ? (
          renderValidarResgate()
        ) : clienteId ? (
          <>
            {activeTab === 'dashboard' && renderDashboard()}
            {activeTab === 'historico' && renderHistorico()}
            {activeTab === 'reservas' && renderReservas()}
            {activeTab === 'estatisticas' && renderEstatisticas()}
          </>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-6xl mb-4">👤</div>
            <p>Selecione um cliente para visualizar os pontos</p>
          </div>
        )}
      </div>
    )
  }

  return (
    <ProtectedRoute>
      {renderContent()}
    </ProtectedRoute>
  )
}

export default function Pontos() {
  return (
    <PontosContent />
  )
}
