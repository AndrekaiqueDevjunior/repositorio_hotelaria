import axios from 'axios'
import { toast } from 'react-toastify'

const baseURL = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

function extrairMensagemErro(error) {
  if (axios.isCancel(error)) return null
  if (!error?.response) return 'Erro de conexao com o servidor. Verifique sua internet.'

  const { detail } = error.response.data || {}
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail) && detail.length > 0) {
    // Erros de validacao do FastAPI (422): lista de {loc, msg, ...}
    return detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
  }
  if (error.response.status === 404) return 'Recurso nao encontrado.'
  if (error.response.status >= 500) return 'Erro interno do servidor. Tente novamente.'
  return 'Ocorreu um erro ao processar a solicitacao.'
}

export const api = axios.create({
  baseURL,
  withCredentials: true,
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token')
    if (token && !config.headers?.Authorization) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      }
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== 'undefined' && error?.response?.status === 401) {
      localStorage.removeItem('token')
    }

    // Feedback padrao: toda chamada que falhar mostra um toast com o motivo real,
    // a menos que o chamador passe { silentError: true } na config da requisicao
    // (ex: polling em background que ja trata o erro de outra forma).
    if (typeof window !== 'undefined' && !error?.config?.silentError) {
      const mensagem = extrairMensagemErro(error)
      if (mensagem) {
        toast.error(mensagem, { toastId: error?.config?.url ? `erro-${error.config.method}-${error.config.url}` : undefined })
      }
    }

    return Promise.reject(error)
  }
)

export function invalidateCache() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event('hotel:invalidate-cache'))
  }
}
