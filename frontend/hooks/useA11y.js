/**
 * Hook Principal de Acessibilidade (A11y)
 * Centraliza todas as funcionalidades de acessibilidade
 */

import { useEffect, useState, useRef } from 'react'
import { useScreenReader, useLandmarks, useLongDescriptions, useAccessibleTable, useAccessibleForm, useKeyboardNavigation as useKeyboardNav } from './useScreenReader'

export const useA11y = (options = {}) => {
  const {
    enableScreenReader = true,
    enableKeyboardNavigation = true,
    enableFocusManagement = true,
    enableAnnouncements = true,
    language = 'pt-BR'
  } = options

  // Hooks específicos
  const screenReader = useScreenReader()
  const landmarks = useLandmarks()
  const descriptions = useLongDescriptions()
  const tables = useAccessibleTable()
  const forms = useAccessibleForm()
  const keyboardNav = useKeyboardNav()

  // Estado geral de acessibilidade
  const [a11yState, setA11yState] = useState({
    highContrast: false,
    reducedMotion: false,
    largeText: false,
    keyboardNavigation: false,
    screenReader: screenReader.isScreenReaderActive
  })

  // Detectar preferências do usuário
  useEffect(() => {
    const detectPreferences = () => {
      const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      const prefersLargeText = window.matchMedia('(prefers-reduced-motion: reduce)').matches // Simplificado

      setA11yState(prev => ({
        ...prev,
        highContrast: prefersHighContrast,
        reducedMotion: prefersReducedMotion,
        largeText: prefersLargeText
      }))
    }

    detectPreferences()

    // Listeners para mudanças de preferência
    const mediaQueries = [
      window.matchMedia('(prefers-contrast: high)'),
      window.matchMedia('(prefers-reduced-motion: reduce)')
    ]

    mediaQueries.forEach(mq => mq.addListener(detectPreferences))

    return () => {
      mediaQueries.forEach(mq => mq.removeListener(detectPreferences))
    }
  }, [])

  // Definir idioma do documento
  useEffect(() => {
    document.documentElement.lang = language
  }, [language])

  // Gerenciar foco
  const focusElement = useCallback((element) => {
    if (element && typeof element.focus === 'function') {
      element.focus()
      // Garantir que o elemento esteja visível
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [])

  // Gerenciar trap de foco
  const createFocusTrap = useCallback((container) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )

    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    const handleTabKey = (e) => {
      if (e.key !== 'Tab') return

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault()
          lastElement.focus()
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault()
          firstElement.focus()
        }
      }
    }

    container.addEventListener('keydown', handleTabKey)

    return () => {
      container.removeEventListener('keydown', handleTabKey)
    }
  }, [])

  // Gerenciar anúncios
  const announce = useCallback((message, priority = 'polite') => {
    if (enableAnnouncements) {
      screenReader.announce(message, priority)
    }
  }, [screenReader, enableAnnouncements])

  // Gerenciar landmarks
  const registerLandmark = useCallback((role, label, element) => {
    landmarks.registerLandmark(role, label, element)
  }, [landmarks])

  // Gerenciar descrições longas
  const addLongDescription = useCallback((id, content) => {
    descriptions.addDescription(id, content)
  }, [descriptions])

  // Gerenciar tabelas
  const configureTable = useCallback((id, caption, rowCount, colCount) => {
    tables.configureTable(id, caption, rowCount, colCount)
  }, [tables])

  // Gerenciar formulários
  const addFormError = useCallback((fieldName, error) => {
    forms.addFormError(fieldName, error)
    announce(`Erro no campo ${fieldName}: ${error}`, 'assertive')
  }, [forms, announce])

  // Gerenciar navegação por teclado
  const createKeyboardNavigation = useCallback((config) => {
    if (enableKeyboardNavigation) {
      return keyboardNav(config)
    }
    return {}
  }, [keyboardNav, enableKeyboardNavigation])

  // Gerenciar cores de alto contraste
  const toggleHighContrast = useCallback(() => {
    setA11yState(prev => {
      const newState = !prev.highContrast
      document.body.classList.toggle('high-contrast', newState)
      return { ...prev, highContrast: newState }
    })
  }, [])

  // Gerenciar animações
  const toggleReducedMotion = useCallback(() => {
    setA11yState(prev => {
      const newState = !prev.reducedMotion
      document.body.classList.toggle('reduced-motion', newState)
      return { ...prev, reducedMotion: newState }
    })
  }, [])

  // Gerenciar tamanho de texto
  const toggleLargeText = useCallback(() => {
    setA11yState(prev => {
      const newState = !prev.largeText
      document.body.classList.toggle('large-text', newState)
      return { ...prev, largeText: newState }
    })
  }, [])

  // Validação de acessibilidade
  const validateAccessibility = useCallback(() => {
    const issues = []

    // Verificar se há imagens sem alt
    const imagesWithoutAlt = document.querySelectorAll('img:not([alt]), img[alt=""]')
    if (imagesWithoutAlt.length > 0) {
      issues.push(`${imagesWithoutAlt.length} imagens sem atributo alt`)
    }

    // Verificar se há botões sem aria-label
    const buttonsWithoutLabel = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby]):empty')
    if (buttonsWithoutLabel.length > 0) {
      issues.push(`${buttonsWithoutLabel.length} botões sem rótulo acessível`)
    }

    // Verificar se há inputs sem label
    const inputsWithoutLabel = document.querySelectorAll('input:not([aria-label]):not([aria-labelledby]):not([id])')
    if (inputsWithoutLabel.length > 0) {
      issues.push(`${inputsWithoutLabel.length} inputs sem rótulo acessível`)
    }

    // Verificar se há headings sem hierarquia
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6')
    let lastLevel = 0
    headings.forEach(heading => {
      const currentLevel = parseInt(heading.tagName.charAt(1))
      if (currentLevel > lastLevel + 1) {
        issues.push(`Hierarquia de headings incorreta: h${lastLevel} para h${currentLevel}`)
      }
      lastLevel = currentLevel
    })

    return issues
  }, [])

  // Gerar relatório de acessibilidade
  const generateAccessibilityReport = useCallback(() => {
    const issues = validateAccessibility()
    const report = {
      timestamp: new Date().toISOString(),
      preferences: a11yState,
      issues: issues,
      score: Math.max(0, 100 - (issues.length * 10)),
      recommendations: []
    }

    // Adicionar recomendações baseadas nos problemas
    if (issues.some(issue => issue.includes('alt'))) {
      report.recommendations.push('Adicione atributos alt descritivos em todas as imagens')
    }
    if (issues.some(issue => issue.includes('botões'))) {
      report.recommendations.push('Adicione aria-label ou aria-labelledby em botões sem texto')
    }
    if (issues.some(issue => issue.includes('inputs'))) {
      report.recommendations.push('Adicione labels ou aria-label em todos os inputs')
    }
    if (issues.some(issue => issue.includes('headings'))) {
      report.recommendations.push('Corrija a hierarquia de headings (h1 → h2 → h3...)')
    }

    return report
  }, [validateAccessibility, a11yState])

  // Atalhos de teclado globais
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      // Alt + A: Toggle anúncios
      if (e.altKey && e.key === 'a') {
        e.preventDefault()
        setA11yState(prev => ({ ...prev, screenReader: !prev.screenReader }))
      }

      // Alt + H: Toggle alto contraste
      if (e.altKey && e.key === 'h') {
        e.preventDefault()
        toggleHighContrast()
      }

      // Alt + M: Toggle movimento reduzido
      if (e.altKey && e.key === 'm') {
        e.preventDefault()
        toggleReducedMotion()
      }

      // Alt + L: Toggle texto grande
      if (e.altKey && e.key === 'l') {
        e.preventDefault()
        toggleLargeText()
      }

      // Alt + K: Toggle navegação por teclado
      if (e.altKey && e.key === 'k') {
        e.preventDefault()
        setA11yState(prev => ({ ...prev, keyboardNavigation: !prev.keyboardNavigation }))
      }

      // Alt + R: Gerar relatório de acessibilidade
      if (e.altKey && e.key === 'r') {
        e.preventDefault()
        const report = generateAccessibilityReport()
        console.log('Relatório de Acessibilidade:', report)
        announce(`Relatório gerado. Score: ${report.score}%. ${issues.length} problemas encontrados.`, 'polite')
      }
    }

    document.addEventListener('keydown', handleGlobalKeyDown)
    return () => document.removeEventListener('keydown', handleGlobalKeyDown)
  }, [toggleHighContrast, toggleReducedMotion, toggleLargeText, generateAccessibilityReport, announce])

  return {
    // Estado
    a11yState,
    
    // Screen Reader
    announce,
    announceStateChange: screenReader.announceStateChange,
    announceNavigation: screenReader.announceNavigation,
    announceError: screenReader.announceError,
    announceSuccess: screenReader.announceSuccess,
    announceProgress: screenReader.announceProgress,
    announceLoadingComplete: screenReader.announceLoadingComplete,
    
    // Landmarks
    registerLandmark,
    navigateToLandmark: landmarks.navigateToLandmark,
    getAvailableLandmarks: landmarks.getAvailableLandmarks,
    
    // Descrições
    addLongDescription,
    getDescription: descriptions.getDescription,
    removeDescription: descriptions.removeDescription,
    
    // Tabelas
    configureTable,
    announceTableInfo: tables.announceTableInfo,
    
    // Formulários
    addFormError,
    removeFormError: forms.removeFormError,
    hasFormErrors: forms.hasErrors,
    getFirstFormError: forms.getFirstError,
    isFormValid: forms.isFormValid,
    
    // Navegação
    createKeyboardNavigation,
    focusElement,
    createFocusTrap,
    
    // Preferências
    toggleHighContrast,
    toggleReducedMotion,
    toggleLargeText,
    
    // Validação
    validateAccessibility,
    generateAccessibilityReport
  }
}

export default useA11y
