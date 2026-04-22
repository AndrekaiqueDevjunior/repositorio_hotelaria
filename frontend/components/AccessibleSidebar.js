/**
 * Sidebar Acessível com navegação por teclado e suporte a screen readers
 */

import { useState, useRef, useEffect } from 'react'
import { ChevronDown, ChevronRight, Menu, X } from 'lucide-react'

const AccessibleSidebar = ({ 
  items, 
  isOpen, 
  onClose, 
  user, 
  currentPath 
}) => {
  const [expandedItems, setExpandedItems] = useState({})
  const sidebarRef = useRef(null)
  const firstFocusableRef = useRef(null)
  const lastFocusableRef = useRef(null)

  // Gerenciar expansão de itens
  const toggleExpanded = (itemId) => {
    setExpandedItems(prev => ({
      ...prev,
      [itemId]: !prev[itemId]
    }))
  }

  // Focus trap
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose()
        return
      }

      if (e.key === 'Tab') {
        const focusableElements = sidebarRef.current?.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )

        if (!focusableElements?.length) return

        const firstElement = focusableElements[0]
        const lastElement = focusableElements[focusableElements.length - 1]

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
    }

    document.addEventListener('keydown', handleKeyDown)
    
    // Focar no primeiro elemento quando abre
    setTimeout(() => {
      firstFocusableRef.current?.focus()
    }, 100)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, onClose])

  // Renderizar item de menu
  const renderMenuItem = (item, level = 0) => {
    const isActive = currentPath === item.href
    const hasSubItems = item.items && item.items.length > 0
    const isExpanded = expandedItems[item.id]

    return (
      <div key={item.id} className="w-full">
        {/* Item Principal */}
        <div className="relative">
          {item.href ? (
            <a
              href={item.href}
              ref={level === 0 && !firstFocusableRef.current ? firstFocusableRef : null}
              className={`
                flex items-center w-full px-4 py-2 text-sm rounded-lg transition-all duration-200
                ${isActive 
                  ? 'bg-blue-100 text-blue-700 font-medium' 
                  : 'text-gray-700 hover:bg-gray-100'
                }
                ${level > 0 ? 'ml-' + (level * 4) : ''}
              `}
              onClick={() => {
                if (hasSubItems) {
                  toggleExpanded(item.id)
                } else {
                  onClose()
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  if (hasSubItems) {
                    toggleExpanded(item.id)
                  } else {
                    window.location.href = item.href
                  }
                }
              }}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
              aria-expanded={hasSubItems ? isExpanded : undefined}
              aria-haspopup={hasSubItems ? 'menu' : undefined}
              role="menuitem"
            >
              <span className="flex items-center flex-1">
                {item.icon && <span className="mr-3" aria-hidden="true">{item.icon}</span>}
                <span>{item.label}</span>
                {item.badge && (
                  <span className="ml-auto bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                    {item.badge}
                  </span>
                )}
              </span>
              {hasSubItems && (
                <span className="ml-2" aria-hidden="true">
                  {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </span>
              )}
            </a>
          ) : (
            <button
              ref={level === 0 && !firstFocusableRef.current ? firstFocusableRef : null}
              className={`
                flex items-center w-full px-4 py-2 text-sm rounded-lg transition-all duration-200
                ${isActive 
                  ? 'bg-blue-100 text-blue-700 font-medium' 
                  : 'text-gray-700 hover:bg-gray-100'
                }
                ${level > 0 ? 'ml-' + (level * 4) : ''}
              `}
              onClick={() => toggleExpanded(item.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  toggleExpanded(item.id)
                }
              }}
              aria-label={item.label}
              aria-expanded={isExpanded}
              aria-haspopup="menu"
              role="menuitem"
            >
              <span className="flex items-center flex-1">
                {item.icon && <span className="mr-3" aria-hidden="true">{item.icon}</span>}
                <span>{item.label}</span>
                {item.badge && (
                  <span className="ml-auto bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                    {item.badge}
                  </span>
                )}
              </span>
              <span className="ml-2" aria-hidden="true">
                {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </span>
            </button>
          )}
        </div>

        {/* Sub-itens */}
        {hasSubItems && isExpanded && (
          <div 
            className="mt-1 space-y-1"
            role="menu"
            aria-label={`${item.label} sub-menu`}
          >
            {item.items.map(subItem => renderMenuItem(subItem, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <div
        ref={sidebarRef}
        className={`
          fixed top-0 left-0 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out z-50
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:static lg:inset-0
        `}
        role="navigation"
        aria-label="Menu de navegação principal"
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-lg font-bold">🏨</span>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Hotel Real</h2>
                <p className="text-sm text-gray-500">Cabo Frio</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="lg:hidden p-2 text-gray-500 hover:text-gray-700 rounded-lg"
              aria-label="Fechar menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* User Info */}
        {user && (
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-gray-600">
                  {user.nome?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user.nome || 'Usuário'}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user.perfil || 'Funcionário'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Menu */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto" role="menu">
          {items.map(item => renderMenuItem(item))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          <div className="space-y-2">
            <button
              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              onClick={() => {
                // Abrir painel de acessibilidade
                const event = new CustomEvent('open-accessibility-panel')
                window.dispatchEvent(event)
              }}
              aria-label="Abrir configurações de acessibilidade"
            >
              <span className="flex items-center">
                <span className="mr-2">♿</span>
                Acessibilidade
              </span>
            </button>
            <button
              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              onClick={() => {
                // Sair do sistema
                window.location.href = '/logout'
              }}
              aria-label="Sair do sistema"
            >
              <span className="flex items-center">
                <span className="mr-2">🚪</span>
                Sair
              </span>
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

export default AccessibleSidebar
