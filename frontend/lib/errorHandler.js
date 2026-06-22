export function formatErrorMessage(error) {
  if (!error) return 'Erro inesperado'

  const status = error?.response?.status
  const data = error?.response?.data

  if (typeof data === 'string' && data.trim()) return data
  if (data?.detail) return String(data.detail)
  if (data?.message) return String(data.message)
  if (error?.message) return String(error.message)

  if (status === 401) return 'Nao autorizado'
  if (status === 403) return 'Acesso negado'
  if (status === 404) return 'Recurso nao encontrado'
  if (status === 409) return 'Conflito de operacao'
  if (status >= 500) return 'Erro interno do servidor'

  return 'Falha ao processar solicitacao'
}
