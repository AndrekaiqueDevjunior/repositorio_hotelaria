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

const ROTAS_PUBLICAS_JORNADA_REAL = [
  '/consultar-pontos',
  '/entrar-jornada-real',
  '/meu-cupom',
  '/nivel_jornada_real',
  '/resgate_dos_premios',
  '/termos-jornada-real',
]

function isPaginaPublicaJornadaReal() {
  if (typeof window === 'undefined') return false
  return ROTAS_PUBLICAS_JORNADA_REAL.some((rota) => window.location.pathname.startsWith(rota))
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

// Renovacao de sessao (single-flight): o access token do staff dura 60min e
// o refresh cookie 7 dias, mas nada renovava — sessao caia no meio de fluxos
// longos (ex.: venda TEF com cliente no pinpad, que ficava PENDENTE).
let refreshEmAndamento = null

export async function renovarSessao() {
  if (typeof window === 'undefined') return false
  if (!refreshEmAndamento) {
    refreshEmAndamento = axios
      .post(`${baseURL}/auth/refresh`, null, { withCredentials: true, timeout: 15000 })
      .then(() => true)
      .catch(() => false)
      .finally(() => {
        setTimeout(() => {
          refreshEmAndamento = null
        }, 0)
      })
  }
  return refreshEmAndamento
}

const ROTAS_SEM_RETRY_401 = ['/auth/login', '/auth/refresh', '/auth/logout', '/auth/otp']

function podeTentarRefresh(config) {
  if (!config || config._retried401) return false
  const url = String(config.url || '')
  return !ROTAS_SEM_RETRY_401.some((rota) => url.includes(rota))
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // 401 em sessao de staff: tenta renovar via refresh cookie e repete a
    // requisicao UMA vez antes de desistir (evita perder venda TEF etc.).
    if (
      typeof window !== 'undefined' &&
      error?.response?.status === 401 &&
      !isPaginaPublicaJornadaReal() &&
      podeTentarRefresh(error?.config)
    ) {
      const renovado = await renovarSessao()
      if (renovado) {
        // O backend prioriza o header Authorization sobre o cookie renovado;
        // descarta qualquer Bearer velho (header e localStorage legado) para
        // a repeticao autenticar pelo cookie fresco.
        localStorage.removeItem('token')
        const config = { ...error.config, _retried401: true }
        if (config.headers?.Authorization) {
          delete config.headers.Authorization
        }
        return api.request(config)
      }
    }

    if (typeof window !== 'undefined' && error?.response?.status === 401) {
      localStorage.removeItem('token')
    }

    // Paginas publicas do Jornada Real nao tem sessao de funcionario logada;
    // um 401 ali e normal (sem token de staff) e nao "sessao expirada" pro hospede.
    const ignorarToken401 = error?.response?.status === 401 && isPaginaPublicaJornadaReal()

    // Feedback padrao: toda chamada que falhar mostra um toast com o motivo real,
    // a menos que o chamador passe { silentError: true } na config da requisicao
    // (ex: polling em background que ja trata o erro de outra forma).
    if (typeof window !== 'undefined' && !error?.config?.silentError && !ignorarToken401) {
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
