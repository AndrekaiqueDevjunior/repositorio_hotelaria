'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

import { api } from '../../lib/api'
import GoldParticles from '@/components/GoldParticles'

import Header from './components/Header'
import Footer from './components/Footer'
import ProgressIndicator from './components/ProgressIndicator'
import StepDatas from './components/StepDatas'
import StepQuarto from './components/StepQuarto'
import StepDados from './components/StepDados'
import StepPagamento from './components/StepPagamento'
import StepConfirmacao from './components/StepConfirmacao'

import { useReservationForm } from './hooks/useReservationForm'
import { useGuestData } from './hooks/useGuestData'
import { useCustomerAuth } from './hooks/useCustomerAuth'
import { useCoupon } from './hooks/useCoupon'

import { onlyDigits, formatCPF, formatTelefone } from './utils/formatters'
import { isValidCPF, isValidEmail, isValidTelefone, normalizeCouponCode } from './utils/validators'

export default function Reservar() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [step, setStep] = useState(1)

  // Hooks customizados
  const reservation = useReservationForm()
  const guest = useGuestData()
  const auth = useCustomerAuth()
  const coupon = useCoupon()

  // Estados adicionais
  const [pontuacaoPorSuite, setPontuacaoPorSuite] = useState([])
  const [loyaltyInfo, setLoyaltyInfo] = useState(null)
  const [reservaConfirmada, setReservaConfirmada] = useState(null)
  const [loading, setLoading] = useState(false)

  const cpfLimpo = onlyDigits(guest.hospedeData.documento)
  const telefoneLimpo = onlyDigits(guest.hospedeData.telefone)

  // Valores da reserva
  const valoresReserva = useMemo(() => {
    const subtotal = Number(reservation.quartoSelecionado?.preco_total || 0)
    const desconto = coupon.cupomValidacao?.valido
      ? Number(coupon.cupomValidacao?.valor_desconto_calculado || 0)
      : 0
    const totalEstimado = coupon.cupomValidacao?.valido
      ? Number(coupon.cupomValidacao?.valor_final_estimado ?? subtotal - desconto)
      : subtotal

    return {
      subtotal,
      desconto,
      total: Math.max(totalEstimado, 0),
      percentualCupom: coupon.cupomValidacao?.valido
        ? Number(coupon.cupomValidacao?.valor_desconto || 10)
        : 0,
    }
  }, [reservation.quartoSelecionado, coupon.cupomValidacao])

  // Pontos estimados
  const pontosEstimados = useMemo(() => {
    if (!reservation.quartoSelecionado || !reservation.numDiarias) return null

    const suiteInfo = pontuacaoPorSuite.find(
      (item) => String(item.suite || '').toUpperCase() === String(reservation.quartoSelecionado.tipo || '').toUpperCase()
    )
    if (!suiteInfo) return null

    const pontosPorDiaria = Number(suiteInfo.pontos_por_diaria) || 0
    const pontosN = pontosPorDiaria * reservation.numDiarias
    if (pontosN <= 0) return null

    const multiplicador = Number(loyaltyInfo?.current_level?.multiplicador) || 1
    const pontosR = Math.ceil(pontosN * multiplicador)

    return {
      pontosN,
      pontosR,
      multiplicador,
      nivelNome: loyaltyInfo?.current_level_name || loyaltyInfo?.current_level?.nome,
    }
  }, [reservation.quartoSelecionado, reservation.numDiarias, pontuacaoPorSuite, loyaltyInfo])

  const getApiErrorMessage = (error, fallback) => {
    const detail = error?.response?.data?.detail
    if (Array.isArray(detail)) return detail[0]?.msg || fallback
    return detail || error?.message || fallback
  }

  // Carregar cupom do URL
  useEffect(() => {
    const codigoCupom = searchParams.get('cupom') || searchParams.get('codigo') || ''
    if (codigoCupom) {
      coupon.setCupomCodigo(normalizeCouponCode(codigoCupom))
    }
  }, [searchParams])

  // Carregar tabela de pontuação
  useEffect(() => {
    let isMounted = true
    api.get('/jornada/regras')
      .then((response) => {
        if (isMounted) setPontuacaoPorSuite(response.data?.pontuacao_por_suite || [])
      })
      .catch(() => {})
    return () => {
      isMounted = false
    }
  }, [])

  // Polling de disponibilidade
  useEffect(() => {
    if (step !== 2) return
    if (!reservation.searchData.data_checkin || !reservation.searchData.data_checkout) return

    const intervalMs = 10000
    const id = setInterval(() => {
      buscarDisponibilidade({ silent: true, keepStep: true })
    }, intervalMs)

    return () => clearInterval(id)
  }, [step, reservation.searchData.data_checkin, reservation.searchData.data_checkout])

  // Buscar disponibilidade
  const buscarDisponibilidade = async (options = {}) => {
    const { silent = false, keepStep = false } = options
    if (!reservation.searchData.data_checkin || !reservation.searchData.data_checkout) {
      if (!silent) toast.warning('Selecione as datas de check-in e check-out')
      return
    }

    if (reservation.searchData.data_checkout <= reservation.searchData.data_checkin) {
      if (!silent) toast.warning('Data de check-out deve ser posterior ao check-in')
      return
    }

    if (!silent) reservation.setLoading(true)

    try {
      const response = await api.get(`/public/quartos/disponiveis`, {
        params: {
          data_checkin: reservation.searchData.data_checkin,
          data_checkout: reservation.searchData.data_checkout
        }
      })

      const data = response.data

      if (data.success) {
        const tipos = data.tipos_disponiveis || []
        reservation.setTiposDisponiveis(tipos)
        reservation.setNumDiarias(data.num_diarias || 0)

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
      if (!silent) reservation.setLoading(false)
    }
  }

  // Buscar CPF
  const buscarCadastroCpf = async () => {
    if (!isValidCPF(cpfLimpo)) {
      toast.warning('Informe um CPF válido para autenticar a reserva')
      return
    }

    auth.setAuthLoading(true)
    try {
      const response = await api.get(`/customers/${cpfLimpo}`)
      const customer = response.data
      guest.applyCustomerData(customer)
      auth.setCustomer(customer)
      toast.success('Cadastro encontrado. Envie o código por WhatsApp.')
    } catch (error) {
      if (error?.response?.status === 404) {
        auth.setNotFound()
        guest.updateField('documento', formatCPF(cpfLimpo))
        toast.info('CPF ainda não cadastrado. Complete seus dados para criar o cadastro.')
      } else {
        toast.error(getApiErrorMessage(error, 'Erro ao consultar CPF'))
      }
    } finally {
      auth.setAuthLoading(false)
    }
  }

  // Criar cadastro
  const criarCadastroCustomer = async () => {
    if (!isValidCPF(cpfLimpo)) {
      toast.warning('CPF inválido')
      return
    }
    if (!guest.hospedeData.nome_completo || !guest.hospedeData.email || !guest.hospedeData.telefone) {
      toast.warning('Preencha nome, email e telefone para criar o cadastro')
      return
    }
    if (!isValidEmail(guest.hospedeData.email)) {
      toast.warning('Email inválido')
      return
    }
    if (!isValidTelefone(guest.hospedeData.telefone)) {
      toast.warning('Telefone inválido')
      return
    }

    auth.setAuthLoading(true)
    try {
      const response = await api.post('/customers/create', {
        nome_completo: guest.hospedeData.nome_completo.trim(),
        documento: cpfLimpo,
        email: guest.hospedeData.email.trim(),
        telefone: telefoneLimpo,
      })
      const customer = response.data
      guest.applyCustomerData(customer)
      auth.setCustomer(customer)
      toast.success('Cadastro criado. Agora envie o código por WhatsApp.')
    } catch (error) {
      if (error?.response?.status === 409) {
        toast.info('CPF já cadastrado. Vou buscar seus dados para autenticação.')
        await buscarCadastroCpf()
      } else {
        toast.error(getApiErrorMessage(error, 'Erro ao criar cadastro'))
      }
    } finally {
      auth.setAuthLoading(false)
    }
  }

  // Enviar OTP
  const enviarOtpCustomer = async () => {
    if (!auth.customerAuth.customer) {
      toast.warning('Consulte ou crie o cadastro antes de enviar o código')
      return
    }

    auth.setAuthLoading(true)
    try {
      const response = await api.post('/auth/otp/generate', {
        cpf: cpfLimpo,
      })
      auth.setOtpSent(response.data.otp_id, response.data.expires_in_seconds || 300)
      toast.success('Código enviado pelo WhatsApp')
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Erro ao enviar código por WhatsApp'))
    } finally {
      auth.setAuthLoading(false)
    }
  }

  // Validar OTP
  const validarOtpCustomer = async () => {
    if (!auth.customerAuth.otpId) {
      toast.warning('Envie o código por WhatsApp antes de validar')
      return
    }
    if (!/^\d{6}$/.test(auth.customerAuth.otpCode)) {
      toast.warning('Digite o código de 6 dígitos')
      return
    }

    auth.setAuthLoading(true)
    try {
      const response = await api.post('/auth/otp/validate', {
        otp_id: auth.customerAuth.otpId,
        code: auth.customerAuth.otpCode,
      })
      const customer = response.data.customer || auth.customerAuth.customer
      guest.applyCustomerData(customer)
      auth.setVerified(customer, response.data.access_token)
      toast.success('Cadastro autenticado. Você pode continuar a reserva.')

      // Carregar info de loyalty
      const documentoCliente = onlyDigits(customer?.documento || cpfLimpo)
      if (documentoCliente) {
        api.get(`/customers/${documentoCliente}/loyalty`)
          .then((res) => setLoyaltyInfo(res.data))
          .catch(() => {})
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Erro ao validar código'))
    } finally {
      auth.setAuthLoading(false)
    }
  }

  // Validar cupom
  const validarCupomReserva = async () => {
    const codigo = normalizeCouponCode(coupon.cupomCodigo)
    if (!codigo) {
      toast.warning('Informe um cupom para validar')
      return
    }
    if (!reservation.quartoSelecionado || !reservation.numDiarias) {
      toast.warning('Escolha uma suite antes de validar o cupom')
      return
    }

    coupon.setCupomLoading(true)
    coupon.setCupomValidacao(null)
    try {
      const payload = {
        codigo,
        suite_tipo: reservation.quartoSelecionado.tipo,
        num_diarias: reservation.numDiarias,
        valor_total_base: reservation.quartoSelecionado.preco_total,
      }
      if (auth.customerAuth.customer?.id) {
        payload.cliente_id = auth.customerAuth.customer.id
      }

      const response = await api.post('/cupons/validar', payload)
      coupon.setCupomCodigo(codigo)
      coupon.setCupomValidacao(response.data)
      if (response.data?.valido) {
        toast.success('Cupom validado. Ele sera confirmado junto com a reserva.')
      } else {
        toast.warning(response.data?.mensagem || 'Cupom invalido')
      }
    } catch (error) {
      coupon.setCupomValidacao({ valido: false, mensagem: getApiErrorMessage(error, 'Cupom invalido') })
    } finally {
      coupon.setCupomLoading(false)
    }
  }

  // Criar reserva
  const criarReserva = async () => {
    if (loading) return

    if (!auth.isAuthenticated) {
      toast.warning('Autentique seu cadastro por WhatsApp antes de confirmar a reserva')
      setStep(3)
      return
    }

    if (!guest.hospedeData.nome_completo || !guest.hospedeData.documento || !guest.hospedeData.email || !guest.hospedeData.telefone) {
      toast.warning('Preencha todos os campos obrigatórios')
      return
    }

    if (!isValidCPF(cpfLimpo)) {
      toast.warning('CPF inválido')
      return
    }

    if (onlyDigits(auth.customerAuth.customer?.documento) !== cpfLimpo) {
      toast.warning('O CPF autenticado não corresponde ao CPF informado')
      setStep(3)
      return
    }

    if (!isValidEmail(guest.hospedeData.email)) {
      toast.warning('Email inválido')
      return
    }

    setLoading(true)

    try {
      const payload = {
        nome_completo: guest.hospedeData.nome_completo,
        documento: cpfLimpo,
        email: guest.hospedeData.email,
        telefone: telefoneLimpo,
        quarto_numero: reservation.quartoSelecionado.numero,
        tipo_suite: reservation.quartoSelecionado.tipo,
        data_checkin: reservation.searchData.data_checkin,
        data_checkout: reservation.searchData.data_checkout,
        num_hospedes: guest.hospedeData.num_hospedes,
        num_criancas: guest.hospedeData.num_criancas,
        observacoes: guest.hospedeData.observacoes,
        metodo_pagamento: 'tef',
        customer_auth_token: auth.customerAuth.accessToken
      }

      const cupomNormalizado = normalizeCouponCode(coupon.cupomCodigo)
      if (cupomNormalizado) {
        payload.cupom_codigo = cupomNormalizado
      }

      const idempotencyKey = typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : `reserva-${Date.now()}-${Math.random().toString(16).slice(2)}`

      const response = await api.post('/public/reservas', payload, {
        headers: { 'Idempotency-Key': idempotencyKey }
      })

      const data = response.data

      if (data.success) {
        setReservaConfirmada(data)
        toast.success('🎉 Reserva confirmada com sucesso!')
        setStep(5)
      } else {
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

      if (error.code === 'ECONNREFUSED') {
        toast.error('❌ Servidor indisponível. Tente novamente em alguns instantes.')
      } else if ([401, 403].includes(error.response?.status)) {
        toast.error('❌ Autenticação expirada ou CPF divergente. Valide o código novamente.')
        auth.resetOtp()
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

  // Reset para nova reserva
  const resetarTudo = () => {
    setStep(1)
    setReservaConfirmada(null)
    reservation.resetarBusca()
    guest.resetarDados()
    auth.reset()
    coupon.reset()
  }

  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-[#050403] text-white">
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[#050403]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(218,166,55,0.18),transparent_22rem),radial-gradient(circle_at_12%_34%,rgba(157,91,8,0.22),transparent_18rem),radial-gradient(circle_at_88%_28%,rgba(246,198,55,0.11),transparent_16rem),radial-gradient(circle_at_50%_82%,rgba(92,36,145,0.12),transparent_18rem)]" />
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(0,0,0,0.16)_0%,rgba(5,4,3,0.86)_44%,#050403_100%)]" />
      </div>

      <GoldParticles />

      <Header />
      <ProgressIndicator currentStep={step} />

      <main className="relative z-30 mx-auto w-full max-w-[820px] flex-1 px-4 pb-12 sm:px-8">
        {step === 1 && (
          <StepDatas
            searchData={reservation.searchData}
            onSearchDataChange={reservation.handleSearchDataChange}
            onBuscar={buscarDisponibilidade}
            loading={reservation.loading}
            today={reservation.today}
          />
        )}

        {step === 2 && (
          <StepQuarto
            searchData={reservation.searchData}
            tiposDisponiveis={reservation.tiposDisponiveis}
            numDiarias={reservation.numDiarias}
            onSelecionarQuarto={(tipo, quarto) => {
              coupon.reset()
              reservation.selecionarQuarto(tipo, quarto)
              setStep(3)
            }}
            onVoltar={() => setStep(1)}
          />
        )}

        {step === 3 && reservation.quartoSelecionado && (
          <StepDados
            hospedeData={guest.hospedeData}
            onUpdateField={guest.updateField}
            quartoSelecionado={reservation.quartoSelecionado}
            numDiarias={reservation.numDiarias}
            customerAuth={auth.customerAuth}
            onBuscarCpf={buscarCadastroCpf}
            onCriarCadastro={criarCadastroCustomer}
            onEnviarOtp={enviarOtpCustomer}
            onValidarOtp={validarOtpCustomer}
            authLoading={auth.authLoading}
            isAuthenticated={auth.isAuthenticated}
            onVoltar={() => setStep(2)}
            onContinuar={() => setStep(4)}
          />
        )}

        {step === 4 && reservation.quartoSelecionado && (
          <StepPagamento
            hospedeData={guest.hospedeData}
            quartoSelecionado={reservation.quartoSelecionado}
            searchData={reservation.searchData}
            numDiarias={reservation.numDiarias}
            valoresReserva={valoresReserva}
            pontosEstimados={pontosEstimados}
            cupomCodigo={coupon.cupomCodigo}
            cupomValidacao={coupon.cupomValidacao}
            cupomLoading={coupon.cupomLoading}
            onCupomCodigoChange={(code) => {
              coupon.setCupomCodigo(normalizeCouponCode(code))
              coupon.setCupomValidacao(null)
            }}
            onValidarCupom={validarCupomReserva}
            onVoltar={() => setStep(3)}
            onConfirmarReserva={criarReserva}
            loading={loading}
          />
        )}

        {step === 5 && reservaConfirmada && (
          <StepConfirmacao
            reservaConfirmada={reservaConfirmada}
            onNovaReserva={resetarTudo}
          />
        )}
      </main>

      <Footer />

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
