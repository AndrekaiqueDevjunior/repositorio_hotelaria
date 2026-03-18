'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../lib/api'
import UploadComprovanteModal from './UploadComprovanteModal'

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value || 0)
}

const escapeTipoCampo = (value) => String(value || '').replace(/\n/g, '\\n')

const defaultValorPrompt = (prompt) => prompt?.default_value || ''

export default function ModalEscolhaPagamento({ reserva, onClose, onSuccess }) {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [pagamentoCriado, setPagamentoCriado] = useState(null)
  const tefSessionRef = useRef(null)
  const tefStartRequestedRef = useRef(false)

  const [showTefFlow, setShowTefFlow] = useState(false)
  const [tefSessionId, setTefSessionId] = useState(null)
  const [tefPrompt, setTefPrompt] = useState(null)
  const [tefInput, setTefInput] = useState('')
  const [tefProcessando, setTefProcessando] = useState(false)
  const [tefErro, setTefErro] = useState('')
  const [tefResultado, setTefResultado] = useState(null)
  const [cupomDialog, setCupomDialog] = useState({ open: false, titulo: '', conteudo: '' })
  const [cupomQueue, setCupomQueue] = useState([])

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

  const resetTefFlow = () => {
    tefSessionRef.current = null
    tefStartRequestedRef.current = false
    setTefSessionId(null)
    setTefPrompt(null)
    setTefInput('')
    setTefErro('')
    setTefResultado(null)
    setTefProcessando(false)
  }

  const abrirFluxoTef = async () => {
    resetTefFlow()
    setShowTefFlow(true)
    tefStartRequestedRef.current = true
    await iniciarFluxoTef()
  }

  const cancelarSessaoTef = async () => {
    const sessionIdAtual = tefSessionRef.current || tefSessionId || tefPrompt?.session_id
    if (!sessionIdAtual) return
    try {
      await api.post('/pagamentos/tef/cancelar', {
        session_id: sessionIdAtual
      })
    } catch (err) {
      console.error('Erro ao cancelar sessao TEF:', err)
    }
  }

  const fecharFluxoTef = async () => {
    if (tefSessionId && !tefResultado) {
      await cancelarSessaoTef()
    }
    setShowTefFlow(false)
    resetTefFlow()
    setCupomDialog({ open: false, titulo: '', conteudo: '' })
    setCupomQueue([])
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

  const abrirCupomDialog = (titulo, conteudo) => {
    setCupomDialog({
      open: true,
      titulo,
      conteudo: conteudo || 'Nao retornado'
    })
  }

  useEffect(() => {
    if (!tefResultado) return
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
  }, [tefResultado])

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
    const tipoCampos = Array.isArray(resultado?.tipo_campos) ? resultado.tipo_campos : []
    if (tipoCampos.length > 0) {
      return tipoCampos.map((item) => `{"TipoCampo":"${item.TipoCampo}","Valor":"${escapeTipoCampo(item.Valor)}"}`).join(',\n')
    }

    const nsu = resultado?.nsu || resultado?.tef_nsu || ''
    const aut = resultado?.autorizacao || resultado?.tef_autorizacao || ''
    const cupomEstabelecimento = resultado?.cupom_estabelecimento || resultado?.tef_cupom_estabelecimento || ''
    const cupomCliente = resultado?.cupom_cliente || resultado?.tef_cupom_cliente || ''

    return [
      `{"TipoCampo":"131","Valor":"${escapeTipoCampo(nsu)}"}`,
      `{"TipoCampo":"132","Valor":"${escapeTipoCampo(aut)}"}`,
      `{"TipoCampo":"121","Valor":"${escapeTipoCampo(cupomEstabelecimento)}"}`,
      `{"TipoCampo":"122","Valor":"${escapeTipoCampo(cupomCliente)}"}`
    ].join(',\n')
  }

  const aplicarRespostaInterativa = (payload) => {
    if (payload?.session_id) {
      tefSessionRef.current = payload.session_id
      setTefSessionId(payload.session_id)
    }

    if (payload?.success === false) {
      setTefErro(payload?.error || 'Erro no fluxo TEF')
      return
    }

    if (payload?.finish_required) {
      setTefPrompt(null)
      setTefResultado(payload)
      setTefInput('')
      return
    }

    setTefResultado(null)
    setTefPrompt(payload)
    setTefInput(defaultValorPrompt(payload))
  }

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
      })

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

      setTefErro('')
      setTefProcessando(true)

      const res = await api.post('/pagamentos/tef/continuar', {
        session_id: sessionIdAtual,
        continue_flag: continueFlag,
        data: value
      })

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

      setTefErro('')
      setTefProcessando(true)

      const res = await api.post('/pagamentos/tef/finalizar', {
        session_id: sessionIdAtual,
        reserva_id: parseInt(reserva.id, 10),
        valor: valorReserva,
        confirm: Boolean(tefResultado?.aprovado)
      })

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
    const prompt = tefPrompt?.prompt || ''
    const ehPerguntaSimNao = tefPrompt?.command_id === 20
    const linhasPrompt = prompt.split('\n').filter(Boolean)

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="w-full max-w-5xl rounded-lg overflow-hidden shadow-xl">
          <div className="bg-sky-600 text-white px-6 py-5">
            <h2 className="text-3xl font-semibold">Exemplo AgenteCliSiTef</h2>
          </div>

          <div className="bg-zinc-300 min-h-[420px] p-6">
            {tefResultado ? (
              <div className="space-y-4">
                <h3 className="text-3xl font-bold text-zinc-900">Transacao {isAprovado ? 'Aprov.' : 'Nao Aprov.'}</h3>

                <div className="rounded border bg-white p-4">
                  <p className="text-sm text-zinc-700">Fim - Retorno: {isAprovado ? '0' : '-1'}</p>
                  <p className="font-mono text-sm mt-1">{tefResultado?.message || tefErro || '-'}</p>
                  <p className="font-mono text-sm mt-1">NSU: {tefResultado?.nsu || '-'}</p>
                  <p className="font-mono text-sm mt-1">Autorizacao: {tefResultado?.autorizacao || '-'}</p>
                </div>

                <div className="rounded border bg-white p-4">
                  <pre className="text-xs max-h-56 overflow-auto bg-zinc-50 p-2 rounded">
{montarResumoTipoCampo(tefResultado)}
                  </pre>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="rounded border bg-white p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-semibold">Cupom Estabelecimento (121)</p>
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
                          onClick={() => imprimirTexto('Cupom Estabelecimento', cupomEstabelecimento)}
                          className="px-3 py-1 text-xs rounded bg-sky-600 text-white"
                        >
                          Imprimir
                        </button>
                      </div>
                    </div>
                    <pre className="text-xs max-h-44 overflow-auto bg-zinc-50 p-2 rounded">
                      {cupomEstabelecimento || 'Nao retornado'}
                    </pre>
                  </div>

                  <div className="rounded border bg-white p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-semibold">Cupom Cliente (122)</p>
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
                          onClick={() => imprimirTexto('Cupom Cliente', cupomCliente)}
                          className="px-3 py-1 text-xs rounded bg-sky-600 text-white"
                        >
                          Imprimir
                        </button>
                      </div>
                    </div>
                    <pre className="text-xs max-h-44 overflow-auto bg-zinc-50 p-2 rounded">
                      {cupomCliente || 'Nao retornado'}
                    </pre>
                  </div>
                </div>

                {tefErro && (
                  <div className="mb-3 text-red-700 bg-red-100 border border-red-300 px-3 py-2 rounded">
                    {tefErro}
                  </div>
                )}

                <div className="pt-2 flex gap-3">
                  <button
                    type="button"
                    onClick={concluirFluxoTef}
                    disabled={tefProcessando}
                    className="bg-sky-600 hover:bg-sky-700 text-white font-semibold px-6 py-2 rounded disabled:opacity-60"
                  >
                    {tefProcessando ? '...' : 'Concluir'}
                  </button>
                  <button
                    type="button"
                    onClick={fecharFluxoTef}
                    disabled={tefProcessando}
                    className="bg-zinc-500 hover:bg-zinc-600 text-white font-semibold px-6 py-2 rounded disabled:opacity-60"
                  >
                    Nova tentativa
                  </button>
                </div>
              </div>
            ) : (
              <div className="max-w-xl">
                {linhasPrompt.map((linha, index) => (
                  <p key={`${linha}-${index}`} className={`text-2xl text-zinc-900 ${index === 0 ? 'mb-2' : 'mb-1'}`}>
                    {linha}
                  </p>
                ))}

                {!ehPerguntaSimNao && (
                  <input
                    type="text"
                    value={tefInput}
                    onChange={(e) => setTefInput(e.target.value)}
                    className="w-full md:w-[420px] border border-zinc-400 bg-zinc-100 text-2xl px-3 py-2 mb-4"
                  />
                )}

                {tefErro && (
                  <div className="mb-3 text-red-700 bg-red-100 border border-red-300 px-3 py-2 rounded">
                    {tefErro}
                  </div>
                )}

                <div className="flex gap-2">
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
                      <button
                        type="button"
                        onClick={fecharFluxoTef}
                        disabled={tefProcessando}
                        className="w-36 bg-sky-600 hover:bg-sky-700 text-white text-2xl font-semibold py-2 rounded disabled:opacity-60"
                      >
                        Cancelar
                      </button>
                    </>
                  )}
                </div>
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
