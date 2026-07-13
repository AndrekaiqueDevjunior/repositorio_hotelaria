/**
 * Throttle: Executa função no máximo 1x a cada X ms
 * Útil para: scroll, resize, API calls
 */
export function throttle(fn, delay) {
  let lastCall = 0
  let timeoutId = null

  return function throttled(...args) {
    const now = Date.now()
    const timeSinceLastCall = now - lastCall

    if (timeSinceLastCall >= delay) {
      // Executar imediatamente
      lastCall = now
      fn.apply(this, args)
    } else {
      // Agendar para depois
      if (timeoutId) clearTimeout(timeoutId)
      timeoutId = setTimeout(() => {
        lastCall = Date.now()
        fn.apply(this, args)
      }, delay - timeSinceLastCall)
    }
  }
}

/**
 * Debounce: Aguarda X ms sem chamadas antes de executar
 * Útil para: search, validação de form
 */
export function debounce(fn, delay) {
  let timeoutId = null

  return function debounced(...args) {
    if (timeoutId) clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

/**
 * Cache simples com TTL (Time To Live)
 * Previne requisições duplicadas dentro de X ms
 */
export class RequestCache {
  constructor(ttlMs = 60000) {
    this.cache = new Map()
    this.ttl = ttlMs
  }

  /**
   * Obter valor do cache se ainda válido
   */
  get(key) {
    const entry = this.cache.get(key)
    if (!entry) return null

    const now = Date.now()
    if (now - entry.timestamp > this.ttl) {
      // Cache expirou
      this.cache.delete(key)
      return null
    }

    return entry.value
  }

  /**
   * Armazenar valor no cache
   */
  set(key, value) {
    this.cache.set(key, {
      value,
      timestamp: Date.now()
    })
  }

  /**
   * Limpar cache inteiro
   */
  clear() {
    this.cache.clear()
  }

  /**
   * Remover uma chave específica
   */
  delete(key) {
    this.cache.delete(key)
  }

  /**
   * Executar função com cache automático
   * Se resultado estiver em cache e válido, retorna do cache
   * Senão, executa função e armazena resultado
   */
  async getOrFetch(key, fetchFn) {
    const cached = this.get(key)
    if (cached !== null) {
      return cached
    }

    const result = await fetchFn()
    this.set(key, result)
    return result
  }
}

/**
 * Criar cache global para requisições
 * TTL padrão: 1 minuto
 */
export const apiCache = new RequestCache(60000)

/**
 * Limpar cache quando dados forem atualizados
 * Útil em mutations/POST/PUT/DELETE
 */
export function invalidateCachePattern(pattern) {
  for (const key of apiCache.cache.keys()) {
    if (key.includes(pattern)) {
      apiCache.delete(key)
    }
  }
}
