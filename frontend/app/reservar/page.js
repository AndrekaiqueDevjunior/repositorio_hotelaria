'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import {
  ArrowLeft,
  CalendarDays,
  ChevronDown,
  Crown,
  Gift,
  Mail,
  Phone,
  Search,
  ShieldCheck,
  Star,
  User,
} from 'lucide-react'
import { api } from '../../lib/api'
import GoldParticles from '@/components/GoldParticles'

const initialCustomerAuth = {
  status: 'idle',
  customer: null,
  otpId: '',
  otpCode: '',
  accessToken: '',
  expiresInSeconds: 0,
}

export default function Reservar() {
  const router = useRouter()
  
  // Estados do fluxo
  const [step, setStep] = useState(1) // 1: Datas, 2: Quarto, 3: Dados, 4: Pagamento, 5: Confirmação
  const [loading, setLoading] = useState(false)
  
  // Dados da busca
  const [searchData, setSearchData] = useState({
    data_checkin: '',
    data_checkout: '',
    num_hospedes: 1
  })
  
  // Quartos disponíveis
  const [tiposDisponiveis, setTiposDisponiveis] = useState([])
  const [numDiarias, setNumDiarias] = useState(0)
  
  // Quarto selecionado
  const [quartoSelecionado, setQuartoSelecionado] = useState(null)
  
  // Dados do hóspede
  const [hospedeData, setHospedeData] = useState({
    nome_completo: '',
    documento: '',
    email: '',
    telefone: '',
    num_hospedes: 1,
    num_criancas: 0,
    observacoes: ''
  })
  const [customerAuth, setCustomerAuth] = useState(initialCustomerAuth)
  const [authLoading, setAuthLoading] = useState(false)
  
  // Pagamento
  const [metodoPagamento, setMetodoPagamento] = useState('balcao')
  
  // Reserva confirmada
  const [reservaConfirmada, setReservaConfirmada] = useState(null)
  
  // Definir data mínima (hoje)
  const today = new Date().toISOString().split('T')[0]
  const onlyDigits = (value) => (value || '').replace(/\D/g, '')
  const cpfLimpo = onlyDigits(hospedeData.documento)
  const telefoneLimpo = onlyDigits(hospedeData.telefone)
  const isCustomerAuthenticated = Boolean(customerAuth.accessToken && customerAuth.customer)

  const isValidCPF = (value) => {
    const cpf = onlyDigits(value)
    if (cpf.length !== 11 || cpf === cpf[0]?.repeat(11)) return false

    const calcDigit = (base) => {
      const sum = base
        .split('')
        .reduce((total, digit, index) => total + Number(digit) * (base.length + 1 - index), 0)
      const rest = (sum * 10) % 11
      return rest === 10 ? '0' : String(rest)
    }

    return cpf.slice(9) === `${calcDigit(cpf.slice(0, 9))}${calcDigit(cpf.slice(0, 10))}`
  }

  const getApiErrorMessage = (error, fallback) => {
    const detail = error?.response?.data?.detail
    if (Array.isArray(detail)) return detail[0]?.msg || fallback
    return detail || error?.message || fallback
  }

  const resetCustomerAuth = () => {
    setCustomerAuth({ ...initialCustomerAuth })
  }

  const applyCustomerToForm = (customer) => {
    setHospedeData((current) => ({
      ...current,
      nome_completo: customer?.nome_completo || current.nome_completo,
      documento: formatCPF(customer?.documento || current.documento),
      email: customer?.email || current.email,
      telefone: formatTelefone(customer?.telefone || current.telefone),
    }))
  }

  const handleCpfChange = (value) => {
    setHospedeData((current) => ({
      ...current,
      documento: formatCPF(value),
    }))
    resetCustomerAuth()
  }
  
  // Buscar disponibilidade
  const buscarDisponibilidade = async (options = {}) => {
    const { silent = false, keepStep = false } = options
    if (!searchData.data_checkin || !searchData.data_checkout) {
      if (!silent) toast.warning('Selecione as datas de check-in e check-out')
      return
    }
    
    if (searchData.data_checkout <= searchData.data_checkin) {
      if (!silent) toast.warning('Data de check-out deve ser posterior ao check-in')
      return
    }
    
    if (!silent) setLoading(true)
    
    try {
      const response = await api.get(`/public/quartos/disponiveis`, {
        params: {
          data_checkin: searchData.data_checkin,
          data_checkout: searchData.data_checkout
        }
      })
      
      const data = response.data
      
      if (data.success) {
        const tipos = data.tipos_disponiveis || []
        setTiposDisponiveis(tipos)
        setNumDiarias(data.num_diarias || 0)

        if (!silent) {
          if (tipos.length === 0) {
            toast.info('Não há quartos disponíveis para as datas selecionadas')
          } else {
            toast.success(`${data.total_quartos_disponiveis} quartos disponíveis!`)
            if (!keepStep) setStep(2)
          }
        }
      } else {
        if (!silent) toast.error(data.detail || 'Erro ao buscar disponibilidade')
      }
    } catch (error) {
      console.error('Erro:', error)
      if (!silent) toast.error('Erro ao conectar com o servidor')
    } finally {
      if (!silent) setLoading(false)
    }
  }

  // Atualizar disponibilidade "em tempo real" durante seleção (polling)
  useEffect(() => {
    if (step !== 2) return
    if (!searchData.data_checkin || !searchData.data_checkout) return

    const intervalMs = 10000
    const id = setInterval(() => {
      buscarDisponibilidade({ silent: true, keepStep: true })
    }, intervalMs)

    return () => clearInterval(id)
  }, [step, searchData.data_checkin, searchData.data_checkout])
  
  // Selecionar quarto
  const selecionarQuarto = (tipo, quarto) => {
    setQuartoSelecionado({
      numero: quarto.numero,
      tipo: tipo.tipo,
      preco_diaria: tipo.preco_diaria,
      preco_total: tipo.preco_total
    })
    setStep(3)
  }

  const buscarCadastroCpf = async () => {
    if (!isValidCPF(cpfLimpo)) {
      toast.warning('Informe um CPF válido para autenticar a reserva')
      return
    }

    setAuthLoading(true)
    try {
      const response = await api.get(`/customers/${cpfLimpo}`)
      const customer = response.data
      applyCustomerToForm(customer)
      setCustomerAuth({
        ...initialCustomerAuth,
        status: 'found',
        customer,
      })
      toast.success('Cadastro encontrado. Envie o código por WhatsApp.')
    } catch (error) {
      if (error?.response?.status === 404) {
        setCustomerAuth({
          ...initialCustomerAuth,
          status: 'not_found',
        })
        setHospedeData((current) => ({
          ...current,
          documento: formatCPF(cpfLimpo),
        }))
        toast.info('CPF ainda não cadastrado. Complete seus dados para criar o cadastro.')
      } else {
        toast.error(getApiErrorMessage(error, 'Erro ao consultar CPF'))
      }
    } finally {
      setAuthLoading(false)
    }
  }

  const criarCadastroCustomer = async () => {
    if (!isValidCPF(cpfLimpo)) {
      toast.warning('CPF inválido')
      return
    }
    if (!hospedeData.nome_completo || !hospedeData.email || !hospedeData.telefone) {
      toast.warning('Preencha nome, email e telefone para criar o cadastro')
      return
    }
    if (!hospedeData.email.includes('@')) {
      toast.warning('Email inválido')
      return
    }
    if (telefoneLimpo.length < 10) {
      toast.warning('Telefone inválido')
      return
    }

    setAuthLoading(true)
    try {
      const response = await api.post('/customers/create', {
        nome_completo: hospedeData.nome_completo.trim(),
        documento: cpfLimpo,
        email: hospedeData.email.trim(),
        telefone: telefoneLimpo,
      })
      const customer = response.data
      applyCustomerToForm(customer)
      setCustomerAuth({
        ...initialCustomerAuth,
        status: 'found',
        customer,
      })
      toast.success('Cadastro criado. Agora envie o código por WhatsApp.')
    } catch (error) {
      if (error?.response?.status === 409) {
        toast.info('CPF já cadastrado. Vou buscar seus dados para autenticação.')
        await buscarCadastroCpf()
      } else {
        toast.error(getApiErrorMessage(error, 'Erro ao criar cadastro'))
      }
    } finally {
      setAuthLoading(false)
    }
  }

  const enviarOtpCustomer = async () => {
    if (!customerAuth.customer) {
      toast.warning('Consulte ou crie o cadastro antes de enviar o código')
      return
    }

    setAuthLoading(true)
    try {
      const response = await api.post('/auth/otp/generate', {
        cpf: cpfLimpo,
      })
      setCustomerAuth((current) => ({
        ...current,
        status: 'otp_sent',
        otpId: response.data.otp_id,
        otpCode: '',
        accessToken: '',
        expiresInSeconds: response.data.expires_in_seconds || 300,
      }))
      toast.success('Código enviado pelo WhatsApp')
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Erro ao enviar código por WhatsApp'))
    } finally {
      setAuthLoading(false)
    }
  }

  const validarOtpCustomer = async () => {
    if (!customerAuth.otpId) {
      toast.warning('Envie o código por WhatsApp antes de validar')
      return
    }
    if (!/^\d{6}$/.test(customerAuth.otpCode)) {
      toast.warning('Digite o código de 6 dígitos')
      return
    }

    setAuthLoading(true)
    try {
      const response = await api.post('/auth/otp/validate', {
        otp_id: customerAuth.otpId,
        code: customerAuth.otpCode,
      })
      const customer = response.data.customer || customerAuth.customer
      applyCustomerToForm(customer)
      setCustomerAuth((current) => ({
        ...current,
        status: 'verified',
        customer,
        accessToken: response.data.access_token,
      }))
      toast.success('Cadastro autenticado. Você pode continuar a reserva.')
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Erro ao validar código'))
    } finally {
      setAuthLoading(false)
    }
  }
  
  // Criar reserva
  const criarReserva = async () => {
    if (!isCustomerAuthenticated) {
      toast.warning('Autentique seu cadastro por WhatsApp antes de confirmar a reserva')
      setStep(3)
      return
    }

    // Validações
    if (!hospedeData.nome_completo || !hospedeData.documento || !hospedeData.email || !hospedeData.telefone) {
      toast.warning('Preencha todos os campos obrigatórios')
      return
    }
    
    if (!isValidCPF(cpfLimpo)) {
      toast.warning('CPF inválido')
      return
    }

    if (onlyDigits(customerAuth.customer?.documento) !== cpfLimpo) {
      toast.warning('O CPF autenticado não corresponde ao CPF informado')
      setStep(3)
      return
    }
    
    // Validar email
    if (!hospedeData.email.includes('@')) {
      toast.warning('Email inválido')
      return
    }
    
    setLoading(true)
    
    try {
      const payload = {
        nome_completo: hospedeData.nome_completo,
        documento: cpfLimpo,
        email: hospedeData.email,
        telefone: hospedeData.telefone.replace(/\D/g, ''),
        quarto_numero: quartoSelecionado.numero,
        tipo_suite: quartoSelecionado.tipo,
        data_checkin: searchData.data_checkin,
        data_checkout: searchData.data_checkout,
        num_hospedes: hospedeData.num_hospedes,
        num_criancas: hospedeData.num_criancas,
        observacoes: hospedeData.observacoes,
        metodo_pagamento: metodoPagamento,
        customer_auth_token: customerAuth.accessToken
      }
      
      const response = await api.post('/public/reservas', payload)
      
      const data = response.data
      
      if (data.success) {
        setReservaConfirmada(data)
        toast.success('🎉 Reserva confirmada com sucesso!')
        setStep(5)
      } else {
        // Tratamento específico de erros
        const errorMessage = data.detail || 'Erro ao criar reserva'
        
        if (errorMessage.includes('Quarto já reservado')) {
          toast.error('❌ Este quarto já está reservado para o período selecionado. Por favor, escolha outro quarto.')
        } else if (errorMessage.includes('CLIENTE JÁ POSSUI RESERVA ATIVA')) {
          toast.error('❌ Você já possui uma reserva ativa para este período. Verifique suas reservas existentes.')
        } else if (errorMessage.includes('CPF inválido')) {
          toast.error('❌ CPF inválido. Verifique o número digitado.')
        } else if (errorMessage.includes('Email inválido')) {
          toast.error('❌ Email inválido. Verifique o endereço digitado.')
        } else {
          toast.error('❌ ' + errorMessage)
        }
      }
    } catch (error) {
      console.error('Erro:', error)
      
      // Tratamento de erros de rede
      if (error.code === 'ECONNREFUSED') {
        toast.error('❌ Servidor indisponível. Tente novamente em alguns instantes.')
      } else if ([401, 403].includes(error.response?.status)) {
        toast.error('❌ Autenticação expirada ou CPF divergente. Valide o código novamente.')
        setCustomerAuth((current) => ({
          ...current,
          status: current.customer ? 'found' : 'idle',
          otpId: '',
          otpCode: '',
          accessToken: '',
        }))
        setStep(3)
      } else if (error.response?.status === 400) {
        toast.error('❌ Dados inválidos. Verifique as informações e tente novamente.')
      } else if (error.response?.status === 500) {
        toast.error('❌ Erro interno do servidor. Tente novamente.')
      } else {
        toast.error('❌ Erro ao conectar com o servidor. Tente novamente.')
      }
    } finally {
      setLoading(false)
    }
  }
  
  // Formatar CPF
  const formatCPF = (value) => {
    const numbers = value.replace(/\D/g, '').substring(0, 11)
    if (numbers.length <= 3) return numbers
    if (numbers.length <= 6) return `${numbers.slice(0, 3)}.${numbers.slice(3)}`
    if (numbers.length <= 9) return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`
    return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9)}`
  }
  
  // Formatar telefone
  const formatTelefone = (value) => {
    const numbers = value.replace(/\D/g, '').substring(0, 11)
    if (numbers.length <= 2) return numbers
    if (numbers.length <= 7) return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7)}`
  }
  
  // Descrição do tipo de suíte
  const getDescricaoSuite = (tipo) => {
    const descricoes = {
      'LUXO': {
        titulo: 'Suíte Luxo',
        descricao: 'Conforto e elegância com vista privilegiada',
        amenidades: ['Ar condicionado', 'TV 32"', 'Frigobar', 'Wi-Fi', 'Varanda', 'Secador de cabelo']
      },
      'MASTER': {
        titulo: 'Suíte Master',
        descricao: 'Espaço amplo com acabamentos premium',
        amenidades: ['Ar condicionado Split', 'TV 50"', 'Frigobar completo', 'Wi-Fi', 'Varanda', 'Secador de cabelo']
      },
      'REAL': {
        titulo: 'Suíte Real',
        descricao: 'O máximo em luxo e exclusividade',
        amenidades: ['Ar condicionado Split', 'TV 55" Smart', 'Frigobar premium', 'Wi-Fi 5G', 'Terraço privativo', 'Banheira', 'Secador de cabelo']
      }
    }
    return descricoes[tipo] || { titulo: tipo, descricao: '', amenidades: [] }
  }

  const reservationSteps = [
    { num: 1, label: 'Datas' },
    { num: 2, label: 'Quarto' },
    { num: 3, label: 'Dados' },
    { num: 4, label: 'Pagamento' },
    { num: 5, label: 'Confirmação' },
  ]
  const canEditCustomerFields = customerAuth.status === 'not_found'
  const authBadge = {
    idle: { label: 'Pendente', className: 'border-blue-200 bg-blue-100 text-blue-800' },
    not_found: { label: 'Novo cadastro', className: 'border-amber-200 bg-amber-100 text-amber-800' },
    found: { label: 'Cadastro localizado', className: 'border-blue-200 bg-blue-100 text-blue-800' },
    otp_sent: { label: 'Código enviado', className: 'border-purple-200 bg-purple-100 text-purple-800' },
    verified: { label: 'Autenticado', className: 'border-green-200 bg-green-100 text-green-800' },
  }[customerAuth.status] || { label: 'Pendente', className: 'border-blue-200 bg-blue-100 text-blue-800' }

  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-[#050403] text-white">
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[#050403]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(218,166,55,0.18),transparent_22rem),radial-gradient(circle_at_12%_34%,rgba(157,91,8,0.22),transparent_18rem),radial-gradient(circle_at_88%_28%,rgba(246,198,55,0.11),transparent_16rem),radial-gradient(circle_at_50%_82%,rgba(92,36,145,0.12),transparent_18rem)]" />
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(0,0,0,0.16)_0%,rgba(5,4,3,0.86)_44%,#050403_100%)]" />
      </div>

      <GoldParticles />

      <header className="relative z-40 border-b border-[#b9821b]/35 bg-black/42 backdrop-blur-[2px]">
        <div className="mx-auto grid w-full max-w-[820px] grid-cols-[72px_minmax(0,1fr)_72px] items-start px-4 py-5 sm:grid-cols-[88px_minmax(0,1fr)_88px] sm:px-8 sm:py-7">
          <button
            type="button"
            aria-label="Voltar"
            onClick={() => router.push('/entrar-jornada-real')}
            className="mt-1 grid h-16 w-16 place-items-center rounded-full border border-white/15 bg-black/24 text-white/80 shadow-[inset_0_0_14px_rgba(255,255,255,0.04)] transition hover:border-[#e5b84a]/60 hover:text-[#e5b84a]"
          >
            <ArrowLeft size={34} strokeWidth={1.6} />
          </button>

          <div className="min-w-0 justify-self-center text-center">
            <img
              src="/images/logo-jornada-real.png"
              alt="Hotel Real Cabo Frio"
              className="mx-auto h-auto w-[230px] max-w-full object-contain drop-shadow-[0_8px_18px_rgba(0,0,0,0.9)] sm:w-[330px]"
            />
            <div className="mx-auto mt-4 w-fit max-w-full space-y-3 font-serif text-[0.76rem] uppercase tracking-wide text-[#f4ead2] sm:text-[1.08rem]">
              <p className="flex items-center justify-center gap-4">
                <Phone size={22} className="shrink-0 text-[#d7a52c] drop-shadow-[0_0_8px_rgba(215,165,44,0.7)]" />
                <span>(22) 2648-5900</span>
              </p>
              <p className="flex items-center justify-center gap-4 break-all leading-snug">
                <Mail size={22} className="shrink-0 text-[#d7a52c] drop-shadow-[0_0_8px_rgba(215,165,44,0.7)]" />
                <span>contato@hotelrealcabofrio.com.br</span>
              </p>
            </div>
          </div>

          <div aria-hidden="true" />
        </div>
      </header>

      {/* Header */}
      <header className="hidden">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl sm:text-4xl">🏨</span>
            <div>
              <h1 className="text-xl font-bold text-white sm:text-2xl">Hotel Real</h1>
              <p className="text-sm text-yellow-400">Cabo Frio</p>
            </div>
          </div>
          <div className="space-y-1 text-left text-xs text-white/80 sm:text-right sm:text-sm">
            <p className="break-words">📞 (22) 2648-5900</p>
            <p className="break-all">📧 contato@hotelrealcabofrio.com.br</p>
          </div>
        </div>
      </header>
      
      <div className="relative z-40 mx-auto w-full max-w-[820px] px-4 py-5 sm:px-8">
        <div className="grid grid-cols-5 gap-2 border-b border-[#b9821b]/25 pb-5">
          {reservationSteps.map((s) => (
            <div key={s.num} className="flex flex-col items-center gap-2">
              <div className={`grid h-14 w-14 place-items-center rounded-full border font-serif text-2xl font-bold transition-all sm:h-[72px] sm:w-[72px] sm:text-3xl ${
                step >= s.num
                  ? 'border-[#fff0ad] bg-[radial-gradient(circle_at_30%_22%,#fff3b4,#d79b22_58%,#8c5706)] text-[#1e1004] shadow-[0_0_22px_rgba(235,190,75,0.7)]'
                  : 'border-[#9f721f]/38 bg-black/28 text-white/38'
              }`}>
                {step > s.num ? '✓' : s.num}
              </div>
              <span className={`font-serif text-[0.52rem] font-bold uppercase leading-none sm:text-[1rem] ${
                step >= s.num ? 'text-[#e5b84a]' : 'text-white/78'
              }`}>
                {s.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Progress Steps */}
      <div className="hidden">
        <div className="mb-6 grid grid-cols-5 items-start gap-2 sm:mb-8 sm:flex sm:items-center sm:justify-between">
          {[
            { num: 1, label: 'Datas' },
            { num: 2, label: 'Quarto' },
            { num: 3, label: 'Dados' },
            { num: 4, label: 'Pagamento' },
            { num: 5, label: 'Confirmação' }
          ].map((s, i) => (
            <div key={s.num} className="flex flex-col items-center gap-2 sm:flex-row sm:items-center sm:gap-0">
              <div className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold transition-all sm:h-10 sm:w-10 sm:text-base ${
                step >= s.num 
                  ? 'border border-[#fff0b8]/45 bg-gradient-to-b from-[#ffe89a] via-[#e7b938] to-[#bf7d0e] text-[#241102] shadow-[0_0_18px_rgba(212,175,55,0.25)]' 
                  : 'border border-[#d4af37]/20 bg-[#2a1814]/70 text-[#f8e9c2]/55'
              }`}>
                {step > s.num ? '✓' : s.num}
              </div>
              <span className={`text-center text-[10px] font-semibold uppercase tracking-[0.14em] sm:ml-2 sm:text-sm sm:normal-case sm:tracking-normal ${step >= s.num ? 'text-yellow-400' : 'text-white/60'}`}>
                {s.label}
              </span>
              {i < 4 && (
                <div className={`hidden h-1 w-8 rounded sm:mx-2 sm:block sm:w-16 ${step > s.num ? 'bg-gradient-to-r from-[#f7d878] via-[#d8a83b] to-[#8d5a14]' : 'bg-[#6d5846]/45'}`} />
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* Content */}
      <main className="relative z-30 mx-auto w-full max-w-[820px] flex-1 px-4 pb-12 sm:px-8">
        
        {/* Step 1: Datas */}
        {step === 1 && (
          <div>
          <div className="overflow-hidden rounded-[22px] border border-[#8b651c]/70 bg-black/64 shadow-[0_0_36px_rgba(0,0,0,0.62),inset_0_0_28px_rgba(229,184,74,0.06)] backdrop-blur-[2px]">
            <div className="px-5 pb-5 pt-8 text-center sm:px-9 sm:pt-9">
              <h2 className="font-serif text-[2rem] font-bold uppercase leading-none tracking-wide text-[#e5b84a] drop-shadow-[0_0_10px_rgba(229,184,74,0.35)] sm:text-[2.4rem]">
                Encontre Sua Data Ideal
              </h2>
              <div className="mx-auto mt-5 flex w-[78%] items-center justify-center gap-2 text-[#d7a52c]">
                <span className="h-px flex-1 bg-gradient-to-r from-transparent via-[#8e651b] to-[#d7a52c]" />
                <span className="h-2 w-2 rotate-45 border border-[#d7a52c]" />
                <span className="h-px flex-1 bg-gradient-to-l from-transparent via-[#8e651b] to-[#d7a52c]" />
              </div>
              <p className="mt-5 text-xl text-[#f4ead2] sm:text-2xl">Escolha as datas da sua estadia</p>
            </div>

            <div className="mx-4 rounded-[24px] border border-white/10 bg-[#120d09]/72 p-5 shadow-[inset_0_0_18px_rgba(255,255,255,0.03)] sm:mx-9 sm:p-7">
              <div className="grid gap-6">
                <label className="grid grid-cols-[74px_1fr] items-center gap-4 border-b border-white/10 pb-6">
                  <span className="grid h-14 w-14 place-items-center rounded-full border border-[#9f721f]/65 bg-black/30 text-[#e5b84a] shadow-[0_0_14px_rgba(229,184,74,0.22)]">
                    <CalendarDays size={30} strokeWidth={1.7} />
                  </span>
                  <span className="min-w-0">
                    <span className="block font-serif text-xl font-bold uppercase text-[#f4ead2]">Check-in</span>
                    <span className="relative mt-2 block">
                      <input
                        type="date"
                        min={today}
                        value={searchData.data_checkin}
                        onChange={(e) => setSearchData({ ...searchData, data_checkin: e.target.value })}
                        className="royal-date-input peer w-full border-0 border-b border-white/10 bg-transparent py-2 pr-12 text-2xl uppercase text-[#f4ead2] outline-none [color-scheme:dark] focus:border-[#e5b84a]"
                      />
                      <CalendarDays className="hidden" size={30} />
                    </span>
                    <span className="mt-3 block text-lg text-[#c7b99b]">A partir das <strong className="text-[#e5b84a]">12:00</strong></span>
                  </span>
                </label>

                <label className="grid grid-cols-[74px_1fr] items-center gap-4 border-b border-white/10 pb-6">
                  <span className="grid h-14 w-14 place-items-center rounded-full border border-[#9f721f]/65 bg-black/30 text-[#e5b84a] shadow-[0_0_14px_rgba(229,184,74,0.22)]">
                    <CalendarDays size={30} strokeWidth={1.7} />
                  </span>
                  <span className="min-w-0">
                    <span className="block font-serif text-xl font-bold uppercase text-[#f4ead2]">Check-out</span>
                    <span className="relative mt-2 block">
                      <input
                        type="date"
                        min={searchData.data_checkin || today}
                        value={searchData.data_checkout}
                        onChange={(e) => setSearchData({ ...searchData, data_checkout: e.target.value })}
                        className="royal-date-input w-full border-0 border-b border-white/10 bg-transparent py-2 pr-12 text-2xl uppercase text-[#f4ead2] outline-none [color-scheme:dark] focus:border-[#e5b84a]"
                      />
                      <CalendarDays className="hidden" size={30} />
                    </span>
                    <span className="mt-3 block text-lg text-[#c7b99b]">Até as <strong className="text-[#e5b84a]">11:00</strong></span>
                  </span>
                </label>

                <label className="grid grid-cols-[74px_1fr] items-center gap-4">
                  <span className="grid h-14 w-14 place-items-center rounded-full border border-[#9f721f]/65 bg-black/30 text-[#e5b84a] shadow-[0_0_14px_rgba(229,184,74,0.22)]">
                    <User size={30} strokeWidth={1.7} />
                  </span>
                  <span className="min-w-0">
                    <span className="block font-serif text-xl font-bold uppercase text-[#f4ead2]">Hóspedes</span>
                    <span className="relative mt-3 block">
                      <select
                        value={searchData.num_hospedes}
                        onChange={(e) => setSearchData({ ...searchData, num_hospedes: parseInt(e.target.value) })}
                        className="w-full appearance-none rounded-xl border border-white/12 bg-[#080604] px-5 py-4 text-2xl text-[#f4ead2] outline-none [color-scheme:dark] focus:border-[#e5b84a]"
                      >
                        {[1, 2, 3, 4, 5, 6].map(n => (
                          <option key={n} value={n}>{n} {n === 1 ? 'hóspede' : 'hóspedes'}</option>
                        ))}
                      </select>
                      <ChevronDown className="pointer-events-none absolute right-5 top-1/2 -translate-y-1/2 text-white/70" size={28} />
                    </span>
                  </span>
                </label>
              </div>

              <button
                onClick={buscarDisponibilidade}
                disabled={loading}
                className="mt-7 grid min-h-[76px] w-full grid-cols-[46px_minmax(0,1fr)_42px] items-center gap-2 rounded-[28px] border border-[#fff0ad]/65 bg-[linear-gradient(180deg,#fff0ad_0%,#e7b943_48%,#a86608_100%)] px-4 font-serif text-[0.78rem] font-bold uppercase tracking-wide text-[#160d04] shadow-[0_14px_28px_rgba(0,0,0,0.48),0_0_28px_rgba(229,184,74,0.4),inset_0_1px_0_rgba(255,255,255,0.5)] transition hover:scale-[1.01] disabled:opacity-55 sm:grid-cols-[58px_minmax(0,1fr)_48px] sm:gap-4 sm:px-5 sm:text-[1.45rem]"
              >
                <span className="grid h-11 w-11 place-items-center justify-self-start rounded-full border-2 border-[#1d1205]/70 sm:h-14 sm:w-14">
                  <Search size={27} strokeWidth={1.8} />
                </span>
                <span className="min-w-0 text-center leading-tight">{loading ? 'Buscando...' : 'Verificar Disponibilidade'}</span>
                <img className="jr-button-crest justify-self-end" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
              </button>
            </div>

            <div className="mt-5 border-t border-[#8b651c]/45 px-5 py-5 sm:px-7">
              <div className="grid grid-cols-3 divide-x divide-white/12 rounded-[20px] border border-white/10 bg-black/22 py-4 text-center">
                {[
                  { icon: ShieldCheck, title: 'Reserva Segura', text: 'Ambiente 100% protegido' },
                  { icon: Gift, title: 'Melhor Preço', text: 'Condições exclusivas para você' },
                  { icon: Star, title: 'Acumule Pontos', text: 'Ganhe pontos na Jornada Real' },
                ].map((item) => {
                  const Icon = item.icon
                  return (
                    <div key={item.title} className="px-2">
                      <Icon className="mx-auto mb-2 text-[#d7a52c]" size={30} strokeWidth={1.7} />
                      <strong className="block font-serif text-[0.75rem] uppercase text-[#e5b84a] sm:text-[0.95rem]">{item.title}</strong>
                      <span className="mt-2 block text-[0.72rem] leading-snug text-[#f4ead2] sm:text-[0.9rem]">{item.text}</span>
                    </div>
                  )
                })}
              </div>

              <p className="mx-auto mt-5 flex w-fit items-center justify-center gap-3 rounded-full border border-[#8b651c]/55 bg-black/30 px-6 py-3 text-center text-[#f4ead2]">
                <Crown size={26} className="text-[#e5b84a]" />
                <span>Sua reserva é garantida e seus pontos também!</span>
              </p>
            </div>
          </div>

          <div className="hidden">
            <div className="border-b border-[#d4af37]/30 bg-gradient-to-b from-[#f7d878] via-[#d8a83b] to-[#8d5a14] px-4 py-5 text-center sm:p-6">
              <h2 className="text-xl font-bold text-blue-900 sm:text-2xl">🔍 Buscar Disponibilidade</h2>
              <p className="mt-1 text-sm text-blue-800 sm:text-base">Selecione as datas da sua estadia</p>
            </div>
            
            <div className="bg-[linear-gradient(180deg,rgba(36,20,13,0.9)_0%,rgba(21,11,8,0.96)_100%)] p-6 sm:p-8">
              <div className="grid md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-[#f3dfab] font-medium mb-2">📅 Check-in</label>
                  <input
                    type="date"
                    min={today}
                    value={searchData.data_checkin}
                    onChange={(e) => setSearchData({ ...searchData, data_checkin: e.target.value })}
                    className="w-full rounded-xl border border-[#d4af37]/28 bg-[#241611] p-4 text-lg text-[#fff4d6] focus:border-[#f4cf65] focus:outline-none focus:shadow-[0_0_18px_rgba(212,175,55,0.18)]"
                  />
                  <p className="text-sm text-[#cdbb97] mt-1">A partir das 12:00</p>
                </div>
                
                <div>
                  <label className="block text-[#f3dfab] font-medium mb-2">📅 Check-out</label>
                  <input
                    type="date"
                    min={searchData.data_checkin || today}
                    value={searchData.data_checkout}
                    onChange={(e) => setSearchData({ ...searchData, data_checkout: e.target.value })}
                    className="w-full rounded-xl border border-[#d4af37]/28 bg-[#241611] p-4 text-lg text-[#fff4d6] focus:border-[#f4cf65] focus:outline-none focus:shadow-[0_0_18px_rgba(212,175,55,0.18)]"
                  />
                  <p className="text-sm text-[#cdbb97] mt-1">Até as 11:00</p>
                </div>
                
                <div>
                  <label className="block text-[#f3dfab] font-medium mb-2">👥 Hóspedes</label>
                  <select
                    value={searchData.num_hospedes}
                    onChange={(e) => setSearchData({ ...searchData, num_hospedes: parseInt(e.target.value) })}
                    className="w-full rounded-xl border border-[#d4af37]/28 bg-[#241611] p-4 text-lg text-[#fff4d6] focus:border-[#f4cf65] focus:outline-none focus:shadow-[0_0_18px_rgba(212,175,55,0.18)]"
                  >
                    {[1, 2, 3, 4, 5, 6].map(n => (
                      <option key={n} value={n}>{n} {n === 1 ? 'hóspede' : 'hóspedes'}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <button
                onClick={buscarDisponibilidade}
                disabled={loading}
                className="mt-8 flex w-full items-center justify-center gap-2 rounded-xl border border-[#fff0b8]/40 bg-gradient-to-b from-[#ffe89a] via-[#e7b938] to-[#bf7d0e] py-4 text-lg font-bold text-[#241102] shadow-[0_12px_24px_rgba(0,0,0,0.34),0_0_24px_rgba(212,175,55,0.18)] transition-all hover:scale-[1.01] disabled:opacity-50"
              >
                {loading ? (
                  <>⏳ Buscando...</>
                ) : (
                  <>🔍 Verificar Disponibilidade</>
                )}
              </button>
            </div>
          </div>
          </div>
        )}
        
        {/* Step 2: Seleção de Quarto */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 text-white flex items-center justify-between">
              <div>
                <p className="text-sm opacity-80">Período selecionado</p>
                <p className="font-bold">
                  {new Date(searchData.data_checkin).toLocaleDateString('pt-BR')} → {new Date(searchData.data_checkout).toLocaleDateString('pt-BR')}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm opacity-80">Duração</p>
                <p className="font-bold text-yellow-400">{numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'}</p>
              </div>
              <button
                onClick={() => setStep(1)}
                className="px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-all"
              >
                ✏️ Alterar
              </button>
            </div>
            
            <h2 className="text-2xl font-bold text-white text-center">🛏️ Escolha sua Suíte</h2>
            
            {tiposDisponiveis.length === 0 ? (
              <div className="bg-white rounded-xl p-8 text-center text-gray-900">
                <p className="text-gray-600">Não há quartos disponíveis para as datas selecionadas.</p>
                <button
                  onClick={() => setStep(1)}
                  className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg"
                >
                  Tentar outras datas
                </button>
              </div>
            ) : (
              <div className="grid gap-6">
                {tiposDisponiveis.map((tipo) => {
                  const info = getDescricaoSuite(tipo.tipo)
                  return (
                    <div key={tipo.tipo} className="bg-white rounded-2xl shadow-xl overflow-hidden text-gray-900">
                      <div className="md:flex">
                        {/* Imagem da suíte */}
                        <div className="md:w-1/3 relative h-48 md:h-auto">
                          <img
                            src={
                              tipo.tipo === 'REAL' 
                                ? '/images/suites/suite-real.png'
                                : tipo.tipo === 'MASTER'
                                ? '/images/suites/suite-master.png'
                                : tipo.tipo === 'DUPLA'
                                ? '/images/suites/suite-dupla.png'
                                : '/images/suites/suite-luxo.png'
                            }
                            alt={info.titulo}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                          <div className="absolute bottom-4 left-4 text-white">
                            <span className="text-2xl font-bold">{info.titulo}</span>
                          </div>
                        </div>
                        
                        {/* Detalhes */}
                        <div className="md:w-2/3 p-6">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <h3 className="text-xl font-bold text-gray-800">{info.titulo}</h3>
                              <p className="text-gray-600">{info.descricao}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm text-gray-500">a partir de</p>
                              <p className="text-2xl font-bold text-green-600">
                                R$ {tipo.preco_diaria.toFixed(2)}
                              </p>
                              <p className="text-sm text-gray-500">por noite</p>
                            </div>
                          </div>
                          
                          {/* Amenidades */}
                          <div className="flex flex-wrap gap-2 mb-4">
                            {info.amenidades.map((amenidade, i) => (
                              <span key={i} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                                {amenidade}
                              </span>
                            ))}
                          </div>
                          
                          {/* Quartos disponíveis */}
                          <div className="border-t pt-4">
                            <p className="text-sm text-gray-600 mb-2">
                              {tipo.quantidade_disponivel} {tipo.quantidade_disponivel === 1 ? 'quarto disponível' : 'quartos disponíveis'}
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {tipo.quartos.slice(0, 5).map((quarto) => (
                                <button
                                  key={quarto.numero}
                                  onClick={() => selecionarQuarto(tipo, quarto)}
                                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all"
                                >
                                  Quarto {quarto.numero}
                                  <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
                                </button>
                              ))}
                              {tipo.quartos.length > 5 && (
                                <span className="px-4 py-2 text-gray-500">+{tipo.quartos.length - 5} mais</span>
                              )}
                            </div>
                          </div>
                          
                          {/* Total */}
                          <div className="mt-4 p-3 bg-yellow-50 rounded-lg flex justify-between items-center">
                            <span className="text-gray-700">Total para {numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'}:</span>
                            <span className="text-xl font-bold text-green-600">R$ {tipo.preco_total.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
        
        {/* Step 3: Dados do Hóspede */}
        {step === 3 && quartoSelecionado && (
          <div className="bg-white rounded-2xl shadow-2xl overflow-hidden text-gray-900">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6">
              <h2 className="text-xl font-bold text-white sm:text-2xl">📝 Seus Dados</h2>
              <p className="text-blue-100">Autentique seu cadastro para liberar a reserva</p>
            </div>
            
            {/* Resumo */}
            <div className="bg-blue-50 p-4 border-b flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Quarto selecionado</p>
                <p className="font-bold text-blue-800">
                  {getDescricaoSuite(quartoSelecionado.tipo).titulo} - Quarto {quartoSelecionado.numero}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">{numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'}</p>
                <p className="font-bold text-green-600">R$ {quartoSelecionado.preco_total.toFixed(2)}</p>
              </div>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-gray-800">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex items-start gap-3">
                    <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-blue-600 text-white">
                      <ShieldCheck size={24} strokeWidth={1.8} />
                    </span>
                    <div>
                      <h3 className="font-bold text-blue-900">Autenticação do cadastro</h3>
                      <p className="text-sm text-blue-800">
                        O código é enviado para o WhatsApp do cadastro e vincula esta reserva ao CPF.
                      </p>
                    </div>
                  </div>
                  <span className={`w-fit rounded-full border px-3 py-1 text-xs font-bold uppercase ${authBadge.className}`}>
                    {authBadge.label}
                  </span>
                </div>

                <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
                  <label className="block">
                    <span className="mb-1 block text-sm font-medium text-gray-700">CPF *</span>
                    <input
                      type="text"
                      placeholder="000.000.000-00"
                      value={hospedeData.documento}
                      onChange={(e) => handleCpfChange(e.target.value)}
                      disabled={customerAuth.status !== 'idle' && customerAuth.status !== 'not_found'}
                      className="w-full rounded-lg border-2 border-gray-200 p-3 focus:border-blue-400 focus:outline-none disabled:bg-gray-100 disabled:text-gray-500"
                      maxLength={14}
                    />
                  </label>
                  <div className="flex items-end gap-2">
                    <button
                      type="button"
                      onClick={buscarCadastroCpf}
                      disabled={authLoading || customerAuth.status !== 'idle'}
                      className="min-h-[48px] rounded-lg bg-blue-600 px-5 font-bold text-white transition-all hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {authLoading && customerAuth.status === 'idle' ? 'Consultando...' : 'Consultar'}
                    </button>
                    {customerAuth.status !== 'idle' && (
                      <button
                        type="button"
                        onClick={() => {
                          resetCustomerAuth()
                          setHospedeData((current) => ({
                            ...current,
                            documento: '',
                            nome_completo: '',
                            email: '',
                            telefone: '',
                          }))
                        }}
                        className="min-h-[48px] rounded-lg border border-gray-300 px-4 font-medium text-gray-700 transition-all hover:bg-white"
                      >
                        Trocar
                      </button>
                    )}
                  </div>
                </div>

                {customerAuth.status === 'not_found' && (
                  <div className="mt-4 rounded-lg border border-amber-200 bg-white p-4 text-gray-900">
                    <p className="text-sm text-amber-800">
                      CPF não cadastrado. Preencha nome, email e telefone abaixo para criar o cadastro antes do OTP.
                    </p>
                    <button
                      type="button"
                      onClick={criarCadastroCustomer}
                      disabled={authLoading}
                      className="mt-3 rounded-lg bg-amber-500 px-5 py-3 font-bold text-white transition-all hover:bg-amber-600 disabled:opacity-50"
                    >
                      {authLoading ? 'Criando cadastro...' : 'Criar cadastro'}
                    </button>
                  </div>
                )}

                {customerAuth.customer && customerAuth.status !== 'verified' && (
                  <div className="mt-4 rounded-lg border border-blue-200 bg-white p-4 text-gray-900">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="font-bold text-gray-900">{customerAuth.customer.nome_completo}</p>
                        <p className="text-sm text-gray-600">
                          WhatsApp cadastrado: {formatTelefone(customerAuth.customer.telefone || '') || 'telefone indisponível'}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={enviarOtpCustomer}
                        disabled={authLoading}
                        className="rounded-lg bg-blue-600 px-5 py-3 font-bold text-white transition-all hover:bg-blue-700 disabled:opacity-50"
                      >
                        {customerAuth.status === 'otp_sent' ? 'Reenviar código' : 'Enviar código'}
                      </button>
                    </div>

                    {customerAuth.status === 'otp_sent' && (
                      <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,220px)_auto]">
                        <input
                          type="text"
                          inputMode="numeric"
                          placeholder="000000"
                          value={customerAuth.otpCode}
                          onChange={(e) => setCustomerAuth((current) => ({
                            ...current,
                            otpCode: onlyDigits(e.target.value).slice(0, 6),
                          }))}
                          className="rounded-lg border-2 border-gray-200 p-3 text-center text-xl font-bold tracking-[0.2em] focus:border-blue-400 focus:outline-none"
                          maxLength={6}
                        />
                        <button
                          type="button"
                          onClick={validarOtpCustomer}
                          disabled={authLoading}
                          className="rounded-lg bg-green-600 px-5 py-3 font-bold text-white transition-all hover:bg-green-700 disabled:opacity-50"
                        >
                          {authLoading ? 'Validando...' : 'Validar código'}
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {isCustomerAuthenticated && (
                  <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-4 text-sm font-medium text-green-800">
                    Cadastro autenticado. Você já pode revisar os dados da reserva e continuar.
                  </div>
                )}
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 font-medium mb-1">Nome Completo *</label>
                  <input
                    type="text"
                    placeholder="Como está no documento"
                    value={hospedeData.nome_completo}
                    onChange={(e) => setHospedeData({ ...hospedeData, nome_completo: e.target.value })}
                    disabled={!canEditCustomerFields}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none disabled:bg-gray-100 disabled:text-gray-500"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-700 font-medium mb-1">Email *</label>
                  <input
                    type="email"
                    placeholder="seu@email.com"
                    value={hospedeData.email}
                    onChange={(e) => setHospedeData({ ...hospedeData, email: e.target.value })}
                    disabled={!canEditCustomerFields}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none disabled:bg-gray-100 disabled:text-gray-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Enviaremos a confirmação para este email</p>
                </div>
                
                <div>
                  <label className="block text-gray-700 font-medium mb-1">Telefone *</label>
                  <input
                    type="text"
                    placeholder="(00) 00000-0000"
                    value={hospedeData.telefone}
                    onChange={(e) => setHospedeData({ ...hospedeData, telefone: formatTelefone(e.target.value) })}
                    disabled={!canEditCustomerFields}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none disabled:bg-gray-100 disabled:text-gray-500"
                    maxLength={15}
                  />
                </div>
                
                <div>
                  <label className="block text-gray-700 font-medium mb-1">Adultos</label>
                  <select
                    value={hospedeData.num_hospedes}
                    onChange={(e) => setHospedeData({ ...hospedeData, num_hospedes: parseInt(e.target.value) })}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none"
                  >
                    {[1, 2, 3, 4].map(n => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-gray-700 font-medium mb-1">Crianças (0-12 anos)</label>
                  <select
                    value={hospedeData.num_criancas}
                    onChange={(e) => setHospedeData({ ...hospedeData, num_criancas: parseInt(e.target.value) })}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none"
                  >
                    {[0, 1, 2, 3].map(n => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-gray-700 font-medium mb-1">Observações (opcional)</label>
                <textarea
                  placeholder="Solicitações especiais, preferências, restrições alimentares..."
                  value={hospedeData.observacoes}
                  onChange={(e) => setHospedeData({ ...hospedeData, observacoes: e.target.value })}
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none resize-none"
                  rows={3}
                />
              </div>
              
              <div className="flex gap-4 pt-4">
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 py-3 border-2 border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-all"
                >
                  ← Voltar
                </button>
                <button
                  onClick={() => setStep(4)}
                  disabled={!isCustomerAuthenticated}
                  className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition-all disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isCustomerAuthenticated ? 'Continuar →' : 'Autentique para continuar'}
                  <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Step 4: Pagamento */}
        {step === 4 && quartoSelecionado && (
          <div className="bg-white rounded-2xl shadow-2xl overflow-hidden text-gray-900">
            <div className="bg-gradient-to-r from-green-600 to-green-700 p-6">
              <h2 className="text-xl font-bold text-white sm:text-2xl">💳 Forma de Pagamento</h2>
              <p className="text-green-100">Escolha como deseja pagar</p>
            </div>
            
            {/* Resumo */}
            <div className="bg-green-50 p-4 border-b">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-bold text-gray-800">{hospedeData.nome_completo}</p>
                  <p className="text-sm text-gray-600">
                    {getDescricaoSuite(quartoSelecionado.tipo).titulo} - Quarto {quartoSelecionado.numero}
                  </p>
                  <p className="text-sm text-gray-600">
                    {new Date(searchData.data_checkin).toLocaleDateString('pt-BR')} → {new Date(searchData.data_checkout).toLocaleDateString('pt-BR')} ({numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'})
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-2xl font-bold text-green-600">R$ {quartoSelecionado.preco_total.toFixed(2)}</p>
                </div>
              </div>
            </div>
            
            <div className="p-6 space-y-4">
              <p className="text-gray-700 font-medium mb-4">Selecione uma opção:</p>
              
              {/* Opções de pagamento */}
              <div className="space-y-3">
                <label className={`block p-4 border-2 rounded-xl cursor-pointer transition-all ${
                  metodoPagamento === 'balcao' ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-green-300'
                }`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="balcao"
                    checked={metodoPagamento === 'balcao'}
                    onChange={(e) => setMetodoPagamento(e.target.value)}
                    className="hidden"
                  />
                  <div className="flex items-center gap-4">
                    <span className="text-3xl">🏦</span>
                    <div>
                      <p className="font-bold text-gray-800">Pagamento no Balcão</p>
                      <p className="text-sm text-gray-600">Pague no check-in ou antecipadamente no balcão</p>
                    </div>
                    {metodoPagamento === 'balcao' && <span className="ml-auto text-green-600 font-bold">✓</span>}
                  </div>
                </label>
                
                <label className={`block p-4 border-2 rounded-xl cursor-pointer transition-all ${
                  metodoPagamento === 'credit_card' ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-green-300'
                }`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="credit_card"
                    checked={metodoPagamento === 'credit_card'}
                    onChange={(e) => setMetodoPagamento(e.target.value)}
                    className="hidden"
                  />
                  <div className="flex items-center gap-4">
                    <span className="text-3xl">💳</span>
                    <div>
                      <p className="font-bold text-gray-800">Cartão de Crédito</p>
                      <p className="text-sm text-gray-600">Pague agora em até 12x</p>
                    </div>
                    {metodoPagamento === 'credit_card' && <span className="ml-auto text-green-600 font-bold">✓</span>}
                  </div>
                </label>
                
                <label className={`block p-4 border-2 rounded-xl cursor-pointer transition-all ${
                  metodoPagamento === 'pix' ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-green-300'
                }`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="pix"
                    checked={metodoPagamento === 'pix'}
                    onChange={(e) => setMetodoPagamento(e.target.value)}
                    className="hidden"
                  />
                  <div className="flex items-center gap-4">
                    <span className="text-3xl">📱</span>
                    <div>
                      <p className="font-bold text-gray-800">PIX</p>
                      <p className="text-sm text-gray-600">Aprovação instantânea</p>
                    </div>
                    {metodoPagamento === 'pix' && <span className="ml-auto text-green-600 font-bold">✓</span>}
                  </div>
                </label>
                
                <label className={`block p-4 border-2 rounded-xl cursor-pointer transition-all ${
                  metodoPagamento === 'na_chegada' ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-green-300'
                }`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="na_chegada"
                    checked={metodoPagamento === 'na_chegada'}
                    onChange={(e) => setMetodoPagamento(e.target.value)}
                    className="hidden"
                  />
                  <div className="flex items-center gap-4">
                    <span className="text-3xl">🏨</span>
                    <div>
                      <p className="font-bold text-gray-800">Pagar na Chegada</p>
                      <p className="text-sm text-gray-600">Pague no check-in (cartão, PIX ou dinheiro)</p>
                    </div>
                    {metodoPagamento === 'na_chegada' && <span className="ml-auto text-green-600 font-bold">✓</span>}
                  </div>
                </label>
              </div>
              
              <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200 mt-4">
                <p className="text-yellow-800 text-sm">
                  ⚠️ <strong>Importante:</strong> A reserva só é garantida após confirmação. 
                  Cancelamentos podem ser feitos até 24h antes do check-in sem custo.
                </p>
              </div>
              
              <div className="flex gap-4 pt-4">
                <button
                  onClick={() => setStep(3)}
                  className="flex-1 py-3 border-2 border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-all"
                >
                  ← Voltar
                </button>
                <button
                  onClick={criarReserva}
                  disabled={loading}
                  className="flex-1 py-3 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 transition-all disabled:opacity-50"
                >
                  {loading ? '⏳ Processando...' : '✅ Confirmar Reserva'}
                  <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Step 5: Confirmação */}
        {step === 5 && reservaConfirmada && (
          <div className="bg-white rounded-2xl shadow-2xl overflow-hidden text-gray-900">
            <div className="bg-gradient-to-r from-green-500 to-green-600 p-8 text-center">
              <div className="text-6xl mb-4">🎉</div>
              <h2 className="text-3xl font-bold text-white">Reserva Confirmada!</h2>
              <p className="text-green-100 mt-2">Sua reserva foi realizada com sucesso</p>
            </div>
            
            <div className="p-6">
              {/* Código da reserva */}
              <div className="bg-blue-50 p-6 rounded-xl text-center mb-6">
                <p className="text-gray-600 mb-1">Código da Reserva</p>
                <p className="text-3xl font-bold text-blue-600 font-mono">{reservaConfirmada.reserva.codigo}</p>
                <p className="text-sm text-gray-500 mt-2">Guarde este código para consultar sua reserva</p>
              </div>
              
              {/* Detalhes */}
              <div className="space-y-4 mb-6">
                <h3 className="font-bold text-gray-800 text-lg">📋 Detalhes da Reserva</h3>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-500">Hóspede</p>
                    <p className="font-medium">{reservaConfirmada.reserva.cliente}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-500">Acomodação</p>
                    <p className="font-medium">{reservaConfirmada.reserva.tipo_suite} - Quarto {reservaConfirmada.reserva.quarto}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-500">Check-in</p>
                    <p className="font-medium">{new Date(reservaConfirmada.reserva.checkin).toLocaleDateString('pt-BR')} às 12:00</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-500">Check-out</p>
                    <p className="font-medium">{new Date(reservaConfirmada.reserva.checkout).toLocaleDateString('pt-BR')} às 11:00</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-500">Duração</p>
                    <p className="font-medium">{reservaConfirmada.reserva.num_diarias} {reservaConfirmada.reserva.num_diarias === 1 ? 'diária' : 'diárias'}</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-500">Valor Total</p>
                    <p className="font-bold text-green-600 text-xl">R$ {reservaConfirmada.reserva.valor_total.toFixed(2)}</p>
                  </div>
                </div>
              </div>
              
              {/* Instruções */}
              <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200 mb-6">
                <h4 className="font-bold text-yellow-800 mb-2">📌 Instruções Importantes</h4>
                <ul className="text-sm text-yellow-800 space-y-1">
                  <li>• {reservaConfirmada.instrucoes.documentos}</li>
                  <li>• Check-in a partir das {reservaConfirmada.instrucoes.checkin_horario}</li>
                  <li>• Check-out até as {reservaConfirmada.instrucoes.checkout_horario}</li>
                  <li>• Contato: {reservaConfirmada.instrucoes.contato}</li>
                </ul>
              </div>
              
              {/* Ações */}
              <div className="flex flex-col sm:flex-row gap-4">
                <button
                  onClick={() => window.print()}
                  className="flex-1 py-3 border-2 border-blue-600 text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-all flex items-center justify-center gap-2"
                >
                  🖨️ Imprimir Comprovante
                  <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
                </button>
                <button
                  onClick={() => {
                    setStep(1)
                    setReservaConfirmada(null)
                    setQuartoSelecionado(null)
                    setHospedeData({
                      nome_completo: '',
                      documento: '',
                      email: '',
                      telefone: '',
                      num_hospedes: 1,
                      num_criancas: 0,
                      observacoes: ''
                    })
                    resetCustomerAuth()
                  }}
                  className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all flex items-center justify-center gap-2"
                >
                  🏨 Nova Reserva
                  <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        )}
        
      </main>
      
      {/* Footer */}
      <footer className="relative z-30 mt-auto border-t border-[#d4af37]/15 bg-[#090504]/70 py-8 text-white/80 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <span className="text-3xl">🏨</span>
            <div>
              <h3 className="text-xl font-bold text-white">Hotel Real Cabo Frio</h3>
              <p className="text-sm text-yellow-400">O melhor da região</p>
            </div>
          </div>
          <p className="text-sm">Av. Beira Mar, 1000 - Cabo Frio, RJ</p>
          <p className="text-sm mt-1">📞 (22) 2648-5900 | 📧 contato@hotelrealcabofrio.com.br</p>
          <p className="text-xs mt-4 opacity-60">© 2024 Hotel Real Cabo Frio. Todos os direitos reservados.</p>
        </div>
      </footer>
      
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

      <style jsx global>{`
        button[aria-label="Abrir configurações de acessibilidade"] {
          display: none !important;
        }

        input[type='date']::-webkit-datetime-edit,
        input[type='date']::-webkit-datetime-edit-text,
        input[type='date']::-webkit-datetime-edit-month-field,
        input[type='date']::-webkit-datetime-edit-day-field,
        input[type='date']::-webkit-datetime-edit-year-field,
        input[type='date']::-webkit-calendar-picker-indicator,
        select {
          color: #f3dfab;
        }

        .royal-date-input::-webkit-calendar-picker-indicator {
          cursor: pointer;
          filter: invert(76%) sepia(74%) saturate(567%) hue-rotate(358deg) brightness(99%) contrast(91%);
        }

        select {
          background-color: #080604;
        }

        @media (max-width: 430px) {
          .Toastify {
            font-size: 0.86rem;
          }
        }
      `}</style>
    </div>
  )
}
