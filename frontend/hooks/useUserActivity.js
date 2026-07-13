import { useEffect, useRef, useState, useCallback } from 'react'

/**
 * Hook que detecta se o usuário está ativo/navegando
 * Retorna false se:
 * - Tab não está visível (document hidden)
 * - Usuário não fez atividade por X segundos
 * - Página está em background
 */
export function useUserActivity(inactivityTimeout = 300000) {
  const [isActive, setIsActive] = useState(true)
  const inactivityTimerRef = useRef(null)

  const resetInactivityTimer = useCallback(() => {
    // Limpar timer anterior
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current)
    }

    // Ativar imediatamente
    setIsActive(true)

    // Iniciar novo timer
    inactivityTimerRef.current = setTimeout(() => {
      setIsActive(false)
    }, inactivityTimeout)
  }, [inactivityTimeout])

  useEffect(() => {
    // Eventos de atividade do usuário
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click']

    const handleActivity = () => {
      resetInactivityTimer()
    }

    // Adicionar listeners
    events.forEach(event => {
      document.addEventListener(event, handleActivity, true)
    })

    // Verificar visibilidade da página
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setIsActive(false)
        if (inactivityTimerRef.current) {
          clearTimeout(inactivityTimerRef.current)
        }
      } else {
        resetInactivityTimer()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    // Inicializar timer
    resetInactivityTimer()

    // Cleanup
    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity, true)
      })
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      if (inactivityTimerRef.current) {
        clearTimeout(inactivityTimerRef.current)
      }
    }
  }, [resetInactivityTimer])

  return isActive
}
