export const TEF_PENDENCIAS_CHECK_EVENT = 'hotel:tef-pendencias:checked'
const TEF_PENDENCIAS_WINDOW_KEY = '__HOTEL_TEF_PENDENCIAS_CHECKED_AT__'

export function getTefPendenciasCheckedAt() {
  if (typeof window === 'undefined') return ''
  return window[TEF_PENDENCIAS_WINDOW_KEY] || ''
}

export function hasTefPendenciasStartupCheck() {
  return Boolean(getTefPendenciasCheckedAt())
}

export function markTefPendenciasChecked(detail = {}) {
  if (typeof window === 'undefined') return ''

  const checkedAt = new Date().toISOString()
  window[TEF_PENDENCIAS_WINDOW_KEY] = checkedAt

  window.dispatchEvent(new CustomEvent(TEF_PENDENCIAS_CHECK_EVENT, {
    detail: {
      checked_at: checkedAt,
      ...detail
    }
  }))

  return checkedAt
}

export function clearTefPendenciasCheck() {
  if (typeof window === 'undefined') return
  window[TEF_PENDENCIAS_WINDOW_KEY] = ''
  window.dispatchEvent(new CustomEvent(TEF_PENDENCIAS_CHECK_EVENT, {
    detail: {
      checked_at: '',
      cleared: true
    }
  }))
}
