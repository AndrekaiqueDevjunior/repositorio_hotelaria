'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../lib/api'
import {
  NFPAG_COLLECTION_LABELS,
  NFPAG_FIELD_OPTIONS,
  NFPAG_TYPE_LABELS,
  buildNfpagExtras,
  buildNfpagString,
  getNfpagFieldPlaceholder,
  getNfpagTypeDetail,
  getNfpagTypeOptions,
  getClisitefStatusDescription,
  getTefEventDescription,
  getTefEventTone,
  normalizeTefFlag,
  parseNfpagValor
} from '../lib/tefHelpers'
import UploadComprovanteModal from './UploadComprovanteModal'

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value || 0)
}

const escapeTipoCampo = (value) => String(value || '').replace(/\n/g, '\\n')

const resolveTimeoutMs = (value, fallback) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

const TEF_IDLE_TIMEOUT_MS = Math.max(resolveTimeoutMs(process.env.NEXT_PUBLIC_TEF_IDLE_TIMEOUT_MS, 300000), 60000)
const TEF_IDLE_TIMEOUT_SECONDS = Math.max(Math.round(TEF_IDLE_TIMEOUT_MS / 1000), 60)
const TEF_REQUEST_TIMEOUT_MS = resolveTimeoutMs(process.env.NEXT_PUBLIC_TEF_REQUEST_TIMEOUT_MS, 180000)
const TEF_PROCESSING_POLL_DELAY_MS = 800

const defaultValorPrompt = (prompt) => {
  if (Number(prompt?.command_id) === 22) {
    return ''
  }
  if (prompt?.field_is_secret || Number(prompt?.field_id) === 500) {
    return ''
  }
  return prompt?.default_value || ''
}

const resolveInputMode = (commandId) => {
  if (commandId === 31) return 'linha'
  if (commandId === 35) return 'manual'
  return 'manual'
}

const isAutoProcessingPrompt = (prompt) => Number(prompt?.command_id) === 3

const parseMenuOptions = (commandId, promptText) => {
  const raw = String(promptText || '').trim()
  if (!raw) return []

  if (commandId === 21) {
    return raw
      .split(';')
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => {
        const [index, ...textParts] = part.split(':')
        const text = textParts.join(':').trim()
        if (!index || !text) return null
        return { index: index.trim(), text }
      })
      .filter(Boolean)
  }

  if (commandId === 42) {
    const [classePart, rest] = raw.split('|')
    const classe = (classePart || '').trim()
    if (!rest) return []
    return rest
      .split(';')
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => {
        const [index, text, code, type] = part.split(':').map((value) => (value || '').trim())
        if (!index || !text) return null
        return { index, text, code, type, classe }
      })
      .filter(Boolean)
  }

  return []
}

const resolveMensagemLabel = (target) => {
  if (Number(target) === 1) return 'Operador'
  if (Number(target) === 2) return 'Cliente'
  if (Number(target) === 3) return 'Ambos'
  return 'Mensagem'
}

const buildInputValue = (prompt, value, inputMode) => {
  const commandId = Number(prompt?.command_id)
  const fieldId = Number(prompt?.field_id)
  if (commandId === 31) {
    const prefix = inputMode === 'cmc7_leitor' ? '1' : inputMode === 'cmc7_digitado' ? '2' : '0'
    return `${prefix}:${value}`
  }
  if (commandId === 35) {
    const prefix = inputMode === 'leitor' ? '1' : '0'
    return `${prefix}:${value}`
  }
  if (fieldId === 601) {
    const digits = String(value || '').replace(/\D/g, '')
    return digits || value
  }
  return value
}

const formatFloatInput = (value, decimals) => {
  const raw = String(value || '')
  const digits = raw.replace(/\D/g, '')
  if (!digits) return ''
  if (!Number.isFinite(decimals) || decimals <= 0) return digits
  const padded = digits.padStart(decimals + 1, '0')
  const intPart = padded.slice(0, -decimals)
  const decPart = padded.slice(-decimals)
  return `${intPart},${decPart}`
}

const toneClasses = {
  green: 'border-green-200 bg-green-50 text-green-800',
  red: 'border-red-200 bg-red-50 text-red-800',
  amber: 'border-amber-200 bg-amber-50 text-amber-800',
  sky: 'border-sky-200 bg-sky-50 text-sky-800'
}

const renderTefEventInfo = (payload) => {
  const eventoAtual = payload?.evento_atual
  const eventos = Array.isArray(payload?.eventos) ? payload.eventos.slice(-6) : []
  if (!eventoAtual && eventos.length === 0) return null

  const tone = toneClasses[getTefEventTone(eventoAtual?.codigo)] || toneClasses.sky

  return (
    <div className={`mb-4 rounded border px-4 py-3 ${tone}`}>
      <p className="font-semibold">Evento TEF / PinPad</p>
      {eventoAtual && (
        <div className="mt-1 text-sm space-y-1">
          <p>
            Atual: <span className="font-mono">{eventoAtual?.codigo}</span> - {eventoAtual?.descricao || getTefEventDescription(eventoAtual?.codigo)}
          </p>
          {eventoAtual?.valor && (
            <pre className="whitespace-pre-wrap text-xs bg-white/60 border border-current/20 rounded p-2">{eventoAtual.valor}</pre>
          )}
        </div>
      )}
      {eventos.length > 0 && (
        <div className="mt-3 text-xs space-y-1">
          <p className="font-semibold">Historico recente</p>
          {eventos.map((evento, index) => (
            <div key={`${evento?.codigo || 'evento'}-${index}`} className="font-mono">
              {evento?.codigo} - {evento?.descricao || getTefEventDescription(evento?.codigo)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const renderTefReimpressaoInfo = (reimpressao) => {
  const clienteDisponivel = normalizeTefFlag(reimpressao?.cupom_cliente_disponivel)
  const estabelecimentoDisponivel = normalizeTefFlag(reimpressao?.cupom_estabelecimento_disponivel)
  const diasDisponiveis = reimpressao?.dias_disponiveis
  const hasDias = diasDisponiveis !== undefined && diasDisponiveis !== null && String(diasDisponiveis).trim() !== ''

  if (!clienteDisponivel && !estabelecimentoDisponivel && !hasDias) return null

  return (
    <div className="mb-4 rounded border border-violet-200 bg-violet-50 px-4 py-3 text-violet-900">
      <p className="font-semibold">Retaguarda / Reimpressao SiTef</p>
      <div className="mt-1 text-sm space-y-1">
        <p>Cupom cliente na base do SiTef: {clienteDisponivel ? 'Sim' : 'Nao'}</p>
        <p>Cupom estabelecimento na base do SiTef: {estabelecimentoDisponivel ? 'Sim' : 'Nao'}</p>
        {hasDias && <p>Prazo informado pelo SiTef: {diasDisponiveis} dia(s)</p>}
      </div>
    </div>
  )
}

export default function ModalEscolhaPagamento({ reserva, onClose, onSuccess }) {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [pagamentoCriado, setPagamentoCriado] = useState(null)
  const tefSessionRef = useRef(null)
  const tefStartRequestedRef = useRef(false)
  const tefIdleTimerRef = useRef(null)

  const [showTefFlow, setShowTefFlow] = useState(false)
  const [tefSessionId, setTefSessionId] = useState(null)
  const [tefPrompt, setTefPrompt] = useState(null)
  const [tefInput, setTefInput] = useState('')
  const [tefInputMode, setTefInputMode] = useState('manual')
  const [tefProcessando, setTefProcessando] = useState(false)
  const [tefErro, setTefErro] = useState('')
  const [tefResultado, setTefResultado] = useState(null)
  const [pendenciaStatus, setPendenciaStatus] = useState('')
  const [cupomDialog, setCupomDialog] = useState({ open: false, titulo: '', conteudo: '' })
  const [cupomQueue, setCupomQueue] = useState([])
  const [comprovanteMetodo, setComprovanteMetodo] = useState('')
  const [comprovanteEmail, setComprovanteEmail] = useState('')
  const [comprovanteTelefone, setComprovanteTelefone] = useState('')
  const [comprovanteEntregue, setComprovanteEntregue] = useState(false)
  const [comprovanteErro, setComprovanteErro] = useState('')
  const [impressaoCliente, setImpressaoCliente] = useState(false)
  const [impressaoEstabelecimento, setImpressaoEstabelecimento] = useState(false)
  const [enviandoComprovante, setEnviandoComprovante] = useState(false)
  const [nfpagRaw, setNfpagRaw] = useState('')
  const [nfpagItems, setNfpagItems] = useState([])
  const [nfpagTipo, setNfpagTipo] = useState('')
  const [nfpagValor, setNfpagValor] = useState('')
  const [nfpagExtraFields, setNfpagExtraFields] = useState({})
  const [nfpagError, setNfpagError] = useState('')

  const opcoesPagamento = [
    {
      id: 'pix',
      nome: 'PIX',
      descricao: 'Pagamento instantaneo via PIX',
      disponivel: true,
      action: 'pix'
    },
    {
      id: 'cartao_online',
      nome: 'Cartao Online',
      descricao: 'Pagamento com cartao de credito/debito',
      disponivel: true,
      action: 'cielo'
    },
    {
      id: 'tef',
      nome: 'TEF (Cartao na Maquininha)',
      descricao: 'Pagamento TEF com fluxo interativo no padrao Agente CliSiTef',
      disponivel: true,
      action: 'tef'
    },
    {
      id: 'balcao',
      nome: 'Pagamento no Balcao',
      descricao: 'Pagamento presencial (dinheiro ou cartao na maquininha)',
      disponivel: true,
      action: 'comprovante'
    }
  ]

  const valorReserva = useMemo(() => {
    return Number(reserva?.valor_total || reserva?.valor_previsto || 0)
  }, [reserva])

  const nfpagTypeOptions = useMemo(() => getNfpagTypeOptions(tefResultado?.nfpag), [tefResultado])
  const nfpagSelectedType = useMemo(() => getNfpagTypeDetail(tefResultado?.nfpag, nfpagTipo), [tefResultado, nfpagTipo])

  const formatarDataHostNfpag = (value) => {
    const digits = String(value || '').replace(/\D/g, '')
    if (digits.length >= 8) {
      return `${digits.slice(6, 8)}${digits.slice(4, 6)}${digits.slice(0, 4)}`
    }
    return ''
  }

  const buildDefaultNfpagFields = (typeCode) => {
    const detail = getNfpagTypeDetail(tefResultado?.nfpag, typeCode)
    const defaults = {}
    ;(detail?.coletas_detalhes || []).forEach((coleta) => {
      const codigo = String(coleta?.codigo || '').padStart(2, '0')
      if (codigo === '03') defaults[codigo] = tefResultado?.rede_autorizadora || ''
      if (codigo === '04') defaults[codigo] = tefResultado?.nsu_sitef || ''
      if (codigo === '07') defaults[codigo] = tefResultado?.nsu_host || tefResultado?.nsu || ''
      if (codigo === '08') defaults[codigo] = formatarDataHostNfpag(tefResultado?.data_hora_transacao)
      if (codigo === '09') defaults[codigo] = tefResultado?.codigo_estabelecimento || ''
      if (codigo === '11') defaults[codigo] = tefResultado?.autorizacao || ''
      if (codigo === '14') defaults[codigo] = tefResultado?.bandeira || ''
    })
    return defaults
  }

  const resetTefFlow = () => {
    if (tefIdleTimerRef.current) {
      clearTimeout(tefIdleTimerRef.current)
      tefIdleTimerRef.current = null
    }
    tefSessionRef.current = null
    tefStartRequestedRef.current = false
    setTefSessionId(null)
    setTefPrompt(null)
    setTefInput('')
    setTefInputMode('manual')
    setTefErro('')
    setTefResultado(null)
    setTefProcessando(false)
    setComprovanteMetodo('')
    setComprovanteEmail('')
    setComprovanteTelefone('')
    setComprovanteEntregue(false)
    setComprovanteErro('')
    setImpressaoCliente(false)
    setImpressaoEstabelecimento(false)
    setEnviandoComprovante(false)
    setNfpagRaw('')
    setNfpagItems([])
    setNfpagTipo('')
    setNfpagValor('')
    setNfpagExtraFields({})
    setNfpagError('')
    setPendenciaStatus('')
  }

  const abrirFluxoTef = async () => {
    resetTefFlow()
    setShowTefFlow(true)
    tefStartRequestedRef.current = true
    await iniciarFluxoTef()
  }

  const iniciarTimeoutInatividade = () => {
    if (tefIdleTimerRef.current) {
      clearTimeout(tefIdleTimerRef.current)
    }
    tefIdleTimerRef.current = setTimeout(() => {
      encerrarFluxoTef(`Sessao TEF expirada por inatividade (${TEF_IDLE_TIMEOUT_SECONDS}s).`)
    }, TEF_IDLE_TIMEOUT_MS)
  }

  const registrarAtividadeTef = () => {
    if (!showTefFlow) return
    iniciarTimeoutInatividade()
  }

  const encerrarFluxoTef = async (motivo) => {
    if (motivo) {
      toast.error(motivo)
    }
    await cancelarSessaoTef()
    setShowTefFlow(false)
    resetTefFlow()
    setCupomDialog({ open: false, titulo: '', conteudo: '' })
    setCupomQueue([])
  }

  const finalizarOperacaoTef = async (motivo) => {
    await encerrarFluxoTef(motivo)
    if (onClose) onClose()
  }

  const cancelarSessaoTef = async () => {
    const sessionIdAtual = tefSessionRef.current || tefSessionId || tefPrompt?.session_id
    if (!sessionIdAtual) return
    try {
      await api.post('/pagamentos/tef/cancelar', {
        session_id: sessionIdAtual
      }, { timeout: TEF_REQUEST_TIMEOUT_MS })
    } catch (err) {
      console.error('Erro ao cancelar sessao TEF:', err)
    }
  }

  const imprimirTexto = (titulo, texto) => {
    if (!texto) return
    const janela = window.open('', '_blank')
    if (!janela) return

    janela.document.write(`
      <html>
        <head>
          <title>${titulo}</title>
          <style>
            body { font-family: monospace; padding: 16px; }
            pre { white-space: pre-wrap; font-size: 12px; }
          </style>
        </head>
        <body>
          <h2>${titulo}</h2>
          <pre>${texto}</pre>
        </body>
      </html>
    `)
    janela.document.close()
    janela.focus()
    janela.print()
  }

  const imprimirCupom = (tipo, conteudo) => {
    if (!conteudo) return
    if (tipo === 'cliente') {
      imprimirTexto('Cupom Cliente', conteudo)
      setImpressaoCliente(true)
    } else {
      imprimirTexto('Cupom Estabelecimento', conteudo)
      setImpressaoEstabelecimento(true)
    }
    setComprovanteErro('')
  }

  const enviarComprovanteEmail = async () => {
    const email = comprovanteEmail.trim()
    if (!email) {
      setComprovanteErro('Informe o e-mail para envio do comprovante.')
      return
    }
    setComprovanteErro('')
    setEnviandoComprovante(true)
    try {
      const res = await api.post('/pagamentos/tef/enviar-comprovante', {
        email,
        cupom_cliente: tefResultado?.cupom_cliente || tefResultado?.tef_cupom_cliente || '',
        cupom_estabelecimento: tefResultado?.cupom_estabelecimento || tefResultado?.tef_cupom_estabelecimento || '',
        nsu: tefResultado?.nsu,
        autorizacao: tefResultado?.autorizacao
      }, { timeout: TEF_REQUEST_TIMEOUT_MS })

      if (res.data?.success) {
        setComprovanteEntregue(true)
        setComprovanteErro('')
      } else {
        setComprovanteErro(res.data?.error || 'Falha ao enviar comprovante')
      }
    } catch (err) {
      setComprovanteErro(err.response?.data?.detail || 'Falha ao enviar comprovante')
    } finally {
      setEnviandoComprovante(false)
    }
  }

  const enviarComprovanteSms = async () => {
    const telefone = comprovanteTelefone.trim()
    if (!telefone) {
      setComprovanteErro('Informe o telefone para envio do comprovante.')
      return
    }
    setComprovanteErro('')
    setEnviandoComprovante(true)
    try {
      const res = await api.post('/pagamentos/tef/enviar-sms', {
        telefone,
        cupom_cliente: tefResultado?.cupom_cliente || tefResultado?.tef_cupom_cliente || '',
        cupom_estabelecimento: tefResultado?.cupom_estabelecimento || tefResultado?.tef_cupom_estabelecimento || '',
        nsu: tefResultado?.nsu,
        autorizacao: tefResultado?.autorizacao
      }, { timeout: TEF_REQUEST_TIMEOUT_MS })

      if (res.data?.success) {
        setComprovanteEntregue(true)
        setComprovanteErro('')
      } else {
        setComprovanteErro(res.data?.error || 'Falha ao enviar comprovante')
      }
    } catch (err) {
      setComprovanteErro(err.response?.data?.detail || 'Falha ao enviar comprovante')
    } finally {
      setEnviandoComprovante(false)
    }
  }

  const atualizarCampoNfpag = (codigo, valor) => {
    setNfpagExtraFields((prev) => ({
      ...prev,
      [String(codigo || '').padStart(2, '0')]: valor
    }))
  }

  const selecionarTipoNfpag = (tipo) => {
    const rawTipo = String(tipo || '').trim()
    if (!rawTipo) {
      setNfpagTipo('')
      setNfpagExtraFields({})
      setNfpagError('')
      return
    }
    const codigo = rawTipo.padStart(2, '0')
    setNfpagTipo(codigo)
    setNfpagExtraFields(buildDefaultNfpagFields(codigo))
    setNfpagError('')
  }

  const adicionarNfpagItem = () => {
    const rawTipo = String(nfpagTipo || '').trim()
    const tipo = rawTipo ? rawTipo.padStart(2, '0') : ''
    const valor = parseNfpagValor(nfpagValor)
    const maxFormas = Number(tefResultado?.nfpag?.max_formas)

    if (!tipo || !valor) {
      setNfpagError('Informe a forma de pagamento e o valor antes de adicionar.')
      return
    }

    if (Number.isFinite(maxFormas) && maxFormas > 0 && nfpagItems.length >= maxFormas) {
      setNfpagError(`A CliSiTef limitou o NFPAG a ${maxFormas} forma(s).`)
      return
    }

    const detalhesTipo = getNfpagTypeDetail(tefResultado?.nfpag, tipo)
    const coletasObrigatorias = (detalhesTipo?.coletas_detalhes || []).filter((coleta) => {
      const codigo = String(coleta?.codigo || '').padStart(2, '0')
      return !['00', '05', '13'].includes(codigo)
    })
    const faltantes = coletasObrigatorias.filter((coleta) => !String(nfpagExtraFields?.[coleta.codigo] || '').trim())

    if (faltantes.length > 0) {
      const nomes = faltantes.map((coleta) => coleta.descricao || NFPAG_COLLECTION_LABELS[coleta.codigo] || coleta.codigo).join(', ')
      setNfpagError(`Preencha os campos obrigatorios do NFPAG: ${nomes}.`)
      return
    }

    const novo = {
      tipo,
      descricao: detalhesTipo?.descricao || NFPAG_TYPE_LABELS[tipo] || 'Forma nao mapeada',
      valor,
      extras: buildNfpagExtras(nfpagExtraFields),
      extra_fields: { ...nfpagExtraFields },
      coletas_detalhes: detalhesTipo?.coletas_detalhes || []
    }

    setNfpagItems((prev) => [...prev, novo])
    setNfpagTipo('')
    setNfpagValor('')
    setNfpagExtraFields({})
    setNfpagError('')
  }

  const removerNfpagItem = (index) => {
    setNfpagItems((prev) => prev.filter((_, i) => i !== index))
  }

  const aplicarNfpagGerado = () => {
    const gerado = buildNfpagString(nfpagItems)
    if (!gerado) {
      setNfpagError('Nenhuma forma de pagamento adicionada.')
      return
    }
    setNfpagRaw(`NFPAG=${gerado}`)
    setNfpagError('')
  }

  const abrirCupomDialog = (titulo, conteudo) => {
    setCupomDialog({
      open: true,
      titulo,
      conteudo: conteudo || 'Nao retornado'
    })
  }

  useEffect(() => {
    if (!tefResultado) return
    setComprovanteMetodo('')
    setComprovanteEmail('')
    setComprovanteTelefone('')
    setComprovanteEntregue(false)
    setComprovanteErro('')
    setImpressaoCliente(false)
    setImpressaoEstabelecimento(false)
    const cupomEstabelecimento = tefResultado?.cupom_estabelecimento || tefResultado?.tef_cupom_estabelecimento || ''
    const cupomCliente = tefResultado?.cupom_cliente || tefResultado?.tef_cupom_cliente || ''

    const fila = []
    if (cupomEstabelecimento) {
      fila.push({ titulo: 'Cupom Estabelecimento', conteudo: cupomEstabelecimento })
    }
    if (cupomCliente) {
      fila.push({ titulo: 'Cupom Cliente', conteudo: cupomCliente })
    }

    if (fila.length > 0) {
      setCupomQueue(fila.slice(1))
      setCupomDialog({ open: true, titulo: fila[0].titulo, conteudo: fila[0].conteudo })
    }

    const tipos = getNfpagTypeOptions(tefResultado?.nfpag)
    if (tipos.length === 1) {
      setNfpagTipo(tipos[0].codigo)
      setNfpagExtraFields(buildDefaultNfpagFields(tipos[0].codigo))
    } else {
      setNfpagTipo('')
      setNfpagExtraFields({})
    }
  }, [tefResultado])

  useEffect(() => {
    const buscarPendencias = async () => {
      if (!showTefFlow) return
      try {
        const res = await api.get('/pagamentos/tef/pendencias/status')
        const message = res.data?.message
        if (message) {
          setPendenciaStatus(message)
        }
      } catch (err) {
        console.error('Erro ao buscar pendencias TEF:', err)
      }
    }
    buscarPendencias()
  }, [showTefFlow])

  useEffect(() => {
    if (!tefResultado || comprovanteMetodo !== 'impressao') return
    const cupomEstabelecimento = tefResultado?.cupom_estabelecimento || tefResultado?.tef_cupom_estabelecimento || ''
    const cupomCliente = tefResultado?.cupom_cliente || tefResultado?.tef_cupom_cliente || ''
    const clienteOk = !cupomCliente || impressaoCliente
    const estabelecimentoOk = !cupomEstabelecimento || impressaoEstabelecimento
    setComprovanteEntregue(clienteOk && estabelecimentoOk)
  }, [tefResultado, comprovanteMetodo, impressaoCliente, impressaoEstabelecimento])

  const fecharCupomDialog = () => {
    if (cupomQueue.length > 0) {
      const [next, ...rest] = cupomQueue
      setCupomQueue(rest)
      setCupomDialog({ open: true, titulo: next.titulo, conteudo: next.conteudo })
      return
    }
    setCupomDialog({ open: false, titulo: '', conteudo: '' })
  }

  const montarResumoTipoCampo = (resultado) => {
    const tipoCampos = Array.isArray(resultado?.tipo_campos)
      ? resultado.tipo_campos.filter((item) => String(item?.TipoCampo) !== '500')
      : []
    if (tipoCampos.length > 0) {
      return tipoCampos.map((item) => `{"TipoCampo":"${item.TipoCampo}","Valor":"${escapeTipoCampo(item.Valor)}"}`).join(',\n')
    }

    const rede = resultado?.rede_autorizadora || ''
    const bandeira = resultado?.bandeira || ''
    const nsuSitef = resultado?.nsu_sitef || ''
    const nsuHost = resultado?.nsu_host || resultado?.nsu || resultado?.tef_nsu || ''
    const aut = resultado?.autorizacao || resultado?.tef_autorizacao || ''
    const cupomCliente = resultado?.cupom_cliente || resultado?.tef_cupom_cliente || ''
    const cupomEstabelecimento = resultado?.cupom_estabelecimento || resultado?.tef_cupom_estabelecimento || ''

    return [
      `{"TipoCampo":"131","Valor":"${escapeTipoCampo(rede)}"}`,
      `{"TipoCampo":"132","Valor":"${escapeTipoCampo(bandeira)}"}`,
      `{"TipoCampo":"133","Valor":"${escapeTipoCampo(nsuSitef)}"}`,
      `{"TipoCampo":"134","Valor":"${escapeTipoCampo(nsuHost)}"}`,
      `{"TipoCampo":"135","Valor":"${escapeTipoCampo(aut)}"}`,
      `{"TipoCampo":"121","Valor":"${escapeTipoCampo(cupomCliente)}"}`,
      `{"TipoCampo":"122","Valor":"${escapeTipoCampo(cupomEstabelecimento)}"}`
    ].join(',\n')
  }

  const renderMensagens = (messages) => {
    if (!Array.isArray(messages) || messages.length === 0) return null

    return (
      <div className="space-y-2 mb-4">
        {messages.map((msg, index) => (
          <div key={`${msg?.target || 'msg'}-${index}`} className="bg-white border border-zinc-300 px-3 py-2 rounded text-sm space-y-2">
            <pre className="whitespace-pre-wrap font-mono text-sm text-zinc-900">{msg?.text || ''}</pre>
            <pre className="whitespace-pre-wrap text-xs text-zinc-600">{`MsgCliSiTef

Destino: ${resolveMensagemLabel(msg?.target)}`}</pre>
          </div>
        ))}
      </div>
    )
  }

  const aplicarRespostaInterativa = (payload) => {
    if (payload?.session_id) {
      tefSessionRef.current = payload.session_id
      setTefSessionId(payload.session_id)
    }

    if (payload?.success === false) {
      if (tefIdleTimerRef.current) {
        clearTimeout(tefIdleTimerRef.current)
        tefIdleTimerRef.current = null
      }
      setTefErro(payload?.error || 'Erro no fluxo TEF')
      return
    }

    if (payload?.finish_required) {
      setTefPrompt(null)
      setTefResultado(payload)
      setTefInput('')
      iniciarTimeoutInatividade()
      return
    }

    setTefResultado(null)
    setTefPrompt(payload)
    setTefInput(defaultValorPrompt(payload))
    setTefInputMode(resolveInputMode(Number(payload?.command_id)))
    iniciarTimeoutInatividade()
  }
  useEffect(() => {
    if (!showTefFlow || tefResultado || tefProcessando || !isAutoProcessingPrompt(tefPrompt)) {
      return undefined
    }

    const timer = setTimeout(() => {
      continuarFluxoTef(0, '')
    }, TEF_PROCESSING_POLL_DELAY_MS)

    return () => clearTimeout(timer)
  }, [showTefFlow, tefResultado, tefProcessando, tefPrompt])

  const iniciarFluxoTef = async () => {
    try {
      if (!reserva?.id) {
        setTefErro('Reserva invalida. Recarregue a pagina e tente novamente.')
        return
      }

      if (!valorReserva || Number.isNaN(valorReserva)) {
        setTefErro('Valor da reserva invalido. Recarregue a pagina e tente novamente.')
        return
      }

      setTefErro('')
      setTefProcessando(true)

      const res = await api.post('/pagamentos/tef/iniciar', {
        reserva_id: parseInt(reserva.id, 10),
        valor: valorReserva
      }, { timeout: TEF_REQUEST_TIMEOUT_MS })

      aplicarRespostaInterativa(res.data)
    } catch (err) {
      console.error('Erro ao iniciar fluxo TEF:', err)
      setTefErro(err.response?.data?.detail || 'Erro ao iniciar fluxo TEF')
    } finally {
      setTefProcessando(false)
    }
  }

  const continuarFluxoTef = async (continueFlag = 0, value = tefInput) => {
    try {
      const sessionIdAtual = tefSessionRef.current || tefSessionId || tefPrompt?.session_id
      if (!sessionIdAtual) {
        setTefErro('Sessao TEF nao encontrada.')
        return
      }

      const senhaObrigatoria = Boolean(tefPrompt?.field_is_secret || Number(tefPrompt?.field_id) === 500)
      if (senhaObrigatoria && !String(value || '').trim()) {
        setTefErro('Senha do supervisor obrigatoria.')
        return
      }

      setTefErro('')
      setTefProcessando(true)

      let payloadValue = continueFlag === 0
        ? buildInputValue(tefPrompt, value, tefInputMode)
        : value

      if (continueFlag === 0 && (Number(tefPrompt?.command_id) === 31 || Number(tefPrompt?.command_id) === 35)) {
        const trimmed = String(value || '').trim()
        if (trimmed.startsWith('0:') || trimmed.startsWith('1:') || trimmed.startsWith('2:')) {
          payloadValue = trimmed
        }
      }

      const res = await api.post('/pagamentos/tef/continuar', {
        session_id: sessionIdAtual,
        continue_flag: continueFlag,
        data: payloadValue
      }, { timeout: TEF_REQUEST_TIMEOUT_MS })

      aplicarRespostaInterativa(res.data)
    } catch (err) {
      console.error('Erro ao continuar fluxo TEF:', err)
      setTefErro(err.response?.data?.detail || 'Erro ao continuar fluxo TEF')
    } finally {
      setTefProcessando(false)
    }
  }

  const concluirFluxoTef = async () => {
    try {
      const sessionIdAtual = tefSessionRef.current || tefSessionId || tefResultado?.session_id
      if (!sessionIdAtual) {
        setTefErro('Sessao TEF nao encontrada.')
        return
      }

      const cupomEstabelecimento = tefResultado?.cupom_estabelecimento || tefResultado?.tef_cupom_estabelecimento || ''
      const cupomCliente = tefResultado?.cupom_cliente || tefResultado?.tef_cupom_cliente || ''
      const precisaEntrega = Boolean(tefResultado?.aprovado && (cupomEstabelecimento || cupomCliente))
      if (precisaEntrega && !comprovanteEntregue) {
        setComprovanteErro('Selecione e conclua a entrega do comprovante antes de finalizar.')
        return
      }

      setTefErro('')
      setComprovanteErro('')
      setTefProcessando(true)

      const res = await api.post('/pagamentos/tef/finalizar', {
        session_id: sessionIdAtual,
        reserva_id: parseInt(reserva.id, 10),
        valor: valorReserva,
        confirm: Boolean(tefResultado?.aprovado),
        numero_pagamento_nfpag: tefResultado?.nfpag?.numero_pagamento || undefined,
        nfpag_raw: nfpagRaw || undefined
      }, { timeout: TEF_REQUEST_TIMEOUT_MS })

      if (tefIdleTimerRef.current) {
        clearTimeout(tefIdleTimerRef.current)
        tefIdleTimerRef.current = null
      }
      setPagamentoCriado(res.data)
      tefSessionRef.current = null
      tefStartRequestedRef.current = false
      setTefSessionId(null)

      if (res.data?.success) {
        if (onSuccess) onSuccess()
        return
      }

      setTefErro(res.data?.error || 'Pagamento TEF nao aprovado.')
    } catch (err) {
      console.error('Erro ao finalizar fluxo TEF:', err)
      setTefErro(err.response?.data?.detail || 'Erro ao finalizar fluxo TEF')
    } finally {
      setTefProcessando(false)
    }
  }

  const handleEscolha = async (opcao) => {
    if (opcao.action === 'comprovante') {
      try {
        if (!reserva?.id) {
          toast.error('Reserva invalida. Recarregue a pagina e tente novamente.')
          return
        }

        if (!valorReserva || Number.isNaN(valorReserva)) {
          toast.error('Valor da reserva invalido. Recarregue a pagina e tente novamente.')
          return
        }

        const pagamentoPayload = {
          reserva_id: parseInt(reserva.id, 10),
          valor: valorReserva,
          metodo: 'na_chegada'
        }

        const res = await api.post('/pagamentos', pagamentoPayload)
        setPagamentoCriado(res.data)
        setShowUploadModal(true)
      } catch (err) {
        console.error('Erro ao criar pagamento (balcao):', err)
        toast.error(err.response?.data?.detail || 'Erro ao iniciar pagamento no balcao')
      }
      return
    }

    if (opcao.action === 'pix') {
      toast.info('Integracao PIX em desenvolvimento')
      return
    }

    if (opcao.action === 'cielo') {
      toast.info('Integracao Cielo em desenvolvimento')
      return
    }

    if (opcao.action === 'tef') {
      await abrirFluxoTef()
      return
    }
  }

  if (showUploadModal) {
    return (
      <UploadComprovanteModal
        reserva={reserva}
        pagamento={pagamentoCriado || { valor: valorReserva }}
        onClose={() => {
          setShowUploadModal(false)
          setPagamentoCriado(null)
          onClose()
        }}
        onSuccess={() => {
          setShowUploadModal(false)
          setPagamentoCriado(null)
          if (onSuccess) onSuccess()
        }}
      />
    )
  }

  if (showTefFlow) {
    const isAprovado = Boolean(tefResultado?.aprovado)
    const cupomEstabelecimento = tefResultado?.cupom_estabelecimento || tefResultado?.tef_cupom_estabelecimento || ''
    const cupomCliente = tefResultado?.cupom_cliente || tefResultado?.tef_cupom_cliente || ''
    const precisaEntregaComprovante = Boolean(isAprovado && (cupomCliente || cupomEstabelecimento))
    const prompt = tefPrompt?.prompt || ''
    const menuTitle = tefPrompt?.menu_title || ''
    const headerText = tefPrompt?.header || ''
    const mensagens = tefPrompt?.messages || []
    const ehPerguntaSimNao = tefPrompt?.command_id === 20
    const ehAguardarTecla = tefPrompt?.command_id === 22
    const ehInterromper = tefPrompt?.command_id === 23
    const ehMenu = tefPrompt?.command_id === 21 || tefPrompt?.command_id === 42
    const ehRecibo = Boolean(tefPrompt?.receipt_required)
    const ehProcessandoAutomatico = isAutoProcessingPrompt(tefPrompt)
    const floatDecimals = tefPrompt?.float_decimals
    const comandoEntrada = Number(tefPrompt?.command_id)
    const exigeModoCheque = comandoEntrada === 31
    const exigeModoCodigoBarras = comandoEntrada === 35
    const senhaObrigatoria = Boolean(tefPrompt?.field_is_secret || Number(tefPrompt?.field_id) === 500)
    const menuOptions = ehMenu ? parseMenuOptions(Number(tefPrompt?.command_id), prompt) : []
    const hasMenuOptions = ehMenu && menuOptions.length > 0
    const retornoCliSiTef = Number(tefResultado?.clisitef_status ?? tefResultado?.detail?.clisitefStatus ?? (isAprovado ? 0 : -1))

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onMouseMove={registrarAtividadeTef}
        onKeyDown={registrarAtividadeTef}
        onClick={registrarAtividadeTef}
        onTouchStart={registrarAtividadeTef}
      >
        <div className="w-full max-w-5xl rounded-lg overflow-hidden shadow-xl">
          <div className="bg-sky-600 text-white px-6 py-5">
            <h2 className="text-3xl font-semibold">Exemplo AgenteCliSiTef</h2>
          </div>

          <div className="bg-zinc-300 min-h-[420px] p-6">
                <div className="mb-4 rounded border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
                  Este fluxo cobre as sequencias de venda e multiplos pagamentos do roteiro (4 a 10 e 21 a 23). Para menu 110, reimpressao,
                  cancelamento, QR Code, pendencias e TLS, use o modal `TEF Gerencial` em `Pagamentos`.
                </div>
                {tefResultado ? (
                  <div className="space-y-4">
                    {pendenciaStatus && (
                      <div className="bg-amber-50 border border-amber-200 text-amber-800 px-3 py-2 rounded text-sm">
                        {pendenciaStatus}
                      </div>
                    )}
                    {renderTefEventInfo(tefResultado)}
                    {renderTefReimpressaoInfo(tefResultado?.reimpressao)}
                    <h3 className="text-3xl font-bold text-zinc-900">Transacao {isAprovado ? 'Aprov.' : 'Nao Aprov.'}</h3>

                <div className="rounded border bg-white p-4">
                  <p className="text-sm text-zinc-700">Fim - Retorno CliSiTef: {retornoCliSiTef} ({getClisitefStatusDescription(retornoCliSiTef)})</p>
                  <p className="font-mono text-sm mt-1">{tefResultado?.message || tefErro || '-'}</p>
                  <p className="font-mono text-sm mt-1">NSU Host: {tefResultado?.nsu_host || tefResultado?.nsu || '-'}</p>
                  <p className="font-mono text-sm mt-1">NSU SiTef: {tefResultado?.nsu_sitef || '-'}</p>
                  <p className="font-mono text-sm mt-1">Autorizacao: {tefResultado?.autorizacao || '-'}</p>
                </div>

                <div className="rounded border bg-white p-4">
                  <pre className="text-xs max-h-56 overflow-auto bg-zinc-50 p-2 rounded">
{montarResumoTipoCampo(tefResultado)}
                  </pre>
                </div>

                {tefResultado?.nfpag && (tefResultado.nfpag.max_formas || nfpagTypeOptions.length > 0) && (
                  <div className="rounded border bg-white p-4 space-y-3">
                    <p className="font-semibold">NFPAG (multiplas formas de pagamento)</p>
                    <div className="text-xs text-zinc-600 space-y-1">
                      {tefResultado.nfpag.numero_pagamento && (
                        <p>NumeroPagamentoNFPAG: {tefResultado.nfpag.numero_pagamento}</p>
                      )}
                      {tefResultado.nfpag.max_formas != null && (
                        <p>Max formas permitidas: {tefResultado.nfpag.max_formas}</p>
                      )}
                      {nfpagTypeOptions.length > 0 && (
                        <p>
                          Formas habilitadas: {nfpagTypeOptions.map((item) => `${item.codigo} - ${item.descricao}`).join(' | ')}
                        </p>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
                      <div>
                        <label className="text-xs text-zinc-600">Forma de pagamento (campo 731)</label>
                        {nfpagTypeOptions.length > 0 ? (
                          <select
                            value={nfpagTipo}
                            onChange={(e) => selecionarTipoNfpag(e.target.value)}
                            className="w-full border border-zinc-300 rounded px-2 py-2 text-xs"
                          >
                            <option value="">Selecione...</option>
                            {nfpagTypeOptions.map((item) => (
                              <option key={item.codigo} value={item.codigo}>{item.codigo} - {item.descricao}</option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type="text"
                            value={nfpagTipo}
                            onChange={(e) => selecionarTipoNfpag(e.target.value)}
                            placeholder="00, 02, 03..."
                            className="w-full border border-zinc-300 rounded px-2 py-2 text-xs"
                          />
                        )}
                      </div>
                      <div>
                        <label className="text-xs text-zinc-600">Valor usado na forma (R$)</label>
                        <input
                          type="text"
                          value={nfpagValor}
                          onChange={(e) => setNfpagValor(e.target.value)}
                          placeholder="Ex: 20,00"
                          className="w-full border border-zinc-300 rounded px-2 py-2 text-xs"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={adicionarNfpagItem}
                        className="px-3 py-2 text-xs rounded bg-emerald-600 text-white"
                      >
                        Adicionar forma
                      </button>
                    </div>

                    {nfpagSelectedType?.coletas_detalhes?.length > 0 && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 rounded border border-zinc-200 bg-zinc-50 p-3">
                        {nfpagSelectedType.coletas_detalhes.map((coleta) => {
                          const codigo = String(coleta?.codigo || '').padStart(2, '0')
                          const options = NFPAG_FIELD_OPTIONS[codigo] || []
                          const optional = ['00', '05', '13'].includes(codigo)
                          return (
                            <div key={`${nfpagSelectedType.codigo}-${codigo}`}>
                              <label className="text-xs text-zinc-600">
                                {codigo} - {coleta?.descricao || NFPAG_COLLECTION_LABELS[codigo] || 'Campo'}{optional ? ' (opcional)' : ''}
                              </label>
                              {options.length > 0 ? (
                                <select
                                  value={nfpagExtraFields?.[codigo] || ''}
                                  onChange={(e) => atualizarCampoNfpag(codigo, e.target.value)}
                                  className="w-full border border-zinc-300 rounded px-2 py-2 text-xs"
                                >
                                  <option value="">Selecione...</option>
                                  {options.map((option) => (
                                    <option key={`${codigo}-${option.value}`} value={option.value}>{option.value} - {option.label}</option>
                                  ))}
                                </select>
                              ) : (
                                <input
                                  type="text"
                                  value={nfpagExtraFields?.[codigo] || ''}
                                  onChange={(e) => atualizarCampoNfpag(codigo, e.target.value)}
                                  placeholder={getNfpagFieldPlaceholder(codigo)}
                                  className="w-full border border-zinc-300 rounded px-2 py-2 text-xs"
                                />
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}

                    {nfpagItems.length > 0 && (
                      <div className="space-y-2">
                        {nfpagItems.map((item, idx) => (
                          <div key={`${item.tipo}-${idx}`} className="flex items-start justify-between gap-3 text-xs bg-zinc-50 border border-zinc-200 rounded px-3 py-2">
                            <div className="space-y-1">
                              <div className="font-semibold">{item.tipo} - {item.descricao}</div>
                              <div>Valor em centavos: <span className="font-mono">{item.valor}</span></div>
                              {item.extras && <div>Extras: <span className="font-mono break-all">{item.extras}</span></div>}
                            </div>
                            <button
                              type="button"
                              onClick={() => removerNfpagItem(idx)}
                              className="text-red-600"
                            >
                              remover
                            </button>
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={aplicarNfpagGerado}
                          className="px-3 py-2 text-xs rounded bg-sky-600 text-white"
                        >
                          Gerar NFPAG
                        </button>
                      </div>
                    )}

                    {nfpagError && (
                      <div className="text-xs text-red-600">{nfpagError}</div>
                    )}

                    <textarea
                      value={nfpagRaw}
                      onChange={(e) => setNfpagRaw(e.target.value)}
                      placeholder="Ex: NFPAG=00:3000;02:2000:03:5-07:123456789-08:15122008-09:000000000000001;"
                      className="w-full border border-zinc-300 rounded px-3 py-2 min-h-[80px] text-xs"
                    />
                    <p className="text-xs text-zinc-500">
                      O backend envia automaticamente <span className="font-mono">NumeroPagamentoNFPAG</span> quando o campo 161 vier da CliSiTef. Se precisar, voce ainda pode sobrescrever o prefixo completo manualmente.
                    </p>
                  </div>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="rounded border bg-white p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-semibold">Cupom Estabelecimento (122)</p>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => abrirCupomDialog('Cupom Estabelecimento', cupomEstabelecimento)}
                          className="px-3 py-1 text-xs rounded bg-indigo-600 text-white"
                        >
                          Ver
                        </button>
                        <button
                          type="button"
                          onClick={() => imprimirCupom('estabelecimento', cupomEstabelecimento)}
                          className="px-3 py-1 text-xs rounded bg-sky-600 text-white"
                        >
                          Imprimir
                        </button>
                      </div>
                    </div>
                    <pre className="text-xs max-h-44 overflow-auto bg-zinc-50 p-2 rounded">{cupomEstabelecimento || 'Nao retornado'}</pre>
                  </div>

                  <div className="rounded border bg-white p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-semibold">Cupom Cliente (121)</p>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => abrirCupomDialog('Cupom Cliente', cupomCliente)}
                          className="px-3 py-1 text-xs rounded bg-indigo-600 text-white"
                        >
                          Ver
                        </button>
                        <button
                          type="button"
                          onClick={() => imprimirCupom('cliente', cupomCliente)}
                          className="px-3 py-1 text-xs rounded bg-sky-600 text-white"
                        >
                          Imprimir
                        </button>
                      </div>
                    </div>
                    <pre className="text-xs max-h-44 overflow-auto bg-zinc-50 p-2 rounded">{cupomCliente || 'Nao retornado'}</pre>
                  </div>
                </div>

                {precisaEntregaComprovante && (
                  <div className="rounded border bg-white p-4 space-y-3">
                    <p className="font-semibold">Entrega do comprovante TEF</p>
                    <div className="flex flex-wrap gap-4 text-sm">
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="metodo-comprovante"
                          value="impressao"
                          checked={comprovanteMetodo === 'impressao'}
                          onChange={(e) => {
                            setComprovanteMetodo(e.target.value)
                            setComprovanteErro('')
                            setComprovanteEntregue(false)
                          }}
                        />
                        Imprimir
                      </label>
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="metodo-comprovante"
                          value="email"
                          checked={comprovanteMetodo === 'email'}
                          onChange={(e) => {
                            setComprovanteMetodo(e.target.value)
                            setComprovanteErro('')
                            setComprovanteEntregue(false)
                          }}
                        />
                        Enviar por e-mail
                      </label>
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="metodo-comprovante"
                          value="sms"
                          checked={comprovanteMetodo === 'sms'}
                          onChange={(e) => {
                            setComprovanteMetodo(e.target.value)
                            setComprovanteErro('')
                            setComprovanteEntregue(false)
                          }}
                        />
                        Enviar por SMS
                      </label>
                    </div>

                    {comprovanteMetodo === 'impressao' && (
                      <div className="text-sm text-zinc-700">
                        Use os botoes de imprimir acima. Status:
                        <span className={`ml-2 ${impressaoCliente ? 'text-green-700' : 'text-zinc-500'}`}>
                          Cliente {impressaoCliente ? 'ok' : 'pendente'}
                        </span>
                        <span className={`ml-3 ${impressaoEstabelecimento ? 'text-green-700' : 'text-zinc-500'}`}>
                          Estabelecimento {impressaoEstabelecimento ? 'ok' : 'pendente'}
                        </span>
                      </div>
                    )}

                    {comprovanteMetodo === 'email' && (
                      <div className="flex flex-col md:flex-row gap-2">
                        <input
                          type="email"
                          value={comprovanteEmail}
                          onChange={(e) => {
                            setComprovanteEmail(e.target.value)
                            if (comprovanteErro) setComprovanteErro('')
                          }}
                          placeholder="email@exemplo.com"
                          className="flex-1 border border-zinc-300 rounded px-3 py-2"
                        />
                        <button
                          type="button"
                          onClick={enviarComprovanteEmail}
                          disabled={enviandoComprovante}
                          className="px-4 py-2 rounded bg-sky-600 text-white font-semibold disabled:opacity-60"
                        >
                          {enviandoComprovante ? 'Enviando...' : 'Enviar'}
                        </button>
                      </div>
                    )}

                    {comprovanteMetodo === 'sms' && (
                      <div className="flex flex-col md:flex-row gap-2">
                        <input
                          type="tel"
                          value={comprovanteTelefone}
                          onChange={(e) => {
                            setComprovanteTelefone(e.target.value)
                            if (comprovanteErro) setComprovanteErro('')
                          }}
                          placeholder="+55XXXXXXXXXXX"
                          className="flex-1 border border-zinc-300 rounded px-3 py-2"
                        />
                        <button
                          type="button"
                          onClick={enviarComprovanteSms}
                          disabled={enviandoComprovante}
                          className="px-4 py-2 rounded bg-sky-600 text-white font-semibold disabled:opacity-60"
                        >
                          {enviandoComprovante ? 'Enviando...' : 'Enviar'}
                        </button>
                      </div>
                    )}

                    {comprovanteEntregue && (
                      <div className="text-green-700 bg-green-50 border border-green-200 px-3 py-2 rounded text-sm">
                        Comprovante entregue com sucesso.
                      </div>
                    )}

                    {comprovanteErro && (
                      <div className="text-red-700 bg-red-100 border border-red-300 px-3 py-2 rounded text-sm">
                        {comprovanteErro}
                      </div>
                    )}
                  </div>
                )}

                {tefErro && (
                  <div className="mb-3 text-red-700 bg-red-100 border border-red-300 px-3 py-2 rounded">
                    {tefErro}
                  </div>
                )}

                <div className="pt-2 flex gap-3">
                  <button
                    type="button"
                    onClick={concluirFluxoTef}
                    disabled={tefProcessando || (precisaEntregaComprovante && !comprovanteEntregue)}
                    className="bg-sky-600 hover:bg-sky-700 text-white font-semibold px-6 py-2 rounded disabled:opacity-60"
                  >
                    {tefProcessando ? '...' : 'Concluir'}
                  </button>
                  <button
                    type="button"
                    onClick={() => finalizarOperacaoTef()}
                    disabled={tefProcessando}
                    className="bg-zinc-500 hover:bg-zinc-600 text-white font-semibold px-6 py-2 rounded disabled:opacity-60"
                  >
                    ENCERRAR
                  </button>
                  <button
                    type="button"
                    onClick={() => encerrarFluxoTef()}
                    disabled={tefProcessando}
                    className="bg-zinc-400 hover:bg-zinc-500 text-white font-semibold px-6 py-2 rounded disabled:opacity-60"
                  >
                    MENU INICIAL
                  </button>
                </div>
              </div>
            ) : (
              <div className="max-w-xl">
                {menuTitle && (
                  <div className="text-xl font-semibold text-zinc-900 mb-2">{menuTitle}</div>
                )}
                {pendenciaStatus && (
                  <div className="bg-amber-50 border border-amber-200 text-amber-800 px-3 py-2 rounded text-sm mb-2">
                    {pendenciaStatus}
                  </div>
                )}
                {headerText && (
                  <pre className="text-sm text-zinc-800 whitespace-pre-wrap mb-2">{headerText}</pre>
                )}
                {renderMensagens(mensagens)}
                {renderTefEventInfo(tefPrompt)}
                {renderTefReimpressaoInfo(tefPrompt?.reimpressao)}
                {ehRecibo ? (
                  <div className="rounded border bg-white p-4 mb-4">
                    <p className="font-semibold mb-2">
                      Cupom {tefPrompt?.receipt_kind === 'cliente' ? 'Cliente' : 'Estabelecimento'}
                    </p>
                    <pre className="text-xs whitespace-pre-wrap bg-zinc-50 p-2 rounded max-h-60 overflow-auto">
                      {prompt || 'Nao retornado'}
                    </pre>
                    <div className="mt-3 flex gap-2">
                      <button
                        type="button"
                        onClick={() => imprimirCupom(tefPrompt?.receipt_kind === 'cliente' ? 'cliente' : 'estabelecimento', prompt)}
                        className="px-3 py-1 text-xs rounded bg-sky-600 text-white"
                      >
                        Imprimir
                      </button>
                    </div>
                  </div>
                ) : hasMenuOptions ? (
                  <div className="mb-4 space-y-3">
                    <pre className="text-sm text-zinc-900 whitespace-pre-wrap bg-white border border-zinc-300 rounded p-3">{prompt || ''}</pre>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {menuOptions.map((opt) => (
                        <button
                          key={`${opt.index}-${opt.text}`}
                          type="button"
                          onClick={() => continuarFluxoTef(0, String(opt.index))}
                          disabled={tefProcessando}
                          className="text-left px-4 py-3 rounded border border-zinc-300 bg-white hover:bg-zinc-50 disabled:opacity-60"
                        >
                          <div className="text-lg font-semibold text-zinc-900">{opt.index}. {opt.text}</div>
                          {opt.code && (
                            <div className="text-xs text-zinc-600 mt-1">
                              Codigo: {opt.code} {opt.type ? `| Tipo: ${opt.type}` : ''} {opt.classe ? `| Classe: ${opt.classe}` : ''}
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  (prompt || (!menuTitle && !headerText && mensagens.length === 0)) && (
                    <pre className="text-2xl text-zinc-900 whitespace-pre-wrap mb-4">{prompt || ''}</pre>
                  )
                )}

                {floatDecimals != null && !ehRecibo && (
                  <p className="text-xs text-zinc-600 mb-2">Casas decimais: {floatDecimals}</p>
                )}

                {exigeModoCheque && !ehRecibo && (
                  <div className="mb-3 flex flex-wrap gap-3 text-sm">
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="modo-cheque"
                        value="linha"
                        checked={tefInputMode === 'linha'}
                        onChange={() => setTefInputMode('linha')}
                      />
                      Linha do cheque (0)
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="modo-cheque"
                        value="cmc7_digitado"
                        checked={tefInputMode === 'cmc7_digitado'}
                        onChange={() => setTefInputMode('cmc7_digitado')}
                      />
                      CMC-7 digitado (2)
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="modo-cheque"
                        value="cmc7_leitor"
                        checked={tefInputMode === 'cmc7_leitor'}
                        onChange={() => setTefInputMode('cmc7_leitor')}
                      />
                      CMC-7 leitora (1)
                    </label>
                  </div>
                )}

                {exigeModoCodigoBarras && !ehRecibo && (
                  <div className="mb-3 flex flex-wrap gap-3 text-sm">
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="modo-barcode"
                        value="manual"
                        checked={tefInputMode === 'manual'}
                        onChange={() => setTefInputMode('manual')}
                      />
                      Manual (0)
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="modo-barcode"
                        value="leitor"
                        checked={tefInputMode === 'leitor'}
                        onChange={() => setTefInputMode('leitor')}
                      />
                      Leitora (1)
                    </label>
                  </div>
                )}

                {!ehPerguntaSimNao && !ehAguardarTecla && !ehInterromper && !ehRecibo && !ehProcessandoAutomatico && !hasMenuOptions && (
                  <input
                    type={senhaObrigatoria ? 'password' : 'text'}
                    value={tefInput}
                    onChange={(e) => {
                      if (floatDecimals != null) {
                        setTefInput(formatFloatInput(e.target.value, floatDecimals))
                        return
                      }
                      setTefInput(e.target.value)
                    }}
                    autoComplete="off"
                    className="w-full md:w-[420px] border border-zinc-400 bg-zinc-100 text-2xl px-3 py-2 mb-4"
                  />
                )}

                {tefErro && (
                  <div className="mb-3 text-red-700 bg-red-100 border border-red-300 px-3 py-2 rounded">
                    {tefErro}
                  </div>
                )}

                <div className="flex gap-2 flex-wrap">
                  {ehPerguntaSimNao ? (
                    <>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(0, '0')}
                        disabled={tefProcessando}
                        className="w-36 bg-sky-600 hover:bg-sky-700 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        Sim
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(0, '1')}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-500 hover:bg-zinc-600 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        Nao
                      </button>
                    </>
                  ) : ehInterromper ? (
                    <>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(0, '')}
                        disabled={tefProcessando}
                        className="w-40 bg-sky-600 hover:bg-sky-700 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        Continuar
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(-1, '')}
                        disabled={tefProcessando}
                        className="w-40 bg-zinc-600 hover:bg-zinc-700 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className="w-40 bg-zinc-400 hover:bg-zinc-500 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        MENU INICIAL
                      </button>
                    </>
                  ) : ehProcessandoAutomatico ? (
                    <>
                      <button
                        type="button"
                        disabled
                        className="w-40 bg-sky-600 text-white text-2xl font-semibold py-2 rounded opacity-60"
                      >
                        {tefProcessando ? '...' : 'AGUARDANDO'}
                      </button>
                      <button
                        type="button"
                        onClick={() => finalizarOperacaoTef()}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-500 hover:bg-zinc-600 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-400 hover:bg-zinc-500 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        MENU INICIAL
                      </button>
                    </>
                  ) : ehRecibo ? (
                    <>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(0, '')}
                        disabled={tefProcessando}
                        className="w-36 bg-sky-600 hover:bg-sky-700 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        {tefProcessando ? '...' : 'OK'}
                      </button>
                      <button
                        type="button"
                        onClick={() => finalizarOperacaoTef()}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-500 hover:bg-zinc-600 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-400 hover:bg-zinc-500 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        MENU INICIAL
                      </button>
                    </>
                  ) : ehAguardarTecla ? (
                    <>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(0, '')}
                        disabled={tefProcessando}
                        className="w-36 bg-sky-600 hover:bg-sky-700 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        {tefProcessando ? '...' : 'OK'}
                      </button>
                      <button
                        type="button"
                        onClick={() => finalizarOperacaoTef()}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-500 hover:bg-zinc-600 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-400 hover:bg-zinc-500 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        MENU INICIAL
                      </button>
                    </>
                  ) : hasMenuOptions ? (
                    <>
                      <button
                        type="button"
                        onClick={() => finalizarOperacaoTef()}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-500 hover:bg-zinc-600 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-400 hover:bg-zinc-500 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        MENU INICIAL
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(0, tefInput)}
                        disabled={tefProcessando}
                        className="w-36 bg-sky-600 hover:bg-sky-700 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        {tefProcessando ? '...' : 'OK'}
                      </button>
                      {exigeModoCodigoBarras && (
                        <button
                          type="button"
                          onClick={() => continuarFluxoTef(0, '2:')}
                          disabled={tefProcessando}
                          className="w-40 bg-amber-500 hover:bg-amber-600 text-white text-xl font-semibold py-2 rounded disabled:opacity-60"
                        >
                          Cancelar leitura
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => finalizarOperacaoTef()}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-500 hover:bg-zinc-600 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className="w-36 bg-zinc-400 hover:bg-zinc-500 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        MENU INICIAL
                      </button>
                    </>
                  )}
                </div>
                {ehPerguntaSimNao && (
                  <div className="mt-3 flex gap-2">
                    <button
                      type="button"
                      onClick={() => finalizarOperacaoTef()}
                      disabled={tefProcessando}
                      className="w-36 bg-zinc-700 hover:bg-zinc-800 text-white text-xl font-semibold py-2 rounded disabled:opacity-60"
                    >
                      ENCERRAR
                    </button>
                    <button
                      type="button"
                      onClick={() => continuarFluxoTef(1, '1')}
                      disabled={tefProcessando}
                      className="w-36 bg-zinc-400 hover:bg-zinc-500 text-white text-xl font-semibold py-2 rounded disabled:opacity-60"
                    >
                      MENU INICIAL
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {cupomDialog.open && (
          <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-[60] p-4">
            <div className="bg-zinc-100 w-full max-w-xl rounded-2xl border shadow-2xl overflow-hidden">
              <div className="px-6 py-4 text-3xl font-semibold">Essa pagina diz</div>
              <div className="px-6 py-2 max-h-[360px] overflow-auto">
                <pre className="whitespace-pre-wrap text-base leading-6">{cupomDialog.titulo}:
{cupomDialog.conteudo}</pre>
              </div>
              <div className="px-6 py-4 flex justify-end">
                <button
                  type="button"
                  onClick={fecharCupomDialog}
                  className="px-8 py-2 rounded-full bg-indigo-700 text-white font-semibold hover:bg-indigo-800"
                >
                  OK
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="bg-gradient-to-r from-green-600 to-green-800 text-white p-6 rounded-t-lg">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">Escolha a Forma de Pagamento</h2>
              <p className="text-green-100">
                Reserva: {reserva?.codigo_reserva || `#${reserva?.id}`}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-2xl"
            >
              x
            </button>
          </div>
        </div>

        <div className="bg-blue-50 p-6 border-b-2 border-blue-200">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">Valor Total da Reserva</p>
            <p className="text-4xl font-bold text-blue-600">
              {formatCurrency(reserva?.valor_total || reserva?.valor_previsto)}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              {reserva?.num_diarias} diaria(s) x {formatCurrency(reserva?.valor_diaria)}
            </p>
          </div>
        </div>

        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Selecione como deseja pagar:
          </h3>

          <div className="space-y-4">
            {opcoesPagamento.map((opcao) => (
              <button
                key={opcao.id}
                onClick={() => handleEscolha(opcao)}
                disabled={!opcao.disponivel}
                className={`w-full p-6 rounded-lg border-2 transition-all text-left ${
                  opcao.disponivel
                    ? 'border-gray-300 hover:border-green-500 hover:shadow-lg cursor-pointer'
                    : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-50'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-1">
                    <h4 className="text-xl font-bold text-gray-800 mb-1">
                      {opcao.nome}
                    </h4>
                    <p className="text-gray-600">{opcao.descricao}</p>

                    {opcao.id === 'balcao' && (
                      <div className="mt-3 bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
                        <p className="text-sm text-yellow-800">
                          <strong>Importante:</strong> sera necessario enviar o comprovante para aprovacao antes do check-in.
                        </p>
                      </div>
                    )}

                    {opcao.id === 'tef' && (
                      <div className="mt-3 bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
                        <p className="text-sm text-blue-800">
                          <strong>TEF:</strong> o fluxo agora segue os retornos reais de startTransaction, continueTransaction e finishTransaction.
                        </p>
                      </div>
                    )}
                  </div>

                  {opcao.disponivel && (
                    <div className="text-green-600 text-2xl">{'>'}</div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="p-6 bg-gray-50 rounded-b-lg border-t">
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 font-medium transition-colors"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}
