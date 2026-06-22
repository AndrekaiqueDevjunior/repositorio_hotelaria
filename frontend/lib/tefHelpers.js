export const TEF_EVENT_LABELS = {
  5000: 'Aguardando leitura de cartao',
  5001: 'Aguardando digitacao da senha pelo usuario',
  5002: 'Aguardando confirmacao positiva pelo usuario',
  5003: 'Aguardando leitura do bilhete unico',
  5004: 'Aguardando remocao do bilhete unico',
  5005: 'Transacao finalizada',
  5006: 'Confirma dados do favorecido',
  5007: 'SiTef conectado',
  5008: 'SiTef conectando',
  5009: 'Consulta OK',
  5010: 'Colher assinatura',
  5011: 'Coleta de novo produto',
  5012: 'Confirma operacao',
  5013: 'Confirma cancelamento',
  5014: 'Confirma valor total',
  5015: 'Conclusao de recarga de bilhete unico',
  5016: 'Reservado',
  5017: 'Aguardando leitura de cartao',
  5018: 'Aguardando digitacao da senha no PinPad',
  5019: 'Aguardando processamento do chip',
  5020: 'Aguardando remocao do cartao',
  5021: 'Aguardando confirmacao da operacao',
  5027: 'Leitura do cartao cancelada',
  5028: 'Digitacao da senha cancelada',
  5029: 'Processamento do cartao com chip cancelado',
  5030: 'Remocao do cartao cancelada',
  5031: 'Confirmacao da operacao cancelada',
  5036: 'Antes da leitura do cartao magnetico',
  5037: 'Antes da leitura do cartao com chip',
  5038: 'Antes da remocao do cartao com chip',
  5039: 'Antes da coleta da senha no pinpad',
  5040: 'Antes de abrir a comunicacao com o PinPad',
  5041: 'Antes de fechar a comunicacao com o PinPad',
  5042: 'Bloquear recursos do PinPad',
  5043: 'Liberar recursos do PinPad',
  5044: 'Depois de abrir a comunicacao com o PinPad',
  5049: 'Timeout com o SiTef',
  5050: 'Atualizacao de tabelas para transacoes offline',
  5051: 'Senha coletada no pinpad',
  5052: 'Cartao com chip processado',
  5053: 'Cartao com chip removido',
  5054: 'Entrega de dados sensiveis',
  5055: 'Atualizando tabelas no pinpad',
  5056: 'Enviando arquivos para o SiTef',
  5057: 'Inicio do envio de dados sensiveis',
  5058: 'Fim do envio de dados sensiveis',
  5059: 'Aguardando leitura de cartao (modalidade 29)',
  5060: 'Reservado',
  5061: 'Reservado',
  5062: 'Inicio do envio de campos de produtos',
  5063: 'Fim do envio de campos de produtos',
  5064: 'Inicio do envio de campos de recarga TEF',
  5065: 'Fim do envio de campos de recarga TEF',
  5066: 'Antes do envio de campos de conecta SiTef',
  5067: 'Depois do envio de campos de conecta SiTef',
  5068: 'Antes do envio de campos de desconecta SiTef',
  5069: 'Depois do envio de campos de desconecta SiTef',
  5070: 'Antes do envio de campos de envia SiTef',
  5071: 'Depois do envio de campos de envia SiTef',
  5072: 'Antes do envio de campos de recebe SiTef',
  5073: 'Depois do envio de campos de recebe SiTef',
  5074: 'Assinatura em papel obrigatoria',
  5084: 'Mensagem vinda do SiTef ou do autorizador'
}

export const CLISITEF_STATUS_LABELS = {
  0: 'Sucesso',
  10000: 'Fluxo interativo em andamento',
  '-1': 'Modulo nao inicializado',
  '-2': 'Operacao cancelada pelo operador',
  '-3': 'Funcao/modalidade invalida',
  '-4': 'Falta de memoria no PDV',
  '-5': 'Sem comunicacao com o SiTef',
  '-6': 'Operacao cancelada no PinPad',
  '-8': 'CliSiTef desatualizada',
  '-9': 'Fluxo interativo nao iniciado',
  '-10': 'Parametro obrigatorio ausente',
  '-12': 'Erro no fluxo iterativo',
  '-13': 'Documento fiscal nao encontrado',
  '-15': 'Operacao cancelada pela automacao',
  '-20': 'Parametro invalido',
  '-21': 'Palavra proibida em coleta aberta',
  '-25': 'Erro no correspondente bancario (sangria)',
  '-30': 'Erro de acesso a arquivo',
  '-40': 'Transacao negada pelo SiTef',
  '-41': 'Dados invalidos',
  '-43': 'Falha em rotina de PinPad',
  '-50': 'Transacao nao segura',
  '-100': 'Erro interno do modulo'
}

export const NFPAG_TYPE_LABELS = {
  '00': 'Dinheiro',
  '01': 'Cheque',
  '02': 'TEF Debito',
  '03': 'TEF Credito',
  '04': 'Cartao Presente Carrefour',
  '05': 'Cartao Bonus Carrefour',
  '06': 'Cartao Carrefour',
  '07': 'Saque para pagamento',
  '08': 'Saque',
  '09': 'DCC Carrefour',
  '10': 'Ticket Eletronico',
  '11': 'Ticket Papel',
  '12': 'Carteira Digital',
  '13': 'Pix',
  '50': 'TEF Cartao',
  '77': 'Reservado',
  '98': 'Sem Pagamento',
  '99': 'Outras Formas'
}

export const NFPAG_COLLECTION_LABELS = {
  '00': 'Campo reservado',
  '01': 'Tipo de entrada do cheque',
  '02': 'Dados do cheque',
  '03': 'Rede destino',
  '04': 'NSU do SiTef',
  '05': 'Data do SiTef (nao utilizado)',
  '06': 'Codigo da empresa',
  '07': 'NSU do Host',
  '08': 'Data do Host',
  '09': 'Codigo de origem',
  '10': 'Servico Z',
  '11': 'Codigo de autorizacao',
  '12': 'Valor do cheque',
  '13': 'Redes permitidas para Rede Destino',
  '14': 'Bandeira do cartao',
  '15': 'Tipo de pagamento',
  '16': 'Id da carteira digital'
}

export const NFPAG_FIELD_OPTIONS = {
  '01': [
    { value: '0', label: 'CMC-7 lido' },
    { value: '1', label: 'Primeira linha digitada' },
    { value: '2', label: 'CMC-7 digitado' }
  ],
  '15': [
    { value: '00', label: 'A vista' },
    { value: '01', label: 'Pre-datado' },
    { value: '02', label: 'Parcelado pelo estabelecimento' },
    { value: '03', label: 'Parcelado pela administradora' }
  ]
}

export const getNfpagFieldPlaceholder = (code) => {
  switch (String(code || '').padStart(2, '0')) {
    case '02':
      return 'CMC-7 ou primeira linha do cheque'
    case '03':
      return 'Ex: 5 ou 0005'
    case '04':
      return 'NSU do SiTef (campo 133)'
    case '06':
      return 'Codigo da empresa/loja do TEF'
    case '07':
      return 'NSU do Host (campo 134)'
    case '08':
      return 'DDMMAAAA'
    case '09':
      return 'Codigo de origem (campo 157)'
    case '10':
      return 'Servico Z / dados de confirmacao'
    case '11':
      return 'Codigo de autorizacao (campo 135)'
    case '12':
      return 'Valor total do cheque em centavos'
    case '13':
      return 'Ex: 5,82,174'
    case '14':
      return 'Codigo da bandeira (campo 132)'
    case '16':
      return 'Id da carteira digital'
    default:
      return 'Informe o valor'
  }
}

export const normalizeTefFlag = (value) => {
  const raw = String(value ?? '').trim().toUpperCase()
  return raw !== '' && raw !== '0' && raw !== 'N' && raw !== 'NAO' && raw !== 'FALSE'
}

export const getTefEventDescription = (code) => {
  const numericCode = Number(code)
  return TEF_EVENT_LABELS[numericCode] || `Evento ${numericCode}`
}

export const getClisitefStatusDescription = (status) => {
  const normalized = Number(status)
  if (Number.isNaN(normalized)) return 'Status desconhecido'
  return CLISITEF_STATUS_LABELS[normalized] || CLISITEF_STATUS_LABELS[String(normalized)] || `Status ${normalized}`
}

export const isClisitefCommunicationError = (status, text = '') => {
  const normalized = Number(status)
  if (normalized === -5 || normalized === 5049) return true
  const normalizedText = String(text || '').toLowerCase()
  return /sem conexao|erro de comunicacao|timeout|remote end closed/.test(normalizedText)
}

export const getTefEventTone = (code) => {
  const numericCode = Number(code)
  if ([5005, 5007, 5009, 5051, 5052, 5053].includes(numericCode)) return 'green'
  if ([5027, 5028, 5029, 5030, 5031, 5049].includes(numericCode)) return 'red'
  if ([5000, 5001, 5002, 5003, 5004, 5017, 5018, 5019, 5020, 5021, 5055, 5056].includes(numericCode)) return 'amber'
  return 'sky'
}

export const parseNfpagValor = (valor) => {
  const normalized = String(valor || '').replace(/\./g, '').replace(',', '.')
  const parsed = Number(normalized)
  if (!Number.isFinite(parsed)) return ''
  return String(Math.round(parsed * 100))
}

export const buildNfpagString = (items) => {
  if (!Array.isArray(items) || items.length === 0) return ''
  return items
    .map((item) => {
      const tipo = String(item.tipo || '').padStart(2, '0')
      const valor = String(item.valor || '')
      const extras = String(item.extras || '').trim()
      return extras ? `${tipo}:${valor}:${extras}` : `${tipo}:${valor}`
    })
    .join(';') + ';'
}

export const buildNfpagExtras = (fields) => {
  if (!fields || typeof fields !== 'object') return ''
  return Object.entries(fields)
    .map(([rawCode, rawValue]) => {
      const code = String(rawCode || '').padStart(2, '0')
      const value = String(rawValue || '').trim()
      if (!value || code === '00' || code === '05') return ''
      if (code === '13') {
        const redes = value
          .split(/[;,\s]+/)
          .map((item) => item.trim())
          .filter(Boolean)
          .join(',')
        return redes ? `${code}(${redes})` : ''
      }
      return `${code}:${value}`
    })
    .filter(Boolean)
    .join('-')
}

export const getNfpagTypeOptions = (nfpag) => {
  const detailed = Array.isArray(nfpag?.tipos_habilitados_detalhes) ? nfpag.tipos_habilitados_detalhes : []
  if (detailed.length > 0) {
    return detailed.map((item) => ({
      codigo: String(item?.codigo || '').padStart(2, '0'),
      descricao: item?.descricao || NFPAG_TYPE_LABELS[String(item?.codigo || '').padStart(2, '0')] || 'Forma nao mapeada',
      coletas_detalhes: Array.isArray(item?.coletas_detalhes) ? item.coletas_detalhes : []
    }))
  }

  const flat = Array.isArray(nfpag?.tipos_habilitados) ? nfpag.tipos_habilitados : []
  return [...new Set(flat.map((value) => String(value || '').padStart(2, '0')).filter(Boolean))].map((codigo) => ({
    codigo,
    descricao: NFPAG_TYPE_LABELS[codigo] || 'Forma nao mapeada',
    coletas_detalhes: []
  }))
}

export const getNfpagTypeDetail = (nfpag, code) => {
  const rawCode = String(code || '').trim()
  if (!rawCode) return null
  const normalizedCode = rawCode.padStart(2, '0')
  return getNfpagTypeOptions(nfpag).find((item) => item.codigo === normalizedCode) || null
}
