/**
 * Hook para Suporte a Screen Readers
 * Fornece anúncios e navegação otimizados para leitores de tela
 */

import { useEffect, useRef, useState } from 'react'

export const useScreenReader = () => {
  const [isScreenReaderActive, setIsScreenReaderActive] = useState(false)
  const announcementRef = useRef(null)

  // Detectar se screen reader está ativo
  useEffect(() => {
    const checkScreenReader = () => {
      // Verificar se há leitores de tela comuns
      const hasScreenReader = 
        window.speechSynthesis?.getVoices().length > 0 ||
        navigator.userAgent.includes('NVDA') ||
        navigator.userAgent.includes('JAWS') ||
        navigator.userAgent.includes('VoiceOver') ||
        window.speechSynthesis?.speaking

      setIsScreenReaderActive(hasScreenReader)
    }

    checkScreenReader()
    
    // Verificar periodicamente
    const interval = setInterval(checkScreenReader, 5000)
    
    return () => clearInterval(interval)
  }, [])

  // Anunciar mensagem para screen reader
  const announce = useCallback((message, priority = 'polite') => {
    if (!message) return

    // Criar elemento de anúncio
    const announcement = document.createElement('div')
    announcement.setAttribute('aria-live', priority)
    announcement.setAttribute('aria-atomic', 'true')
    announcement.className = 'sr-only'
    announcement.textContent = message
    
    document.body.appendChild(announcement)
    
    // Remover após anúncio
    setTimeout(() => {
      if (document.body.contains(announcement)) {
        document.body.removeChild(announcement)
      }
    }, 1000)

    // Usar síntese de voz se disponível
    if (window.speechSynthesis && isScreenReaderActive) {
      const utterance = new SpeechSynthesisUtterance(message)
      utterance.lang = 'pt-BR'
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.volume = 0.8
      
      window.speechSynthesis.speak(utterance)
    }
  }, [isScreenReaderActive])

  // Anunciar mudanças de estado
  const announceStateChange = useCallback((element, newState) => {
    const message = `${element} agora está ${newState}`
    announce(message, 'assertive')
  }, [announce])

  // Anunciar navegação
  const announceNavigation = useCallback((section, itemCount = null) => {
    let message = `Navegando para ${section}`
    if (itemCount) {
      message += ` com ${itemCount} ${itemCount === 1 ? 'item' : 'itens'}`
    }
    announce(message, 'polite')
  }, [announce])

  // Anunciar erro
  const announceError = useCallback((error, context = '') => {
    const message = context ? `Erro em ${context}: ${error}` : `Erro: ${error}`
    announce(message, 'assertive')
  }, [announce])

  // Anunciar sucesso
  const announceSuccess = useCallback((message, context = '') => {
    const fullMessage = context ? `${context}: ${message}` : message
    announce(fullMessage, 'polite')
  }, [announce])

  // Anunciar progresso
  const announceProgress = useCallback((current, total, operation = 'Carregando') => {
    const percentage = Math.round((current / total) * 100)
    const message = `${operation}: ${current} de ${total} (${percentage}%)`
    announce(message, 'polite')
  }, [announce])

  // Anunciar quando loading termina
  const announceLoadingComplete = useCallback((itemCount = null) => {
    const message = itemCount 
      ? `Carregamento concluído. ${itemCount} ${itemCount === 1 ? 'item' : 'itens'} encontrados.`
      : 'Carregamento concluído.'
    announce(message, 'polite')
  }, [announce])

  return {
    isScreenReaderActive,
    announce,
    announceStateChange,
    announceNavigation,
    announceError,
    announceSuccess,
    announceProgress,
    announceLoadingComplete
  }
}

/**
 * Hook para gerenciar landmarks de navegação
 */
export const useLandmarks = () => {
  const [landmarks, setLandmarks] = useState({})

  // Registrar landmark
  const registerLandmark = useCallback((role, label, element) => {
    setLandmarks(prev => ({
      ...prev,
      [role]: { label, element }
    }))
  }, [])

  // Navegar para landmark
  const navigateToLandmark = useCallback((role) => {
    const landmark = landmarks[role]
    if (landmark?.element) {
      landmark.element.focus()
      landmark.element.scrollIntoView({ behavior: 'smooth' })
    }
  }, [landmarks])

  // Obter lista de landmarks disponíveis
  const getAvailableLandmarks = useCallback(() => {
    return Object.entries(landmarks).map(([role, { label }]) => ({
      role,
      label
    }))
  }, [landmarks])

  return {
    registerLandmark,
    navigateToLandmark,
    getAvailableLandmarks
  }
}

/**
 * Hook para gerenciar descrições longas
 */
export const useLongDescriptions = () => {
  const [descriptions, setDescriptions] = useState({})

  // Adicionar descrição longa
  const addDescription = useCallback((id, content) => {
    setDescriptions(prev => ({
      ...prev,
      [id]: content
    }))
  }, [])

  // Obter descrição longa
  const getDescription = useCallback((id) => {
    return descriptions[id] || ''
  }, [descriptions])

  // Remover descrição
  const removeDescription = useCallback((id) => {
    setDescriptions(prev => {
      const newDescriptions = { ...prev }
      delete newDescriptions[id]
      return newDescriptions
    })
  }, [])

  return {
    addDescription,
    getDescription,
    removeDescription
  }
}

/**
 * Hook para gerenciar tabelas de dados
 */
export const useAccessibleTable = () => {
  const [tableInfo, setTableInfo] = useState({})

  // Configurar informações da tabela
  const configureTable = useCallback((id, caption, rowCount, colCount) => {
    setTableInfo(prev => ({
      ...prev,
      [id]: { caption, rowCount, colCount }
    }))
  }, [])

  // Anunciar informações da tabela
  const announceTableInfo = useCallback((id, announce) => {
    const info = tableInfo[id]
    if (info && announce) {
      const message = `Tabela: ${info.caption}. ${info.rowCount} linhas e ${info.colCount} colunas.`
      announce(message, 'polite')
    }
  }, [tableInfo])

  return {
    configureTable,
    announceTableInfo
  }
}

/**
 * Hook para gerenciar formulários acessíveis
 */
export const useAccessibleForm = () => {
  const [formErrors, setFormErrors] = useState({})
  const [formState, setFormState] = useState({})

  // Adicionar erro de formulário
  const addFormError = useCallback((fieldName, error) => {
    setFormErrors(prev => ({
      ...prev,
      [fieldName]: error
    }))
  }, [])

  // Remover erro de formulário
  const removeFormError = useCallback((fieldName) => {
    setFormErrors(prev => {
      const newErrors = { ...prev }
      delete newErrors[fieldName]
      return newErrors
    })
  }, [])

  // Verificar se formulário tem erros
  const hasErrors = useCallback(() => {
    return Object.keys(formErrors).length > 0
  }, [formErrors])

  // Obter primeiro erro
  const getFirstError = useCallback(() => {
    const errors = Object.values(formErrors)
    return errors.length > 0 ? errors[0] : null
  }, [formErrors])

  // Atualizar estado do formulário
  const updateFormState = useCallback((fieldName, value, isValid) => {
    setFormState(prev => ({
      ...prev,
      [fieldName]: { value, isValid }
    }))
  }, [])

  // Verificar se formulário é válido
  const isFormValid = useCallback(() => {
    return Object.values(formState).every(field => field.isValid)
  }, [formState])

  return {
    formErrors,
    formState,
    addFormError,
    removeFormError,
    hasErrors,
    getFirstError,
    updateFormState,
    isFormValid
  }
}

/**
 * Hook para gerenciar navegação por teclado em componentes complexos
 */
export const useKeyboardNavigation = (config = {}) => {
  const {
    items = [],
    orientation = 'vertical',
    loop = true,
    wrap = false
  } = config

  const [activeIndex, setActiveIndex] = useState(0)
  const containerRef = useRef(null)

  // Navegar para item anterior
  const navigatePrevious = useCallback(() => {
    if (items.length === 0) return

    let newIndex = activeIndex - 1
    if (newIndex < 0) {
      newIndex = loop ? items.length - 1 : 0
    }

    setActiveIndex(newIndex)
    items[newIndex]?.focus()
  }, [activeIndex, items, loop])

  // Navegar para próximo item
  const navigateNext = useCallback(() => {
    if (items.length === 0) return

    let newIndex = activeIndex + 1
    if (newIndex >= items.length) {
      newIndex = loop ? 0 : items.length - 1
    }

    setActiveIndex(newIndex)
    items[newIndex]?.focus()
  }, [activeIndex, items, loop])

  // Navegar para item específico
  const navigateTo = useCallback((index) => {
    if (index >= 0 && index < items.length) {
      setActiveIndex(index)
      items[index]?.focus()
    }
  }, [items])

  // Lidar com teclas de navegação
  const handleKeyDown = useCallback((e) => {
    switch (e.key) {
      case 'ArrowUp':
        if (orientation === 'vertical') {
          e.preventDefault()
          navigatePrevious()
        }
        break
      case 'ArrowDown':
        if (orientation === 'vertical') {
          e.preventDefault()
          navigateNext()
        }
        break
      case 'ArrowLeft':
        if (orientation === 'horizontal') {
          e.preventDefault()
          navigatePrevious()
        }
        break
      case 'ArrowRight':
        if (orientation === 'horizontal') {
          e.preventDefault()
          navigateNext()
        }
        break
      case 'Home':
        e.preventDefault()
        navigateTo(0)
        break
      case 'End':
        e.preventDefault()
        navigateTo(items.length - 1)
        break
      case 'Enter':
      case ' ':
        if (items[activeIndex]) {
          items[activeIndex].click()
        }
        break
    }
  }, [orientation, activeIndex, items, navigatePrevious, navigateNext, navigateTo])

  return {
    activeIndex,
    setActiveIndex,
    containerRef,
    navigatePrevious,
    navigateNext,
    navigateTo,
    handleKeyDown
  }
}

export default useScreenReader
