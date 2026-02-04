/**
 * Componente de Botão Acessível
 * Segue WCAG 2.1 AA com suporte a screen readers e navegação por teclado
 */

import { forwardRef } from 'react'
import { Loader2 } from 'lucide-react'

const AccessibleButton = forwardRef(({
  children,
  type = 'button',
  variant = 'primary', // primary, secondary, outline, ghost
  size = 'md', // sm, md, lg
  loading = false,
  disabled = false,
  icon,
  iconPosition = 'left',
  onClick,
  onKeyDown,
  className = '',
  ariaLabel,
  ariaDescribedBy,
  ...props
}, ref) => {
  const baseClasses = `
    inline-flex items-center justify-center
    font-medium rounded-lg
    transition-all duration-200
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
  `

  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500',
    outline: 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50 focus:ring-blue-500',
    ghost: 'text-gray-600 hover:bg-gray-100 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500'
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  }

  const handleKeyDown = (e) => {
    // Enter ou Space para ativar
    if ((e.key === 'Enter' || e.key === ' ') && !disabled && !loading) {
      e.preventDefault()
      onClick?.(e)
    }
    onKeyDown?.(e)
  }

  const renderIcon = () => {
    if (!icon) return null
    return <span className={iconPosition === 'left' ? 'mr-2' : 'ml-2'}>{icon}</span>
  }

  const renderContent = () => {
    if (loading) {
      return (
        <>
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
          <span className="ml-2">Carregando...</span>
        </>
      )
    }

    return (
      <>
        {iconPosition === 'left' && renderIcon()}
        {children}
        {iconPosition === 'right' && renderIcon()}
      </>
    )
  }

  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${className}
      `}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      aria-disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {renderContent()}
    </button>
  )
})

AccessibleButton.displayName = 'AccessibleButton'

export default AccessibleButton
