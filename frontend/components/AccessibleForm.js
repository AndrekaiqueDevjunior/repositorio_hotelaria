/**
 * Componente de Formulário Acessível
 * Segue WCAG 2.1 AA com validação em tempo real e navegação por teclado
 */

import { useState, useRef } from 'react'
import { AlertCircle, CheckCircle } from 'lucide-react'

const AccessibleForm = ({
  children,
  onSubmit,
  className = '',
  noValidate = true,
  ...props
}) => {
  const [errors, setErrors] = useState({})
  const [touched, setTouched] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const formRef = useRef(null)

  const validateField = (name, value) => {
    // Validações básicas podem ser expandidas
    const validators = {
      email: (value) => {
        if (!value) return 'Email é obrigatório'
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Email inválido'
        return null
      },
      cpf: (value) => {
        if (!value) return 'CPF é obrigatório'
        const cleanValue = value.replace(/\D/g, '')
        if (cleanValue.length !== 11) return 'CPF deve ter 11 dígitos'
        if (!/^(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})$/.test(cleanValue)) return 'CPF inválido'
        return null
      },
      telefone: (value) => {
        if (!value) return 'Telefone é obrigatório'
        const cleanValue = value.replace(/\D/g, '')
        if (cleanValue.length < 10) return 'Telefone deve ter pelo menos 10 dígitos'
        return null
      },
      required: (value) => {
        if (!value || value.trim() === '') return 'Este campo é obrigatório'
        return null
      }
    }

    const validator = validators[name]
    if (validator) {
      return validator(value)
    }
    return null
  }

  const handleFieldChange = (name, value) => {
    setTouched(prev => ({ ...prev, [name]: true }))
    
    const error = validateField(name, value)
    setErrors(prev => ({ ...prev, [name]: error }))
  }

  const handleFieldBlur = (name, value) => {
    setTouched(prev => ({ ...prev, [name]: true }))
    
    const error = validateField(name, value)
    setErrors(prev => ({ ...prev, [name]: error }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Marcar todos os campos como tocados
    const formData = new FormData(formRef.current)
    const allErrors = {}
    
    for (let [name, value] of formData.entries()) {
      const error = validateField(name, value)
      if (error) {
        allErrors[name] = error
      }
    }
    
    setErrors(allErrors)
    setTouched(Object.fromEntries(formData.keys().map(key => [key, true])))
    
    // Se houver erros, não submeter
    if (Object.keys(allErrors).length > 0) {
      // Focar no primeiro campo com erro
      const firstErrorField = Object.keys(allErrors)[0]
      const errorElement = formRef.current.querySelector(`[name="${firstErrorField}"]`)
      errorElement?.focus()
      return
    }
    
    setIsSubmitting(true)
    
    try {
      await onSubmit(e)
    } catch (error) {
      console.error('Erro no formulário:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getFieldError = (name) => {
    return touched[name] ? errors[name] : null
  }

  const getFieldSuccess = (name) => {
    return touched[name] && !errors[name] && formRef.current?.querySelector(`[name="${name}"]`)?.value
  }

  const handleKeyDown = (e) => {
    // Ctrl+Enter para submeter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      formRef.current?.requestSubmit()
    }
  }

  return (
    <form
      ref={formRef}
      onSubmit={handleSubmit}
      onKeyDown={handleKeyDown}
      noValidate={noValidate}
      className={`space-y-6 ${className}`}
      {...props}
    >
      {typeof children === 'function' 
        ? children({ 
            handleFieldChange, 
            handleFieldBlur, 
            getFieldError, 
            getFieldSuccess, 
            isSubmitting 
          })
        : children
      }
    </form>
  )
}

// Componente de Field que integra com o formulário
export const FormField = ({
  name,
  label,
  type = 'text',
  placeholder,
  required = false,
  disabled = false,
  autoComplete = 'off',
  className = '',
  onChange,
  onBlur,
  value,
  ...props
}) => {
  const formContext = useFormContext()
  
  if (!formContext) {
    throw new Error('FormField deve ser usado dentro de um AccessibleForm')
  }

  const { handleFieldChange, handleFieldBlur, getFieldError, getFieldSuccess, isSubmitting } = formContext
  const error = getFieldError(name)
  const success = getFieldSuccess(name)

  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label 
          htmlFor={name}
          className={`
            block text-sm font-medium text-gray-700
            ${required ? 'required-indicator' : ''}
          `}
        >
          {label}
          {required && <span className="text-red-500 ml-1" aria-label="campo obrigatório">*</span>}
        </label>
      )}

      <div className="relative">
        <input
          name={name}
          type={type}
          value={value}
          onChange={(e) => {
            handleFieldChange(name, e.target.value)
            onChange?.(e)
          }}
          onBlur={(e) => {
            handleFieldBlur(name, e.target.value)
            onBlur?.(e)
          }}
          placeholder={placeholder}
          disabled={disabled || isSubmitting}
          autoComplete={autoComplete}
          required={required}
          className={`
            w-full px-4 py-3 border rounded-lg transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-offset-0
            ${disabled || isSubmitting 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed border-gray-200' 
              : 'bg-white text-gray-900'
            }
            ${error 
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500' 
              : success 
                ? 'border-green-300 focus:ring-green-500 focus:border-green-500'
                : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
            }
          `}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={`${name}-error ${name}-success`}
          {...props}
        />

        {/* Status Icons */}
        {(error || success) && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
            {error && <AlertCircle className="w-5 h-5 text-red-500" aria-hidden="true" />}
            {success && <CheckCircle className="w-5 h-5 text-green-500" aria-hidden="true" />}
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <p 
          id={`${name}-error`}
          className="text-sm text-red-600 flex items-center gap-1"
          role="alert"
          aria-live="assertive"
        >
          <AlertCircle className="w-4 h-4" aria-hidden="true" />
          {error}
        </p>
      )}

      {/* Success Message */}
      {success && (
        <p 
          id={`${name}-success`}
          className="text-sm text-green-600 flex items-center gap-1"
          role="status"
          aria-live="polite"
        >
          <CheckCircle className="w-4 h-4" aria-hidden="true" />
          Campo válido
        </p>
      )}
    </div>
  )
}

// Hook para usar o contexto do formulário
const useFormContext = () => {
  throw new Error('useFormContext deve ser usado dentro de um AccessibleForm')
}

export default AccessibleForm
