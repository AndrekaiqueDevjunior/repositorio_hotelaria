export const HttpStatus = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500,
}

export const StatusReserva = {
  PENDENTE: 'PENDENTE',
  PENDENTE_PAGAMENTO: 'PENDENTE_PAGAMENTO',
  AGUARDANDO_COMPROVANTE: 'AGUARDANDO_COMPROVANTE',
  EM_ANALISE: 'EM_ANALISE',
  CONFIRMADA: 'CONFIRMADA',
  CHECKIN_LIBERADO: 'CHECKIN_LIBERADO',
  HOSPEDADO: 'HOSPEDADO',
  CHECKED_OUT: 'CHECKED_OUT',
  CHECKOUT_REALIZADO: 'CHECKOUT_REALIZADO',
  CANCELADO: 'CANCELADO',
  CANCELADA: 'CANCELADA',
}

export const StatusPagamento = {
  PENDENTE: 'PENDENTE',
  PROCESSANDO: 'PROCESSANDO',
  AGUARDANDO_PAGAMENTO: 'AGUARDANDO_PAGAMENTO',
  APROVADO: 'APROVADO',
  PAGO: 'PAGO',
  RECUSADO: 'RECUSADO',
  FALHOU: 'FALHOU',
  ESTORNADO: 'ESTORNADO',
}

export const MetodoPagamento = {
  PIX: 'pix',
  CREDIT_CARD: 'credit_card',
  DEBIT_CARD: 'debit_card',
  TEF: 'tef',
  NA_CHEGADA: 'na_chegada',
  BALCAO: 'balcao',
  DINHEIRO: 'DINHEIRO',
  DEBITO: 'DEBITO',
  CREDITO: 'CREDITO',
  TRANSFERENCIA: 'TRANSFERENCIA',
}

export const METODO_PAGAMENTO_LABELS = {
  pix: 'PIX',
  credit_card: 'Cartao de Credito',
  debit_card: 'Cartao de Debito',
  tef: 'TEF (Maquininha)',
  na_chegada: 'Pagar na Chegada',
  balcao: 'Pagamento no Balcao',
  DINHEIRO: 'Dinheiro',
  DEBITO: 'Cartao de Debito',
  CREDITO: 'Cartao de Credito',
  TRANSFERENCIA: 'Transferencia',
}

export const STATUS_PAGAMENTO_COLORS = {
  PENDENTE: 'bg-yellow-100 text-yellow-800',
  PROCESSANDO: 'bg-blue-100 text-blue-800',
  AGUARDANDO_PAGAMENTO: 'bg-amber-100 text-amber-800',
  APROVADO: 'bg-green-100 text-green-800',
  PAGO: 'bg-green-100 text-green-800',
  RECUSADO: 'bg-red-100 text-red-800',
  FALHOU: 'bg-red-100 text-red-800',
  ESTORNADO: 'bg-gray-100 text-gray-800',
}

export const StatusValidacao = {
  AGUARDANDO_COMPROVANTE: 'AGUARDANDO_COMPROVANTE',
  EM_ANALISE: 'EM_ANALISE',
  APROVADO: 'APROVADO',
  RECUSADO: 'RECUSADO',
}

export const TipoComprovante = {
  PIX: 'PIX',
  DINHEIRO: 'DINHEIRO',
  DEBITO: 'DEBITO',
  CREDITO: 'CREDITO',
  TRANSFERENCIA: 'TRANSFERENCIA',
  OUTRO: 'OUTRO',
}

export const TIPO_COMPROVANTE_LABELS = {
  PIX: 'PIX',
  DINHEIRO: 'Dinheiro',
  DEBITO: 'Cartao de Debito',
  CREDITO: 'Cartao de Credito',
  TRANSFERENCIA: 'Transferencia',
  OUTRO: 'Outro',
}

export function isPagamentoAprovado(status) {
  return ['APROVADO', 'PAGO', 'CONFIRMADO'].includes((status || '').toUpperCase())
}

export function isPagamentoNegado(status) {
  return ['RECUSADO', 'FALHOU', 'NEGADO'].includes((status || '').toUpperCase())
}
