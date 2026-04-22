/**
 * Componente de Input Acessível
 * Segue WCAG 2.1 AA com suporte a screen readers e navegação por teclado
 */

import { forwardRef, useState } from 'react'
import { Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react'

const AccessibleInput = forwardRef(({
  id,
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  onBlur,
  onFocus,
  error,
  success,
  helperText,
  required = false,
  disabled = false,
  autoComplete = 'off',
  className = '',
  ...props
}, ref) => {
  const [showPassword, setShowPassword] = useState(false)
  const [isFocused, setIsFocused] = useState(false)

  const inputType = type === 'password' && showPassword ? 'text' : type
  const hasError = !!error
  const hasSuccess = !!success

  const getAriaDescribedBy = () => {
    const ids = []
    if (hasError) ids.push(`${id}-error`)
    if (hasSuccess) ids.push(`${id}-success`)
    if (helperText) ids.push(`${id}-helper`)
    return ids.length > 0 ? ids.join(' ') : undefined
  }

  const getAriaInvalid = () => {
    return hasError ? 'true' : 'false'
  }

  const handleKeyDown = (e) => {
    // Escape para limpar campo
    if (e.key === 'Escape' && value) {
      onChange({ target: { value: '', name: props.name || id } })
    }
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Label */}
      {label && (
        <label 
          htmlFor={id}
          className={`
            block text-sm font-medium
            ${disabled ? 'text-gray-400' : 'text-gray-700'}
            ${required ? 'required-indicator' : ''}
          `}
        >
          {label}
          {required && <span className="text-red-500 ml-1" aria-label="campo obrigatório">*</span>}
        </label>
      )}

      {/* Input Container */}
      <div className="relative">
        <input
          ref={ref}
          id={id}
          type={inputType}
          value={value}
          onChange={onChange}
          onBlur={(e) => {
            setIsFocused(false)
            onBlur?.(e)
          }}
          onFocus={(e) => {
            setIsFocused(true)
            onFocus?.(e)
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete={autoComplete}
          aria-describedby={getAriaDescribedBy()}
          aria-invalid={getAriaInvalid()}
          aria-required={required}
          aria-label={label || placeholder}
          className={`
            w-full px-4 py-3 border rounded-lg transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-offset-0
            ${disabled 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed border-gray-200' 
              : 'bg-white text-gray-900'
            }
            ${hasError 
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500' 
              : hasSuccess 
                ? 'border-green-300 focus:ring-green-500 focus:border-green-500'
                : isFocused 
                  ? 'border-blue-500 focus:ring-blue-500 focus:border-blue-500'
                  : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
            }
            ${type === 'password' ? 'pr-12' : ''}
          `}
          {...props}
        />

        {/* Toggle Password Visibility */}
        {type === 'password' && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            disabled={disabled}
            className={`
              absolute right-3 top-1/2 transform -translate-y-1/2
              p-1 rounded-md transition-colors
              ${disabled 
                ? 'text-gray-400 cursor-not-allowed' 
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }
            `}
            aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
            aria-pressed={showPassword}
          >
            {showPassword ? (
              <EyeOff className="w-5 h-5" />
            ) : (
              <Eye className="w-5 h-5" />
            )}
          </button>
        )}

        {/* Status Icons */}
        {(hasError || hasSuccess) && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
            {hasError && <AlertCircle className="w-5 h-5 text-red-500" aria-hidden="true" />}
            {hasSuccess && <CheckCircle className="w-5 h-5 text-green-500" aria-hidden="true" />}
          </div>
        )}
      </div>

      {/* Helper Text */}
      {helperText && (
        <p 
          id={`${id}-helper`}
          className="text-sm text-gray-600"
          role="status"
          aria-live="polite"
        >
          {helperText}
        </p>
      )}

      {/* Error Message */}
      {hasError && (
        <p 
          id={`${id}-error`}
          className="text-sm text-red-600 flex items-center gap-1"
          role="alert"
          aria-live="assertive"
        >
          <AlertCircle className="w-4 h-4" aria-hidden="true" />
          {error}
        </p>
      )}

      {/* Success Message */}
      {hasSuccess && (
        <p 
          id={`${id}-success`}
          className="text-sm text-green-600 flex items-center gap-1"
          role="status"
          aria-live="polite"
        >
          <CheckCircle className="w-4 h-4" aria-hidden="true" />
          {success}
        </p>
      )}
    </div>
  )
})

AccessibleInput.displayName = 'AccessibleInput'

export default AccessibleInput
