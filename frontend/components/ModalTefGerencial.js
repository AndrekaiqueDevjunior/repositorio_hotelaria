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
  getClisitefStatusDescription,
  getNfpagFieldPlaceholder,
  getNfpagTypeDetail,
  getNfpagTypeOptions,
  getTefEventDescription,
  getTefEventTone,
  normalizeTefFlag,
  parseNfpagValor
} from '../lib/tefHelpers'

const escapeTipoCampo = (value) => String(value || '').replace(/\n/g, '\\n')

const resolveTimeoutMs = (value, fallback) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

const TEF_IDLE_TIMEOUT_MS = Math.max(resolveTimeoutMs(process.env.NEXT_PUBLIC_TEF_IDLE_TIMEOUT_MS, 300000), 60000)
const TEF_IDLE_TIMEOUT_SECONDS = Math.max(Math.round(TEF_IDLE_TIMEOUT_MS / 1000), 60)
const TEF_REQUEST_TIMEOUT_MS = resolveTimeoutMs(process.env.NEXT_PUBLIC_TEF_REQUEST_TIMEOUT_MS, 180000)
const TEF_PROCESSING_POLL_DELAY_MS = 800
const REPRINT_LOOKUP_ERROR_PATTERNS = ['documento inexistente', 'doc inexistente', 'doc nao encontrado', 'doc nao encontrando', 'transacao nao encontrada na log', 'transacao nao encontrada no log', 'rede nao existe']
const MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS = '{[10;16;17;18;19;27;28;35;3988;42;43;44];MultiplosCupons=1;VersaoAutomacaoCielo=PEG}'
const MULTIPLE_PAYMENT_DEBIT_ADDITIONAL_PARAMETERS = '{[10;18;24;26;27;28;29;30;34;35;3988;44;73];MultiplosCupons=1;VersaoAutomacaoCielo=PEG}'
const MULTIPLE_PAYMENT_WALLET_ADDITIONAL_PARAMETERS = '{MultiplosCupons=1;VersaoAutomacaoCielo=PEG}'

const defaultValorPrompt = (prompt) => {
  if (Number(prompt?.command_id) === 22) {
    return ''
  }
  if (prompt?.field_is_secret || Number(prompt?.field_id) === 500) {
    return ''
  }
  return prompt?.default_value || ''
}

const resolveMensagemLabel = (target) => {
  if (Number(target) === 1) return 'Operador'
  if (Number(target) === 2) return 'Cliente'
  if (Number(target) === 3) return 'Ambos'
  return 'Mensagem'
}

const resolveInputMode = (commandId) => {
  if (commandId === 31) return 'linha'
  if (commandId === 35) return 'manual'
  return 'manual'
}

const isAutoProcessingPrompt = (prompt) => Number(prompt?.command_id) === 3

const splitMenuEntries = (value) =>
  String(value || '')
    .split(/\r?\n|;/)
    .map((part) => part.trim())
    .filter(Boolean)

const parseSimpleMenuEntry = (entry) => {
  const match = String(entry || '').trim().match(/^(\d+)\s*(?:[:.)-]\s*|\s+)(.+)$/)
  if (!match) return null
  const index = String(match[1] || '').trim()
  const text = String(match[2] || '').trim()
  if (!index || !text) return null
  return { index, text }
}

const parseMenuOptions = (commandId, promptText) => {
  const raw = String(promptText || '').trim()
  if (!raw) return []

  if (commandId === 21) {
    return splitMenuEntries(raw)
      .map((part) => {
        const [index, ...textParts] = part.split(':')
        if (index && textParts.length > 0) {
          const text = textParts.join(':').trim()
          if (!text) return null
          return { index: index.trim(), text }
        }
        return parseSimpleMenuEntry(part)
      })
      .filter(Boolean)
  }

  if (commandId === 42) {
    const [classePart, rest] = raw.split('|')
    const classe = rest ? (classePart || '').trim() : ''
    if (!rest) {
      return splitMenuEntries(raw)
        .map((part) => {
          const [index, ...textParts] = part.split(':')
          if (index && textParts.length > 0) {
            const text = textParts.join(':').trim()
            if (!text) return null
            return { index: index.trim(), text, classe }
          }
          const parsed = parseSimpleMenuEntry(part)
          if (!parsed) return null
          return { ...parsed, classe }
        })
        .filter(Boolean)
    }
    return splitMenuEntries(rest)
      .map((part) => {
        const [index, text, code, type] = part.split(':').map((value) => (value || '').trim())
        if (!index || !text) return null
        return { index, text, code, type, classe }
      })
      .filter(Boolean)
  }

  return []
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

const tefFlowActionBaseClass = 'w-full sm:w-auto sm:min-w-[9rem] rounded px-4 py-2.5 text-sm sm:text-base lg:text-lg font-semibold transition-colors disabled:opacity-60'
const tefFlowPrimaryButtonClass = `${tefFlowActionBaseClass} bg-sky-600 hover:bg-sky-700 text-white`
const tefFlowSecondaryButtonClass = `${tefFlowActionBaseClass} bg-zinc-500 hover:bg-zinc-600 text-white`
const tefFlowMidButtonClass = `${tefFlowActionBaseClass} bg-zinc-600 hover:bg-zinc-700 text-white`
const tefFlowMutedButtonClass = `${tefFlowActionBaseClass} bg-zinc-400 hover:bg-zinc-500 text-white`
const tefFlowDarkButtonClass = `${tefFlowActionBaseClass} bg-zinc-700 hover:bg-zinc-800 text-white`
const tefFlowWarningButtonClass = `${tefFlowActionBaseClass} bg-amber-500 hover:bg-amber-600 text-white`

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

const renderFieldGuidanceInfo = (payload) => {
  const fieldId = Number(payload?.field_id)
  const fieldLabel = String(payload?.field_label || '').trim()
  const fieldHint = String(payload?.field_hint || '').trim()

  if (!fieldLabel && !fieldHint) return null

  return (
    <div className="mb-4 rounded border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900">
      <p className="font-semibold">Campo solicitado{fieldId > 0 ? ` (${fieldId})` : ''}</p>
      {fieldLabel && <p className="mt-1 text-sm">{fieldLabel}</p>}
      {fieldHint && <p className="mt-1 text-sm">{fieldHint}</p>}
    </div>
  )
}

const renderReferenciaReimpressao = (referencia) => {
  const campo146 = String(referencia?.campo_146_valor || '').trim()
  const campo146Bruto = String(referencia?.campo_146_valor_bruto || '').trim()
  const campo516 = String(referencia?.campo_516_valor || '').trim()
  const campo515 = String(referencia?.campo_515_valor || '').trim()
  const campo515Mmdd = String(referencia?.campo_515_valor_mmdd || '').trim()
  const campo146Informado = String(referencia?.campo_146_informado || '').trim()
  const campo516Informado = String(referencia?.campo_516_informado || '').trim()
  const campo515Informado = String(referencia?.campo_515_informado || '').trim()
  const nsuHost = String(referencia?.nsu_host || '').trim()
  const nsuSitef = String(referencia?.nsu_sitef || '').trim()
  const codigoEstabelecimento = String(referencia?.codigo_estabelecimento || '').trim()
  const dataHora = String(referencia?.data_hora_transacao || '').trim()

  const itens = [
    {
      label: referencia?.campo_146_label || 'Campo 146',
      value: campo146,
      hint: referencia?.campo_146_orientacao || ''
    },
    {
      label: referencia?.campo_516_label || 'Campo 516',
      value: campo516,
      hint: referencia?.campo_516_orientacao || ''
    },
    {
      label: referencia?.campo_515_label || 'Campo 515',
      value: campo515,
      hint: referencia?.campo_515_orientacao || ''
    },
    {
      label: 'Campo 515 sugerido (MMDD / Rede)',
      value: campo515Mmdd,
      hint: 'Na reimpressao especifica da Rede, a data original deve seguir MMDD. Ex.: 8 de abril = 0408.'
    },
    {
      label: 'Campo 601 sugerido (valor bruto)',
      value: campo146Bruto,
      hint: 'Use este numero sem virgula ou ponto quando o SiTef pedir Valor da Venda.'
    },
    {
      label: 'Campo 146 informado ao SiTef',
      value: campo146Informado
    },
    {
      label: 'Campo 516 informado ao SiTef',
      value: campo516Informado
    },
    {
      label: 'Campo 515 informado ao SiTef',
      value: campo515Informado
    },
    {
      label: 'NSU Host',
      value: nsuHost
    },
    {
      label: 'NSU SiTef',
      value: nsuSitef
    },
    {
      label: 'Codigo de estabelecimento',
      value: codigoEstabelecimento
    },
    {
      label: 'Data/hora da transacao',
      value: dataHora
    }
  ].filter((item) => item.value)

  if (itens.length === 0) return null

  return (
    <div className="mb-4 rounded border border-sky-200 bg-sky-50 px-4 py-3 text-sky-900">
      <p className="font-semibold">Referencia para copiar em reimpressao/cancelamento</p>
      <p className="mt-1 text-sm">Guarde estes dados da transacao gerada para usar depois no fluxo gerencial.</p>
      <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
        {itens.map((item) => (
          <div key={item.label} className="rounded border border-sky-200 bg-white/90 px-3 py-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-sky-700">{item.label}</p>
            <p className="mt-1 break-all font-mono text-sm text-zinc-900">{item.value}</p>
            {item.hint && <p className="mt-1 text-xs text-zinc-600">{item.hint}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}

const FUNCTION_OPTIONS = [
  { id: 0, label: '0 - Venda (menu geral)' },
  { id: 2, label: '2 - Venda Debito' },
  { id: 3, label: '3 - Venda Credito' },
  { id: 110, label: '110 - Menu Gerencial' },
  { id: 112, label: '112 - Reimpressao (menu)' },
  { id: 113, label: '113 - Reimpressao especifica' },
  { id: 114, label: '114 - Reimpressao do ultimo comprovante' },
  { id: 121, label: '121 - Envio de trace' },
  { id: 122, label: '122 - Venda QR Code' },
  { id: 123, label: '123 - Cancelamento QR Code' },
  { id: 130, label: '130 - Tratamento de pendencias' },
  { id: 669, label: '669 - Registro TLS (roteiro oficial)' },
  { id: 699, label: '699 - Registro TLS (extra/diagnostico)' }
]

const JUSTIFICATIVA_REQUIRED_FUNCTIONS = new Set()

const DEFAULT_TLS_TOKEN = process.env.NEXT_PUBLIC_TEF_TLS_TOKEN || ''
const PRE_HOMO_TLS_TOKEN = '1111-2222-3333-4444'

const SEQUENCE_PRESETS = [
  {
    id: '1',
    label: 'Seq. 1 - Menu 110 completo',
    functionId: 110,
    guidance: 'Abra a funcao 110 sem restricoes para validar o menu gerencial completo.',
    expected: 'Todas as opcoes previstas pela CliSiTef devem aparecer na tela.'
  },
  {
    id: '2',
    label: 'Seq. 2 - Timeout com SitDemo fechado',
    functionId: 3,
    guidance: 'Com o SitDemo fechado, inicie uma venda com qualquer cartao e observe o timeout.',
    expected: 'A automacao deve exibir a mensagem retornada e nao imprimir cupom.'
  },
  {
    id: '3',
    label: 'Seq. 3 - Falha de configuracao Nao Existe Conf',
    functionId: 3,
    guidance: 'Com o codigo de empresa invalido, tente uma venda qualquer e valide a mensagem do m-SiTef.',
    expected: 'A venda nao deve ser autorizada e nao deve haver impressao de cupom.'
  },
  {
    id: '4',
    label: 'Seq. 4 - Credito negado acima de R$ 25.000,00',
    functionId: 3,
    valor: '25000',
    guidance: 'Execute uma venda no credito com chip e selecione a opcao a vista.',
    expected: 'A transacao deve ser negada, com mensagens exibidas e sem cupom.'
  },
  {
    id: '5',
    label: 'Seq. 5 - Debito com chip a partir de R$ 10,00',
    functionId: 2,
    valor: '10',
    guidance: 'Execute uma venda no debito com chip.',
    expected: 'A transacao deve ser autorizada e apresentar cupom.'
  },
  {
    id: '6',
    label: 'Seq. 6 - Credito a vista com chip a partir de R$ 15,00',
    functionId: 3,
    valor: '15',
    guidance: 'Execute uma venda no credito com chip e selecione a opcao a vista.',
    expected: 'A transacao deve ser autorizada e imprimir o cupom TEF.'
  },
  {
    id: '7',
    label: 'Seq. 7 - Credito parcelado pelo estabelecimento',
    functionId: 3,
    valor: '100',
    trnAdditionalParameters: 'TransacoesHabilitadas=27',
    guidance: 'Primeiro selecione Cartao de Credito, insira/aproxime o cartao e, quando a CliSiTef exibir a forma de pagamento, selecione parcelado pelo estabelecimento em 2 ou mais parcelas.',
    expected: 'A transacao deve ser autorizada e imprimir o cupom TEF.'
  },
  {
    id: '8',
    label: 'Seq. 8 - Credito parcelado pela administradora',
    functionId: 3,
    valor: '200',
    trnAdditionalParameters: 'TransacoesHabilitadas=28',
    guidance: 'Primeiro selecione Cartao de Credito, insira/aproxime o cartao e, quando a CliSiTef exibir a forma de pagamento, selecione parcelado pela administradora em 2 ou mais parcelas.',
    expected: 'A transacao deve ser autorizada e imprimir o cupom TEF.'
  },
  {
    id: '9',
    label: 'Seq. 9 - Cancelamento durante a venda',
    functionId: 2,
    guidance: 'Cancele a operacao pelo aplicativo quando o terminal pedir cartao e depois novamente na etapa de senha.',
    expected: 'A aplicacao deve exibir a pergunta de cancelamento e encerrar sem imprimir cupom.'
  },
  {
    id: '10',
    label: 'Seq. 10 - Voltar ao menu anterior',
    functionId: 0,
    guidance: 'Selecione credito, use MENU INICIAL ou VOLTAR e refaca o fluxo em debito.',
    expected: 'O retorno ao menu anterior deve funcionar com continua = 1, a transacao final deve ser autorizada e deve haver impressao de cupom.'
  },
  {
    id: '11',
    label: 'Seq. 11 - Reimpressao do ultimo comprovante',
    functionId: 114,
    guidance: 'Use a funcao 114 ou o menu 110/112 para solicitar o ultimo comprovante sem informar manualmente os dados da transacao.',
    expected: 'A reimpressao deve ser autorizada com cupom e senha de supervisor mascarada.'
  },
  {
    id: '12',
    label: 'Seq. 12 - Reimpressao especifica',
    functionId: 113,
    guidance: 'Use o comprovante da seq. 5 e realize a reimpressao especifica. A abertura da funcao 113 deve usar um novo documento fiscal da operacao atual; quando o SiTef solicitar a transacao original, informe o NSU Host no Campo 516.',
    expected: 'A reimpressao especifica deve ser autorizada com mensagens ao operador, cupom e senha de supervisor mascarada (FieldId 500).'
  },
  {
    id: '13',
    label: 'Seq. 13 - Cancelamento da transacao de debito',
    functionId: 110,
    guidance: 'Utilize o comprovante da seq. 5 e realize o cancelamento da transacao de debito pelo menu gerencial.',
    expected: 'O cancelamento deve ser autorizado com cupom, mensagens ao operador e senha de supervisor mascarada.'
  },
  {
    id: '14',
    label: 'Seq. 14 - Cancelamento da transacao de credito',
    functionId: 110,
    guidance: 'Utilize o comprovante da seq. 6 e realize o cancelamento da transacao de credito pelo menu gerencial.',
    expected: 'O cancelamento deve ser autorizado com cupom, mensagens ao operador e senha de supervisor mascarada.'
  },
  {
    id: '15',
    label: 'Seq. 15 - Reimpressao do cancelamento',
    functionId: 113,
    guidance: 'Separe o comprovante da seq. 13 e solicite a reimpressao especifica pelo menu 110/112 ou diretamente pela funcao 113.',
    expected: 'A reimpressao do cancelamento deve ser autorizada com cupom e senha de supervisor mascarada.'
  },
  {
    id: '16',
    label: 'Seq. 16 - Venda QR Code',
    functionId: 122,
    valor: '10',
    trnInitParameters: '{TransacoesAdicionaisHabilitadas=7;8;9;38;37}',
    guidance: 'Realize a venda por QR Code pelo menu generico (funcao 0) ou diretamente pela funcao 122.',
    expected: 'A transacao deve ser autorizada com mensagens e impressao de cupom.'
  },
  {
    id: '17',
    label: 'Seq. 17 - Cancelamento QR Code',
    functionId: 123,
    valor: '10',
    trnInitParameters: '{TransacoesAdicionaisHabilitadas=7;8;9;38;37}',
    guidance: 'Separe o comprovante da seq. 16 e realize o cancelamento pelo menu 110 ou diretamente pela funcao 123, informando valor, documento e data.',
    expected: 'O cancelamento deve ser autorizado com cupom, mensagens ao operador e senha de supervisor mascarada.'
  },
  {
    id: '18',
    label: 'Seq. 18 - Tratamento de transacoes pendentes',
    functionId: 130,
    guidance: 'Depois da mensagem Retire o Cartao, encerre a aplicacao ou desligue o equipamento antes de remover o cartao e valide o tratamento automatico/manual da pendencia ao retornar.',
    expected: 'A automacao deve confirmar ou desfazer a pendencia automaticamente e informar o resultado ao operador.'
  },
  {
    id: '19',
    label: 'Seq. 19 - Reimpressao apos pendencia confirmada',
    functionId: 114,
    guidance: 'Apos confirmar a pendencia anterior, solicite a reimpressao do ultimo comprovante via 110/112 ou diretamente pela funcao 114.',
    expected: 'A reimpressao deve ser autorizada com cupom.'
  },
  {
    id: '20',
    label: 'Seq. 20 - TLS Fiserv',
    functionId: 669,
    showAdvanced: true,
    guidance: 'Demonstre o envio do TokenRegistro na startTransaction e, se usar registro manual, execute o fluxo pela funcao 669 ou pelo menu 110.',
    expected: 'A tela deve evidenciar o envio dos parametros TLS e/ou o menu de registro do terminal.'
  },
  {
    id: '21',
    label: 'Seq. 21 - Multiplos pagamentos com troco em dinheiro',
    functionId: 3,
    valor: '20',
    trnAdditionalParameters: MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS,
    guidance: 'Valor total da venda: R$ 50,00. Inicie uma transacao de credito no valor de R$ 20,00, realize o pagamento exclusivamente com chip, selecione A Vista e finalize a venda em dinheiro no valor de R$ 50,00, registrando o troco na aplicacao. O dinheiro deve ser lancado por ultimo no cupom fiscal.',
    expected: 'A transacao TEF deve ser autorizada, com cupom e registro do troco em dinheiro na aplicacao.'
  },
  {
    id: '22',
    label: 'Seq. 22 - Multiplos pagamentos com dois cartoes',
    functionId: 3,
    valor: '40',
    trnAdditionalParameters: MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS,
    guidance: 'Valor total da venda: R$ 100,00. Realize a primeira transacao de credito no valor de R$ 40,00, selecione A Vista e conclua a segunda parte no debito, no valor de R$ 60,00, com o mesmo TaxInvoiceNumber/DataFiscal e usando chip.',
    expected: 'As duas transacoes devem ser autorizadas e o cupom deve ser impresso.'
  },
  {
    id: '23',
    label: 'Seq. 23 - Multiplos pagamentos com carteira digital',
    functionId: 3,
    valor: '100',
    trnAdditionalParameters: MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS,
    guidance: 'Valor total da venda: R$ 150,00. Realize a primeira transacao de credito no valor de R$ 100,00, selecione A Vista e conclua o restante, no valor de R$ 50,00, com carteira digital no mesmo TaxInvoiceNumber/DataFiscal.',
    expected: 'As transacoes devem ser autorizadas e o cupom deve ser impresso.'
  },
  {
    id: '28',
    label: 'Seq. 28 - Multiplos pagamentos com troco em dinheiro',
    functionId: 3,
    valor: '20',
    trnAdditionalParameters: MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS,
    guidance: 'Valor total da venda: R$ 50,00. Autorize a parte TEF de R$ 20,00 e conclua a venda com dinheiro por ultimo, registrando o troco na aplicacao.',
    expected: 'A transacao TEF deve ser autorizada, com cupom e registro do troco na aplicacao.'
  },
  {
    id: '29',
    label: 'Seq. 29 - Multiplos pagamentos com dois cartoes',
    functionId: 3,
    valor: '40',
    trnAdditionalParameters: MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS,
    guidance: 'Valor total da venda: R$ 100,00. Autorize a primeira parte no credito a vista (R$ 40,00) e conclua a segunda parte no debito (R$ 60,00) com o mesmo TaxInvoiceNumber/DataFiscal.',
    expected: 'As duas transacoes devem ser autorizadas e o cupom deve ser impresso.'
  },
  {
    id: '30',
    label: 'Seq. 30 - Multiplos pagamentos com carteira digital',
    functionId: 3,
    valor: '100',
    trnAdditionalParameters: MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS,
    guidance: 'Valor total da venda: R$ 150,00. Autorize a primeira parte no credito a vista (R$ 100,00) e conclua o restante (R$ 50,00) com carteira digital no mesmo TaxInvoiceNumber/DataFiscal.',
    expected: 'As transacoes devem ser autorizadas e o cupom deve ser impresso.'
  },
  {
    id: '99',
    label: 'Extra - Timeout de 60 segundos por tela',
    functionId: 3,
    guidance: 'Teste interno fora do roteiro: interrompa o fluxo em qualquer tela por 60 segundos ou mais.',
    expected: 'A automacao deve cancelar por inatividade e nao imprimir cupom.'
  }
]

const SEQUENCES_AUTOGENERATE_FISCAL_DOCUMENT = new Set(['5', '6', '7', '8', '10', '16', '21', '22', '23', '28', '29', '30'])
const SEQUENCES_REQUIRE_ORIGINAL_DOCUMENT_REFERENCE = new Set(['12', '13', '14', '15', '17'])

const getSequencePreset = (sequenceId) => SEQUENCE_PRESETS.find((item) => item.id === String(sequenceId || ''))
const sequenceAutogeneratesFiscalDocument = (sequenceId) => SEQUENCES_AUTOGENERATE_FISCAL_DOCUMENT.has(String(sequenceId || ''))
const sequenceRequiresOriginalDocumentReference = (sequenceId) => SEQUENCES_REQUIRE_ORIGINAL_DOCUMENT_REFERENCE.has(String(sequenceId || ''))
const SEQUENCES_PREFER_NSU_HOST_DOCUMENT = new Set(['12'])
const MULTIPLE_PAYMENT_TOTALS = {
  '21': 50,
  '28': 50
}

const MULTIPLE_PAYMENT_CASH_DEFAULTS = {
  '21': '50,00',
  '28': '50,00'
}
const SEQUENCES_WITH_CASH_CHANGE = new Set(['21', '28'])

const parseCurrencyInputValue = (value) => {
  const normalized = String(value || '').replace(',', '.').trim()
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : 0
}

const formatCurrencyDisplay = (value) =>
  Number(value || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const currencyToCentavos = (value) => Math.max(Math.round((Number(value) || 0) * 100), 0)

const resolvePrimaryTefNfpagType = (functionIdValue) => {
  const normalized = Number(functionIdValue)
  if (normalized === 2) return '02'
  if (normalized === 122) return '12'
  return '03'
}

const buildCashChangeReceiptComplement = (registration) => {
  if (!registration || typeof registration !== 'object') return ''
  const total = Number(registration.total_sale || 0)
  const tef = Number(registration.tef_amount || 0)
  const cashDue = Number(registration.cash_due || 0)
  const cashReceived = Number(registration.cash_received || 0)
  const cashChange = Number(registration.cash_change || 0)
  return [
    '=== PAGAMENTO COMPLEMENTAR ===',
    `Total da venda: R$ ${formatCurrencyDisplay(total)}`,
    `TEF aprovado: R$ ${formatCurrencyDisplay(tef)}`,
    `Dinheiro lancado no cupom: R$ ${formatCurrencyDisplay(cashDue)}`,
    `Dinheiro recebido: R$ ${formatCurrencyDisplay(cashReceived)}`,
    `Troco em dinheiro: R$ ${formatCurrencyDisplay(cashChange)}`
  ].join('\n')
}

const buildAutoCashChangeNfpag = ({
  sequenceId,
  functionIdValue,
  nfpagRawValue,
  firstTefAmount,
  totalSaleAmount,
  cashReceivedAmount
}) => {
  const sequence = String(sequenceId || '')
  const raw = String(nfpagRawValue || '').trim()
  const total = Number(totalSaleAmount || 0)
  const tef = Math.max(Number(firstTefAmount || 0), 0)
  const cashDue = Math.max(total - tef, 0)
  const cashReceivedInput = Math.max(Number(cashReceivedAmount || 0), 0)
  const cashReceived = SEQUENCES_WITH_CASH_CHANGE.has(sequence) && cashReceivedInput <= 0
    ? Math.max(total, 0)
    : cashReceivedInput
  const cashChange = Math.max(cashReceived - cashDue, 0)

  const registration =
    total > 0
      ? {
          total_sale: total,
          tef_amount: tef,
          cash_due: cashDue,
          cash_received: cashReceived,
          cash_change: cashChange
        }
      : null

  if (!SEQUENCES_WITH_CASH_CHANGE.has(sequence)) {
    return { nfpagRawToSend: raw, registration, error: '' }
  }

  if (raw) {
    return { nfpagRawToSend: raw, registration, error: '' }
  }

  if (total <= 0 || tef <= 0 || cashDue <= 0) {
    return { nfpagRawToSend: '', registration, error: '' }
  }

  if (cashReceived < cashDue) {
    return {
      nfpagRawToSend: '',
      registration,
      error: `Dinheiro recebido (R$ ${formatCurrencyDisplay(cashReceived)}) menor que o restante da venda (R$ ${formatCurrencyDisplay(cashDue)}).`
    }
  }

  const generatedNfpag = buildNfpagString([
    { tipo: resolvePrimaryTefNfpagType(functionIdValue), valor: String(currencyToCentavos(tef)), extras: '' },
    { tipo: '00', valor: String(currencyToCentavos(cashDue)), extras: '' }
  ])

  return {
    nfpagRawToSend: generatedNfpag ? `NFPAG=${generatedNfpag}` : '',
    registration,
    error: ''
  }
}

const MULTIPLE_PAYMENT_VALUE_HINTS = {
  '21': 'Este campo representa apenas a 1a parcela TEF do roteiro: R$ 20,00. O total da venda e R$ 50,00, com fechamento em dinheiro e troco.',
  '22': 'Este campo representa apenas a 1a parcela TEF do roteiro: R$ 40,00. O total da venda e R$ 100,00; a 2a parcela e R$ 60,00 no debito.',
  '23': 'Este campo representa apenas a 1a parcela TEF do roteiro: R$ 100,00. O total da venda e R$ 150,00; a 2a parcela e R$ 50,00 na carteira digital.',
  '28': 'Este campo representa apenas a 1a parcela TEF do roteiro: R$ 20,00. O total da venda e R$ 50,00, com fechamento em dinheiro e troco.',
  '29': 'Este campo representa apenas a 1a parcela TEF do roteiro: R$ 40,00. O total da venda e R$ 100,00; a 2a parcela e R$ 60,00 no debito.',
  '30': 'Este campo representa apenas a 1a parcela TEF do roteiro: R$ 100,00. O total da venda e R$ 150,00; a 2a parcela e R$ 50,00 na carteira digital.'
}

const GUIDED_TWO_STEP_CARD_SEQUENCE_CONFIG = {
  '22': {
    firstFunctionId: 3,
    firstAmount: 40,
    firstLabel: 'Credito',
    firstInstallmentLabel: 'A vista',
    firstTrnAdditionalParameters: MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS,
    secondFunctionId: 2,
    secondAmount: 60,
    secondLabel: 'Debito com chip',
    secondTrnAdditionalParameters: MULTIPLE_PAYMENT_DEBIT_ADDITIONAL_PARAMETERS,
    secondExecutionText: 'com o segundo cartao de debito',
    secondRequirementText: 'O pagamento da 2a etapa deve ser realizado exclusivamente com chip, mantendo o mesmo Cupom/Data/Hora.'
  },
  '23': {
    firstFunctionId: 3,
    firstAmount: 100,
    firstLabel: 'Credito',
    firstInstallmentLabel: 'A vista',
    firstTrnAdditionalParameters: MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS,
    secondFunctionId: 122,
    secondAmount: 50,
    secondLabel: 'Carteira digital',
    secondTrnAdditionalParameters: MULTIPLE_PAYMENT_WALLET_ADDITIONAL_PARAMETERS,
    secondExecutionText: 'utilizando carteira digital (QR Code)',
    secondRequirementText: 'Conclua a 2a etapa na carteira digital e mantenha o mesmo Cupom/Data/Hora da 1a etapa.',
    secondTrnInitParameters: '{TransacoesAdicionaisHabilitadas=7;8;9;38;37}'
  },
  '29': {
    firstFunctionId: 3,
    firstAmount: 40,
    firstLabel: 'Credito',
    firstInstallmentLabel: 'A vista',
    firstTrnAdditionalParameters: MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS,
    secondFunctionId: 2,
    secondAmount: 60,
    secondLabel: 'Debito com chip',
    secondTrnAdditionalParameters: MULTIPLE_PAYMENT_DEBIT_ADDITIONAL_PARAMETERS,
    secondExecutionText: 'com o segundo cartao de debito',
    secondRequirementText: 'O pagamento da 2a etapa deve ser realizado exclusivamente com chip, mantendo o mesmo Cupom/Data/Hora.'
  },
  '30': {
    firstFunctionId: 3,
    firstAmount: 100,
    firstLabel: 'Credito',
    firstInstallmentLabel: 'A vista',
    firstTrnAdditionalParameters: MULTIPLE_PAYMENT_CREDIT_ADDITIONAL_PARAMETERS,
    secondFunctionId: 122,
    secondAmount: 50,
    secondLabel: 'Carteira digital',
    secondTrnAdditionalParameters: MULTIPLE_PAYMENT_WALLET_ADDITIONAL_PARAMETERS,
    secondExecutionText: 'utilizando carteira digital (QR Code)',
    secondRequirementText: 'Conclua a 2a etapa na carteira digital e mantenha o mesmo Cupom/Data/Hora da 1a etapa.',
    secondTrnInitParameters: '{TransacoesAdicionaisHabilitadas=7;8;9;38;37}'
  }
}

const sequencePrefersNsuHostDocument = (sequenceId) => SEQUENCES_PREFER_NSU_HOST_DOCUMENT.has(String(sequenceId || ''))
const onlyDigits = (value) => String(value || '').replace(/\D/g, '')
const extractFiscalDateTime = (reference) => {
  const dataHoraDigits = onlyDigits(reference?.data_hora_transacao)
  if (dataHoraDigits.length >= 14) {
    return {
      data_fiscal: dataHoraDigits.slice(0, 8),
      hora_fiscal: dataHoraDigits.slice(8, 14)
    }
  }
  return {
    data_fiscal: '',
    hora_fiscal: ''
  }
}
const normalizeFiscalReference = (reference) => {
  if (!reference) return null
  const cupomFiscal = String(reference?.cupom_fiscal || reference?.campo_516_valor || '').trim()
  const nsuHost = String(reference?.nsu_host || reference?.nsu || '').trim()
  const nsuSitef = String(reference?.nsu_sitef || '').trim()
  const redeAutorizadora = String(reference?.rede_autorizadora || '').trim()
  const bandeira = String(reference?.bandeira || '').trim()
  const fiscalDateTime = extractFiscalDateTime(reference)
  const dataFiscal = fiscalDateTime.data_fiscal || onlyDigits(reference?.data_fiscal)
  const horaFiscal = fiscalDateTime.hora_fiscal || onlyDigits(reference?.hora_fiscal)
  if ((!cupomFiscal && !nsuHost && !nsuSitef) || dataFiscal.length !== 8 || horaFiscal.length !== 6) return null
  return {
    ...reference,
    cupom_fiscal: cupomFiscal || nsuHost || nsuSitef,
    nsu_host: nsuHost || null,
    nsu_sitef: nsuSitef || null,
    data_fiscal: dataFiscal,
    hora_fiscal: horaFiscal,
    rede_autorizadora: redeAutorizadora || null,
    bandeira: bandeira || null,
  }
}

const buildSeq3Conformance = (sequenceId, tefResultado, tefErro) => {
  if (String(sequenceId || '') !== '3') return null

  const mensagem = String(
    tefResultado?.message ||
    tefResultado?.prompt ||
    tefErro ||
    ''
  ).toLowerCase()
  const clisitefStatus = Number(tefResultado?.clisitef_status)
  const temCupom = Boolean(
    tefResultado?.cupom_cliente ||
    tefResultado?.tef_cupom_cliente ||
    tefResultado?.cupom_estabelecimento ||
    tefResultado?.tef_cupom_estabelecimento
  )

  const achouNaoExisteConf = mensagem.includes('nao existe conf') || mensagem.includes('n?o existe conf')
  const bloqueioComunicacao = mensagem.includes('registro do terminal') || mensagem.includes('erro de comunicacao') || clisitefStatus === -5

  if (achouNaoExisteConf && !temCupom) {
    return {
      ok: true,
      title: 'Status Seq. 3: CONFORME',
      detail: 'Fluxo atingiu o retorno esperado "Nao Existe Conf", sem autorizacao e sem cupom.'
    }
  }

  if (bloqueioComunicacao) {
    return {
      ok: false,
      title: 'Status Seq. 3: NAO CONFORME (parcial)',
      detail: 'Enquanto existir o bloqueio de comunicacao/registro do terminal, o fluxo nao chega no erro de configuracao storeId=1111AAAA ("Nao Existe Conf").'
    }
  }

  return {
    ok: false,
    title: 'Status Seq. 3: NAO CONFORME',
    detail: 'Retorno diferente do esperado para a sequencia 3. Revise ambiente, storeId e evidencias da transacao.'
  }
}


const isSessionLostError = (message) => {
  const raw = String(message || '').toLowerCase()
  return raw.includes('sessao tef nao encontrada') || raw.includes('sessao tef expirada') || raw.includes('sessao tef n?o encontrada') || raw.includes('sessao tef n?o encontrada')
}

const normalizeValidationText = (value) =>
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()

const CREDIT_INSTALLMENT_SEQUENCE_TARGETS = {
  '7': 'parcelado pelo estabelecimento',
  '8': 'parcelado pela administradora'
}

const buildCreditInstallmentMenuHint = (sequenceId, prompt, menuOptions) => {
  const target = CREDIT_INSTALLMENT_SEQUENCE_TARGETS[String(sequenceId || '')]
  if (!target || !Array.isArray(menuOptions) || menuOptions.length === 0) return null

  const title = normalizeValidationText(prompt?.menu_title || '')
  const rawPrompt = normalizeValidationText(prompt?.prompt || '')
  const optionTexts = menuOptions.map((item) => normalizeValidationText(item?.text))
  const hasCreditCardTypeOption = optionTexts.some((text) => text === 'cartao de credito' || text.includes('cartao de credito'))
  const hasTargetInstallmentOption = optionTexts.some((text) => text.includes(target))

  if ((title.includes('tipo do cartao de credito') || rawPrompt.includes('cartao de credito')) && hasCreditCardTypeOption && !hasTargetInstallmentOption) {
    return {
      tone: 'info',
      title: 'Este ainda nao e o menu de parcelamento',
      detail: `Selecione Cartao de Credito e insira/aproxime o cartao. O menu ${target} aparece depois da leitura do cartao, conforme o fluxo da CliSiTef.`
    }
  }

  if (hasTargetInstallmentOption) {
    return {
      tone: 'success',
      title: 'Menu de parcelamento encontrado',
      detail: `Agora selecione ${target}.`
    }
  }

  return null
}

const inferSpecificReprintMenuOption = (menuOptions, reference) => {
  if (!Array.isArray(menuOptions) || menuOptions.length === 0 || !reference) return null

  const networkCode = String(reference?.rede_autorizadora || '').replace(/\D/g, '').replace(/^0+/, '')
  const networkLabel = normalizeValidationText(`${reference?.rede_autorizadora || ''} ${reference?.bandeira || ''}`)

  let targetLabel = ''
  if (networkCode === '229' || networkLabel.includes('rede') || networkLabel.includes('redecard') || networkLabel.includes('redeshop')) {
    targetLabel = 'rede'
  } else if (networkCode === '5' || networkCode === '2' || networkLabel.includes('cielo') || networkLabel.includes('visanet')) {
    targetLabel = 'cielo'
  } else if (networkCode || networkLabel) {
    targetLabel = 'outros'
  }

  if (!targetLabel) return null
  return menuOptions.find((item) => normalizeValidationText(item?.text).includes(targetLabel)) || null
}

const APPROVED_SEQUENCE_FAILURE_HINTS = [
  'cartao nao configurado',
  'trn. nao habilitada',
  'trn nao habilitada',
  'nao habilitada',
  'erro pinpad',
  'sem comunicacao com o sitef',
  'modo invalido',
  'transacao negada',
  'nao autorizada'
]

const evaluateSequenceValidation = (sequenceId, tefResultado, tefPrompt, tefErro, pendenciaStatus) => {
  const seq = String(sequenceId || '')
  if (!seq) return null

  const clisitefStatus = Number(tefResultado?.clisitef_status ?? tefPrompt?.clisitef_status ?? NaN)
  const aprovado = Boolean(tefResultado?.aprovado)
  const hasCupom = Boolean(
    tefResultado?.cupom_cliente || tefResultado?.tef_cupom_cliente ||
    tefResultado?.cupom_estabelecimento || tefResultado?.tef_cupom_estabelecimento
  )
  const message = normalizeValidationText(tefResultado?.message || tefPrompt?.prompt || tefErro || '')

  const approvedSeq = new Set(['5', '6', '7', '8', '10', '11', '12', '13', '14', '15', '16', '17', '19', '21', '22', '23', '28', '29', '30'])
  const deniedSeq = new Set(['2', '3', '4', '9', '99'])

  if (seq === '1') {
    const menuOk = ['teste de comunicacao', 'reimpress', 'cancelamento', 'registro'].every((k) => message.includes(k))
    return {
      status: menuOk ? 'pass' : 'pending',
      title: menuOk ? 'PASS' : 'PENDENTE',
      detail: menuOk ? 'Menu 110 completo identificado na tela.' : 'Valide visualmente se todas as opcoes da functionId 110 foram exibidas.'
    }
  }

  if (seq === '3') {
    if (message.includes('nao existe conf') || message.includes('n?o existe conf')) {
      return {
        status: !aprovado && !hasCupom ? 'pass' : 'fail',
        title: !aprovado && !hasCupom ? 'PASS' : 'FAIL',
        detail: !aprovado && !hasCupom ? 'Retorno esperado de configuracao recebido (Nao Existe Conf).' : 'Recebeu Nao Existe Conf, mas o resultado final nao bate com o roteiro.'
      }
    }
    if (message.includes('registro do terminal') || message.includes('erro de comunicacao') || clisitefStatus === -5) {
      return {
        status: 'fail',
        title: 'FAIL',
        detail: 'Bloqueio operacional de comunicacao/registro impede chegar no retorno Nao Existe Conf.'
      }
    }
    return {
      status: 'pending',
      title: 'PENDENTE',
      detail: 'Execute a sequencia ate o retorno final para validar Nao Existe Conf.'
    }
  }

  if (seq === '18') {
    if (typeof tefResultado?.success === 'boolean') {
      const actionLabel = tefResultado?.confirmar === false ? 'desfazimento' : 'confirmacao'
      const ok = Boolean(tefResultado?.success)
      return {
        status: ok ? 'pass' : 'fail',
        title: ok ? 'PASS' : 'FAIL',
        detail: ok
          ? `Tratamento automatico de pendencias concluido com ${actionLabel}.`
          : 'O tratamento automatico de pendencias retornou falha no backend/agente.'
      }
    }

    const pendenciaOk = String(pendenciaStatus || tefResultado?.message || '').toLowerCase().includes('pendenc')
    return {
      status: pendenciaOk ? 'pass' : 'pending',
      title: pendenciaOk ? 'PASS' : 'PENDENTE',
      detail: pendenciaOk ? 'Tratamento de pendencias registrado.' : 'Validar confirmacao/desfazimento automatico de pendencias.'
    }
  }

  if (approvedSeq.has(seq)) {
    if (!tefResultado) {
      const explicitFailure = APPROVED_SEQUENCE_FAILURE_HINTS.some((hint) => message.includes(hint))
      if (explicitFailure) {
        return {
          status: 'fail',
          title: 'FAIL',
          detail: 'Retorno do ambiente indica bloqueio/nao habilitacao (ex.: cartao nao configurado), antes da autorizacao com cupom.'
        }
      }
      return { status: 'pending', title: 'PENDENTE', detail: 'Aguardando resultado final da transacao.' }
    }
    const ok = aprovado && hasCupom
    return {
      status: ok ? 'pass' : 'fail',
      title: ok ? 'PASS' : 'FAIL',
      detail: ok ? 'Transacao autorizada com cupom, conforme roteiro.' : 'Esperava autorizacao com cupom e nao ocorreu.'
    }
  }

  if (deniedSeq.has(seq)) {
    if (!tefResultado && !tefErro) {
      return { status: 'pending', title: 'PENDENTE', detail: 'Aguardando resultado final da transacao.' }
    }
    const ok = !aprovado && !hasCupom
    return {
      status: ok ? 'pass' : 'fail',
      title: ok ? 'PASS' : 'FAIL',
      detail: ok ? 'Transacao negada/cancelada sem cupom, conforme roteiro.' : 'Esperava nao autorizacao sem cupom e nao ocorreu.'
    }
  }

  return { status: 'pending', title: 'PENDENTE', detail: 'Sem regra automatica para esta sequencia. Validacao manual.' }
}

const buildSequenceEvidenceChecklist = (sequenceId, tefResultado, tefPrompt, manualEvidence) => {
  const seq = String(sequenceId || '')
  if (!seq) return []

  const message = String(tefResultado?.message || tefPrompt?.prompt || '').trim()
  const hasCupom = Boolean(
    tefResultado?.cupom_cliente || tefResultado?.tef_cupom_cliente ||
    tefResultado?.cupom_estabelecimento || tefResultado?.tef_cupom_estabelecimento
  )
  const hasDataHora = Boolean(tefResultado?.data_hora_transacao)
  const hasNsuHost = Boolean(tefResultado?.nsu_host || tefResultado?.nsu)
  const hasNsuSitef = Boolean(tefResultado?.nsu_sitef)

  const requiresCupom = new Set(['5', '6', '7', '8', '10', '11', '12', '13', '14', '15', '16', '17', '19', '21', '22', '23'])
  const requiresNoCupom = new Set(['2', '3', '4', '9', '99'])
  const requiresSupervisorMask = new Set(['11', '12', '13', '14', '15'])

  return [
    { id: 'msg', label: 'Mensagem exibida ao operador', required: true, done: Boolean(message), manual: false },
    { id: 'datahora', label: 'Data/hora da transacao registrada', required: true, done: hasDataHora, manual: false },
    { id: 'nsu_host', label: 'NSU Host registrado', required: requiresCupom.has(seq), done: hasNsuHost, manual: false },
    { id: 'nsu_sitef', label: 'NSU SiTef registrado', required: false, done: hasNsuSitef, manual: false },
    { id: 'cupom', label: 'Cupom TEF conforme esperado', required: requiresCupom.has(seq) || requiresNoCupom.has(seq), done: requiresNoCupom.has(seq) ? !hasCupom : hasCupom, manual: false },
    { id: 'supervisor_mask', label: 'Senha supervisor mascarada (FieldId 500)', required: requiresSupervisorMask.has(seq), done: Boolean(manualEvidence?.supervisor_mask), manual: true },
    { id: 'print', label: 'Print de evidencia capturado', required: true, done: Boolean(manualEvidence?.print), manual: true },
  ]
}

export default function ModalTefGerencial({ onClose }) {
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
  const [selectedSequence, setSelectedSequence] = useState('')

  const [functionId, setFunctionId] = useState(110)
  const [valor, setValor] = useState('')
  const [cupomFiscal, setCupomFiscal] = useState('')
  const [dataFiscal, setDataFiscal] = useState('')
  const [horaFiscal, setHoraFiscal] = useState('')
  const [trnAdditionalParameters, setTrnAdditionalParameters] = useState('')
  const [trnInitParameters, setTrnInitParameters] = useState('')
  const [sessionParameters, setSessionParameters] = useState('')
  const [sitefIp, setSitefIp] = useState('')
  const [storeId, setStoreId] = useState('')
  const [terminalId, setTerminalId] = useState('')
  const [cashierOperator, setCashierOperator] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [justificativa, setJustificativa] = useState('')
  const [tlsToken, setTlsToken] = useState(DEFAULT_TLS_TOKEN)
  const [manualEvidence, setManualEvidence] = useState({ print: false, supervisor_mask: false })
  const [diagRunning, setDiagRunning] = useState(false)
  const [diagReport, setDiagReport] = useState(null)
  const [lastFiscalReference, setLastFiscalReference] = useState(null)
  const [nfpagRaw, setNfpagRaw] = useState('')
  const [nfpagItems, setNfpagItems] = useState([])
  const [nfpagTipo, setNfpagTipo] = useState('')
  const [nfpagValor, setNfpagValor] = useState('')
  const [cashReceivedValue, setCashReceivedValue] = useState('')
  const [nfpagExtraFields, setNfpagExtraFields] = useState({})
  const [nfpagError, setNfpagError] = useState('')
  const [deferredBatchSessionId, setDeferredBatchSessionId] = useState('')

  const tefSessionRef = useRef(null)
  const tefIdleTimerRef = useRef(null)
  const tefAutoMenuRef = useRef('')
  const tefAutoFinalizeSessionRef = useRef('')
  const lastStartedFiscalRef = useRef({ cupom_fiscal: '', data_fiscal: '', hora_fiscal: '' })
  const lastGeneratedFiscalNumberRef = useRef('')

  const nfpagTypeOptions = useMemo(() => getNfpagTypeOptions(tefResultado?.nfpag), [tefResultado])
  const nfpagSelectedType = useMemo(() => getNfpagTypeDetail(tefResultado?.nfpag, nfpagTipo), [tefResultado, nfpagTipo])


  const resolvePromptDefaultInput = (payload, fallbackValue) => {
    if (!sequenceRequiresOriginalDocumentReference(selectedSequence)) return fallbackValue

    const fieldId = Number(payload?.field_id)
    const reference = payload?.referencia_reimpressao
    const promptNormalized = String(payload?.prompt || '').toLowerCase()
    const networkCode = String(reference?.rede_autorizadora || '').replace(/\D/g, '').replace(/^0+/, '')
    const isRedeSpecificReprint = fieldId === 515 && (
      networkCode === '229' ||
      (Array.isArray(payload?.tipo_campos) && payload.tipo_campos.some((item) => String(item?.TipoCampo || item?.codigo || '').trim() === '3006'))
    )

    if (fieldId === 601) {
      const suggestedRawValue = String(reference?.campo_146_valor_bruto || '').trim() || String(reference?.campo_146_valor || '').replace(/\D/g, '')
      return suggestedRawValue || ''
    }

    if (fieldId === 146) {
      return String(reference?.campo_146_valor || reference?.campo_146_informado || '').trim()
    }

    if (fieldId === 516) {
      const preferNsuHostDocument = sequencePrefersNsuHostDocument(selectedSequence)
      return String(
        (preferNsuHostDocument && reference?.nsu_host) ||
        reference?.campo_516_valor ||
        reference?.campo_516_informado ||
        ''
      ).trim()
    }

    if (fieldId === 515) {
      if (isRedeSpecificReprint) {
        return String(reference?.campo_515_valor_mmdd || reference?.campo_515_valor || reference?.campo_515_informado || '').trim()
      }
      if (promptNormalized.includes('ddmm') && !promptNormalized.includes('ddmmaaaa')) {
        return String(reference?.campo_515_valor_ddmm || reference?.campo_515_valor || reference?.campo_515_informado || '').trim()
      }
      return String(reference?.campo_515_valor || reference?.campo_515_informado || '').trim()
    }

    return fallbackValue
  }

  const resetTefFlow = () => {
    if (tefIdleTimerRef.current) {
      clearTimeout(tefIdleTimerRef.current)
      tefIdleTimerRef.current = null
    }
    tefSessionRef.current = null
    setTefSessionId(null)
    setTefPrompt(null)
    setTefInput('')
    setTefInputMode('manual')
    setTefErro('')
    setTefResultado(null)
    setTefProcessando(false)
    setPendenciaStatus('')
    setManualEvidence({ print: false, supervisor_mask: false })
    setNfpagRaw('')
    setNfpagItems([])
    setNfpagTipo('')
    setNfpagValor('')
    setCashReceivedValue('')
    setNfpagExtraFields({})
    setNfpagError('')
    setDeferredBatchSessionId('')
    tefAutoFinalizeSessionRef.current = ''
    tefAutoMenuRef.current = ''
  }

  const aplicarPresetSequencia = (sequenceId) => {
    const nextId = String(sequenceId || '')
    setSelectedSequence(nextId)

    const preset = getSequencePreset(nextId)
    if (!preset) return

    const guidedConfig = GUIDED_TWO_STEP_CARD_SEQUENCE_CONFIG[nextId] || null
    setDeferredBatchSessionId('')
    setFunctionId(preset.functionId)
    setValor(preset.valor || '')
    setTrnAdditionalParameters(guidedConfig?.firstTrnAdditionalParameters || preset.trnAdditionalParameters || '')
    setTrnInitParameters(guidedConfig?.firstTrnInitParameters || preset.trnInitParameters || '')
    setSessionParameters(preset.sessionParameters || '')
    setShowAdvanced(Boolean(preset.showAdvanced))
    setCashReceivedValue(MULTIPLE_PAYMENT_CASH_DEFAULTS[nextId] || '')

    if (sequenceRequiresOriginalDocumentReference(nextId)) {
      const fiscal = buildFiscalStamp()
      setCupomFiscal(fiscal.cupom)
      setDataFiscal(fiscal.data)
      setHoraFiscal(fiscal.hora)
    }

    if (JUSTIFICATIVA_REQUIRED_FUNCTIONS.has(preset.functionId)) {
      setJustificativa(`Homologacao TEF - ${preset.label}`)
    } else {
      setJustificativa('')
    }
  }

  useEffect(() => {
    if (!JUSTIFICATIVA_REQUIRED_FUNCTIONS.has(functionId)) {
      setJustificativa('')
    }
  }, [functionId])

  useEffect(() => {
    if (functionId === 110) {
      setValor('')
    }
  }, [functionId])

  useEffect(() => {
    setManualEvidence({ print: false, supervisor_mask: false })
  }, [selectedSequence])

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

  const iniciarTimeoutInatividade = () => {
    if (tefIdleTimerRef.current) {
      clearTimeout(tefIdleTimerRef.current)
    }
    tefIdleTimerRef.current = setTimeout(() => {
      encerrarFluxoTef(`Sessao TEF expirada por inatividade (${TEF_IDLE_TIMEOUT_SECONDS}s).`)
    }, TEF_IDLE_TIMEOUT_MS)
  }

  useEffect(() => {
    const normalized = normalizeFiscalReference(tefResultado?.referencia_reimpressao || tefPrompt?.referencia_reimpressao)
    if (!normalized) return
    if (!normalized.nsu_host && !normalized.nsu_sitef) return
    setLastFiscalReference(normalized)
  }, [tefResultado, tefPrompt])

  useEffect(() => {
    if (!showTefFlow || tefResultado || tefProcessando || !isAutoProcessingPrompt(tefPrompt)) {
      return undefined
    }

    const timer = setTimeout(() => {
      continuarFluxoTef(0, '')
    }, TEF_PROCESSING_POLL_DELAY_MS)

    return () => clearTimeout(timer)
  }, [showTefFlow, tefResultado, tefProcessando, tefPrompt])

  useEffect(() => {
    const sessionId = String(tefResultado?.session_id || '').trim()
    const requiresManualFinalization = SEQUENCES_WITH_CASH_CHANGE.has(String(selectedSequence || ''))
    const canAutoFinalize = Boolean(
      sessionId &&
      tefResultado?.finish_required &&
      !tefResultado?.finish_deferred &&
      !tefResultado?.finalizado &&
      !tefResultado?.pendencia_automatica &&
      !requiresManualFinalization &&
      !tefProcessando
    )

    if (!canAutoFinalize) {
      if (!sessionId) {
        tefAutoFinalizeSessionRef.current = ''
      }
      return undefined
    }

    if (tefAutoFinalizeSessionRef.current === sessionId) {
      return undefined
    }
    tefAutoFinalizeSessionRef.current = sessionId

    const timer = setTimeout(() => {
      concluirFluxoTef()
    }, 250)

    return () => clearTimeout(timer)
  }, [tefResultado, selectedSequence, tefProcessando])


  useEffect(() => {
    if (!showTefFlow || tefResultado || tefProcessando || String(selectedSequence || '') !== '12') {
      return undefined
    }

    const isSpecificReceiptTypeMenu = Number(tefPrompt?.command_id) === 21 &&
      normalizeValidationText(tefPrompt?.menu_title || '').includes('tipo do comprovante')

    if (!isSpecificReceiptTypeMenu) {
      tefAutoMenuRef.current = ''
      return undefined
    }

    const menuOptions = parseMenuOptions(Number(tefPrompt?.command_id), tefPrompt?.prompt || '')
    const reference = normalizeFiscalReference(tefPrompt?.referencia_reimpressao) || lastFiscalReference
    const autoOption = inferSpecificReprintMenuOption(menuOptions, reference)

    if (!autoOption) return undefined

    const signature = `${tefPrompt?.session_id || ''}:${tefPrompt?.menu_title || ''}:${tefPrompt?.prompt || ''}:${autoOption.index}`
    if (tefAutoMenuRef.current === signature) return undefined
    tefAutoMenuRef.current = signature

    const timer = setTimeout(() => {
      continuarFluxoTef(0, String(autoOption.index))
    }, 250)

    return () => clearTimeout(timer)
  }, [showTefFlow, tefResultado, tefProcessando, tefPrompt, selectedSequence, lastFiscalReference])

  const registrarAtividadeTef = () => {

    if (!showTefFlow) return
    iniciarTimeoutInatividade()
  }

  const marcarEvidenciaManual = (key) => {
    setManualEvidence((prev) => ({ ...prev, [key]: !prev?.[key] }))
  }

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

  const atualizarCampoNfpag = (codigo, valorCampo) => {
    setNfpagExtraFields((prev) => ({
      ...prev,
      [String(codigo || '').padStart(2, '0')]: valorCampo
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
    const valorCentavos = parseNfpagValor(nfpagValor)
    const maxFormas = Number(tefResultado?.nfpag?.max_formas)

    if (!tipo || !valorCentavos) {
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
      const nomes = faltantes
        .map((coleta) => coleta.descricao || NFPAG_COLLECTION_LABELS[coleta.codigo] || coleta.codigo)
        .join(', ')
      setNfpagError(`Preencha os campos obrigatorios do NFPAG: ${nomes}.`)
      return
    }

    const novo = {
      tipo,
      descricao: detalhesTipo?.descricao || NFPAG_TYPE_LABELS[tipo] || 'Forma nao mapeada',
      valor: valorCentavos,
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

  const tratarSessaoPerdida = async (mensagem) => {
    const motivo = mensagem || 'Sessao TEF expirada. Reinicie a sequencia.'
    await encerrarFluxoTef(motivo)
    setTefErro(motivo)
  }

  const buildFiscalStamp = () => {
    const now = new Date()
    const pad = (n, size = 2) => String(n).padStart(size, '0')
    const y = now.getFullYear()
    const m = pad(now.getMonth() + 1)
    const d = pad(now.getDate())
    const hh = pad(now.getHours())
    const mm = pad(now.getMinutes())
    const ss = pad(now.getSeconds())
    const ms = pad(now.getMilliseconds(), 3)
    let cupom = `${y}${m}${d}${hh}${mm}${ss}${ms}`
    if (cupom <= String(lastGeneratedFiscalNumberRef.current || '')) {
      cupom = String(Number(lastGeneratedFiscalNumberRef.current || '0') + 1)
    }
    lastGeneratedFiscalNumberRef.current = cupom
    return {
      cupom,
      data: `${y}${m}${d}`,
      hora: `${hh}${mm}${ss}`,
      iso: now.toISOString(),
    }
  }

  const fiscalJaUsadoNaUltimaAbertura = (cupom, data, hora) => {
    const last = lastStartedFiscalRef.current || {}
    return Boolean(
      cupom &&
      data &&
      hora &&
      String(last.cupom_fiscal || '') === String(cupom || '') &&
      String(last.data_fiscal || '') === String(data || '') &&
      String(last.hora_fiscal || '') === String(hora || '')
    )
  }

  const summarizeProbeMessage = (payload) =>
    String(payload?.message || payload?.prompt || '').trim()

  const hasCommunicationBlock = (probe) => {
    const startMsg = summarizeProbeMessage(probe?.start).toLowerCase()
    const contMsg = summarizeProbeMessage(probe?.continue).toLowerCase()
    const status = Number(probe?.continue?.clisitef_status)
    return startMsg.includes('erro de comunicacao') ||
      startMsg.includes('registro do terminal') ||
      contMsg.includes('erro de comunicacao') ||
      contMsg.includes('registro do terminal') ||
      status === -5
  }

  const runFunction3Probe = async (storeIdValue) => {
    const fiscal = buildFiscalStamp()
    const startPayload = {
      function_id: 3,
      valor: 10,
      cupom_fiscal: fiscal.cupom,
      data_fiscal: fiscal.data,
      hora_fiscal: fiscal.hora,
      store_id: storeIdValue,
    }
    const start = (await api.post('/pagamentos/tef/iniciar-funcao', startPayload, { timeout: TEF_REQUEST_TIMEOUT_MS })).data
    let cont = null
    const sid = start?.session_id
    if (sid) {
      cont = (await api.post('/pagamentos/tef/continuar', { session_id: sid, continue_flag: 0, data: '' }, { timeout: TEF_REQUEST_TIMEOUT_MS })).data
      await api.post('/pagamentos/tef/cancelar', { session_id: sid }, { timeout: TEF_REQUEST_TIMEOUT_MS })
    }
    return { start, continue: cont, checked_at: fiscal.iso }
  }

  const runFunction699Probe = async () => {
    const fiscal = buildFiscalStamp()
    const tokenToUse = String(tlsToken || PRE_HOMO_TLS_TOKEN).trim() || PRE_HOMO_TLS_TOKEN
    const initParam = `[TipoComunicacaoExterna=TLSGWP;TokenRegistro=${tokenToUse}]`
    const startPayload = {
      function_id: 699,
      cupom_fiscal: fiscal.cupom,
      data_fiscal: fiscal.data,
      hora_fiscal: fiscal.hora,
      trn_init_parameters: initParam,
    }

    const start = (await api.post('/pagamentos/tef/iniciar-funcao', startPayload, { timeout: TEF_REQUEST_TIMEOUT_MS })).data
    const sid = start?.session_id
    const steps = []
    let current = start

    if (sid) {
      for (let i = 0; i < 4; i += 1) {
        steps.push(current)
        if (current?.finish_required) break
        const sendData = Number(current?.field_id) === 2988 ? tokenToUse : ''
        current = (await api.post('/pagamentos/tef/continuar', { session_id: sid, continue_flag: 0, data: sendData }, { timeout: TEF_REQUEST_TIMEOUT_MS })).data
      }
      await api.post('/pagamentos/tef/cancelar', { session_id: sid }, { timeout: TEF_REQUEST_TIMEOUT_MS })
    }

    return { start, steps, checked_at: fiscal.iso }
  }

  const evaluateDiagnosticChecks = (baseProbe, regProbe, seq3Probe) => {
    const baseBlocked = hasCommunicationBlock(baseProbe)
    const regStartMsg = summarizeProbeMessage(regProbe?.start).toLowerCase()
    const regMsgs = [
      regStartMsg,
      ...(Array.isArray(regProbe?.steps) ? regProbe.steps.map((s) => summarizeProbeMessage(s).toLowerCase()) : []),
    ]
    const regHasField2988 = Number(regProbe?.start?.field_id) === 2988 || (Array.isArray(regProbe?.steps) && regProbe.steps.some((s) => Number(s?.field_id) === 2988))
    const regTokenInvalido = regMsgs.some((m) => m.includes('token invalido'))

    const seq3Msg = `${summarizeProbeMessage(seq3Probe?.start)} ${summarizeProbeMessage(seq3Probe?.continue)}`.toLowerCase()
    const seq3HasNaoExisteConf = seq3Msg.includes('nao existe conf') || seq3Msg.includes('n?o existe conf')
    const seq3Blocked = hasCommunicationBlock(seq3Probe)

    const checks = []

    checks.push({
      code: 'COMUNICACAO_BASE_00000000',
      status: baseBlocked ? 'FAIL' : 'PASS',
      summary: baseBlocked ? 'Bloqueio de comunicacao/registro ativo no store_id 00000000.' : 'Comunicacao base operante no store_id 00000000.',
      details: baseProbe,
    })

    let regStatus = 'FAIL'
    let regSummary = 'FunctionId 699 nao chegou na coleta de token do terminal.'
    if (regHasField2988 && regTokenInvalido) {
      regStatus = 'WARN'
      regSummary = 'FunctionId 699 chegou na coleta do token (campo 2988), mas o token foi invalido.'
    } else if (regHasField2988) {
      regStatus = 'PASS'
      regSummary = 'FunctionId 699 chegou na coleta de token (campo 2988).'
    }

    checks.push({
      code: 'REGISTRO_699',
      status: regStatus,
      summary: regSummary,
      details: regProbe,
    })

    let seq3Status = 'FAIL'
    let seq3Summary = 'Seq. 3 nao atingiu o retorno esperado Nao Existe Conf.'
    if (seq3HasNaoExisteConf) {
      seq3Status = 'PASS'
      seq3Summary = 'Seq. 3 atingiu o retorno esperado Nao Existe Conf.'
    } else if (seq3Blocked) {
      seq3Status = 'FAIL'
      seq3Summary = 'Seq. 3 bloqueada por comunicacao/registro antes de validar store_id=1111AAAA.'
    }

    checks.push({
      code: 'SEQ3_1111AAAA',
      status: seq3Status,
      summary: seq3Summary,
      details: seq3Probe,
    })

    return checks
  }

  const runOperationalDiagnostics = async () => {
    setDiagRunning(true)
    setDiagReport(null)
    setTefErro('')
    try {
      await api.delete('/pagamentos/tef/sessao', { timeout: TEF_REQUEST_TIMEOUT_MS })
      const baseProbe = await runFunction3Probe('00000000')
      const regProbe = await runFunction699Probe()
      await api.delete('/pagamentos/tef/sessao', { timeout: TEF_REQUEST_TIMEOUT_MS })
      const seq3Probe = await runFunction3Probe('1111AAAA')
      const checks = evaluateDiagnosticChecks(baseProbe, regProbe, seq3Probe)
      const report = {
        generated_at: new Date().toISOString(),
        checks,
      }
      setDiagReport(report)
      const hasFail = checks.some((c) => c.status === 'FAIL')
      if (hasFail) {
        toast.error('Diagnostico concluido com falhas operacionais.')
      } else {
        toast.success('Diagnostico operacional concluido.')
      }
    } catch (err) {
      console.error('Erro no diagnostico operacional TEF:', err)
      setTefErro(err?.response?.data?.detail || 'Falha ao executar diagnostico operacional TEF.')
    } finally {
      setDiagRunning(false)
    }
  }

  const imprimirDiagnostico = () => {
    if (!diagReport) return
    const janela = window.open('', '_blank')
    if (!janela) return
    const texto = JSON.stringify(diagReport, null, 2)
    janela.document.write(`
      <html>
        <head>
          <title>Diagnostico Operacional TEF</title>
          <style>
            body { font-family: monospace; padding: 16px; }
            pre { white-space: pre-wrap; font-size: 12px; }
          </style>
        </head>
        <body>
          <h2>Diagnostico Operacional TEF</h2>
          <pre>${texto}</pre>
        </body>
      </html>
    `)
    janela.document.close()
    janela.focus()
    janela.print()
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

  const cancelarSessaoTef = async () => {
    const sessionIdAtual = tefSessionRef.current || tefSessionId || tefPrompt?.session_id || tefResultado?.session_id
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
    const cashChangeComplement = buildCashChangeReceiptComplement(tefResultado?.cash_change_registration)

    const appendComplement = (text) => {
      const base = String(text || '')
      if (!base) return base
      if (!cashChangeComplement) return base
      return `${base}\n\n${cashChangeComplement}`
    }

    const fila = []
    if (cupomEstabelecimento) {
      fila.push({ titulo: 'Cupom Estabelecimento', conteudo: appendComplement(cupomEstabelecimento) })
    }
    if (cupomCliente) {
      fila.push({ titulo: 'Cupom Cliente', conteudo: appendComplement(cupomCliente) })
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
      return tipoCampos.map((item) => {
        const descricao = item?.Descricao ? `,"Descricao":"${escapeTipoCampo(item.Descricao)}"` : ''
        const dica = item?.Dica ? `,"Dica":"${escapeTipoCampo(item.Dica)}"` : ''
        return `{"TipoCampo":"${item.TipoCampo}"${descricao}${dica},"Valor":"${escapeTipoCampo(item.Valor)}"}`
      }).join(',\n')
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

  const aplicarRespostaInterativa = async (payload) => {
    if (payload?.session_id) {
      tefSessionRef.current = payload.session_id
      setTefSessionId(payload.session_id)
      if (payload?.finish_deferred) {
        setDeferredBatchSessionId(payload.session_id)
      }
    }

    const payloadCupomFiscal = String(payload?.cupom_fiscal || '').trim()
    const payloadDataFiscal = onlyDigits(payload?.data_fiscal)
    const payloadHoraFiscal = onlyDigits(payload?.hora_fiscal)
    if (payloadCupomFiscal) {
      setCupomFiscal(payloadCupomFiscal)
    }
    if (payloadDataFiscal.length === 8) {
      setDataFiscal(payloadDataFiscal)
    }
    if (payloadHoraFiscal.length === 6) {
      setHoraFiscal(payloadHoraFiscal)
    }
    if (payloadCupomFiscal && payloadDataFiscal.length === 8 && payloadHoraFiscal.length === 6) {
      lastStartedFiscalRef.current = {
        cupom_fiscal: payloadCupomFiscal,
        data_fiscal: payloadDataFiscal,
        hora_fiscal: payloadHoraFiscal,
      }
    }

    if (payload?.success === false) {
      if (tefIdleTimerRef.current) {
        clearTimeout(tefIdleTimerRef.current)
        tefIdleTimerRef.current = null
      }
      const errorMessage = payload?.error || 'Erro no fluxo TEF'
      if (isSessionLostError(errorMessage)) {
        await tratarSessaoPerdida('Sessao TEF perdida. Reinicie a sequencia.')
        return
      }
      setTefErro(errorMessage)
      return
    }

    if (payload?.finish_required || payload?.finish_deferred) {
      setTefPrompt(null)
      setTefResultado(payload)
      setTefInput('')
      iniciarTimeoutInatividade()
      return
    }

    setTefResultado(null)
    setTefPrompt(payload)
    const fieldId = Number(payload?.field_id)
    const tokenRegistroSolicitado = fieldId === 2988 && tlsToken.trim()
    const fallbackPromptValue = defaultValorPrompt(payload)
    const promptValue = tokenRegistroSolicitado
      ? tlsToken.trim()
      : resolvePromptDefaultInput(payload, fallbackPromptValue)
    setTefInput(promptValue)
    setTefInputMode(resolveInputMode(Number(payload?.command_id)))
    iniciarTimeoutInatividade()
  }

  const resolverPendenciasAutomaticamente = async () => {
    const res = await api.post('/pagamentos/tef/pendencias', {}, { timeout: TEF_REQUEST_TIMEOUT_MS })
    const message = String(res.data?.message || res.data?.detail?.message || 'Tratamento de pendencias executado.')
    setPendenciaStatus(message)
    tefSessionRef.current = null
    setTefSessionId(null)
    setTefPrompt(null)
    setTefInput('')
    setTefResultado({
      ...res.data,
      pendencia_automatica: true,
      aprovado: Boolean(res.data?.success),
      message,
    })
    setShowTefFlow(true)
  }

  const iniciarFluxoTef = async () => {
    try {
      resetTefFlow()
      setTefErro('')
      setTefProcessando(true)

      if (String(selectedSequence || '') === '18' && functionId === 130) {
        await resolverPendenciasAutomaticamente()
        return
      }

      if (JUSTIFICATIVA_REQUIRED_FUNCTIONS.has(functionId) && !justificativa.trim()) {
        setTefErro('Justificativa obrigatoria para esta funcao.')
        setTefProcessando(false)
        return
      }

      if (functionId === 110) {
        const lowerParams = String(trnAdditionalParameters || '').toLowerCase()
        if (lowerParams.includes('transacoeshabilitadas') || lowerParams.includes('transacoesdesabilitadas')) {
          setTefErro('Funcao 110 deve ser executada sem restricoes de menu (remova TransacoesHabilitadas/Desabilitadas).')
          setTefProcessando(false)
          return
        }
      }

      const trnInitLower = String(trnInitParameters || '').toLowerCase()
      const sessionParamsLower = String(sessionParameters || '').toLowerCase()
      const tlsObrigatorio = functionId === 669 || functionId === 699 || selectedSequence === '20'
      const tlsJaInformadoNoInit = trnInitLower.includes('tokenregistro') || trnInitLower.includes('tipocomunicacaoexterna=tlsgwp')
      const tlsJaInformadoNaSessao = sessionParamsLower.includes('tokenregistro') || sessionParamsLower.includes('tipocomunicacaoexterna=tlsgwp')
      if (tlsObrigatorio && !tlsToken.trim() && !tlsJaInformadoNoInit && !tlsJaInformadoNaSessao) {
        setTefErro('Token TLS obrigatorio para a sequencia TLS.')
        setTefProcessando(false)
        return
      }

      let normalizedCupomFiscal = String(cupomFiscal || '').trim()
      let normalizedDataFiscal = onlyDigits(dataFiscal)
      let normalizedHoraFiscal = onlyDigits(horaFiscal)
      const originalDocumentReferenceRequired = sequenceRequiresOriginalDocumentReference(selectedSequence)

      if (originalDocumentReferenceRequired && (
        !normalizedCupomFiscal ||
        normalizedDataFiscal.length !== 8 ||
        normalizedHoraFiscal.length !== 6
      )) {
        const fiscal = buildFiscalStamp()
        normalizedCupomFiscal = fiscal.cupom
        normalizedDataFiscal = fiscal.data
        normalizedHoraFiscal = fiscal.hora
        setCupomFiscal(fiscal.cupom)
        setDataFiscal(fiscal.data)
        setHoraFiscal(fiscal.hora)
      }

      if (originalDocumentReferenceRequired) {
        if (!normalizedCupomFiscal) {
          setTefErro('A abertura desta sequencia exige um Cupom Fiscal, Data Fiscal e Hora Fiscal novos. A referencia original sera usada quando o SiTef solicitar os campos 516, 515, 146 ou 601.')
          setTefProcessando(false)
          return
        }
        if (normalizedCupomFiscal.length > 20) {
          setTefErro('Cupom Fiscal deve ter no maximo 20 caracteres, conforme a documentacao da CliSiTef.')
          setTefProcessando(false)
          return
        }
        if (normalizedDataFiscal.length !== 8) {
          setTefErro('Data Fiscal obrigatoria no formato AAAAMMDD para esta sequencia.')
          setTefProcessando(false)
          return
        }
        if (normalizedHoraFiscal.length !== 6) {
          setTefErro('Hora Fiscal obrigatoria no formato HHMMSS para esta sequencia.')
          setTefProcessando(false)
          return
        }
      } else {
        if (normalizedCupomFiscal && normalizedCupomFiscal.length > 20) {
          setTefErro('Cupom Fiscal deve ter no maximo 20 caracteres, conforme a documentacao da CliSiTef.')
          setTefProcessando(false)
          return
        }
        if (normalizedDataFiscal && normalizedDataFiscal.length !== 8) {
          setTefErro('Data Fiscal deve estar no formato AAAAMMDD quando informada manualmente.')
          setTefProcessando(false)
          return
        }
        if (normalizedHoraFiscal && normalizedHoraFiscal.length !== 6) {
          setTefErro('Hora Fiscal deve estar no formato HHMMSS quando informada manualmente.')
          setTefProcessando(false)
          return
        }
      }

      let trnInitParametersValue = trnInitParameters || undefined
      const deveInjetarTokenTls = tlsObrigatorio || trnInitLower.includes('tipocomunicacaoexterna=tlsgwp')
      if (deveInjetarTokenTls && tlsToken.trim()) {
        const tlsParam = `[TipoComunicacaoExterna=TLSGWP;TokenRegistro=${tlsToken.trim()}]`
        if (trnInitParametersValue) {
          if (!trnInitParametersValue.includes('TokenRegistro')) {
            trnInitParametersValue = `${trnInitParametersValue};${tlsParam}`
          }
        } else {
          trnInitParametersValue = tlsParam
        }
      }

      const guidedStartConfig = GUIDED_TWO_STEP_CARD_SEQUENCE_CONFIG[String(selectedSequence || '')] || null
      const isGuidedFirstStepStart = Boolean(
        guidedStartConfig &&
        Number(functionId) === Number(guidedStartConfig.firstFunctionId) &&
        Math.abs(parseCurrencyInputValue(valor) - Number(guidedStartConfig.firstAmount || 0)) < 0.001
      )
      const isGuidedSecondStepStart = Boolean(
        guidedStartConfig &&
        Number(functionId) === Number(guidedStartConfig.secondFunctionId) &&
        Math.abs(parseCurrencyInputValue(valor) - Number(guidedStartConfig.secondAmount || 0)) < 0.001 &&
        String(cupomFiscal || normalizedCupomFiscal || '').trim()
      )
      const batchSessionIdToReuse = String(deferredBatchSessionId || '').trim()
      if (isGuidedSecondStepStart && !batchSessionIdToReuse) {
        setTefErro('A 2a etapa de multiplos pagamentos deve reutilizar a sessao aprovada na 1a etapa. Prepare a 2a etapa a partir do resultado da 1a.')
        setTefProcessando(false)
        return
      }

      const autogeneratedFiscalDocument = sequenceAutogeneratesFiscalDocument(selectedSequence)
      if (autogeneratedFiscalDocument && !isGuidedSecondStepStart) {
        const incompleteFiscalDocument = !normalizedCupomFiscal || normalizedDataFiscal.length !== 8 || normalizedHoraFiscal.length !== 6
        if (incompleteFiscalDocument || fiscalJaUsadoNaUltimaAbertura(normalizedCupomFiscal, normalizedDataFiscal, normalizedHoraFiscal)) {
          normalizedCupomFiscal = ''
          normalizedDataFiscal = ''
          normalizedHoraFiscal = ''
          setCupomFiscal('')
          setDataFiscal('')
          setHoraFiscal('')
        }
      }

      const payload = {
        function_id: functionId,
        valor: valor ? Number(valor) : undefined,
        cupom_fiscal: normalizedCupomFiscal || undefined,
        data_fiscal: normalizedDataFiscal || undefined,
        hora_fiscal: normalizedHoraFiscal || undefined,
        original_transaction_reference: originalDocumentReferenceRequired ? (lastFiscalReference || undefined) : undefined,
        enforce_fiscal_document: originalDocumentReferenceRequired || undefined,
        trn_additional_parameters: trnAdditionalParameters || undefined,
        trn_init_parameters: trnInitParametersValue,
        session_parameters: sessionParameters || undefined,
        sitef_ip: sitefIp || undefined,
        store_id: storeId || undefined,
        terminal_id: terminalId || undefined,
        cashier_operator: cashierOperator || undefined,
        justificativa: justificativa.trim() || undefined,
        defer_finish: isGuidedFirstStepStart || undefined,
        session_id: isGuidedSecondStepStart && batchSessionIdToReuse ? batchSessionIdToReuse : undefined
      }

      const res = await api.post('/pagamentos/tef/iniciar-funcao', payload, { timeout: TEF_REQUEST_TIMEOUT_MS })
      await aplicarRespostaInterativa(res.data)
      if (!isSessionLostError(res.data?.error)) {
        setShowTefFlow(true)
      }
    } catch (err) {
      console.error('Erro ao iniciar funcao TEF:', err)
      const detail = err.response?.data?.detail || 'Erro ao iniciar funcao TEF'
      if (isSessionLostError(detail)) {
        await tratarSessaoPerdida('Sessao TEF nao encontrada. Reinicie a sequencia.')
      } else {
        setTefErro(detail)
      }
    } finally {
      setTefProcessando(false)
    }
  }

  const continuarFluxoTef = async (continueFlag = 0, value = tefInput) => {
    try {
      const sessionIdAtual = tefSessionRef.current || tefSessionId || tefPrompt?.session_id
      if (!sessionIdAtual) {
        await tratarSessaoPerdida('Sessao TEF nao encontrada. Reinicie a sequencia.')
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

      await aplicarRespostaInterativa(res.data)
    } catch (err) {
      console.error('Erro ao continuar fluxo TEF:', err)
      const detail = err.response?.data?.detail || 'Erro ao continuar fluxo TEF'
      if (isSessionLostError(detail)) {
        await tratarSessaoPerdida('Sessao TEF nao encontrada. Reinicie a sequencia.')
      } else {
        setTefErro(detail)
      }
    } finally {
      setTefProcessando(false)
    }
  }

  const aplicarPrimeiraEtapaCartaoGuiada = () => {
    const config = GUIDED_TWO_STEP_CARD_SEQUENCE_CONFIG[String(selectedSequence || '')]
    if (!config) return
    setDeferredBatchSessionId('')
    setFunctionId(config.firstFunctionId)
    setValor(String(config.firstAmount))
    setTrnAdditionalParameters(config.firstTrnAdditionalParameters || '')
    setTrnInitParameters(config.firstTrnInitParameters || '')
    setNfpagRaw('')
    setNfpagItems([])
    setNfpagTipo('')
    setNfpagValor('')
    setNfpagExtraFields({})
    setNfpagError('')
    setTefErro('')
    toast.success(`Etapa 1 configurada: ${config.firstLabel} de R$ ${formatCurrencyDisplay(config.firstAmount)}.`)
  }

  const prepararSegundaEtapaCartaoGuiada = () => {
    const config = GUIDED_TWO_STEP_CARD_SEQUENCE_CONFIG[String(selectedSequence || '')]
    if (!config) return

    const batchSessionId = String(deferredBatchSessionId || tefResultado?.session_id || tefPrompt?.session_id || tefSessionRef.current || tefSessionId || '').trim()
    const cupom = String(cupomFiscal || tefPrompt?.cupom_fiscal || tefResultado?.cupom_fiscal || '').trim()
    let data = onlyDigits(dataFiscal || tefPrompt?.data_fiscal || tefResultado?.data_fiscal)
    let hora = onlyDigits(horaFiscal || tefPrompt?.hora_fiscal || tefResultado?.hora_fiscal)

    if (data.length !== 8 || hora.length !== 6) {
      const dataHora = onlyDigits(tefResultado?.data_hora_transacao || tefPrompt?.data_hora_transacao)
      if (dataHora.length >= 14) {
        data = dataHora.slice(0, 8)
        hora = dataHora.slice(8, 14)
      }
    }

    if (!cupom || data.length !== 8 || hora.length !== 6) {
      setTefErro('Nao foi possivel preparar a 2a etapa automaticamente. Informe Cupom/Data/Hora da 1a etapa e tente novamente.')
      return
    }

    setShowTefFlow(false)
    resetTefFlow()
    setDeferredBatchSessionId(batchSessionId)
    setFunctionId(config.secondFunctionId)
    setValor(String(config.secondAmount))
    setTrnAdditionalParameters(config.secondTrnAdditionalParameters || '')
    setTrnInitParameters(config.secondTrnInitParameters || '')
    setCupomFiscal(cupom)
    setDataFiscal(data)
    setHoraFiscal(hora)
    setNfpagRaw('')
    setNfpagItems([])
    setNfpagTipo('')
    setNfpagValor('')
    setNfpagExtraFields({})
    setNfpagError('')
    toast.success(`2a etapa preparada: ${config.secondLabel} de R$ ${formatCurrencyDisplay(config.secondAmount)} com o mesmo documento fiscal.`)
  }

  const concluirFluxoTef = async () => {
    try {
      if (tefResultado?.finish_deferred) {
        prepararSegundaEtapaCartaoGuiada()
        return
      }

      if (tefResultado?.pendencia_automatica || tefResultado?.finalizado) {
        await encerrarFluxoTef()
        return
      }

      const sessionIdAtual = tefSessionRef.current || tefSessionId || tefResultado?.session_id
      if (!sessionIdAtual) {
        await tratarSessaoPerdida('Sessao TEF nao encontrada. Reinicie a sequencia.')
        return
      }

      setTefErro('')
      setTefProcessando(true)

      const autoCashChange = buildAutoCashChangeNfpag({
        sequenceId: selectedSequence,
        functionIdValue: functionId,
        nfpagRawValue: nfpagRaw,
        firstTefAmount,
        totalSaleAmount: multiplePaymentTotal,
        cashReceivedAmount
      })

      if (autoCashChange.error) {
        setTefErro(autoCashChange.error)
        setNfpagError(autoCashChange.error)
        setTefProcessando(false)
        return
      }

      const nfpagRawToSend = autoCashChange.nfpagRawToSend || undefined
      if (!String(nfpagRaw || '').trim() && nfpagRawToSend) {
        setNfpagRaw(nfpagRawToSend)
      }
      setNfpagError('')

      const res = await api.post('/pagamentos/tef/finalizar', {
        session_id: sessionIdAtual,
        confirm: Boolean(tefResultado?.aprovado),
        numero_pagamento_nfpag: tefResultado?.nfpag?.numero_pagamento || undefined,
        nfpag_raw: nfpagRawToSend
      }, { timeout: TEF_REQUEST_TIMEOUT_MS })

      if (tefIdleTimerRef.current) {
        clearTimeout(tefIdleTimerRef.current)
        tefIdleTimerRef.current = null
      }
      setTefPrompt(null)
      setTefResultado({
        ...res.data,
        cash_change_registration: autoCashChange.registration || undefined,
        nfpag_raw_aplicado: nfpagRawToSend
      })
      tefSessionRef.current = null
      setTefSessionId(null)
      setDeferredBatchSessionId('')
    } catch (err) {
      console.error('Erro ao finalizar fluxo TEF:', err)
      const detail = err.response?.data?.detail || 'Erro ao finalizar fluxo TEF'
      if (isSessionLostError(detail)) {
        await tratarSessaoPerdida('Sessao TEF nao encontrada. Reinicie a sequencia.')
      } else {
        setTefErro(detail)
      }
    } finally {
      setTefProcessando(false)
    }
  }

  const justificativaObrigatoria = JUSTIFICATIVA_REQUIRED_FUNCTIONS.has(functionId)
  const selectedSequencePreset = getSequencePreset(selectedSequence)
  const multiplePaymentValueHint = MULTIPLE_PAYMENT_VALUE_HINTS[String(selectedSequence || '')] || ''
  const multiplePaymentTotal = MULTIPLE_PAYMENT_TOTALS[String(selectedSequence || '')] || 0
  const firstTefAmount = parseCurrencyInputValue(valor)
  const remainingCashDue = multiplePaymentTotal > 0 ? Math.max(multiplePaymentTotal - firstTefAmount, 0) : 0
  const cashReceivedAmount = parseCurrencyInputValue(cashReceivedValue)
  const cashChangeAmount = multiplePaymentTotal > 0 ? Math.max(cashReceivedAmount - remainingCashDue, 0) : 0
  const guidedTwoStepConfig = GUIDED_TWO_STEP_CARD_SEQUENCE_CONFIG[String(selectedSequence || '')] || null
  const isGuidedFirstStepPrepared = Boolean(
    guidedTwoStepConfig &&
    Number(functionId) === Number(guidedTwoStepConfig.firstFunctionId) &&
    Math.abs(parseCurrencyInputValue(valor) - Number(guidedTwoStepConfig.firstAmount || 0)) < 0.001
  )
  const isGuidedSecondStepPrepared = Boolean(
    guidedTwoStepConfig &&
    Number(functionId) === Number(guidedTwoStepConfig.secondFunctionId) &&
    Math.abs(parseCurrencyInputValue(valor) - Number(guidedTwoStepConfig.secondAmount || 0)) < 0.001 &&
    String(cupomFiscal || '').trim() &&
    onlyDigits(dataFiscal).length === 8 &&
    onlyDigits(horaFiscal).length === 6
  )
  const originalDocumentReferenceRequired = sequenceRequiresOriginalDocumentReference(selectedSequence)
  const preferNsuHostDocument = sequencePrefersNsuHostDocument(selectedSequence)
  const autogeneratedFiscalDocument = sequenceAutogeneratesFiscalDocument(selectedSequence)
  const fluxoFinalizado = Boolean(tefResultado?.finalizado)
  const seq3Conformance = buildSeq3Conformance(selectedSequence, tefResultado, tefErro)
  const seq3ConformancePrompt = buildSeq3Conformance(
    selectedSequence,
    tefPrompt
      ? {
          message: tefPrompt?.prompt || tefPrompt?.message || '',
          clisitef_status: tefPrompt?.clisitef_status,
          cupom_cliente: tefPrompt?.cupom_cliente,
          tef_cupom_cliente: tefPrompt?.tef_cupom_cliente,
          cupom_estabelecimento: tefPrompt?.cupom_estabelecimento,
          tef_cupom_estabelecimento: tefPrompt?.tef_cupom_estabelecimento,
        }
      : null,
    tefErro
  )

  const sequenceValidation = evaluateSequenceValidation(selectedSequence, tefResultado, tefPrompt, tefErro, pendenciaStatus)
  const sequenceEvidence = buildSequenceEvidenceChecklist(selectedSequence, tefResultado, tefPrompt, manualEvidence)
  const pendingEvidence = sequenceEvidence.filter((item) => item.required && !item.done).length
  const reprintLookupMessage = normalizeValidationText(tefResultado?.message || tefPrompt?.prompt || tefErro || '')
  const hasReprintLookupError = REPRINT_LOOKUP_ERROR_PATTERNS.some((pattern) => reprintLookupMessage.includes(pattern))

  if (showTefFlow) {
    const isAprovado = Boolean(tefResultado?.aprovado)
    const isAutomaticPendingResolution = Boolean(tefResultado?.pendencia_automatica)
    const cupomEstabelecimento = tefResultado?.cupom_estabelecimento || tefResultado?.tef_cupom_estabelecimento || ''
    const cupomCliente = tefResultado?.cupom_cliente || tefResultado?.tef_cupom_cliente || ''
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
    const menuNeedsManualSelection = ehMenu && menuOptions.length === 0
    const creditInstallmentMenuHint = ehMenu ? buildCreditInstallmentMenuHint(selectedSequence, tefPrompt, menuOptions) : null
    const retornoCliSiTef = Number(tefResultado?.clisitef_status ?? tefResultado?.detail?.clisitefStatus ?? (isAprovado ? 0 : -1))
    const isDeferredBatchFirstStep = Boolean(tefResultado?.finish_deferred)
    const canPrepareGuidedSecondStep = Boolean(
      guidedTwoStepConfig &&
      isAprovado &&
      Number(functionId) === Number(guidedTwoStepConfig.firstFunctionId) &&
      (fluxoFinalizado || isDeferredBatchFirstStep)
    )

    return (
      <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black bg-opacity-50 p-2 sm:items-center sm:p-4"
        onMouseMove={registrarAtividadeTef}
        onKeyDown={registrarAtividadeTef}
        onClick={registrarAtividadeTef}
        onTouchStart={registrarAtividadeTef}
      >
        <div className="my-2 flex max-h-[calc(100vh-1rem)] w-full max-w-5xl flex-col overflow-hidden rounded-lg shadow-xl sm:my-0 sm:max-h-[92vh]">
          <div className="bg-sky-700 px-4 py-4 text-white sm:px-6 sm:py-5">
            <h2 className="text-xl font-semibold sm:text-2xl lg:text-3xl">TEF Gerencial</h2>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto bg-zinc-200 p-3 sm:p-6">
            {tefResultado ? (
              <div className="space-y-4">
                {pendenciaStatus && (
                  <div className="bg-amber-50 border border-amber-200 text-amber-800 px-3 py-2 rounded text-sm">
                    {pendenciaStatus}
                  </div>
                )}
                {renderTefEventInfo(tefResultado)}
                {renderTefReimpressaoInfo(tefResultado?.reimpressao)}
                {renderReferenciaReimpressao(tefResultado?.referencia_reimpressao)}
                <h3 className="text-xl font-bold text-zinc-900 sm:text-2xl lg:text-3xl">{isAutomaticPendingResolution ? 'Tratamento de Pendencias' : `Transacao ${isAprovado ? 'Aprov.' : 'Nao Aprov.'}`}</h3>

                {isDeferredBatchFirstStep && (
                  <div className="rounded border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900">
                    <p className="font-semibold">Finalizacao adiada para o lote</p>
                    <p className="text-sm mt-1">Esta primeira etapa foi aprovada, mas nao sera finalizada agora. Prepare a 2a etapa e envie a Finaliza somente na ultima transacao do lote.</p>
                  </div>
                )}

                {isAutomaticPendingResolution && tefResultado?.finish_tax_invoice_number && (
                  <div className="rounded border border-emerald-300 bg-emerald-50 px-4 py-3 text-emerald-900">
                    <p className="font-semibold">Finaliza 130 enviada com dados da pendencia</p>
                    <p className="text-sm mt-1">
                      CupomFiscal <span className="font-mono">{tefResultado.finish_tax_invoice_number}</span>, DataFiscal <span className="font-mono">{tefResultado.finish_tax_invoice_date || '-'}</span>, Horario <span className="font-mono">{tefResultado.finish_tax_invoice_time || '-'}</span>.
                    </p>
                  </div>
                )}

                {!isDeferredBatchFirstStep && !fluxoFinalizado && tefResultado?.finish_required && (
                  <div className="rounded border border-emerald-300 bg-emerald-50 px-4 py-3 text-emerald-900">
                    <p className="font-semibold">Finaliza pendente</p>
                    <p className="text-sm mt-1">Apos conferir ou imprimir os comprovantes, clique em Enviar Finaliza. Em transacao aprovada com Retorno = 0, essa chamada confirma a operacao no SiTef.</p>
                  </div>
                )}

                {canPrepareGuidedSecondStep && (
                  <div className="rounded border border-indigo-300 bg-indigo-50 px-4 py-3 text-indigo-900">
                    <p className="font-semibold">1a etapa concluida. Preparar 2a etapa automatica?</p>
                    <p className="text-sm mt-1">Vamos manter o mesmo Cupom Fiscal/Data/Hora e configurar a funcao {guidedTwoStepConfig.secondFunctionId} ({guidedTwoStepConfig.secondLabel}) com valor de R$ {formatCurrencyDisplay(guidedTwoStepConfig.secondAmount)}.</p>
                    <button
                      type="button"
                      onClick={prepararSegundaEtapaCartaoGuiada}
                      disabled={tefProcessando}
                      className="mt-3 px-3 py-2 rounded bg-indigo-600 text-white text-sm font-semibold disabled:opacity-60"
                    >
                      Preparar 2a etapa ({guidedTwoStepConfig.secondLabel} R$ {formatCurrencyDisplay(guidedTwoStepConfig.secondAmount)})
                    </button>
                  </div>
                )}

                {selectedSequencePreset && sequenceValidation && (
                  <div className={`rounded border px-4 py-3 ${sequenceValidation.status === 'pass' ? 'border-green-300 bg-green-50 text-green-800' : sequenceValidation.status === 'fail' ? 'border-red-300 bg-red-50 text-red-800' : 'border-amber-300 bg-amber-50 text-amber-900'}`}>
                    <p className="font-semibold">Validacao automatica da {selectedSequencePreset.label}: {sequenceValidation.title}</p>
                    <p className="text-sm mt-1">{sequenceValidation.detail}</p>
                    {sequenceEvidence.length > 0 && (
                      <div className="mt-3 text-sm space-y-2">
                        <p className="font-semibold">Checklist de evidencias {pendingEvidence > 0 ? `(pendentes: ${pendingEvidence})` : '(completo)'}</p>
                        {sequenceEvidence.map((item) => (
                          <div key={item.id} className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                            <span>{item.done ? 'OK' : 'PEND'} {item.label}{item.required ? '' : ' (opcional)'}</span>
                            {item.manual && (
                              <button
                                type="button"
                                onClick={() => marcarEvidenciaManual(item.id)}
                                className={`px-2 py-1 rounded text-xs font-semibold ${item.done ? 'bg-green-600 text-white' : 'bg-zinc-300 text-zinc-800'}`}
                              >
                                {item.done ? 'Marcado' : 'Marcar'}
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {originalDocumentReferenceRequired && hasReprintLookupError && (
                  <div className="rounded border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900">
                    <p className="font-semibold">SiTef nao localizou a transacao para reimpressao</p>
                    <p className="text-sm mt-1">Confira se os campos 516 (documento), 515 (data) e 146 (valor) sao exatamente os mesmos do comprovante original.</p>
                    {preferNsuHostDocument && lastFiscalReference?.nsu_host && (
                      <p className="text-xs mt-2">Na Seq. 12, o documento deve ser o NSU Host <span className="font-mono">{lastFiscalReference.nsu_host}</span>.</p>
                    )}
                    {lastFiscalReference && (
                      <p className="text-xs mt-2">
                        Use a referencia original somente nos campos solicitados pelo SiTef. Documento <span className="font-mono">{lastFiscalReference.cupom_fiscal || '-'}</span>
                        {lastFiscalReference.nsu_host ? <> , NSU Host <span className="font-mono">{lastFiscalReference.nsu_host}</span></> : null}
                        {lastFiscalReference.nsu_sitef ? <> , NSU SiTef <span className="font-mono">{lastFiscalReference.nsu_sitef}</span></> : null}.
                      </p>
                    )}
                  </div>
                )}

                <div className="rounded border bg-white p-4">
                  <p className="text-sm text-zinc-700">Fim - Retorno CliSiTef: {retornoCliSiTef} ({getClisitefStatusDescription(retornoCliSiTef)})</p>
                  <p className="font-mono text-sm mt-1">{tefResultado?.message || tefErro || '-'}</p>
                  <p className="font-mono text-sm mt-1">NSU Host: {tefResultado?.nsu_host || tefResultado?.nsu || '-'}</p>
                  <p className="font-mono text-sm mt-1">NSU SiTef: {tefResultado?.nsu_sitef || '-'}</p>
                  <p className="font-mono text-sm mt-1">Autorizacao: {tefResultado?.autorizacao || '-'}</p>
                </div>

                {seq3Conformance && (
                  <div className={`rounded border px-4 py-3 ${seq3Conformance.ok ? 'border-green-300 bg-green-50 text-green-800' : 'border-red-300 bg-red-50 text-red-800'}`}>
                    <p className="font-semibold">{seq3Conformance.title}</p>
                    <p className="text-sm mt-1">{seq3Conformance.detail}</p>
                  </div>
                )}

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
                        <p>Formas habilitadas: {nfpagTypeOptions.map((item) => `${item.codigo} - ${item.descricao}`).join(' | ')}</p>
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
                      O backend envia automaticamente <span className="font-mono">NumeroPagamentoNFPAG</span> quando a CliSiTef retornar o campo 161. Use este bloco para fechar as sequencias 21, 22, 23, 28, 29 e 30 no proprio TEF Gerencial.
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="rounded border bg-white p-4">
                    <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <p className="font-semibold">Cupom Estabelecimento (122)</p>
                      <div className="flex flex-wrap gap-2">
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
                    <pre className="text-xs max-h-44 overflow-auto bg-zinc-50 p-2 rounded">{cupomEstabelecimento || 'Nao retornado'}</pre>
                  </div>

                  <div className="rounded border bg-white p-4">
                    <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <p className="font-semibold">Cupom Cliente (121)</p>
                      <div className="flex flex-wrap gap-2">
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
                    <pre className="text-xs max-h-44 overflow-auto bg-zinc-50 p-2 rounded">{cupomCliente || 'Nao retornado'}</pre>
                  </div>
                </div>

                {tefErro && (
                  <div className="mb-3 text-red-700 bg-red-100 border border-red-300 px-3 py-2 rounded">
                    {tefErro}
                  </div>
                )}

                {seq3ConformancePrompt && (
                  <div className={`mb-3 rounded border px-3 py-2 ${seq3ConformancePrompt.ok ? 'border-green-300 bg-green-50 text-green-800' : 'border-red-300 bg-red-50 text-red-800'}`}>
                    <p className="font-semibold">{seq3ConformancePrompt.title}</p>
                    <p className="text-sm mt-1">{seq3ConformancePrompt.detail}</p>
                  </div>
                )}

                <div className="flex flex-col gap-2 pt-2 sm:flex-row sm:flex-wrap">
                  <button
                    type="button"
                    onClick={isDeferredBatchFirstStep ? prepararSegundaEtapaCartaoGuiada : isAutomaticPendingResolution || fluxoFinalizado ? () => encerrarFluxoTef() : concluirFluxoTef}
                    disabled={tefProcessando}
                    className={tefFlowPrimaryButtonClass}
                  >
                    {tefProcessando ? '...' : isDeferredBatchFirstStep ? 'Preparar 2a etapa' : isAutomaticPendingResolution || fluxoFinalizado ? 'OK' : 'Enviar Finaliza'}
                  </button>
                  <button
                    type="button"
                    onClick={() => encerrarFluxoTef()}
                    disabled={tefProcessando}
                    className={tefFlowSecondaryButtonClass}
                  >
                    ENCERRAR
                  </button>
                  <button
                    type="button"
                    onClick={() => encerrarFluxoTef()}
                    disabled={tefProcessando}
                    className={tefFlowMutedButtonClass}
                  >
                    MENU INICIAL
                  </button>
                </div>
              </div>
            ) : (
              <div className="mx-auto w-full max-w-3xl">
                {menuTitle && (
                  <div className="mb-2 text-lg font-semibold text-zinc-900 sm:text-xl">{menuTitle}</div>
                )}
                {pendenciaStatus && (
                  <div className="bg-amber-50 border border-amber-200 text-amber-800 px-3 py-2 rounded text-sm mb-2">
                    {pendenciaStatus}
                  </div>
                )}
                {headerText && (
                  <pre className="mb-2 whitespace-pre-wrap break-words text-sm text-zinc-800 sm:text-base">{headerText}</pre>
                )}
                {renderMensagens(mensagens)}
                {renderTefEventInfo(tefPrompt)}
                {renderTefReimpressaoInfo(tefPrompt?.reimpressao)}
                {renderFieldGuidanceInfo(tefPrompt)}
                {selectedSequencePreset && sequenceValidation && (
                  <div className={`mb-3 rounded border px-3 py-2 ${sequenceValidation.status === 'pass' ? 'border-green-300 bg-green-50 text-green-800' : sequenceValidation.status === 'fail' ? 'border-red-300 bg-red-50 text-red-800' : 'border-amber-300 bg-amber-50 text-amber-900'}`}>
                    <p className="font-semibold">Validacao automatica da {selectedSequencePreset.label}: {sequenceValidation.title}</p>
                    <p className="text-sm mt-1">{sequenceValidation.detail}</p>
                    {sequenceEvidence.length > 0 && (
                      <div className="mt-2 text-xs space-y-1">
                        {sequenceEvidence.map((item) => (
                          <div key={item.id} className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                            <span>{item.done ? 'OK' : 'PEND'} {item.label}</span>
                            {item.manual && (
                              <button
                                type="button"
                                onClick={() => marcarEvidenciaManual(item.id)}
                                className={`px-2 py-1 rounded text-[11px] font-semibold ${item.done ? 'bg-green-600 text-white' : 'bg-zinc-300 text-zinc-800'}`}
                              >
                                {item.done ? 'Marcado' : 'Marcar'}
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {originalDocumentReferenceRequired && hasReprintLookupError && (
                  <div className="rounded border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900">
                    <p className="font-semibold">SiTef nao localizou a transacao para reimpressao</p>
                    <p className="text-sm mt-1">Confira se os campos 516 (documento), 515 (data) e 146 (valor) sao exatamente os mesmos do comprovante original.</p>
                    {preferNsuHostDocument && lastFiscalReference?.nsu_host && (
                      <p className="text-xs mt-2">Na Seq. 12, o documento deve ser o NSU Host <span className="font-mono">{lastFiscalReference.nsu_host}</span>.</p>
                    )}
                    {lastFiscalReference && (
                      <p className="text-xs mt-2">
                        Use a referencia original somente nos campos solicitados pelo SiTef. Documento <span className="font-mono">{lastFiscalReference.cupom_fiscal || '-'}</span>
                        {lastFiscalReference.nsu_host ? <> , NSU Host <span className="font-mono">{lastFiscalReference.nsu_host}</span></> : null}
                        {lastFiscalReference.nsu_sitef ? <> , NSU SiTef <span className="font-mono">{lastFiscalReference.nsu_sitef}</span></> : null}.
                      </p>
                    )}
                  </div>
                )}

                {ehRecibo ? (
                  <div className="rounded border bg-white p-4 mb-4">
                    <p className="font-semibold mb-2">
                      Cupom {tefPrompt?.receipt_kind === 'cliente' ? 'Cliente' : 'Estabelecimento'}
                    </p>
                    <pre className="text-xs whitespace-pre-wrap bg-zinc-50 p-2 rounded max-h-60 overflow-auto">
                      {prompt || 'Nao retornado'}
                    </pre>
                    <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                      <button
                        type="button"
                        onClick={() => imprimirTexto(tefPrompt?.receipt_kind === 'cliente' ? 'Cupom Cliente' : 'Cupom Estabelecimento', prompt)}
                        className="px-3 py-1 text-xs rounded bg-sky-600 text-white"
                      >
                        Imprimir
                      </button>
                    </div>
                  </div>
                ) : ehMenu && menuOptions.length > 0 ? (
                  <div className="mb-4 space-y-3">
                    {creditInstallmentMenuHint && (
                      <div className={`rounded border px-3 py-2 text-sm ${creditInstallmentMenuHint.tone === 'success' ? 'border-emerald-300 bg-emerald-50 text-emerald-900' : 'border-sky-300 bg-sky-50 text-sky-900'}`}>
                        <p className="font-semibold">{creditInstallmentMenuHint.title}</p>
                        <p className="mt-1 text-xs">{creditInstallmentMenuHint.detail}</p>
                      </div>
                    )}
                    <pre className="text-sm text-zinc-900 whitespace-pre-wrap bg-white border border-zinc-300 rounded p-3">{prompt || ''}</pre>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {menuOptions.map((opt) => (
                        <button
                          key={`${opt.index}-${opt.text}`}
                          type="button"
                          onClick={() => continuarFluxoTef(0, String(opt.index))}
                          disabled={tefProcessando}
                          className="rounded border border-zinc-300 bg-white px-4 py-3 text-left hover:bg-zinc-50 disabled:opacity-60"
                        >
                          <div className="text-base font-semibold text-zinc-900 sm:text-lg">{opt.index}. {opt.text}</div>
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
                  <>
                    {(prompt || (!menuTitle && !headerText && mensagens.length === 0)) && (
                      <pre className="mb-4 whitespace-pre-wrap break-words text-lg text-zinc-900 sm:text-xl lg:text-2xl">{prompt || '-'}</pre>
                    )}
                    {menuNeedsManualSelection && (
                      <p className="mb-2 text-xs text-amber-700">
                        Digite manualmente o numero da opcao do menu e pressione Selecionar.
                      </p>
                    )}
                  </>
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

                {!ehPerguntaSimNao && !ehAguardarTecla && !ehInterromper && !ehRecibo && !ehProcessandoAutomatico && (!ehMenu || menuNeedsManualSelection) && (
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
                    className="mb-4 w-full rounded border border-zinc-400 bg-zinc-100 px-3 py-2.5 text-lg sm:max-w-md sm:text-xl"
                  />
                )}

                {tefErro && (
                  <div className="mb-3 text-red-700 bg-red-100 border border-red-300 px-3 py-2 rounded">
                    {tefErro}
                  </div>
                )}

                <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
                  {ehPerguntaSimNao ? (
                    <>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(0, '0')}
                        disabled={tefProcessando}
                        className={tefFlowPrimaryButtonClass}
                      >
                        Sim
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(0, '1')}
                        disabled={tefProcessando}
                        className={tefFlowSecondaryButtonClass}
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
                        className={tefFlowPrimaryButtonClass}
                      >
                        Continuar
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(-1, '')}
                        disabled={tefProcessando}
                        className={tefFlowMidButtonClass}
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className={tefFlowMutedButtonClass}
                      >
                        MENU INICIAL
                      </button>
                    </>
                  ) : ehProcessandoAutomatico ? (
                    <>
                      <button
                        type="button"
                        disabled
                        className={tefFlowPrimaryButtonClass}
                      >
                        {tefProcessando ? '...' : 'AGUARDANDO'}
                      </button>
                      <button
                        type="button"
                        onClick={() => encerrarFluxoTef()}
                        disabled={tefProcessando}
                        className={tefFlowSecondaryButtonClass}
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className={tefFlowMutedButtonClass}
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
                        className={tefFlowPrimaryButtonClass}
                      >
                        {tefProcessando ? '...' : 'OK'}
                      </button>
                      <button
                        type="button"
                        onClick={() => encerrarFluxoTef()}
                        disabled={tefProcessando}
                        className={tefFlowSecondaryButtonClass}
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className={tefFlowMutedButtonClass}
                      >
                        MENU INICIAL
                      </button>
                    </>
                  ) : ehMenu && !menuNeedsManualSelection ? (
                    <>
                      <button
                        type="button"
                        onClick={() => encerrarFluxoTef()}
                        disabled={tefProcessando}
                        className={tefFlowSecondaryButtonClass}
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className={tefFlowMutedButtonClass}
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
                        className={tefFlowPrimaryButtonClass}
                      >
                        {tefProcessando ? '...' : menuNeedsManualSelection ? 'Selecionar' : 'OK'}
                      </button>
                      {exigeModoCodigoBarras && (
                        <button
                          type="button"
                          onClick={() => continuarFluxoTef(0, '2:')}
                          disabled={tefProcessando}
                          className={tefFlowWarningButtonClass}
                        >
                          Cancelar leitura
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => encerrarFluxoTef()}
                        disabled={tefProcessando}
                        className={tefFlowSecondaryButtonClass}
                      >
                        ENCERRAR
                      </button>
                      <button
                        type="button"
                        onClick={() => continuarFluxoTef(1, '1')}
                        disabled={tefProcessando}
                        className={tefFlowMutedButtonClass}
                      >
                        MENU INICIAL
                      </button>
                    </>
                  )}
                </div>
                {ehPerguntaSimNao && (
                  <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                    <button
                      type="button"
                      onClick={() => encerrarFluxoTef()}
                      disabled={tefProcessando}
                      className={tefFlowDarkButtonClass}
                    >
                      ENCERRAR
                    </button>
                    <button
                      type="button"
                      onClick={() => continuarFluxoTef(1, '1')}
                      disabled={tefProcessando}
                      className={tefFlowMutedButtonClass}
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
          <div className="fixed inset-0 z-[60] flex items-start justify-center overflow-y-auto bg-black bg-opacity-40 p-2 sm:items-center sm:p-4">
            <div className="flex max-h-[calc(100vh-1rem)] w-full max-w-xl flex-col overflow-hidden rounded-2xl border bg-zinc-100 shadow-2xl">
              <div className="px-4 py-4 text-xl font-semibold sm:px-6 sm:text-2xl lg:text-3xl">Essa pagina diz</div>
              <div className="flex-1 overflow-auto px-4 py-2 sm:px-6">
                <pre className="whitespace-pre-wrap break-words text-sm leading-6 sm:text-base">{cupomDialog.titulo}:
{cupomDialog.conteudo}</pre>
              </div>
              <div className="flex justify-end px-4 py-4 sm:px-6">
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
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black bg-opacity-50 p-2 sm:items-center sm:p-4">
      <div className="flex max-h-[calc(100vh-1rem)] w-full max-w-4xl flex-col overflow-hidden rounded-lg bg-white shadow-xl sm:max-h-[90vh]">
        <div className="rounded-t-lg bg-gradient-to-r from-sky-700 to-sky-900 p-4 text-white sm:p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="mb-2 text-xl font-bold sm:text-2xl">TEF Gerencial</h2>
              <p className="text-sky-100">
                Funcoes administrativas e testes de homologacao
              </p>
            </div>
            <button
              onClick={() => {
                if (showTefFlow) {
                  encerrarFluxoTef()
                  return
                }
                onClose()
              }}
              className="text-white hover:text-gray-200 text-2xl"
            >
              x
            </button>
          </div>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-6">
          <div className="rounded-lg border border-sky-200 bg-sky-50 p-4 space-y-3">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Sequencia do roteiro</label>
              <select
                value={selectedSequence}
                onChange={(e) => aplicarPresetSequencia(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
              >
                <option value="">Manual</option>
                {SEQUENCE_PRESETS.map((preset) => (
                  <option key={preset.id} value={preset.id}>{preset.label}</option>
                ))}
              </select>
            </div>

            {selectedSequencePreset && (
              <div className="rounded border border-sky-200 bg-white p-3 text-sm space-y-2">
                <p className="font-semibold text-sky-900">{selectedSequencePreset.label}</p>
                <p><span className="font-semibold">Preparacao / execucao:</span> {selectedSequencePreset.guidance}</p>
                <p><span className="font-semibold">Resultado esperado:</span> {selectedSequencePreset.expected}</p>
                <p className="text-xs text-gray-500">Funcao sugerida: {selectedSequencePreset.functionId}</p>
                {guidedTwoStepConfig && (
                  <div className="rounded border border-indigo-200 bg-indigo-50 p-3 text-xs text-indigo-900 space-y-2">
                    <p className="font-semibold">Roteiro guiado desta sequencia</p>
                    <p>1. Realizar uma transacao de {guidedTwoStepConfig.firstLabel} no valor de R$ {formatCurrencyDisplay(guidedTwoStepConfig.firstAmount)}.</p>
                    <p>2. Selecionar a opcao "{guidedTwoStepConfig.firstInstallmentLabel}" quando o SiTef solicitar.</p>
                    <p>3. Efetuar o segundo pagamento de R$ {formatCurrencyDisplay(guidedTwoStepConfig.secondAmount)} {guidedTwoStepConfig.secondExecutionText || `com ${String(guidedTwoStepConfig.secondLabel || '').toLowerCase()}`}.</p>
                    <p>4. {guidedTwoStepConfig.secondRequirementText || 'Manter o mesmo Cupom/Data/Hora entre as duas etapas.'}</p>
                    <div className="flex flex-wrap gap-2 pt-1">
                      <button
                        type="button"
                        onClick={aplicarPrimeiraEtapaCartaoGuiada}
                        className={`rounded px-2 py-1 font-semibold text-white ${isGuidedFirstStepPrepared ? 'bg-emerald-600' : 'bg-indigo-600'}`}
                      >
                        {isGuidedFirstStepPrepared ? 'Etapa 1 pronta' : `Aplicar etapa 1 (${guidedTwoStepConfig.firstLabel} R$ ${formatCurrencyDisplay(guidedTwoStepConfig.firstAmount)})`}
                      </button>
                      <button
                        type="button"
                        onClick={prepararSegundaEtapaCartaoGuiada}
                        className={`rounded px-2 py-1 font-semibold text-white ${isGuidedSecondStepPrepared ? 'bg-emerald-600' : 'bg-indigo-700'}`}
                      >
                        {isGuidedSecondStepPrepared ? 'Etapa 2 pronta' : `Preparar etapa 2 (${guidedTwoStepConfig.secondLabel} R$ ${formatCurrencyDisplay(guidedTwoStepConfig.secondAmount)})`}
                      </button>
                    </div>
                    <p className={`font-semibold ${isGuidedSecondStepPrepared ? 'text-emerald-700' : 'text-indigo-700'}`}>
                      {isGuidedSecondStepPrepared
                        ? `2a etapa pronta: funcao ${guidedTwoStepConfig.secondFunctionId} no valor de R$ ${formatCurrencyDisplay(guidedTwoStepConfig.secondAmount)} com o mesmo documento fiscal.`
                        : `Apos aprovar a 1a etapa, clique em "Preparar etapa 2" para montar automaticamente ${String(guidedTwoStepConfig.secondLabel || '').toLowerCase()} com o mesmo documento fiscal.`}
                    </p>
                  </div>
                )}
              </div>
            )}

            {originalDocumentReferenceRequired && (
              <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm space-y-2 text-amber-900">
                <p className="font-semibold">{preferNsuHostDocument ? 'Referencia original obrigatoria na Seq. 12' : 'Referencia original obrigatoria nesta sequencia'}</p>
                <p>
                  {preferNsuHostDocument
                    ? 'A abertura usa um Cupom/Data/Hora novo. Quando o SiTef pedir a transacao original, informe os dados da Seq. 5 e use o NSU Host no Campo 516.'
                    : 'A abertura usa um Cupom/Data/Hora novo. Quando o SiTef pedir a transacao original, informe os dados fiscais/NSU da venda original.'}
                </p>
                <p className="text-xs">Nao copie a referencia original para o CupomFiscal da abertura; isso evita replicacao entre transacoes.</p>
                {preferNsuHostDocument && (
                  <p className="text-xs text-amber-800">Na Seq. 12, o documento da reimpressao deve ser o NSU Host da venda original. Na trilha REDE, a data original deve seguir MMDD, por exemplo 08/04 = 0408.</p>
                )}
                {lastFiscalReference && (
                  <div className="rounded border border-amber-300 bg-white px-3 py-2 text-xs">
                    <p>
                      Ultima referencia capturada: {preferNsuHostDocument ? 'NSU Host' : 'documento fiscal'} <span className="font-mono">{preferNsuHostDocument ? (lastFiscalReference.nsu_host || '-') : lastFiscalReference.cupom_fiscal}</span>
                      {lastFiscalReference.nsu_host ? (
                        <> , NSU Host <span className="font-mono">{lastFiscalReference.nsu_host}</span></>
                      ) : null}
                      {lastFiscalReference.nsu_sitef ? (
                        <> , NSU SiTef <span className="font-mono">{lastFiscalReference.nsu_sitef}</span></>
                      ) : null},
                      data <span className="font-mono">{lastFiscalReference.data_fiscal}</span>,
                      hora <span className="font-mono">{lastFiscalReference.hora_fiscal}</span>
                    </p>
                    <p className="mt-2 text-[11px] text-amber-800">
                      A abertura do TEF continua com o Cupom/Data/Hora atuais; use esta referencia somente nas perguntas do SiTef.
                    </p>
                  </div>
                )}
              </div>
            )}

            {!originalDocumentReferenceRequired && autogeneratedFiscalDocument && (
              <div className="rounded border border-emerald-200 bg-emerald-50 p-3 text-sm space-y-2 text-emerald-900">
                <p className="font-semibold">Documento fiscal gerado pela automacao</p>
                <p>Conforme a documentacao da CliSiTef, a automacao pode gerar o Cupom Fiscal antes de iniciar a venda e reutilizar esse mesmo documento depois.</p>
                <p className="text-xs">Se estes campos ficarem vazios, a automacao gerara os dados fiscais automaticamente para abrir o TEF.</p>
              </div>
            )}

            <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm space-y-2">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="font-semibold text-amber-900">Diagnostico Operacional (Seq. 2/3)</p>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={runOperationalDiagnostics}
                    disabled={diagRunning || tefProcessando}
                    className="px-3 py-1 rounded bg-amber-600 text-white text-xs font-semibold disabled:opacity-60"
                  >
                    {diagRunning ? 'Executando...' : 'Rodar Diagnostico'}
                  </button>
                  <button
                    type="button"
                    onClick={imprimirDiagnostico}
                    disabled={!diagReport}
                    className="px-3 py-1 rounded bg-zinc-700 text-white text-xs font-semibold disabled:opacity-60"
                  >
                    Imprimir
                  </button>
                </div>
              </div>
              <p className="text-xs text-amber-800">Checks: COMUNICACAO_BASE_00000000, REGISTRO_699 e SEQ3_1111AAAA.</p>
              {diagReport && (
                <div className="space-y-2">
                  <p className="text-xs text-amber-900">Gerado em: {diagReport.generated_at}</p>
                  {diagReport.checks.map((check) => (
                    <div key={check.code} className={`rounded border px-3 py-2 ${check.status === 'PASS' ? 'border-green-300 bg-green-50 text-green-800' : check.status === 'WARN' ? 'border-amber-300 bg-amber-100 text-amber-900' : 'border-red-300 bg-red-50 text-red-800'}`}>
                      <p className="font-semibold">{check.code}: {check.status}</p>
                      <p className="text-xs mt-1">{check.summary}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Funcao</label>
            <select
              value={functionId}
              onChange={(e) => setFunctionId(Number(e.target.value))}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              {FUNCTION_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>{opt.label}</option>
              ))}
            </select>
          </div>

          {justificativaObrigatoria && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Justificativa</label>
              <textarea
                value={justificativa}
                onChange={(e) => {
                  setJustificativa(e.target.value)
                  if (tefErro) setTefErro('')
                }}
                placeholder="Informe o motivo da reimpressao/cancelamento"
                className="w-full border border-gray-300 rounded px-3 py-2 min-h-[80px]"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Valor (R$)</label>
            <input
              type="number"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
              placeholder="Opcional"
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
            {multiplePaymentValueHint && (
              <p className="text-xs text-amber-800 mt-1">{multiplePaymentValueHint}</p>
            )}
          </div>

          {multiplePaymentTotal > 0 && (
            <div className="rounded border border-amber-200 bg-amber-50 p-3 space-y-2 text-sm text-amber-900">
              <p className="font-semibold">Dinheiro e troco</p>
              <p>Valor total da venda: <span className="font-mono">R$ {formatCurrencyDisplay(multiplePaymentTotal)}</span></p>
              <p>Restante a quitar em dinheiro: <span className="font-mono">R$ {formatCurrencyDisplay(remainingCashDue)}</span></p>
              <div>
                <label className="block text-sm font-semibold text-amber-900 mb-1">Dinheiro recebido do cliente (R$)</label>
                <input
                  type="text"
                  value={cashReceivedValue}
                  onChange={(e) => setCashReceivedValue(e.target.value)}
                  placeholder="Ex: 50,00"
                  className="w-full border border-amber-300 rounded px-3 py-2 bg-white"
                />
              </div>
              <p>Troco em dinheiro: <span className="font-mono">R$ {formatCurrencyDisplay(cashChangeAmount)}</span></p>
              <p className="text-xs">Ao finalizar, a automacao envia o NFPAG para lancar TEF + dinheiro no cupom e inclui o resumo de troco no comprovante exibido.</p>
              {tefResultado?.nfpag_raw_aplicado && (
                <p className="text-xs">NFPAG aplicado no fechamento: <span className="font-mono">{tefResultado.nfpag_raw_aplicado}</span></p>
              )}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Cupom Fiscal{originalDocumentReferenceRequired ? ' *' : ''}</label>
              <input
                type="text"
                value={cupomFiscal}
                onChange={(e) => setCupomFiscal(e.target.value)}
                placeholder={originalDocumentReferenceRequired ? 'Novo documento da abertura' : autogeneratedFiscalDocument ? 'Gerado automaticamente se vazio' : 'Opcional'}
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Data Fiscal (AAAAMMDD){originalDocumentReferenceRequired ? ' *' : ''}</label>
              <input
                type="text"
                value={dataFiscal}
                onChange={(e) => setDataFiscal(e.target.value)}
                placeholder={originalDocumentReferenceRequired ? 'Novo documento da abertura' : autogeneratedFiscalDocument ? 'Gerado automaticamente se vazio' : 'Opcional'}
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Hora Fiscal (HHMMSS){originalDocumentReferenceRequired ? ' *' : ''}</label>
              <input
                type="text"
                value={horaFiscal}
                onChange={(e) => setHoraFiscal(e.target.value)}
                placeholder={originalDocumentReferenceRequired ? 'Novo documento da abertura' : autogeneratedFiscalDocument ? 'Gerado automaticamente se vazio' : 'Opcional'}
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>
          </div>
          <p className="text-xs text-gray-500">
            Conforme a documentacao da CliSiTef, o Cupom Fiscal deve ter no maximo 20 caracteres e ser unico por abertura de transacao.
          </p>
          {originalDocumentReferenceRequired && (
            <p className="text-xs text-amber-700">
              Esta sequencia abre com um Cupom/Data/Hora novo. A referencia original fica reservada para os campos 516/515/146/601 solicitados pelo SiTef.
            </p>
          )}
          {!originalDocumentReferenceRequired && autogeneratedFiscalDocument && (
            <p className="text-xs text-emerald-700">
              Se os campos estiverem vazios, a automacao gerara automaticamente o documento fiscal antes de iniciar o TEF.
            </p>
          )}

          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-sky-700 underline"
            >
              {showAdvanced ? 'Ocultar' : 'Mostrar'} parametros avancados
            </button>
          </div>

          {showAdvanced && (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Token TLS Fiserv (opcional)</label>
                <input
                  type="text"
                  value={tlsToken}
                  onChange={(e) => setTlsToken(e.target.value)}
                  placeholder="Ex: 1111-2222-3333-4444"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Se informado, sera enviado no trnInitParameters como TipoComunicacaoExterna=TLSGWP;TokenRegistro=...
                </p>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Parametros adicionais da transacao</label>
                <input
                  type="text"
                  value={trnAdditionalParameters}
                  onChange={(e) => setTrnAdditionalParameters(e.target.value)}
                  placeholder="Ex: TransacoesHabilitadas=26"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => setTrnAdditionalParameters('TransacoesHabilitadas=26')}
                    className="px-2 py-1 rounded bg-sky-100 text-sky-900 border border-sky-200"
                  >
                    Credito a vista (26)
                  </button>
                  <button
                    type="button"
                    onClick={() => setTrnAdditionalParameters('TransacoesHabilitadas=27')}
                    className="px-2 py-1 rounded bg-sky-100 text-sky-900 border border-sky-200"
                  >
                    Parcelado loja (27)
                  </button>
                  <button
                    type="button"
                    onClick={() => setTrnAdditionalParameters('TransacoesHabilitadas=28')}
                    className="px-2 py-1 rounded bg-sky-100 text-sky-900 border border-sky-200"
                  >
                    Parcelado adm (28)
                  </button>
                  <button
                    type="button"
                    onClick={() => setTrnAdditionalParameters('')}
                    className="px-2 py-1 rounded bg-gray-100 text-gray-700 border border-gray-200"
                  >
                    Limpar
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Parametros de inicializacao</label>
                <input
                  type="text"
                  value={trnInitParameters}
                  onChange={(e) => setTrnInitParameters(e.target.value)}
                  placeholder="Opcional"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Parametros de sessao (TLS/ParmsClient)</label>
                <input
                  type="text"
                  value={sessionParameters}
                  onChange={(e) => setSessionParameters(e.target.value)}
                  placeholder="Opcional"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Use para sessao/ParmsClient. Para TLS TokenRegistro, prefira o campo Token TLS ou Parametros de inicializacao.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">SiTef IP</label>
                  <input
                    type="text"
                    value={sitefIp}
                    onChange={(e) => setSitefIp(e.target.value)}
                    placeholder="Opcional"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Store ID</label>
                  <input
                    type="text"
                    value={storeId}
                    onChange={(e) => setStoreId(e.target.value)}
                    placeholder="Opcional"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Terminal ID</label>
                  <input
                    type="text"
                    value={terminalId}
                    onChange={(e) => setTerminalId(e.target.value)}
                    placeholder="Opcional"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Operador</label>
                  <input
                    type="text"
                    value={cashierOperator}
                    onChange={(e) => setCashierOperator(e.target.value)}
                    placeholder="Opcional"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>
              </div>
            </div>
          )}

          {tefErro && (
            <div className="mb-3 text-red-700 bg-red-100 border border-red-300 px-3 py-2 rounded">
              {tefErro}
            </div>
          )}
        </div>

        <div className="flex flex-col-reverse gap-3 border-t bg-gray-50 p-4 sm:flex-row sm:justify-between sm:p-6">
          <button
            onClick={onClose}
            className="w-full rounded-lg bg-gray-300 px-6 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-400 sm:w-auto"
            disabled={tefProcessando}
          >
            Fechar
          </button>
          <button
            onClick={iniciarFluxoTef}
            className="w-full rounded-lg bg-sky-700 px-6 py-3 font-medium text-white transition-colors hover:bg-sky-800 disabled:opacity-60 sm:w-auto"
            disabled={tefProcessando}
          >
            {tefProcessando ? 'Iniciando...' : 'Iniciar Funcao'}
          </button>
        </div>
      </div>
    </div>
  )
}



