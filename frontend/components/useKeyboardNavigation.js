/**
 * Hook para Navegação por Teclado Acessível
 * Segue WCAG 2.1 AA com atalhos e navegação estruturada
 */

import { useEffect, useCallback } from 'react'

export const useKeyboardNavigation = (shortcuts = {}) => {
  const handleKeyDown = useCallback((e) => {
    // Ignorar se o usuário está digitando em um input/textarea
    const target = e.target
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'SELECT' ||
      target.contentEditable === 'true'
    ) {
      return
    }

    const { key, ctrlKey, metaKey, shiftKey, altKey } = e
    const modifiers = { ctrlKey, metaKey, shiftKey, altKey }

    // Verificar atalhos personalizados
    for (const [shortcut, handler] of Object.entries(shortcuts)) {
      const [expectedKey, expectedModifiers = {}] = shortcut.split('+')
      
      if (
        key === expectedKey &&
        Object.entries(expectedModifiers).every(([mod, value]) => {
          return modifiers[mod] === (value === 'true')
        })
      ) {
        e.preventDefault()
        handler(e)
        return
      }
    }

    // Atalhos padrão
    switch (key) {
      case 'Escape':
        // Fechar modais ou voltar
        if (document.activeElement?.closest('[role="dialog"]')) {
          const closeButton = document.querySelector('[aria-label*="Fechar"], [aria-label*="Close"]')
          closeButton?.click()
        }
        break

      case 'Enter':
        // Ativar botões focados
        if (target.tagName === 'BUTTON' || target.role === 'button') {
          target.click()
        }
        break

      case ' ':
        // Ativar checkboxes e radios
        if (target.type === 'checkbox' || target.type === 'radio') {
          target.click()
        }
        break

      case 'F6':
        // Navegar para próxima seção
        e.preventDefault()
        const sections = document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="region"]')
        const currentIndex = Array.from(sections).indexOf(target)
        const nextIndex = currentIndex < sections.length - 1 ? currentIndex + 1 : 0
        sections[nextIndex]?.focus()
        break

      case 'F7':
        // Navegar para seção anterior
        e.preventDefault()
        const sections2 = document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="region"]')
        const currentIndex2 = Array.from(sections2).indexOf(target)
        const prevIndex = currentIndex2 > 0 ? currentIndex2 - 1 : sections2.length - 1
        sections2[prevIndex]?.focus()
        break

      case 'Tab':
        // Tab já é tratado pelo navegador, mas podemos adicionar comportamento personalizado
        break

      case 'ArrowUp':
      case 'ArrowDown':
      case 'ArrowLeft':
      case 'ArrowRight':
        // Navegação em grids e listas
        if (target.getAttribute('role') === 'gridcell' || target.tagName === 'TD') {
          e.preventDefault()
          const grid = target.closest('[role="grid"], table')
          if (grid) {
            const cells = Array.from(grid.querySelectorAll('[role="gridcell"], td'))
            const currentIndex = cells.indexOf(target)
            
            let nextIndex
            if (key === 'ArrowRight') {
              nextIndex = currentIndex < cells.length - 1 ? currentIndex + 1 : 0
            } else if (key === 'ArrowLeft') {
              nextIndex = currentIndex > 0 ? currentIndex - 1 : cells.length - 1
            } else if (key === 'ArrowDown') {
              nextIndex = Math.min(currentIndex + (grid.getAttribute('role') === 'grid' ? 
                parseInt(grid.getAttribute('aria-colcount') || 1) : 1), cells.length - 1)
            } else if (key === 'ArrowUp') {
              nextIndex = Math.max(currentIndex - (grid.getAttribute('role') === 'grid' ? 
                parseInt(grid.getAttribute('aria-colcount') || 1) : 1), 0)
            }
            
            cells[nextIndex]?.focus()
          }
        }
        break

      case 'Home':
      case 'End':
        // Navegar para início/fim da página
        if (!ctrlKey && !metaKey) {
          e.preventDefault()
          if (key === 'Home') {
            window.scrollTo({ top: 0, behavior: 'smooth' })
          } else {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
          }
        }
        break
    }
  }, [shortcuts])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown])

  return { handleKeyDown }
}

/**
 * Hook para Skip Links (atalhos de navegação)
 */
export const useSkipLinks = () => {
  useEffect(() => {
    // Criar skip links dinamicamente
    const skipLinks = [
      { href: '#main-content', text: 'Pular para conteúdo principal' },
      { href: '#navigation', text: 'Pular para navegação' },
      { href: '#search', text: 'Pular para busca' }
    ]

    const skipLinksContainer = document.createElement('div')
    skipLinksContainer.className = 'sr-only'
    skipLinksContainer.innerHTML = skipLinks
      .map(link => `<a href="${link.href}" class="skip-link">${link.text}</a>`)
      .join('')

    document.body.insertBefore(skipLinksContainer, document.body.firstChild)

    // Adicionar estilos para skip links
    const style = document.createElement('style')
    style.textContent = `
      .skip-link {
        position: absolute;
        top: -40px;
        left: 6px;
        background: #000;
        color: #fff;
        padding: 8px;
        text-decoration: none;
        border-radius: 4px;
        z-index: 9999;
        transition: top 0.3s;
      }
      .skip-link:focus {
        top: 6px;
      }
    `
    document.head.appendChild(style)

    return () => {
      document.body.removeChild(skipLinksContainer)
      document.head.removeChild(style)
    }
  }, [])
}

/**
 * Hook para Anúncios de Navegação
 */
export const useNavigationAnnouncements = () => {
  const announce = useCallback((message, priority = 'polite') => {
    const announcement = document.createElement('div')
    announcement.setAttribute('aria-live', priority)
    announcement.setAttribute('aria-atomic', 'true')
    announcement.className = 'sr-only'
    announcement.textContent = message
    
    document.body.appendChild(announcement)
    
    setTimeout(() => {
      document.body.removeChild(announcement)
    }, 1000)
  }, [])

  return { announce }
}

export default useKeyboardNavigation
