'use client'
import { useEffect, useState, useMemo } from 'react'
import { api } from '../../../lib/api'
import { formatErrorMessage } from '../../../lib/errorHandler'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { StatusReserva, StatusPagamento, MetodoPagamento, isPagamentoAprovado, isPagamentoNegado, HttpStatus } from '../../../lib/constants/enums'
import UploadComprovanteModal from '../../../components/UploadComprovanteModal'
import StatusBadge from '../../../components/StatusBadge'
import ModalEscolhaPagamento from '../../../components/ModalEscolhaPagamento'

// Mapeamento de cores para estados (mantido para compatibilidade)
const STATUS_RESERVA_COLORS = {
  'PENDENTE': 'text-yellow-600 bg-yellow-100',
  'PENDENTE_PAGAMENTO': 'text-yellow-600 bg-yellow-100',
  'AGUARDANDO_COMPROVANTE': 'text-orange-600 bg-orange-100',
  'EM_ANALISE': 'text-blue-600 bg-blue-100',
  'PAGA_APROVADA': 'text-green-600 bg-green-100',
  'PAGA_REJEITADA': 'text-red-600 bg-red-100',
  'CHECKIN_LIBERADO': 'text-purple-600 bg-purple-100',
  'CHECKIN_REALIZADO': 'text-indigo-600 bg-indigo-100',
  'CONFIRMADA': 'text-blue-600 bg-blue-100',
  'HOSPEDADO': 'text-green-600 bg-green-100',
  'CHECKED_OUT': 'text-gray-600 bg-gray-100',
  'CHECKOUT_REALIZADO': 'text-gray-600 bg-gray-100',
  'CANCELADO': 'text-red-600 bg-red-100',
  'CANCELADA': 'text-red-600 bg-red-100',
  'NO_SHOW': 'text-orange-600 bg-orange-100'
}

export default function Reservas() {
  const [reservas, setReservas] = useState([])
  const [clientes, setClientes] = useState([])
  const [quartos, setQuartos] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [totalReservas, setTotalReservas] = useState(0)

  const STATUS_FINALIZADAS = ['CHECKED_OUT', 'CHECKOUT_REALIZADO', 'CANCELADO', 'CANCELADA']
  const STATUS_CANCELADAS = ['CANCELADO', 'CANCELADA']
  const STATUS_CHECKOUTS = ['CHECKED_OUT', 'CHECKOUT_REALIZADO']
  const STATUS_HOSPEDADAS = ['HOSPEDADO', 'CHECKIN_REALIZADO']
  const STATUS_PENDENTES = ['PENDENTE', 'PENDENTE_PAGAMENTO', 'AGUARDANDO_COMPROVANTE', 'EM_ANALISE']
  const STATUS_PODE_PAGAR = ['PENDENTE', 'PENDENTE_PAGAMENTO', 'PAGA_REJEITADA', 'CONFIRMADA']
  const STATUS_PODE_CANCELAR = ['PENDENTE', 'PENDENTE_PAGAMENTO', 'AGUARDANDO_COMPROVANTE', 'EM_ANALISE', 'CONFIRMADA', 'PAGA_APROVADA', 'CHECKIN_LIBERADO', 'PAGA_REJEITADA']
  const STATUS_PODE_CHECKIN = ['CONFIRMADA', 'PAGA_APROVADA', 'CHECKIN_LIBERADO']
  
  // Estados para visão operacional profissional
  const [activeTab, setActiveTab] = useState('ativas')
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [dateFilterInicio, setDateFilterInicio] = useState('')
  const [dateFilterFim, setDateFilterFim] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)
  const [showPagamentoModal, setShowPagamentoModal] = useState(false)
  const [showModalEscolhaPagamento, setShowModalEscolhaPagamento] = useState(false)
  const [showCheckinModal, setShowCheckinModal] = useState(false)
  const [showCheckoutModal, setShowCheckoutModal] = useState(false)
  const [showQuartoModal, setShowQuartoModal] = useState(false)
  const [showHistoricoModal, setShowHistoricoModal] = useState(false)
  const [showDetalhesModal, setShowDetalhesModal] = useState(false)
  const [showUploadComprovanteModal, setShowUploadComprovanteModal] = useState(false)
  const [selectedPagamento, setSelectedPagamento] = useState(null)
  const [historicoQuarto, setHistoricoQuarto] = useState(null)
  const [loadingHistorico, setLoadingHistorico] = useState(false)
  const [editingQuarto, setEditingQuarto] = useState(null)
  const [selectedReserva, setSelectedReserva] = useState(null)
  const [validacaoCodigo, setValidacaoCodigo] = useState(null)
  const [codigoValidar, setCodigoValidar] = useState('')
  
  // Estados para Check-in/Check-out robusto
  const [checkinValidacao, setCheckinValidacao] = useState(null)
  const [checkoutValidacao, setCheckoutValidacao] = useState(null)
  const [hospedes, setHospedes] = useState([])
  const [pagamentoForm, setPagamentoForm] = useState({
    forma: 'CREDITO',
    numero: '',
    validade: '',
    cvv: '',
    nome: ''
  })
  const [checkinForm, setCheckinForm] = useState({
    hospede_titular_nome: '',
    hospede_titular_documento: '',
    hospede_titular_documento_tipo: 'CPF',
    num_hospedes_real: 1,
    num_criancas: 0,
    veiculo_placa: '',
    observacoes_checkin: '',
    caucao_cobrada: 0,
    caucao_forma_pagamento: 'DINHEIRO',
    pagamento_validado: true,
    documentos_conferidos: true,
    termos_aceitos: true,
    assinatura_digital: ''
  })
  const [checkoutForm, setCheckoutForm] = useState({
    vistoria_ok: true,
    danos_encontrados: '',
    valor_danos: 0,
    consumo_frigobar: 0,
    servicos_extras: 0,
    taxa_late_checkout: 0,
    caucao_devolvida: 0,
    caucao_retida: 0,
    motivo_retencao: '',
    avaliacao_hospede: 5,
    comentario_hospede: '',
    forma_acerto: 'DINHEIRO',
    observacoes_checkout: ''
  })
  const [quartoForm, setQuartoForm] = useState({
    numero: '',
    tipo_suite: 'LUXO',
    status: 'LIVRE'
  })
  const [form, setForm] = useState({
    cliente_id: '',
    quarto_numero: '',
    tipo_suite: 'LUXO',
    data_entrada: '',
    data_saida: '',
    valor_diaria: '',
    num_diarias: 1,
    valor_total: ''
  })
  const [tarifaAtual, setTarifaAtual] = useState(null)
  const [tarifaLoading, setTarifaLoading] = useState(false)
  const [tarifaError, setTarifaError] = useState('')

  const [quartosDisponiveis, setQuartosDisponiveis] = useState([])
  const [disponibilidadeLoading, setDisponibilidadeLoading] = useState(false)
  const [disponibilidadeError, setDisponibilidadeError] = useState('')

  useEffect(() => {
    loadReservas()
    loadClientes()
    loadQuartos()
  }, [])

  const fetchDisponibilidade = async (opts = {}) => {
    const { silent = false } = opts

    if (!showForm) return
    if (!form.data_entrada || !form.data_saida) return
    if (form.data_saida <= form.data_entrada) return

    if (!silent) {
      setDisponibilidadeLoading(true)
      setDisponibilidadeError('')
    }

    try {
      const res = await api.get('/public/quartos/disponiveis', {
        params: {
          data_checkin: form.data_entrada,
          data_checkout: form.data_saida
        }
      })

      const tipos = res.data?.tipos_disponiveis || []
      const tipoSelecionado = (form.tipo_suite || '').toUpperCase().trim()
      const entry = tipoSelecionado
        ? tipos.find((t) => String(t.tipo || '').toUpperCase() === tipoSelecionado)
        : null

      const quartos = entry?.quartos || []
      setQuartosDisponiveis(quartos)

      if (form.quarto_numero && !quartos.some((q) => q.numero === form.quarto_numero)) {
        setForm((prev) => ({ ...prev, quarto_numero: '' }))
      }
    } catch (error) {
      if (!silent) {
        setDisponibilidadeError('Erro ao buscar disponibilidade')
      }
      setQuartosDisponiveis([])
    } finally {
      if (!silent) setDisponibilidadeLoading(false)
    }
  }

  useEffect(() => {
    if (!showForm) return
    fetchDisponibilidade({ silent: false })
  }, [showForm, form.data_entrada, form.data_saida, form.tipo_suite])

  useEffect(() => {
    if (!showForm) return
    if (!form.data_entrada || !form.data_saida) return

    const intervalMs = 10000
    const id = setInterval(() => {
      fetchDisponibilidade({ silent: true })
    }, intervalMs)

    return () => clearInterval(id)
  }, [showForm, form.data_entrada, form.data_saida, form.tipo_suite])

  useEffect(() => {
    if (!form.tipo_suite || !form.data_entrada) return
    fetchTarifa(form.tipo_suite, form.data_entrada)
  }, [form.tipo_suite, form.data_entrada])

  useEffect(() => {
    if (tarifaAtual === null || tarifaAtual === undefined) return
    const tarifaStr = String(tarifaAtual)
    setForm((prev) => {
      if (prev.valor_diaria === tarifaStr) return prev
      return { ...prev, valor_diaria: tarifaStr }
    })
  }, [tarifaAtual])

  useEffect(() => {
    if (!form.data_entrada || !form.data_saida) return

    const start = new Date(form.data_entrada)
    const end = new Date(form.data_saida)
    const diffMs = end - start
    const numDiarias = diffMs > 0 ? Math.ceil(diffMs / (1000 * 60 * 60 * 24)) : 0

    const diariaNumber = parseFloat(tarifaAtual || 0)
    const valorTotal = (numDiarias > 0 && diariaNumber > 0)
      ? (numDiarias * diariaNumber).toFixed(2)
      : ''

    setForm((prev) => {
      if (prev.num_diarias === numDiarias && prev.valor_total === valorTotal) return prev
      return { ...prev, num_diarias: numDiarias, valor_total: valorTotal }
    })
  }, [form.data_entrada, form.data_saida, tarifaAtual])

  // Cálculo de indicadores
  const indicadores = useMemo(() => {
    const pendentes = reservas.filter(r => STATUS_PENDENTES.includes(r.status)).length
    const hospedadas = reservas.filter(r => STATUS_HOSPEDADAS.includes(r.status)).length
    const checkouts = reservas.filter(r => STATUS_CHECKOUTS.includes(r.status)).length
    const canceladas = reservas.filter(r => STATUS_CANCELADAS.includes(r.status)).length
    const valorPrevisto = reservas.reduce((sum, r) => sum + (Number(r.valor_total) || 0), 0)
    
    return {
      total: reservas.length,
      pendentes,
      hospedadas,
      checkouts,
      canceladas,
      valorPrevisto
    }
  }, [reservas])

  // Filtragem de reservas
  const reservasFiltradas = useMemo(() => {
    let filtradas = [...reservas]
    
    if (activeTab === 'ativas') {
      filtradas = filtradas.filter(r => !STATUS_FINALIZADAS.includes(r.status))
    } else if (activeTab === 'excluidas') {
      filtradas = filtradas.filter(r => STATUS_FINALIZADAS.includes(r.status))
    }
    
    if (searchTerm) {
      filtradas = filtradas.filter(r => 
        r.cliente_nome?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.quarto_numero?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.codigo_reserva?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }
    
    if (statusFilter) {
      filtradas = filtradas.filter(r => r.status === statusFilter)
    }
    
    if (dateFilterInicio) {
      filtradas = filtradas.filter(r => {
        if (!r.checkin_previsto) return false
        return new Date(r.checkin_previsto) >= new Date(dateFilterInicio)
      })
    }
    
    if (dateFilterFim) {
      filtradas = filtradas.filter(r => {
        if (!r.checkin_previsto) return false
        return new Date(r.checkin_previsto) <= new Date(dateFilterFim)
      })
    }
    
    return filtradas
  }, [reservas, activeTab, searchTerm, statusFilter, dateFilterInicio, dateFilterFim])

  const paginatedReservas = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    return reservasFiltradas.slice(startIndex, startIndex + itemsPerPage)
  }, [reservasFiltradas, currentPage, itemsPerPage])

  const totalPages = Math.ceil(reservasFiltradas.length / itemsPerPage)
  const startRange = (currentPage - 1) * itemsPerPage + 1
  const endRange = Math.min(currentPage * itemsPerPage, reservasFiltradas.length)

  const loadReservas = async () => {
    try {
      setLoading(true)
      const res = await api.get('/reservas')
      const reservas = res.data.reservas || []
      setReservas(reservas)
      setTotalReservas(reservas.length)
      console.log('Reservas carregadas:', reservas.length, reservas)
      
      // Debug específico para checkout
      const reservaCheckout = reservas.find(r => r.codigo_reserva === 'RCF-202601-AB4526')
      if (reservaCheckout) {
        console.log('🔍 DEBUG CHECKOUT - Reserva encontrada:', {
          codigo: reservaCheckout.codigo_reserva,
          status: reservaCheckout.status,
          tem_hospedagem: !!reservaCheckout.hospedagem,
          hospedagem_status: reservaCheckout.hospedagem?.status_hospedagem,
          ja_fez_checkin: jaFezCheckin(reservaCheckout),
          ja_fez_checkout: jaFezCheckout(reservaCheckout),
          pode_checkout: podeCheckout(reservaCheckout)
        })
      }
    } catch (error) {
      console.error('Erro ao carregar reservas:', error)
      toast.error('Erro ao carregar reservas')
      setReservas([])
    } finally {
      setLoading(false)
    }
  }

  const loadClientes = async () => {
    try {
      const res = await api.get('/clientes')
      setClientes(res.data.clientes || [])
    } catch (error) {
      toast.error('Erro ao carregar clientes')
    }
  }

  const loadQuartos = async () => {
    try {
      const res = await api.get('/quartos')
      const quartos = Array.isArray(res.data) ? res.data : (res.data.quartos || [])
      setQuartos(quartos)
    } catch (error) {
      toast.error('Erro ao carregar quartos')
    }
  }

  const updateFormField = async (field, value) => {
    setForm(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const fetchTarifa = async (suiteTipo, dataEntrada) => {
    try {
      setTarifaLoading(true)
      setTarifaError('')
      const response = await api.get(`/tarifas/ativa?suite_tipo=${suiteTipo}&data=${dataEntrada}`)
      setTarifaAtual(response.data.preco_diaria)
    } catch (error) {
      setTarifaError('Tarifa não encontrada')
      setTarifaAtual(null)
    } finally {
      setTarifaLoading(false)
    }
  }

  const updateQuartoForm = (field, value) => {
    setQuartoForm(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.cliente_id || !form.quarto_numero || !form.data_entrada || !form.data_saida) {
      toast.warning('Preencha todos os campos')
      return
    }

    setLoading(true)
    const checkinPrevisto = new Date(`${form.data_entrada}T15:00:00`)
    const checkoutPrevisto = new Date(`${form.data_saida}T12:00:00`)
    
    const payload = {
      cliente_id: Number(form.cliente_id),
      quarto_numero: form.quarto_numero,
      tipo_suite: form.tipo_suite,
      checkin_previsto: checkinPrevisto.toISOString(),
      checkout_previsto: checkoutPrevisto.toISOString(),
      valor_diaria: parseFloat(form.valor_diaria),
      num_diarias: form.num_diarias
    }

    try {
      await api.post('/reservas', payload)
      toast.success('Reserva criada com sucesso!')
      await loadReservas()
      setShowForm(false)
      setForm({ cliente_id: '', quarto_numero: '', tipo_suite: 'LUXO', data_entrada: '', data_saida: '', valor_diaria: '', num_diarias: 1, valor_total: '' })
    } catch (error) {
      const msg = formatErrorMessage(error)
      toast.error(`Erro: ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleCancelar = async (id) => {
    if (!confirm('Deseja cancelar esta reserva?')) return
    try {
      await api.patch(`/reservas/${id}/cancelar`)
      toast.success('Reserva cancelada')
      await loadReservas()
    } catch (error) {
      toast.error('Erro ao cancelar')
    }
  }

  // Funções para gestão de quartos
  const handleCreateQuarto = async () => {
    try {
      setLoading(true)
      
      // Validar formulário
      if (!quartoForm.numero.trim()) {
        toast.error('Número do quarto é obrigatório')
        return
      }
      
      // Verificar se quarto já existe
      const quartoExistente = quartos.find(q => q.numero === quartoForm.numero)
      if (quartoExistente && !editingQuarto) {
        toast.error('Quarto com este número já existe')
        return
      }
      
      const quartoData = {
        numero: quartoForm.numero,
        tipo_suite: quartoForm.tipo_suite,
        status: quartoForm.status
      }
      
      if (editingQuarto) {
        // Editar quarto existente
        await api.put(`/quartos/${editingQuarto.numero}`, quartoData)
        toast.success('Quarto atualizado com sucesso!')
      } else {
        // Criar novo quarto
        await api.post('/quartos', quartoData)
        toast.success('Quarto criado com sucesso!')
      }
      
      // Resetar formulário e recarregar
      setQuartoForm({ numero: '', tipo_suite: 'LUXO', status: 'LIVRE' })
      setEditingQuarto(null)
      setShowQuartoModal(false)
      loadQuartos()
      
    } catch (error) {
      console.error('Erro ao salvar quarto:', error)
      toast.error(formatErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }
  
  const handleEditQuarto = (quarto) => {
    setEditingQuarto(quarto)
    setQuartoForm({
      numero: quarto.numero,
      tipo_suite: quarto.tipo_suite,
      status: quarto.status
    })
    setShowQuartoModal(true)
  }
  
  const handleDeleteQuarto = async (quarto) => {
    if (!window.confirm(`Tem certeza que deseja excluir o quarto ${quarto.numero}?`)) {
      return
    }
    
    try {
      setLoading(true)
      await api.delete(`/quartos/${quarto.numero}`)
      toast.success('Quarto excluído com sucesso!')
      loadQuartos()
    } catch (error) {
      console.error('Erro ao excluir quarto:', error)
      toast.error(formatErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }
  
  const handleHistoricoQuarto = async (quarto) => {
    try {
      setLoadingHistorico(true)
      setHistoricoQuarto(quarto)
      
      // Buscar histórico do quarto
      const res = await api.get(`/quartos/${quarto.numero}/historico`)
      setHistoricoQuarto({
        ...quarto,
        ...res.data
      })
      
      setShowHistoricoModal(true)
    } catch (error) {
      console.error('Erro ao carregar histórico:', error)
      toast.error('Erro ao carregar histórico do quarto')
    } finally {
      setLoadingHistorico(false)
    }
  }

  // Funções do Check-in robusto
  const validarCheckin = async (reserva) => {
    try {
      setLoading(true)
      
      // VALIDAÇÃO CRÍTICA: Check-in só pode acontecer se status == CHECKIN_LIBERADO
      if (reserva.status !== 'CHECKIN_LIBERADO' && reserva.status !== 'CONFIRMADA') {
        if (reserva.status === 'PENDENTE_PAGAMENTO') {
          toast.error('❌ Check-in bloqueado: Reserva aguardando pagamento')
        } else if (reserva.status === 'AGUARDANDO_COMPROVANTE') {
          toast.error('❌ Check-in bloqueado: Aguardando upload do comprovante de pagamento')
        } else if (reserva.status === 'EM_ANALISE') {
          toast.error('❌ Check-in bloqueado: Comprovante em análise pelo administrador')
        } else if (reserva.status === 'PAGA_REJEITADA') {
          toast.error('❌ Check-in bloqueado: Comprovante de pagamento foi rejeitado')
        } else {
          toast.error('❌ Check-in bloqueado: Status não permite check-in (' + reserva.status + ')')
        }
        return
      }
      
      // Chamar API real de validação de check-in
      const res = await api.get(`/checkin/${reserva.id}/validar`)
      const validacao = res.data
      
      if (!validacao.pode_checkin) {
        toast.error(validacao.motivo || 'Check-in não permitido')
        return
      }
      
      // Pré-preencher formulário com dados da validação
      setCheckinForm(prev => ({
        ...prev,
        hospede_titular_nome: reserva.cliente_nome || '',
        num_hospedes_real: validacao.capacidade_maxima || 1
      }))
      
      setSelectedReserva(reserva)
      setShowCheckinModal(true)
      toast.success('✅ Validação de check-in concluída!')
      
    } catch (error) {
      const msg = error.response?.data?.detail || 'Erro ao validar check-in'
      toast.error(`❌ ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  const realizarCheckin = async () => {
    if (!selectedReserva) return
    
    try {
      setLoading(true)
      
      if (!checkinForm.termos_aceitos) {
        toast.error('É obrigatório aceitar os termos de hospedagem')
        return
      }
      
      const payload = {
        hospede_titular_nome: checkinForm.hospede_titular_nome,
        hospede_titular_documento: checkinForm.hospede_titular_documento,
        hospede_titular_documento_tipo: checkinForm.hospede_titular_documento_tipo,
        num_hospedes_real: checkinForm.num_hospedes_real,
        num_criancas: checkinForm.num_criancas,
        veiculo_placa: checkinForm.veiculo_placa,
        observacoes_checkin: checkinForm.observacoes_checkin,
        caucao_cobrada: checkinForm.caucao_cobrada,
        caucao_forma_pagamento: checkinForm.caucao_forma_pagamento,
        pagamento_validado: checkinForm.pagamento_validado,
        documentos_conferidos: checkinForm.documentos_conferidos,
        termos_aceitos: checkinForm.termos_aceitos,
        assinatura_digital: checkinForm.assinatura_digital
      }
      
      // Chamar API real de check-in
      const res = await api.post(`/checkin/${selectedReserva.id}/realizar`, payload)
      
      toast.success('🔑 Check-in realizado com sucesso!')
      setShowCheckinModal(false)
      await loadReservas()
      
    } catch (error) {
      const msg = error.response?.data?.detail || 'Erro ao realizar check-in'
      toast.error(`❌ ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  const adicionarHospede = () => {
    const novoHospede = {
      id: Date.now(),
      nome_completo: '',
      documento: '',
      documento_tipo: 'CPF',
      nacionalidade: 'Brasil',
      data_nascimento: '',
      telefone: '',
      email: '',
      e_menor: false,
      responsavel_nome: '',
      responsavel_documento: ''
    }
    setHospedes([...hospedes, novoHospede])
  }

  const removerHospede = (id) => {
    setHospedes(hospedes.filter(h => h.id !== id))
  }

  const atualizarHospede = (id, campo, valor) => {
    setHospedes(hospedes.map(h => 
      h.id === id ? { ...h, [campo]: valor } : h
    ))
  }

  // Funções do Check-out robusto
  const validarCheckout = async (reserva) => {
    try {
      setLoading(true)
      
      // Validações básicas
      if (reserva.status !== 'HOSPEDADO') {
        toast.error('Check-out requer status HOSPEDADO. Status atual: ' + reserva.status)
        return
      }
      
      // Chamar API real de validação de checkout
      const res = await api.get(`/checkin/${reserva.id}/checkout/validar`)
      const validacao = res.data
      
      setCheckoutValidacao(validacao)
      
      // Pré-preencher caução
      setCheckoutForm(prev => ({
        ...prev,
        caucao_devolvida: validacao.caucao_cobrada || 0
      }))
      
      setSelectedReserva(reserva)
      setShowCheckoutModal(true)
      toast.success('Validação de check-out concluída!')
      
    } catch (error) {
      const msg = error.response?.data?.detail || 'Erro ao validar check-out'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const getCheckinTooltip = (reserva) => {
    if (podeCheckin(reserva)) {
      return 'Realizar check-in'
    }
    
    if (reserva.status !== 'CONFIRMADA') {
      return 'Reserva deve estar confirmada'
    }
    
    // Se está confirmada mas não pode fazer check-in, é problema de pagamento
    if (reserva.pagamentos && reserva.pagamentos.length > 0) {
      const pagamentosAprovados = reserva.pagamentos.filter(p => isPagamentoAprovado(p.status))
      if (pagamentosAprovados.length === 0) {
        return 'Pagamento precisa ser aprovado para check-in'
      }
    }
    
    return 'Pagamento aprovado necessário para check-in'
  }

  const podeCheckin = (reserva) => {
    // Verificar se reserva está confirmada E tem pagamento aprovado
    if (!STATUS_PODE_CHECKIN.includes(reserva.status)) return false
    
    // Verificar se existe pagamento aprovado
    if (reserva.pagamentos && reserva.pagamentos.length > 0) {
      return reserva.pagamentos.some(pagamento => 
        isPagamentoAprovado(pagamento.status)
      )
    }
    
    // Se não tiver dados de pagamentos, verificar status da reserva
    return STATUS_PODE_CHECKIN.includes(reserva.status)
  }

  const jaFezCheckin = (reserva) => {
    // Verificar se já existe hospedagem com check-in realizado
    return reserva.hospedagem && reserva.hospedagem.status_hospedagem === 'CHECKIN_REALIZADO'
  }

  const podeCheckout = (reserva) => {
    // Checkout pode ser feito se check-in já foi realizado E checkout ainda não foi feito
    return jaFezCheckin(reserva) && !jaFezCheckout(reserva)
  }

  const jaFezCheckout = (reserva) => {
    // Verificar se checkout já foi realizado
    return reserva.hospedagem && reserva.hospedagem.status_hospedagem === 'CHECKOUT_REALIZADO'
  }

  const podePagar = (reserva) => {
    return STATUS_PODE_PAGAR.includes(reserva.status)
  }

  const temPagamentoEmAndamento = (reserva) => {
    // Verificar se a reserva tem pagamentos e se algum está em andamento
    if (!reserva.pagamentos || reserva.pagamentos.length === 0) {
      return false
    }
    
    return reserva.pagamentos.some(pg => 
      ['PENDENTE', 'PROCESSANDO', 'AGUARDANDO_PAGAMENTO'].includes(pg.status)
    )
  }

  const podeCancelar = (reserva) => {
    return STATUS_PODE_CANCELAR.includes(reserva.status)
  }

  // Função real de checkout usando API
  const realizarCheckout = async () => {
    if (!selectedReserva || !checkoutValidacao) return
    
    try {
      setLoading(true)
      
      const payload = {
        vistoria_ok: checkoutForm.vistoria_ok,
        danos_encontrados: checkoutForm.danos_encontrados || '',
        valor_danos: checkoutForm.valor_danos || 0,
        consumo_frigobar: checkoutForm.consumo_frigobar || 0,
        servicos_extras: checkoutForm.servicos_extras || 0,
        taxa_late_checkout: checkoutForm.taxa_late_checkout || 0,
        caucao_devolvida: checkoutForm.caucao_devolvida || 0,
        caucao_retida: checkoutForm.caucao_retida || 0,
        motivo_retencao: checkoutForm.motivo_retencao || '',
        avaliacao_hospede: checkoutForm.avaliacao_hospede || 5,
        comentario_hospede: checkoutForm.comentario_hospede || '',
        forma_acerto: checkoutForm.forma_acerto || 'DINHEIRO',
        observacoes_checkout: checkoutForm.observacoes_checkout || ''
      }
      
      // Chamar API real de checkout
      const res = await api.post(`/checkin/${selectedReserva.id}/checkout/realizar`, payload)
      
      toast.success('Check-out realizado com sucesso!')
      setShowCheckoutModal(false)
      await loadReservas()
      
    } catch (error) {
      const msg = error.response?.data?.detail || 'Erro ao realizar check-out'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const validarCodigoReserva = async () => {
    if (!codigoValidar.trim()) {
      toast.error('Digite um código de reserva')
      return
    }
    
    try {
      setLoading(true)
      // Buscar na API real
      const res = await api.get(`/reservas?search=${encodeURIComponent(codigoValidar.trim())}`)
      const reservas = res.data.reservas || []
      const reserva = reservas.find(r => r.codigo_reserva === codigoValidar.trim())
      
      if (reserva) {
        setValidacaoCodigo(reserva)
        toast.success('✅ Reserva válida!')
      } else {
        setValidacaoCodigo(null)
        toast.error('❌ Código de reserva inválido')
      }
    } catch (error) {
      setValidacaoCodigo(null)
      toast.error('Erro ao validar código: ' + formatErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  const limparFiltros = () => {
    setSearchTerm('')
    setStatusFilter('')
    setDateFilterInicio('')
    setDateFilterFim('')
    setCurrentPage(1)
  }

  const exportarCSV = () => {
    const headers = ['Código', 'Cliente', 'Quarto', 'Check-in', 'Check-out', 'Valor', 'Status']
    const rows = reservasFiltradas.map(r => [
      r.codigo_reserva,
      r.cliente_nome,
      r.quarto_numero,
      r.checkin_previsto ? new Date(r.checkin_previsto).toLocaleDateString('pt-BR') : '-',
      r.checkout_previsto ? new Date(r.checkout_previsto).toLocaleDateString('pt-BR') : '-',
      `R$ ${Number(r.valor_total || 0).toFixed(2)}`,
      r.status
    ])
    
    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `reservas_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    toast.success('CSV exportado com sucesso!')
  }

  const exportarPDF = () => {
    toast.info('Exportação PDF em desenvolvimento')
  }

  const handlePagar = (reserva) => {
    setSelectedReserva(reserva)
    // Usar novo modal de escolha de pagamento
    setShowModalEscolhaPagamento(true)
  }

  const handleUploadComprovante = (reserva, pagamento) => {
    setSelectedReserva(reserva)
    setSelectedPagamento(pagamento)
    setShowUploadComprovanteModal(true)
  }

  const handleUploadSuccess = async () => {
    await loadReservas()
    setShowUploadComprovanteModal(false)
    setSelectedPagamento(null)
    setSelectedReserva(null)
  }

  const processarPagamento = async () => {
    if (!selectedReserva) return
    
    try {
      setLoading(true)
      
      // Gerar chave de idempotência baseada na reserva
      const idempotencyKey = `reserva-${selectedReserva.id}-${Date.now()}`
      
      const payload = {
        reserva_id: selectedReserva.id,
        cliente_id: selectedReserva.cliente_id,
        metodo: pagamentoForm.forma,
        valor: Number(selectedReserva.valor_total),
        observacao: `Pagamento via ${pagamentoForm.forma}`
      }
      
      // Chamar API real de pagamentos
      const res = await api.post('/pagamentos', payload, {
        headers: {
          'Idempotency-Key': idempotencyKey
        }
      })
      
      if (res.data.success) {
        toast.success('💳 Pagamento processado com sucesso!')
        setShowPagamentoModal(false)
        await loadReservas()
      } else {
        toast.error(res.data.message || 'Erro ao processar pagamento')
      }
      
    } catch (error) {
      let msg = error.response?.data?.detail || 'Erro ao processar pagamento'
      
      // Verificar se é erro de pagamento duplicado
      if (msg.includes('Já existe um pagamento em andamento') || 
          error.response?.data?.error?.includes('Já existe um pagamento em andamento')) {
        msg = '⚠️ Já existe um pagamento em andamento para esta reserva. Verifique o status do pagamento existente.'
      }
      
      toast.error(`❌ ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDetalhes = (reserva) => {
    setSelectedReserva(reserva)
    setShowDetalhesModal(true)
  }

  const getStatusColor = (status) => STATUS_RESERVA_COLORS[status] || 'text-gray-600 bg-gray-100'
  
  const getStatusBadgeClass = (status) => {
    const classes = {
      'PENDENTE': 'bg-yellow-100 text-yellow-800',
      'CONFIRMADA': 'bg-blue-100 text-blue-800',
      'HOSPEDADO': 'bg-green-100 text-green-800',
      'CHECKED_OUT': 'bg-gray-100 text-gray-800',
      'CANCELADO': 'bg-red-100 text-red-800',
      'NO_SHOW': 'bg-orange-100 text-orange-800'
    }
    return classes[status] || 'bg-gray-100 text-gray-600'
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-blue-900">📊 Gestão de Reservas</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          ➕ Nova Reserva
        </button>
      </div>

      {/* Indicadores no topo */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
          <p className="text-sm text-gray-600 font-medium">Total de Reservas</p>
          <p className="text-3xl font-bold text-blue-900 mt-2">{indicadores.total}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
          <p className="text-sm text-gray-600 font-medium">Pendentes</p>
          <p className="text-3xl font-bold text-yellow-600 mt-2">{indicadores.pendentes}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
          <p className="text-sm text-gray-600 font-medium">Hospedadas</p>
          <p className="text-3xl font-bold text-green-600 mt-2">{indicadores.hospedadas}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-gray-500">
          <p className="text-sm text-gray-600 font-medium">Check-outs</p>
          <p className="text-3xl font-bold text-gray-600 mt-2">{indicadores.checkouts}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
          <p className="text-sm text-gray-600 font-medium">Valor Previsto</p>
          <p className="text-2xl font-bold text-purple-600 mt-2">R$ {indicadores.valorPrevisto.toFixed(2)}</p>
        </div>
      </div>

      {/* Validador de Código de Reserva */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6 rounded-lg">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <span className="text-2xl">🔍</span>
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium text-yellow-800">
              Validador de Código de Reserva
            </h3>
            <p className="mt-1 text-sm text-yellow-700">
              ⚠️ Sempre valide o código antes do check-in para garantir autenticidade
            </p>
            <div className="mt-3 flex gap-2">
              <input
                type="text"
                placeholder="Digite o código da reserva"
                value={codigoValidar}
                onChange={(e) => setCodigoValidar(e.target.value.toUpperCase())}
                className="flex-1 p-2 border rounded-lg"
                onKeyPress={(e) => e.key === 'Enter' && validarCodigoReserva()}
              />
              <button
                onClick={validarCodigoReserva}
                disabled={loading}
                className="bg-yellow-600 text-white px-6 py-2 rounded-lg hover:bg-yellow-700 disabled:opacity-50"
              >
                Validar
              </button>
            </div>
            {validacaoCodigo && (
              <div className="mt-3 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
                ✅ <strong>Reserva Válida:</strong> {validacaoCodigo.cliente_nome} - Quarto {validacaoCodigo.quarto_numero} - Status: {validacaoCodigo.status}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Filtros e Busca */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h3 className="font-semibold text-gray-800 mb-3">🔎 Filtros e Busca</h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <input
            type="text"
            placeholder="Buscar cliente, quarto ou código..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="p-2 border rounded-lg"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="p-2 border rounded-lg"
          >
            <option value="">Todos os Status</option>
            <option value="PENDENTE">Pendente</option>
            <option value="CONFIRMADA">Confirmada</option>
            <option value="HOSPEDADO">Hospedada</option>
            <option value="CHECKED_OUT">Check-out</option>
            <option value="CANCELADO">Cancelada</option>
          </select>
          <input
            type="date"
            placeholder="Check-in de"
            value={dateFilterInicio}
            onChange={(e) => setDateFilterInicio(e.target.value)}
            className="p-2 border rounded-lg"
          />
          <input
            type="date"
            placeholder="Check-in até"
            value={dateFilterFim}
            onChange={(e) => setDateFilterFim(e.target.value)}
            className="p-2 border rounded-lg"
          />
          <div className="flex gap-2">
            <button
              onClick={limparFiltros}
              className="flex-1 bg-gray-500 text-white px-3 py-2 rounded-lg hover:bg-gray-600"
            >
              Limpar
            </button>
          </div>
        </div>
        <div className="flex gap-2 mt-3">
          <button
            onClick={exportarCSV}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            📄 Exportar CSV
          </button>
          <button
            onClick={exportarPDF}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex items-center gap-2"
          >
            📕 Exportar PDF
          </button>
        </div>
      </div>

      {/* Abas */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              onClick={() => setActiveTab('ativas')}
              className={`py-4 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'ativas'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📅 Reservas Ativas ({reservas.filter(r => !STATUS_FINALIZADAS.includes(r.status)).length})
            </button>
            <button
              onClick={() => setActiveTab('excluidas')}
              className={`py-4 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'excluidas'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🗑️ Excluídas / Finalizadas ({reservas.filter(r => STATUS_FINALIZADAS.includes(r.status)).length})
            </button>
            <button
              onClick={() => setActiveTab('quartos')}
              className={`py-4 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'quartos'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🏠 Quartos ({quartos.length})
            </button>
          </nav>
        </div>

        {/* Conteúdo das Abas */}
        <div className="p-4">
          {activeTab === 'ativas' && (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cliente</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo Suíte</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check-in</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check-out</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Valor</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {paginatedReservas.length === 0 ? (
                      <tr>
                        <td colSpan="8" className="px-4 py-8 text-center text-gray-500">
                          Nenhuma reserva ativa encontrada
                        </td>
                      </tr>
                    ) : (
                      paginatedReservas.map(r => (
                        <tr key={r.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-mono text-gray-900">{r.codigo_reserva}</td>
                          <td className="px-4 py-3 text-sm text-gray-900">{r.cliente_nome}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{r.quarto_numero} - {r.tipo_suite || 'LUXO'}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {r.checkin_previsto ? new Date(r.checkin_previsto).toLocaleDateString('pt-BR') : '-'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {r.checkout_previsto ? new Date(r.checkout_previsto).toLocaleDateString('pt-BR') : '-'}
                          </td>
                          <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                            R$ {Number(r.valor_total || 0).toFixed(2)}
                          </td>
                          <td className="px-4 py-3">
                            <StatusBadge status={r.status} />
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-col gap-1">
                              <button
                                onClick={() => handleDetalhes(r)}
                                className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                              >
                                👁️ Detalhes
                              </button>
                              {podePagar(r) && !temPagamentoEmAndamento(r) && (
                                <button
                                  onClick={() => handlePagar(r)}
                                  className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                                >
                                  💳 Pagar
                                </button>
                              )}
                              {podePagar(r) && temPagamentoEmAndamento(r) && (
                                <>
                                  <button
                                    disabled
                                    className="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded cursor-not-allowed"
                                    title="Pagamento em andamento"
                                  >
                                    ⏳ Pagamento em andamento
                                  </button>
                                  {r.pagamentos && r.pagamentos.length > 0 && r.pagamentos[0].status === 'PENDENTE' && (
                                    <button
                                      onClick={() => handleUploadComprovante(r, r.pagamentos[0])}
                                      className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                                      title="Enviar comprovante de pagamento"
                                    >
                                      📤 Comprovante
                                    </button>
                                  )}
                                </>
                              )}
                              {podeCheckin(r) && !jaFezCheckin(r) && (
                                <button
                                  onClick={() => validarCheckin(r)}
                                  className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                                >
                                  🔑 Check-in
                                </button>
                              )}
                              {jaFezCheckin(r) && (
                                <button
                                  disabled
                                  className="text-xs px-2 py-1 bg-gray-100 text-gray-500 rounded cursor-not-allowed"
                                  title="Check-in já realizado"
                                >
                                  ✅ Check-in feito
                                </button>
                              )}
                              {podeCheckout(r) && (
                                <button
                                  onClick={() => validarCheckout(r)}
                                  className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
                                >
                                  🏃 Checkout
                                </button>
                              )}
                              {jaFezCheckout(r) && (
                                <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
                                  ✅ Checkout Realizado
                                </span>
                              )}
                              {podeCancelar(r) && (
                                <button
                                  onClick={() => handleCancelar(r.id)}
                                  className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                                >
                                  ❌ Cancelar
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              
              {/* Paginação */}
              {reservasFiltradas.length > 0 && (
                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    Mostrando <span className="font-semibold">{startRange}</span> a{' '}
                    <span className="font-semibold">{endRange}</span> de{' '}
                    <span className="font-semibold">{reservasFiltradas.length}</span> resultados
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      ← Anterior
                    </button>
                    <span className="px-3 py-1 border rounded bg-blue-50 text-blue-600 font-semibold">
                      {currentPage} / {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Próxima →
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {activeTab === 'excluidas' && (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cliente</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo Suíte</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check-in</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check-out</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Valor</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {paginatedReservas.length === 0 ? (
                      <tr>
                        <td colSpan="9" className="px-4 py-8 text-center text-gray-500">
                          Nenhuma reserva finalizada/excluída encontrada
                        </td>
                      </tr>
                    ) : (
                      paginatedReservas.map(r => (
                        <tr key={r.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-mono text-gray-900">{r.codigo_reserva}</td>
                          <td className="px-4 py-3 text-sm text-gray-900">{r.cliente_nome}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{r.quarto_numero} - {r.tipo_suite || 'LUXO'}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {r.checkin_previsto ? new Date(r.checkin_previsto).toLocaleDateString('pt-BR') : '-'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {r.checkout_previsto ? new Date(r.checkout_previsto).toLocaleDateString('pt-BR') : '-'}
                          </td>
                          <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                            R$ {Number(r.valor_total || 0).toFixed(2)}
                          </td>
                          <td className="px-4 py-3">
                            <StatusBadge status={r.status} />
                          </td>
                          <td className="px-4 py-3">
                            <span className={`text-xs font-medium ${r.status === 'CANCELADO' ? 'text-red-600' : 'text-gray-600'}`}>
                              {r.status === 'CANCELADO' ? '❌ Cancelada' : '✅ Finalizada'}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <button
                              onClick={() => handleDetalhes(r)}
                              className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
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
            </>
          )}

          {activeTab === 'quartos' && (
            <div>
              <div className="mb-4">
                <button
                  onClick={() => setShowQuartoModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  ➕ Novo Quarto
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Número</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo de Suíte</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {quartos.map(q => (
                      <tr key={q.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-semibold text-gray-900">{q.numero}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{q.tipo_suite}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            q.status === 'LIVRE' ? 'bg-green-100 text-green-800' : 
                            q.status === 'OCUPADO' ? 'bg-red-100 text-red-800' :
                            q.status === 'MANUTENCAO' ? 'bg-yellow-100 text-yellow-800' :
                            q.status === 'BLOQUEADO' ? 'bg-gray-100 text-gray-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {q.status === 'LIVRE' ? '✅ LIVRE' : 
                             q.status === 'OCUPADO' ? '🔴 OCUPADO' :
                             q.status === 'MANUTENCAO' ? '🔧 MANUTENÇÃO' :
                             q.status === 'BLOQUEADO' ? '🚫 BLOQUEADO' :
                             q.status}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex gap-2">
                            <button 
                              onClick={() => handleHistoricoQuarto(q)}
                              className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                              title="Ver histórico do quarto"
                            >
                              📋 Histórico
                            </button>
                            <button 
                              onClick={() => handleEditQuarto(q)}
                              className="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200"
                              title="Editar quarto"
                            >
                              ✏️ Editar
                            </button>
                            <button 
                              onClick={() => handleDeleteQuarto(q)}
                              className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                              title="Excluir quarto"
                            >
                              🗑️ Excluir
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Nova Reserva</h2>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="text-gray-500 hover:text-gray-700"
                aria-label="Fechar"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
              <select value={form.cliente_id} onChange={(e) => updateFormField('cliente_id', e.target.value)} className="p-2 border rounded" required>
                <option value="">Selecione o Cliente</option>
                {clientes.map(c => <option key={c.id} value={c.id}>{c.nome_completo}</option>)}
              </select>

              <select value={form.tipo_suite} onChange={(e) => updateFormField('tipo_suite', e.target.value)} className="p-2 border rounded">
                <option value="LUXO">Luxo</option>
                <option value="DUPLA">Dupla</option>
                <option value="MASTER">Master</option>
                <option value="REAL">Real</option>
              </select>

              <input type="date" value={form.data_entrada} onChange={(e) => updateFormField('data_entrada', e.target.value)} className="p-2 border rounded" required />
              <input type="date" value={form.data_saida} onChange={(e) => updateFormField('data_saida', e.target.value)} className="p-2 border rounded" required />

              <select value={form.quarto_numero} onChange={(e) => updateFormField('quarto_numero', e.target.value)} className="p-2 border rounded" required>
                <option value="">Selecione o Quarto</option>
                {quartosDisponiveis.map(q => <option key={q.numero} value={q.numero}>{q.numero}</option>)}
              </select>
              <div className="p-2 border rounded bg-gray-50">
                <span className="text-sm">Disponibilidade: </span>
                {disponibilidadeLoading ? (
                  <span className="text-xs text-blue-600">Atualizando...</span>
                ) : disponibilidadeError ? (
                  <span className="text-xs text-red-600">{disponibilidadeError}</span>
                ) : (
                  <span className="text-xs text-green-700">{quartosDisponiveis.length} quarto(s) disponível(is)</span>
                )}
              </div>

              <div className="p-2 border rounded bg-gray-50">
                <span className="text-sm">Diária: R$ {tarifaAtual || '0.00'}</span>
                {tarifaLoading && <span className="text-xs text-blue-600 ml-2">Buscando tarifa...</span>}
                {tarifaError && <span className="text-xs text-red-600 ml-2">{tarifaError}</span>}
              </div>
              <div className="p-2 border rounded bg-gray-50"><span className="text-sm">Diárias: {form.num_diarias}</span></div>
              <div className="p-2 border rounded bg-gray-50"><span className="text-sm font-semibold">Total: R$ {form.valor_total || '0.00'}</span></div>

              <div className="col-span-2 flex gap-2">
                <button type="submit" disabled={loading} className="flex-1 bg-real-blue text-white py-2 rounded hover:bg-blue-800">{loading ? 'Salvando...' : 'Criar Reserva'}</button>
                <button type="button" onClick={() => setShowForm(false)} className="px-6 bg-gray-300 text-gray-700 rounded hover:bg-gray-400">Cancelar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Check-in Robusto */}
      {showCheckinModal && selectedReserva && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-blue-800">🏨 Check-in Profissional</h2>
              <button onClick={() => setShowCheckinModal(false)} className="text-gray-500 hover:text-gray-700">
                ✕
              </button>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg mb-6">
              <h3 className="font-semibold text-blue-800 mb-2">Reserva #{selectedReserva.codigo_reserva}</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><strong>Cliente:</strong> {selectedReserva.cliente_nome}</div>
                <div><strong>Quarto:</strong> {selectedReserva.quarto_numero}</div>
                <div><strong>Entrada:</strong> {new Date(selectedReserva.checkin_previsto).toLocaleDateString('pt-BR')}</div>
                <div><strong>Saída:</strong> {new Date(selectedReserva.checkout_previsto).toLocaleDateString('pt-BR')}</div>
              </div>
            </div>

            {/* Dados do Titular */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">👤 Dados do Hóspede Titular</h4>
              <div className="grid grid-cols-2 gap-4">
                <input
                  type="text"
                  placeholder="Nome Completo do Titular"
                  value={checkinForm.hospede_titular_nome}
                  onChange={(e) => setCheckinForm({...checkinForm, hospede_titular_nome: e.target.value})}
                  className="p-2 border rounded"
                  required
                />
                <input
                  type="text"
                  placeholder="Documento (CPF/RG/Passaporte)"
                  value={checkinForm.hospede_titular_documento}
                  onChange={(e) => setCheckinForm({...checkinForm, hospede_titular_documento: e.target.value})}
                  className="p-2 border rounded"
                  required
                />
                <select
                  value={checkinForm.hospede_titular_documento_tipo}
                  onChange={(e) => setCheckinForm({...checkinForm, hospede_titular_documento_tipo: e.target.value})}
                  className="p-2 border rounded"
                >
                  <option value="CPF">CPF</option>
                  <option value="RG">RG</option>
                  <option value="CNH">CNH</option>
                  <option value="PASSAPORTE">Passaporte</option>
                </select>
                <input
                  type="text"
                  placeholder="Placa do Veículo (opcional)"
                  value={checkinForm.veiculo_placa}
                  onChange={(e) => setCheckinForm({...checkinForm, veiculo_placa: e.target.value})}
                  className="p-2 border rounded"
                />
              </div>
            </div>

            {/* Informações da Hospedagem */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">🏠 Informações da Hospedagem</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Número de Hóspedes</label>
                  <input
                    type="number"
                    min="1"
                    value={checkinForm.num_hospedes_real}
                    onChange={(e) => setCheckinForm({...checkinForm, num_hospedes_real: parseInt(e.target.value)})}
                    className="p-2 border rounded w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Crianças</label>
                  <input
                    type="number"
                    min="0"
                    value={checkinForm.num_criancas}
                    onChange={(e) => setCheckinForm({...checkinForm, num_criancas: parseInt(e.target.value)})}
                    className="p-2 border rounded w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Caução (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={checkinForm.caucao_cobrada}
                    onChange={(e) => setCheckinForm({...checkinForm, caucao_cobrada: parseFloat(e.target.value) || 0})}
                    className="p-2 border rounded w-full"
                  />
                </div>
              </div>
            </div>

            {/* Lista de Hóspedes Adicionais */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <div className="flex justify-between items-center mb-3">
                <h4 className="font-semibold">👥 Hóspedes Adicionais</h4>
                <button
                  onClick={adicionarHospede}
                  className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                >
                  + Adicionar Hóspede
                </button>
              </div>
              
              {hospedes.map((hospede, index) => (
                <div key={hospede.id} className="bg-white p-3 rounded border mb-2">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-sm">Hóspede {index + 2}</span>
                    <button
                      onClick={() => removerHospede(hospede.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Remover
                    </button>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <input
                      type="text"
                      placeholder="Nome Completo"
                      value={hospede.nome_completo}
                      onChange={(e) => atualizarHospede(hospede.id, 'nome_completo', e.target.value)}
                      className="p-2 border rounded text-sm"
                    />
                    <input
                      type="text"
                      placeholder="Documento"
                      value={hospede.documento}
                      onChange={(e) => atualizarHospede(hospede.id, 'documento', e.target.value)}
                      className="p-2 border rounded text-sm"
                    />
                    <select
                      value={hospede.documento_tipo}
                      onChange={(e) => atualizarHospede(hospede.id, 'documento_tipo', e.target.value)}
                      className="p-2 border rounded text-sm"
                    >
                      <option value="CPF">CPF</option>
                      <option value="RG">RG</option>
                      <option value="PASSAPORTE">Passaporte</option>
                      <option value="CERTIDAO_NASCIMENTO">Certidão (menor)</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>

            {/* Validações Obrigatórias */}
            <div className="bg-yellow-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">✅ Validações Obrigatórias</h4>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={checkinForm.documentos_conferidos}
                    onChange={(e) => setCheckinForm({...checkinForm, documentos_conferidos: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm">Documentos conferidos e válidos</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={checkinForm.pagamento_validado}
                    onChange={(e) => setCheckinForm({...checkinForm, pagamento_validado: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm">Pagamento validado (mín. 80%)</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={checkinForm.termos_aceitos}
                    onChange={(e) => setCheckinForm({...checkinForm, termos_aceitos: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm font-bold text-red-600">Termos de hospedagem aceitos (obrigatório)</span>
                </label>
              </div>
            </div>

            <div className="flex gap-4">
              <button
                onClick={realizarCheckin}
                disabled={loading || !checkinForm.termos_aceitos}
                className="flex-1 bg-blue-600 text-white py-3 rounded font-semibold hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Processando...' : '🔑 Realizar Check-in'}
              </button>
              <button
                onClick={() => setShowCheckinModal(false)}
                className="px-6 bg-gray-300 text-gray-700 py-3 rounded font-semibold hover:bg-gray-400"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Check-out Robusto */}
      {showCheckoutModal && selectedReserva && checkoutValidacao && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-green-800">🏃‍♂️ Check-out Profissional</h2>
              <button onClick={() => setShowCheckoutModal(false)} className="text-gray-500 hover:text-gray-700">
                ✕
              </button>
            </div>

            <div className="bg-green-50 p-4 rounded-lg mb-6">
              <h3 className="font-semibold text-green-800 mb-2">Reserva #{selectedReserva.codigo_reserva}</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><strong>Cliente:</strong> {selectedReserva.cliente_nome}</div>
                <div><strong>Quarto:</strong> {selectedReserva.quarto_numero}</div>
                <div><strong>Check-in:</strong> {checkoutValidacao.checkin_datetime ? new Date(checkoutValidacao.checkin_datetime).toLocaleString('pt-BR') : 'N/A'}</div>
                <div><strong>Dias hospedado:</strong> {checkoutValidacao.dias_hospedado || 0} dias</div>
              </div>
            </div>

            {/* Acerto Financeiro */}
            {checkoutValidacao.calculo_financeiro && (
              <div className="bg-blue-50 p-4 rounded-lg mb-4">
                <h4 className="font-semibold mb-3">💰 Acerto Financeiro</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div><strong>Valor Hospedagem:</strong> R$ {checkoutValidacao.calculo_financeiro.valor_hospedagem?.toFixed(2)}</div>
                  <div><strong>Já Pago:</strong> R$ {checkoutValidacao.calculo_financeiro.valor_pago?.toFixed(2)}</div>
                  <div><strong>Consumos:</strong> R$ {checkoutValidacao.calculo_financeiro.valor_consumos?.toFixed(2)}</div>
                  <div><strong>Caução:</strong> R$ {checkoutValidacao.calculo_financeiro.caucao_cobrada?.toFixed(2)}</div>
                  <div><strong>Total Final:</strong> R$ {checkoutValidacao.calculo_financeiro.valor_total_final?.toFixed(2)}</div>
                  <div className={`font-bold ${
                    checkoutValidacao.calculo_financeiro.saldo >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    <strong>Saldo:</strong> R$ {checkoutValidacao.calculo_financeiro.saldo?.toFixed(2)}
                  </div>
                </div>
              </div>
            )}

            {/* Vistoria do Quarto */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">🔍 Vistoria do Quarto</h4>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={checkoutForm.vistoria_ok}
                    onChange={(e) => setCheckoutForm({...checkoutForm, vistoria_ok: e.target.checked})}
                    className="mr-2"
                  />
                  <span>Quarto em perfeitas condições</span>
                </label>
                
                {!checkoutForm.vistoria_ok && (
                  <div className="grid grid-cols-2 gap-4">
                    <textarea
                      placeholder="Descreva os danos encontrados"
                      value={checkoutForm.danos_encontrados}
                      onChange={(e) => setCheckoutForm({...checkoutForm, danos_encontrados: e.target.value})}
                      className="p-2 border rounded"
                      rows={3}
                    />
                    <input
                      type="number"
                      step="0.01"
                      placeholder="Valor dos danos (R$)"
                      value={checkoutForm.valor_danos}
                      onChange={(e) => setCheckoutForm({...checkoutForm, valor_danos: parseFloat(e.target.value) || 0})}
                      className="p-2 border rounded"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Consumos Finais */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">🥤 Consumos Finais</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Frigobar (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={checkoutForm.consumo_frigobar}
                    onChange={(e) => setCheckoutForm({...checkoutForm, consumo_frigobar: parseFloat(e.target.value) || 0})}
                    className="p-2 border rounded w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Serviços Extras (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={checkoutForm.servicos_extras}
                    onChange={(e) => setCheckoutForm({...checkoutForm, servicos_extras: parseFloat(e.target.value) || 0})}
                    className="p-2 border rounded w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Taxa Late Checkout (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={checkoutForm.taxa_late_checkout}
                    onChange={(e) => setCheckoutForm({...checkoutForm, taxa_late_checkout: parseFloat(e.target.value) || 0})}
                    className="p-2 border rounded w-full"
                  />
                </div>
              </div>
            </div>

            {/* Caução */}
            <div className="bg-yellow-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">💳 Devolução de Caução</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Valor a Devolver (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={checkoutForm.caucao_devolvida}
                    onChange={(e) => setCheckoutForm({...checkoutForm, caucao_devolvida: parseFloat(e.target.value) || 0})}
                    className="p-2 border rounded w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Valor Retido (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={checkoutForm.caucao_retida}
                    onChange={(e) => setCheckoutForm({...checkoutForm, caucao_retida: parseFloat(e.target.value) || 0})}
                    className="p-2 border rounded w-full"
                  />
                </div>
              </div>
              {checkoutForm.caucao_retida > 0 && (
                <textarea
                  placeholder="Motivo da retenção da caução"
                  value={checkoutForm.motivo_retencao}
                  onChange={(e) => setCheckoutForm({...checkoutForm, motivo_retencao: e.target.value})}
                  className="p-2 border rounded w-full mt-2"
                  rows={2}
                />
              )}
            </div>

            {/* Satisfação */}
            <div className="bg-purple-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">⭐ Avaliação da Hospedagem</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Nota (1-5)</label>
                  <select
                    value={checkoutForm.avaliacao_hospede}
                    onChange={(e) => setCheckoutForm({...checkoutForm, avaliacao_hospede: parseInt(e.target.value)})}
                    className="p-2 border rounded w-full"
                  >
                    <option value={5}>⭐⭐⭐⭐⭐ (5) Excelente</option>
                    <option value={4}>⭐⭐⭐⭐ (4) Muito Bom</option>
                    <option value={3}>⭐⭐⭐ (3) Bom</option>
                    <option value={2}>⭐⭐ (2) Regular</option>
                    <option value={1}>⭐ (1) Ruim</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Forma de Acerto</label>
                  <select
                    value={checkoutForm.forma_acerto}
                    onChange={(e) => setCheckoutForm({...checkoutForm, forma_acerto: e.target.value})}
                    className="p-2 border rounded w-full"
                  >
                    <option value="DINHEIRO">Dinheiro</option>
                    <option value="CARTAO">Cartão</option>
                    <option value="PIX">PIX</option>
                    <option value="TRANSFERENCIA">Transferência</option>
                  </select>
                </div>
              </div>
              <textarea
                placeholder="Comentários do hóspede (opcional)"
                value={checkoutForm.comentario_hospede}
                onChange={(e) => setCheckoutForm({...checkoutForm, comentario_hospede: e.target.value})}
                className="p-2 border rounded w-full mt-2"
                rows={2}
              />
            </div>

            <div className="flex gap-4">
              <button
                onClick={realizarCheckout}
                disabled={loading}
                className="flex-1 bg-green-600 text-white py-3 rounded font-semibold hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Processando...' : '✅ Finalizar Check-out'}
              </button>
              <button
                onClick={() => setShowCheckoutModal(false)}
                className="px-6 bg-gray-300 text-gray-700 py-3 rounded font-semibold hover:bg-gray-400"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Pagamento */}
      {showPagamentoModal && selectedReserva && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-green-800">💳 Pagamento - Cielo</h2>
              <button onClick={() => setShowPagamentoModal(false)} className="text-gray-500 hover:text-gray-700">
                ✕
              </button>
            </div>

            <div className="bg-green-50 p-4 rounded-lg mb-6">
              <h3 className="font-semibold text-green-800 mb-2">Reserva #{selectedReserva.codigo_reserva}</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><strong>Cliente:</strong> {selectedReserva.cliente_nome}</div>
                <div><strong>Quarto:</strong> {selectedReserva.quarto_numero}</div>
                <div><strong>Diárias:</strong> {selectedReserva.num_diarias || 0}</div>
                <div><strong>Valor Total:</strong> R$ {Number(selectedReserva.valor_total || 0).toFixed(2)}</div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Forma de Pagamento</label>
                <select
                  value={pagamentoForm.forma}
                  onChange={(e) => setPagamentoForm({...pagamentoForm, forma: e.target.value})}
                  className="w-full p-2 border rounded"
                >
                  <option value="CREDITO">Cartão de Crédito</option>
                  <option value="DEBITO">Cartão de Débito</option>
                  <option value="PIX">PIX</option>
                </select>
              </div>

              {(pagamentoForm.forma === 'CREDITO' || pagamentoForm.forma === 'DEBITO') && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-2">Número do Cartão</label>
                    <input
                      type="text"
                      placeholder="0000 0000 0000 0000"
                      value={pagamentoForm.numero}
                      onChange={(e) => setPagamentoForm({...pagamentoForm, numero: e.target.value})}
                      className="w-full p-2 border rounded"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Validade</label>
                      <input
                        type="text"
                        placeholder="MM/AA"
                        value={pagamentoForm.validade}
                        onChange={(e) => setPagamentoForm({...pagamentoForm, validade: e.target.value})}
                        className="w-full p-2 border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">CVV</label>
                      <input
                        type="text"
                        placeholder="123"
                        value={pagamentoForm.cvv}
                        onChange={(e) => setPagamentoForm({...pagamentoForm, cvv: e.target.value})}
                        className="w-full p-2 border rounded"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Nome no Cartão</label>
                    <input
                      type="text"
                      placeholder="Nome como está no cartão"
                      value={pagamentoForm.nome}
                      onChange={(e) => setPagamentoForm({...pagamentoForm, nome: e.target.value})}
                      className="w-full p-2 border rounded"
                    />
                  </div>
                </>
              )}
            </div>

            <div className="flex gap-4 mt-6">
              <button
                onClick={processarPagamento}
                disabled={loading}
                className="flex-1 bg-green-600 text-white py-3 rounded font-semibold hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Processando...' : '💳 Pagar'}
              </button>
              <button
                onClick={() => setShowPagamentoModal(false)}
                className="px-6 bg-gray-300 text-gray-700 py-3 rounded font-semibold hover:bg-gray-400"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Detalhes da Reserva */}
      {showDetalhesModal && selectedReserva && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-blue-800">📋 Detalhes da Reserva</h2>
              <button onClick={() => setShowDetalhesModal(false)} className="text-gray-500 hover:text-gray-700">
                ✕
              </button>
            </div>

            {/* Cabeçalho da Reserva */}
            <div className="bg-blue-50 p-4 rounded-lg mb-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold text-blue-800 mb-2">Reserva #{selectedReserva.codigo_reserva}</h3>
                  <p className="text-sm text-gray-600 flex items-center gap-2">
                    <strong>Status:</strong>
                    <StatusBadge status={selectedReserva.status} />
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600"><strong>Valor Total:</strong></p>
                  <p className="text-2xl font-bold text-green-600">R$ {Number(selectedReserva.valor_total || 0).toFixed(2)}</p>
                </div>
              </div>
            </div>

            {/* Informações do Cliente */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">👤 Informações do Cliente</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><strong>Nome:</strong> {selectedReserva.cliente_nome}</div>
                <div><strong>ID Cliente:</strong> {selectedReserva.cliente_id}</div>
              </div>
            </div>

            {/* Informações do Quarto */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">🏠 Informações do Quarto</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div><strong>Quarto:</strong> {selectedReserva.quarto_numero}</div>
                <div><strong>Tipo Suíte:</strong> {selectedReserva.tipo_suite || 'LUXO'}</div>
                <div><strong>Diárias:</strong> {selectedReserva.num_diarias || 0}</div>
              </div>
            </div>

            {/* Datas da Reserva */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">📅 Datas da Reserva</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <strong>Check-in Previsto:</strong><br/>
                  {selectedReserva.checkin_previsto ? new Date(selectedReserva.checkin_previsto).toLocaleString('pt-BR') : '-'}
                </div>
                <div>
                  <strong>Check-out Previsto:</strong><br/>
                  {selectedReserva.checkout_previsto ? new Date(selectedReserva.checkout_previsto).toLocaleString('pt-BR') : '-'}
                </div>
              </div>
            </div>

            {/* Valores */}
            <div className="bg-green-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">💰 Detalhes Financeiros</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div><strong>Valor Diária:</strong> R$ {Number(selectedReserva.valor_diaria || 0).toFixed(2)}</div>
                <div><strong>Nº Diárias:</strong> {selectedReserva.num_diarias || 0}</div>
                <div><strong>Valor Total:</strong> R$ {Number(selectedReserva.valor_total || 0).toFixed(2)}</div>
              </div>
            </div>

            {/* Informações de Sistema */}
            <div className="bg-yellow-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-3">⚙️ Informações de Sistema</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><strong>ID Reserva:</strong> {selectedReserva.id}</div>
                <div><strong>Criado em:</strong> {selectedReserva.created_at ? new Date(selectedReserva.created_at).toLocaleString('pt-BR') : '-'}</div>
                <div><strong>Atualizado em:</strong> {selectedReserva.updated_at ? new Date(selectedReserva.updated_at).toLocaleString('pt-BR') : '-'}</div>
                <div><strong>Criado por:</strong> {selectedReserva.criado_por || '-'}</div>
              </div>
            </div>

            {/* Ações Rápidas */}
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-3">🚀 Ações Rápidas</h4>
              <div className="flex flex-wrap gap-2">
                {podePagar(selectedReserva) && (
                  <button
                    onClick={() => {
                      setShowDetalhesModal(false)
                      handlePagar(selectedReserva)
                    }}
                    className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700"
                  >
                    💳 Pagar
                  </button>
                )}
                {podeCheckin(selectedReserva) && (
                  <button
                    onClick={() => {
                      setShowDetalhesModal(false)
                      validarCheckin(selectedReserva)
                    }}
                    className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
                  >
                    🔑 Check-in
                  </button>
                )}
                {podeCheckout(selectedReserva) && (
                  <button
                    onClick={() => {
                      setShowDetalhesModal(false)
                      validarCheckout(selectedReserva)
                    }}
                    className="bg-purple-600 text-white px-4 py-2 rounded text-sm hover:bg-purple-700"
                  >
                    🏃 Checkout
                  </button>
                )}
                {podeCancelar(selectedReserva) && (
                  <button
                    onClick={() => {
                      setShowDetalhesModal(false)
                      handleCancelar(selectedReserva.id)
                    }}
                    className="bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700"
                  >
                    ❌ Cancelar
                  </button>
                )}
              </div>
            </div>

            <div className="flex gap-4 mt-6">
              <button
                onClick={() => setShowDetalhesModal(false)}
                className="flex-1 bg-gray-600 text-white py-3 rounded font-semibold hover:bg-gray-700"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Criação/Edição de Quarto */}
      {showQuartoModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">
              {editingQuarto ? '✏️ Editar Quarto' : '➕ Novo Quarto'}
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Número do Quarto
                </label>
                <input
                  type="text"
                  value={quartoForm.numero}
                  onChange={(e) => updateQuartoForm('numero', e.target.value)}
                  className="w-full p-2 border rounded-lg"
                  placeholder="Ex: 101, 201, 301"
                  disabled={!!editingQuarto}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Suíte
                </label>
                <select
                  value={quartoForm.tipo_suite}
                  onChange={(e) => updateQuartoForm('tipo_suite', e.target.value)}
                  className="w-full p-2 border rounded-lg"
                >
                  <option value="LUXO">Luxo</option>
                  <option value="MASTER">Master</option>
                  <option value="REAL">Real</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={quartoForm.status}
                  onChange={(e) => updateQuartoForm('status', e.target.value)}
                  className="w-full p-2 border rounded-lg"
                >
                  <option value="LIVRE">Livre</option>
                  <option value="OCUPADO">Ocupado</option>
                  <option value="MANUTENCAO">Manutenção</option>
                  <option value="BLOQUEADO">Bloqueado</option>
                </select>
              </div>
            </div>
            
            <div className="flex gap-2 mt-6">
              <button
                onClick={handleCreateQuarto}
                disabled={loading}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Salvando...' : (editingQuarto ? 'Atualizar' : 'Criar')}
              </button>
              <button
                onClick={() => {
                  setShowQuartoModal(false)
                  setEditingQuarto(null)
                  setQuartoForm({ numero: '', tipo_suite: 'LUXO', status: 'LIVRE' })
                }}
                className="px-4 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Histórico do Quarto */}
      {showHistoricoModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">
                📋 Histórico do Quarto {historicoQuarto?.numero}
              </h3>
              <button
                onClick={() => setShowHistoricoModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            {loadingHistorico ? (
              <div className="flex justify-center items-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <>
                {/* Informações do Quarto */}
                <div className="bg-gray-50 p-4 rounded-lg mb-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Número</p>
                      <p className="font-semibold">{historicoQuarto?.numero}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Tipo</p>
                      <p className="font-semibold">{historicoQuarto?.tipo_suite}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Status</p>
                      <p className="font-semibold">{historicoQuarto?.status}</p>
                    </div>
                  </div>
                </div>

                {/* Estatísticas */}
                {historicoQuarto?.estatisticas && (
                  <div className="bg-blue-50 p-4 rounded-lg mb-4">
                    <h4 className="font-semibold mb-3">📊 Estatísticas</h4>
                    <div className="grid grid-cols-4 gap-4 text-center">
                      <div>
                        <p className="text-2xl font-bold text-blue-600">{historicoQuarto.estatisticas.total_reservas}</p>
                        <p className="text-sm text-gray-600">Total Reservas</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-green-600">{historicoQuarto.estatisticas.concluidas}</p>
                        <p className="text-sm text-gray-600">Concluídas</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-red-600">{historicoQuarto.estatisticas.canceladas}</p>
                        <p className="text-sm text-gray-600">Canceladas</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-orange-600">{historicoQuarto.estatisticas.taxa_ocupacao_90d}%</p>
                        <p className="text-sm text-gray-600">Taxa Ocupação</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Histórico de Reservas */}
                <div className="bg-white border rounded-lg">
                  <h4 className="font-semibold p-4 border-b">📅 Histórico de Reservas</h4>
                  <div className="max-h-96 overflow-y-auto">
                    {historicoQuarto?.historico?.length > 0 ? (
                      <div className="divide-y">
                        {historicoQuarto.historico.map((reserva, index) => (
                          <div key={index} className="p-4 hover:bg-gray-50">
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                                    {reserva.status}
                                  </span>
                                  <span className="text-sm text-gray-500">
                                    #{reserva.id}
                                  </span>
                                </div>
                                <div className="space-y-1">
                                  <p className="text-sm">
                                    <span className="font-medium">Cliente:</span> {reserva.cliente?.nome || 'N/A'}
                                  </p>
                                  {reserva.data_checkin && (
                                    <p className="text-sm">
                                      <span className="font-medium">Check-in:</span>{' '}
                                      {new Date(reserva.data_checkin).toLocaleDateString('pt-BR')} às{' '}
                                      {new Date(reserva.data_checkin).toLocaleTimeString('pt-BR')}
                                    </p>
                                  )}
                                  {reserva.data_checkout && (
                                    <p className="text-sm">
                                      <span className="font-medium">Check-out:</span>{' '}
                                      {new Date(reserva.data_checkout).toLocaleDateString('pt-BR')} às{' '}
                                      {new Date(reserva.data_checkout).toLocaleTimeString('pt-BR')}
                                    </p>
                                  )}
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="text-sm font-semibold text-gray-900">
                                  R$ {reserva.valor_total || '0.00'}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-8 text-center text-gray-500">
                        <p>Nenhuma reserva encontrada no histórico deste quarto</p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
            
            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowHistoricoModal(false)}
                className="flex-1 bg-gray-600 text-white py-2 rounded-lg hover:bg-gray-700"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Upload de Comprovante */}
      {showUploadComprovanteModal && selectedReserva && selectedPagamento && (
        <UploadComprovanteModal
          pagamento={selectedPagamento}
          reserva={selectedReserva}
          onClose={() => {
            setShowUploadComprovanteModal(false)
            setSelectedPagamento(null)
            setSelectedReserva(null)
          }}
          onSuccess={handleUploadSuccess}
        />
      )}

      {/* Modal de Escolha de Pagamento */}
      {showModalEscolhaPagamento && selectedReserva && (
        <ModalEscolhaPagamento
          reserva={selectedReserva}
          onClose={() => {
            setShowModalEscolhaPagamento(false)
            setSelectedReserva(null)
          }}
          onSuccess={async () => {
            setShowModalEscolhaPagamento(false)
            setSelectedReserva(null)
            await loadReservas()
            toast.success('✅ Operação concluída com sucesso!')
          }}
        />
      )}

      <ToastContainer />
    </div>
  )
}
