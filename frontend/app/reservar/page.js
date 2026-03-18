'use client'
import { useState, useEffect, useRef, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Script from 'next/script'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { api } from '../../lib/api'

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || ''
const WHATSAPP_PHONE = '552226485900'

export default function Reservar() {
  const router = useRouter()
  
  // Estados do fluxo
  const [step, setStep] = useState(1) // 1: Datas, 2: Quarto, 3: Dados, 4: Pagamento, 5: Confirmação
  const [loading, setLoading] = useState(false)
  const [perfilReserva, setPerfilReserva] = useState('primeira_reserva')
  const [clienteLookupLoading, setClienteLookupLoading] = useState(false)
  const [clienteLookupStatus, setClienteLookupStatus] = useState('idle')
  const [clienteRecorrente, setClienteRecorrente] = useState(null)
  const [reservaAtivaCliente, setReservaAtivaCliente] = useState(null)
  const [cupomCodigo, setCupomCodigo] = useState('')
  const [cupomLoading, setCupomLoading] = useState(false)
  const [cupomStatus, setCupomStatus] = useState('idle')
  const [cupomInfo, setCupomInfo] = useState(null)
  const [captchaStatus, setCaptchaStatus] = useState(TURNSTILE_SITE_KEY ? 'ready' : 'disabled')
  const [turnstileLoaded, setTurnstileLoaded] = useState(false)
  const [turnstileToken, setTurnstileToken] = useState('')
  const turnstileContainerRef = useRef(null)
  const turnstileWidgetIdRef = useRef(null)
  
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
  
  // Pagamento
  const [metodoPagamento, setMetodoPagamento] = useState('balcao')
  
  // Reserva confirmada
  const [reservaConfirmada, setReservaConfirmada] = useState(null)
  
  // Definir data mínima (hoje)
  const today = new Date().toISOString().split('T')[0]
  
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

  const resetTurnstile = () => {
    if (!TURNSTILE_SITE_KEY) return

    try {
      if (
        typeof window !== 'undefined' &&
        window.turnstile &&
        turnstileWidgetIdRef.current !== null
      ) {
        window.turnstile.reset(turnstileWidgetIdRef.current)
      }
    } catch (error) {
      console.error('Erro ao resetar Turnstile:', error)
    } finally {
      setTurnstileToken('')
      setCaptchaStatus('ready')
    }
  }

  useEffect(() => {
    if (!TURNSTILE_SITE_KEY) return
    if (step !== 3) return
    if (!turnstileLoaded) return
    if (!turnstileContainerRef.current) return
    if (typeof window === 'undefined' || !window.turnstile?.render) return

    if (turnstileWidgetIdRef.current !== null) {
      return
    }

    turnstileWidgetIdRef.current = window.turnstile.render(turnstileContainerRef.current, {
      sitekey: TURNSTILE_SITE_KEY,
      action: 'criar_reserva_publica',
      theme: 'light',
      callback: (token) => {
        setTurnstileToken(token)
        setCaptchaStatus('verified')
      },
      'expired-callback': () => {
        setTurnstileToken('')
        setCaptchaStatus('ready')
      },
      'error-callback': () => {
        setTurnstileToken('')
        setCaptchaStatus('error')
      }
    })
  }, [step, turnstileLoaded])

  useEffect(() => {
    if (!TURNSTILE_SITE_KEY) return
    if (step === 3 || step === 4 || step === 5) return

    turnstileWidgetIdRef.current = null
    setTurnstileToken('')
    setCaptchaStatus('ready')
  }, [step])

  useEffect(() => {
    setClienteLookupStatus('idle')
    setClienteRecorrente(null)
    setReservaAtivaCliente(null)
  }, [hospedeData.documento, hospedeData.email])

  useEffect(() => {
    setCupomStatus('idle')
    setCupomInfo(null)
    setCupomCodigo('')
  }, [searchData.data_checkin, searchData.data_checkout, quartoSelecionado?.numero])
  
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

  const buscarClienteRecorrente = async () => {
    const cpfLimpo = hospedeData.documento.replace(/\D/g, '')
    const emailNormalizado = hospedeData.email.trim().toLowerCase()

    if (cpfLimpo.length !== 11) {
      toast.warning('Informe um CPF válido para buscar seus dados')
      return
    }

    if (!emailNormalizado.includes('@')) {
      toast.warning('Informe o mesmo email usado na reserva anterior')
      return
    }

    setClienteLookupLoading(true)

    try {
      const response = await api.post('/public/clientes/identificar', {
        documento: cpfLimpo,
        email: emailNormalizado
      })

      const data = response.data
      if (data?.cliente_encontrado && data?.cliente) {
        setHospedeData((prev) => ({
          ...prev,
          nome_completo: data.cliente.nome_completo || prev.nome_completo,
          email: data.cliente.email || prev.email,
          telefone: data.cliente.telefone ? formatTelefone(data.cliente.telefone) : prev.telefone
        }))
        setClienteRecorrente(data.cliente)
        setReservaAtivaCliente(data.reserva_ativa || null)
        if (data.tem_reserva_ativa) {
          setClienteLookupStatus('active_reservation')
          toast.warning(data.mensagem || `${data.cliente.nome_completo}, você já tem uma reserva ativa.`)
        } else {
          setClienteLookupStatus('found')
          toast.success('Dados do cadastro anterior carregados')
        }
        return
      }

      setClienteRecorrente(null)
      setReservaAtivaCliente(null)
      setClienteLookupStatus('not_found')
      toast.info('Nenhum cadastro compatível encontrado para CPF + email')
    } catch (error) {
      console.error('Erro ao buscar cliente recorrente:', error)
      setClienteRecorrente(null)
      setReservaAtivaCliente(null)
      setClienteLookupStatus('error')
      toast.error(error?.response?.data?.detail || 'Erro ao buscar cadastro anterior')
    } finally {
      setClienteLookupLoading(false)
    }
  }
  
  // Criar reserva
  const criarReserva = async () => {
    // Validações
    if (!hospedeData.nome_completo || !hospedeData.documento || !hospedeData.email || !hospedeData.telefone) {
      toast.warning('Preencha todos os campos obrigatórios')
      return
    }
    
    // Validar CPF (simples)
    const cpfLimpo = hospedeData.documento.replace(/\D/g, '')
    if (cpfLimpo.length !== 11) {
      toast.warning('CPF inválido')
      return
    }
    
    // Validar email
    if (!hospedeData.email.includes('@')) {
      toast.warning('Email inválido')
      return
    }

    if (reservaAtivaCliente) {
      toast.warning(`${hospedeData.nome_completo || 'Cliente'}, você já tem uma reserva ativa.`)
      return
    }
    
    setLoading(true)
    let attemptedCaptcha = false
    let captchaVerified = false

    try {
      let antibotHeaders = {}
      if (TURNSTILE_SITE_KEY) {
        attemptedCaptcha = true
        if (!turnstileToken) {
          setCaptchaStatus('error')
          toast.error('❌ Resolva o captcha antes de confirmar a reserva.')
          return
        }

        setCaptchaStatus('checking')
        antibotHeaders = {
          'X-Turnstile-Token': turnstileToken,
          'X-Turnstile-Action': 'criar_reserva_publica'
        }
      }

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
        cupom_codigo: cupomStatus === 'valid' && cupomInfo?.codigo ? cupomInfo.codigo : null
      }
      
      const response = await api.post(
        '/public/reservas',
        payload,
        Object.keys(antibotHeaders).length ? { headers: antibotHeaders } : undefined
      )
      
      const data = response.data
      
      if (data.success) {
        captchaVerified = true
        setCaptchaStatus(TURNSTILE_SITE_KEY ? 'verified' : 'disabled')
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
      } else if (error.response?.status === 403) {
        setCaptchaStatus('error')
        toast.error(`❌ ${error.response?.data?.detail || 'Captcha inválido ou expirado.'}`)
      } else if (error.response?.status === 409) {
        toast.warning(error.response?.data?.detail || `${hospedeData.nome_completo || 'Cliente'}, você já tem uma reserva ativa.`)
      } else if (error.response?.status === 400) {
        toast.error('❌ Dados inválidos. Verifique as informações e tente novamente.')
      } else if (error.response?.status === 500) {
        toast.error('❌ Erro interno do servidor. Tente novamente.')
      } else {
        toast.error('❌ Erro ao conectar com o servidor. Tente novamente.')
      }
    } finally {
      if (TURNSTILE_SITE_KEY && attemptedCaptcha && !captchaVerified) {
        resetTurnstile()
      }
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

  const getCaptchaBadge = () => {
    switch (captchaStatus) {
      case 'checking':
        return {
          label: 'Validando',
          classes: 'bg-amber-100 text-amber-800 border-amber-200',
          description: 'Validando o captcha antes de confirmar a reserva.'
        }
      case 'verified':
        return {
          label: 'Validado',
          classes: 'bg-green-100 text-green-800 border-green-200',
          description: 'Captcha concluído. Você pode confirmar a reserva.'
        }
      case 'error':
        return {
          label: 'Falhou',
          classes: 'bg-red-100 text-red-800 border-red-200',
          description: 'O captcha falhou ou expirou. Resolva novamente antes de prosseguir.'
        }
      case 'disabled':
        return {
          label: 'Dev',
          classes: 'bg-slate-100 text-slate-700 border-slate-200',
          description: 'Captcha visível desativado neste ambiente. Ative as chaves para produção.'
        }
      case 'ready':
      default:
        return {
          label: 'Pendente',
          classes: 'bg-blue-100 text-blue-800 border-blue-200',
          description: 'Resolva o captcha visível antes de confirmar a reserva.'
        }
    }
  }

  const captchaBadge = getCaptchaBadge()
  const resumoValores = useMemo(() => {
    const subtotal = Number(quartoSelecionado?.preco_total || 0)
    const desconto = Number(cupomInfo?.valor_desconto_calculado || 0)
    const total = cupomStatus === 'valid' && cupomInfo?.valor_final_estimado != null
      ? Number(cupomInfo.valor_final_estimado)
      : subtotal

    return { subtotal, desconto, total }
  }, [quartoSelecionado, cupomInfo, cupomStatus])
  const whatsappReservaAtivaUrl = reservaAtivaCliente
    ? `https://api.whatsapp.com/send/?phone=${WHATSAPP_PHONE}&text=${encodeURIComponent(
        `Olá Hotel real cabo frio, tudo bem?\n\nGostaria de falar sobre minha reserva.\nCódigo ${reservaAtivaCliente.codigo} | Quarto ${reservaAtivaCliente.quarto_numero} | Status ${reservaAtivaCliente.status}`
      )}&type=phone_number&app_absent=0`
    : null
  const tabsReserva = [
    {
      id: 'primeira_reserva',
      titulo: 'Primeira reserva',
      descricao: 'Fluxo guiado para quem ainda vai se cadastrar.'
    },
    {
      id: 'ja_sou_cliente',
      titulo: 'Já sou cliente',
      descricao: 'Vamos reaproveitar seus dados no passo seguinte.'
    }
  ]

  const validarCupom = async () => {
    if (!cupomCodigo.trim()) {
      toast.warning('Informe um código de cupom para validar')
      return
    }

    if (!quartoSelecionado || !numDiarias) {
      toast.warning('Selecione as datas e o quarto antes de validar o cupom')
      return
    }

    try {
      setCupomLoading(true)
      setCupomStatus('checking')

      const response = await api.post('/cupons/validar', {
        codigo: cupomCodigo.trim().toUpperCase(),
        suite_tipo: quartoSelecionado.tipo,
        num_diarias: numDiarias,
        valor_total_base: Number(quartoSelecionado.preco_total)
      })

      if (response.data?.valido) {
        setCupomInfo(response.data)
        setCupomCodigo(response.data.codigo || cupomCodigo.trim().toUpperCase())
        setCupomStatus('valid')
        toast.success(`Cupom ${response.data.codigo} aplicado ao resumo da reserva`)
        return
      }

      setCupomInfo(response.data || null)
      setCupomStatus('invalid')
      toast.warning(response.data?.mensagem || 'Cupom inválido para esta reserva')
    } catch (error) {
      console.error('Erro ao validar cupom:', error)
      setCupomInfo(null)
      setCupomStatus('invalid')
      toast.error(error?.response?.data?.detail || 'Não foi possível validar o cupom agora')
    } finally {
      setCupomLoading(false)
    }
  }

  const removerCupom = () => {
    setCupomCodigo('')
    setCupomInfo(null)
    setCupomStatus('idle')
  }

  const renderResumoFinanceiro = (variant = 'default') => {
    const containerClasses = variant === 'compact'
      ? 'rounded-xl border border-slate-200 bg-slate-50 p-4'
      : 'rounded-xl border border-green-100 bg-green-50 p-4'
    const titleClasses = variant === 'compact'
      ? 'text-sm font-semibold text-slate-900'
      : 'text-sm font-semibold text-green-900'

    return (
      <div className={containerClasses}>
        <p className={titleClasses}>Resumo financeiro</p>
        <div className="mt-3 space-y-2 text-sm">
          <div className="flex items-center justify-between text-gray-700">
            <span>Subtotal da hospedagem</span>
            <strong>R$ {resumoValores.subtotal.toFixed(2)}</strong>
          </div>
          {cupomStatus === 'valid' && cupomInfo ? (
            <>
              <div className="flex items-center justify-between text-green-700">
                <span>Desconto do cupom {cupomInfo.codigo}</span>
                <strong>- R$ {resumoValores.desconto.toFixed(2)}</strong>
              </div>
              {cupomInfo.pontos_bonus > 0 ? (
                <div className="flex items-center justify-between text-blue-700">
                  <span>Bônus previsto no checkout</span>
                  <strong>+ {cupomInfo.pontos_bonus} RP</strong>
                </div>
              ) : null}
            </>
          ) : null}
          <div className="flex items-center justify-between border-t border-white/70 pt-2 text-base font-bold text-gray-900">
            <span>Total estimado</span>
            <span>R$ {resumoValores.total.toFixed(2)}</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-800 to-blue-900">
      {TURNSTILE_SITE_KEY && (
        <Script
          src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"
          strategy="afterInteractive"
          onLoad={() => setTurnstileLoaded(true)}
        />
      )}
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-4xl">🏨</span>
            <div>
              <h1 className="text-2xl font-bold text-white">Hotel Real</h1>
              <p className="text-yellow-400 text-sm">Cabo Frio</p>
            </div>
          </div>
          <div className="text-right text-white/80 text-sm">
            <p>📞 (22) 2648-5900</p>
            <p>📧 contato@hotelrealcabofrio.com.br</p>
          </div>
        </div>
      </header>
      
      {/* Progress Steps */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-8">
          {[
            { num: 1, label: 'Datas' },
            { num: 2, label: 'Quarto' },
            { num: 3, label: 'Dados' },
            { num: 4, label: 'Pagamento' },
            { num: 5, label: 'Confirmação' }
          ].map((s, i) => (
            <div key={s.num} className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all ${
                step >= s.num 
                  ? 'bg-yellow-400 text-blue-900' 
                  : 'bg-white/20 text-white/60'
              }`}>
                {step > s.num ? '✓' : s.num}
              </div>
              <span className={`ml-2 text-sm hidden sm:inline ${step >= s.num ? 'text-yellow-400' : 'text-white/60'}`}>
                {s.label}
              </span>
              {i < 4 && (
                <div className={`w-8 sm:w-16 h-1 mx-2 rounded ${step > s.num ? 'bg-yellow-400' : 'bg-white/20'}`} />
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 pb-12">
        
        {/* Step 1: Datas */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="rounded-2xl border border-white/15 bg-white/10 p-2 shadow-xl backdrop-blur-md">
              <div className="grid gap-2 md:grid-cols-3">
                {tabsReserva.map((tab) => {
                  const ativo = perfilReserva === tab.id
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setPerfilReserva(tab.id)}
                      className={`rounded-xl px-5 py-4 text-left transition-all ${
                        ativo
                          ? 'bg-white text-blue-900 shadow-lg ring-2 ring-yellow-300/80'
                          : 'bg-transparent text-white/80 hover:bg-white/10 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-base font-bold">{tab.titulo}</p>
                          <p className={`mt-1 text-sm ${ativo ? 'text-blue-700' : 'text-white/65'}`}>
                            {tab.descricao}
                          </p>
                        </div>
                        <span
                          className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] ${
                            ativo
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-white/10 text-white/60'
                          }`}
                        >
                          {ativo ? 'ativo' : 'opção'}
                        </span>
                      </div>
                    </button>
                  )
                })}
                <Link
                  href="/consultar"
                  className="rounded-xl px-5 py-4 text-left transition-all bg-transparent text-white/80 hover:bg-white/10 hover:text-white"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-base font-bold">Consultar minha reserva</p>
                      <p className="mt-1 text-sm text-white/65">
                        Acesse código, status e instruções da sua reserva atual.
                      </p>
                    </div>
                    <span className="rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] bg-white/10 text-white/60">
                      consulta
                    </span>
                  </div>
                </Link>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-500 p-6 text-center">
              <h2 className="text-2xl font-bold text-blue-900">🔍 Buscar Disponibilidade</h2>
              <p className="text-blue-800">
                {perfilReserva === 'ja_sou_cliente'
                  ? 'Selecione as datas da sua estadia e depois recuperamos seu cadastro.'
                  : 'Selecione as datas da sua estadia'}
              </p>
            </div>
            
            <div className="p-8">
              {perfilReserva === 'ja_sou_cliente' && (
                <div className="mb-6 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-left">
                  <p className="text-sm font-semibold text-blue-900">Cliente recorrente</p>
                  <p className="mt-1 text-sm text-blue-800">
                    No passo de dados, informe o mesmo CPF e email usados antes para preencher seu cadastro automaticamente.
                  </p>
                </div>
              )}

              <div className="grid md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-gray-700 font-medium mb-2">📅 Check-in</label>
                  <input
                    type="date"
                    min={today}
                    value={searchData.data_checkin}
                    onChange={(e) => setSearchData({ ...searchData, data_checkin: e.target.value })}
                    className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-yellow-400 focus:outline-none text-lg"
                  />
                  <p className="text-sm text-gray-500 mt-1">A partir das 12:00</p>
                </div>
                
                <div>
                  <label className="block text-gray-700 font-medium mb-2">📅 Check-out</label>
                  <input
                    type="date"
                    min={searchData.data_checkin || today}
                    value={searchData.data_checkout}
                    onChange={(e) => setSearchData({ ...searchData, data_checkout: e.target.value })}
                    className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-yellow-400 focus:outline-none text-lg"
                  />
                  <p className="text-sm text-gray-500 mt-1">Até as 11:00</p>
                </div>
                
                <div>
                  <label className="block text-gray-700 font-medium mb-2">👥 Hóspedes</label>
                  <select
                    value={searchData.num_hospedes}
                    onChange={(e) => setSearchData({ ...searchData, num_hospedes: parseInt(e.target.value) })}
                    className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-yellow-400 focus:outline-none text-lg"
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
                className="w-full mt-8 bg-gradient-to-r from-blue-600 to-blue-700 text-white py-4 rounded-xl font-bold text-lg hover:from-blue-700 hover:to-blue-800 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
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
              <div className="bg-white rounded-xl p-8 text-center">
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
                    <div key={tipo.tipo} className="bg-white rounded-2xl shadow-xl overflow-hidden">
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
          <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6">
              <h2 className="text-2xl font-bold text-white">📝 Seus Dados</h2>
              <p className="text-blue-100">Preencha os dados para a reserva</p>
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
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 font-medium mb-1">Nome Completo *</label>
                  <input
                    type="text"
                    placeholder="Como está no documento"
                    value={hospedeData.nome_completo}
                    onChange={(e) => setHospedeData({ ...hospedeData, nome_completo: e.target.value })}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-700 font-medium mb-1">CPF *</label>
                  <input
                    type="text"
                    placeholder="000.000.000-00"
                    value={hospedeData.documento}
                    onChange={(e) => setHospedeData({ ...hospedeData, documento: formatCPF(e.target.value) })}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none"
                    maxLength={14}
                  />
                </div>
                
                <div>
                  <label className="block text-gray-700 font-medium mb-1">Email *</label>
                  <input
                    type="email"
                    placeholder="seu@email.com"
                    value={hospedeData.email}
                    onChange={(e) => setHospedeData({ ...hospedeData, email: e.target.value })}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none"
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
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none"
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

              <div className={`rounded-xl border p-4 ${
                perfilReserva === 'ja_sou_cliente'
                  ? 'border-blue-200 bg-blue-50'
                  : 'border-gray-200 bg-gray-50'
              }`}>
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">Já reservou antes?</p>
                    <p className="mt-1 text-sm text-gray-600">
                      Informe o mesmo CPF e email usados anteriormente para reaproveitar seu cadastro.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={buscarClienteRecorrente}
                    disabled={clienteLookupLoading}
                    className="rounded-lg border border-blue-200 bg-white px-4 py-2 text-sm font-semibold text-blue-700 transition hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {clienteLookupLoading ? 'Buscando...' : 'Buscar meus dados'}
                  </button>
                </div>

                {clienteLookupStatus === 'found' && clienteRecorrente && (
                  <div className="mt-3 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
                    Cadastro anterior localizado para <strong>{clienteRecorrente.nome_completo}</strong>.
                    Revise telefone e demais dados antes de continuar.
                  </div>
                )}

                {clienteLookupStatus === 'active_reservation' && clienteRecorrente && reservaAtivaCliente && (
                  <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                    <p>
                      <strong>{clienteRecorrente.nome_completo}</strong>, você já tem uma reserva ativa.
                    </p>
                    <p className="mt-2">
                      Código {reservaAtivaCliente.codigo} | Quarto {reservaAtivaCliente.quarto_numero} | Status {reservaAtivaCliente.status}
                    </p>
                    <p className="mt-2">
                      Cliente recorrente só pode criar nova reserva após ter histórico com check-out realizado e nenhuma reserva aberta.
                    </p>
                    {whatsappReservaAtivaUrl && (
                      <a
                        href={whatsappReservaAtivaUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-3 inline-flex items-center rounded-lg border border-amber-300 bg-white px-4 py-2 font-semibold text-amber-900 transition hover:bg-amber-100"
                      >
                        Falar no WhatsApp sobre essa reserva
                      </a>
                    )}
                  </div>
                )}

                {clienteLookupStatus === 'not_found' && (
                  <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                    Nenhum cadastro compatível foi encontrado. Você pode seguir com uma nova reserva normalmente.
                  </div>
                )}

                {clienteLookupStatus === 'error' && (
                  <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                    Não foi possível buscar o cadastro anterior agora. Tente novamente em instantes.
                  </div>
                )}
              </div>

              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-emerald-900">Cupom de desconto</p>
                    <p className="mt-1 text-sm text-emerald-800">
                      Se você recebeu um código promocional, valide agora antes de seguir para o pagamento.
                    </p>
                  </div>
                  {cupomStatus === 'valid' ? (
                    <span className="rounded-full border border-emerald-300 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-800">
                      Aplicado
                    </span>
                  ) : null}
                </div>

                <div className="mt-4 flex flex-col gap-3 md:flex-row">
                  <input
                    type="text"
                    value={cupomCodigo}
                    onChange={(e) => {
                      setCupomCodigo(e.target.value.toUpperCase())
                      if (cupomStatus !== 'idle') {
                        setCupomStatus('idle')
                        setCupomInfo(null)
                      }
                    }}
                    className="flex-1 rounded-lg border-2 border-emerald-200 bg-white p-3 focus:border-emerald-400 focus:outline-none"
                    placeholder="Ex: CARNAVAL10"
                  />
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={validarCupom}
                      disabled={cupomLoading}
                      className="rounded-lg bg-emerald-600 px-4 py-3 font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-60"
                    >
                      {cupomLoading ? 'Validando...' : 'Validar cupom'}
                    </button>
                    {cupomStatus === 'valid' ? (
                      <button
                        type="button"
                        onClick={removerCupom}
                        className="rounded-lg border border-gray-300 bg-white px-4 py-3 font-semibold text-gray-700 transition hover:bg-gray-50"
                      >
                        Remover
                      </button>
                    ) : null}
                  </div>
                </div>

                {cupomStatus === 'valid' && cupomInfo ? (
                  <div className="mt-3 rounded-lg border border-emerald-200 bg-white px-4 py-3 text-sm text-emerald-900">
                    <p>
                      <strong>{cupomInfo.codigo}</strong> validado com sucesso.
                      {cupomInfo.tipo_desconto === 'PERCENTUAL'
                        ? ` Desconto de ${cupomInfo.valor_desconto}% aplicado nesta reserva.`
                        : ` Desconto fixo de R$ ${Number(cupomInfo.valor_desconto || 0).toFixed(2)} aplicado nesta reserva.`}
                    </p>
                    <p className="mt-2">
                      Total estimado com cupom: <strong>R$ {resumoValores.total.toFixed(2)}</strong>
                    </p>
                  </div>
                ) : null}

                {cupomStatus === 'invalid' ? (
                  <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                    {cupomInfo?.mensagem || 'O cupom informado não pode ser usado nesta reserva.'}
                  </div>
                ) : null}
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

              <div className="rounded-xl border border-blue-100 bg-blue-50/80 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-blue-900">Proteção anti-bot</p>
                    <p className="mt-1 text-sm text-blue-800">
                      Resolva o captcha antes de seguir para a etapa de pagamento.
                    </p>
                    <p className="mt-2 text-xs text-blue-700">
                      Isso reduz spam automatizado e valida a solicitação ainda na etapa de dados.
                    </p>
                  </div>
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${captchaBadge.classes}`}>
                    {captchaBadge.label}
                  </span>
                </div>

                <div className="mt-4 rounded-lg border border-white/70 bg-white/90 p-4">
                  {TURNSTILE_SITE_KEY ? (
                    <>
                      <div ref={turnstileContainerRef} className="min-h-[65px]" />
                      <p className="mt-3 text-xs text-gray-600">{captchaBadge.description}</p>
                    </>
                  ) : (
                    <p className="text-xs text-gray-600">
                      Captcha visível desativado neste ambiente. Configure as chaves para habilitar a validação.
                    </p>
                  )}
                </div>
              </div>

              {renderResumoFinanceiro('default')}
              
              <div className="flex gap-4 pt-4">
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 py-3 border-2 border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-all"
                >
                  ← Voltar
                </button>
                <button
                  onClick={() => setStep(4)}
                  disabled={Boolean(reservaAtivaCliente) || (TURNSTILE_SITE_KEY && !turnstileToken)}
                  className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition-all disabled:cursor-not-allowed disabled:bg-blue-300"
                >
                  Continuar →
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Step 4: Pagamento */}
        {step === 4 && quartoSelecionado && (
          <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-green-600 to-green-700 p-6">
              <h2 className="text-2xl font-bold text-white">💳 Forma de Pagamento</h2>
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
                  <p className="text-2xl font-bold text-green-600">R$ {resumoValores.total.toFixed(2)}</p>
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
                  metodoPagamento === 'tef' ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-green-300'
                }`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="tef"
                    checked={metodoPagamento === 'tef'}
                    onChange={(e) => setMetodoPagamento(e.target.value)}
                    className="hidden"
                  />
                  <div className="flex items-center gap-4">
                    <span className="text-3xl">🖥️</span>
                    <div>
                      <p className="font-bold text-gray-800">TEF (Maquininha)</p>
                      <p className="text-sm text-gray-600">Pagamento via CliSiTef no balcão</p>
                    </div>
                    {metodoPagamento === 'tef' && <span className="ml-auto text-green-600 font-bold">✓</span>}
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

              {renderResumoFinanceiro('compact')}
              
              <div className="flex gap-4 pt-4">
                <button
                  onClick={() => setStep(3)}
                  className="flex-1 py-3 border-2 border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-all"
                >
                  ← Voltar
                </button>
                <button
                  onClick={criarReserva}
                  disabled={loading || (TURNSTILE_SITE_KEY && !turnstileToken)}
                  className="flex-1 py-3 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 transition-all disabled:opacity-50"
                >
                  {loading ? '⏳ Processando...' : '✅ Confirmar Reserva'}
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Step 5: Confirmação */}
        {step === 5 && reservaConfirmada && (
          <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
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
                    <p className="text-sm text-gray-500">Valor Final</p>
                    <p className="font-bold text-green-600 text-xl">
                      R$ {(reservaConfirmada.reserva.valor_total_com_desconto ?? reservaConfirmada.reserva.valor_total).toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>

              {reservaConfirmada.reserva.cupom_uso ? (
                <div className="mb-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                  <h3 className="font-bold text-emerald-900">🎟️ Cupom aplicado</h3>
                  <div className="mt-3 grid gap-3 md:grid-cols-3">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-emerald-700">Código</p>
                      <p className="font-semibold text-emerald-900">{reservaConfirmada.reserva.cupom_uso.codigo}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-emerald-700">Desconto</p>
                      <p className="font-semibold text-emerald-900">
                        R$ {(reservaConfirmada.reserva.valor_desconto || 0).toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-emerald-700">Total final</p>
                      <p className="font-semibold text-emerald-900">
                        R$ {(reservaConfirmada.reserva.valor_total_com_desconto || reservaConfirmada.reserva.valor_total).toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              ) : null}
              
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
                  }}
                  className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all flex items-center justify-center gap-2"
                >
                  🏨 Nova Reserva
                </button>
              </div>
            </div>
          </div>
        )}
        
      </main>
      
      {/* Footer */}
      <footer className="bg-blue-950 text-white/80 py-8 mt-12">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <span className="text-3xl">🏨</span>
            <div>
              <h3 className="text-xl font-bold text-white">Hotel Real Cabo Frio</h3>
              <p className="text-yellow-400 text-sm">O melhor da região</p>
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
    </div>
  )
}

