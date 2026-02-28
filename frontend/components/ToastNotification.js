'use client'
import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { playNotificationSound } from '../sounds/notification-sound'

export default function ToastNotification({ toast, onClose }) {
  const [isExiting, setIsExiting] = useState(false)
  const [timeLeft, setTimeLeft] = useState(5)
  const router = useRouter()

  // Função para formatar valor monetário
  const formatCurrency = (value) => {
    if (value === undefined || value === null) return 'R$ 0,00'
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(Number(value))
  }

  // Tocar som quando o toast é exibido pela primeira vez
  useEffect(() => {
    // Tocar som para notificações importantes
    if (toast.tipo === 'success' || toast.tipo === 'reserva' || toast.categoria === 'financeiro') {
      // Som especial para financeiro (pagamento aprovado)
      if (toast.categoria === 'financeiro') {
        playNotificationSound() // Som de "dinheiro"
      } else {
        playNotificationSound() // Som padrão de notificação
      }
    }
  }, []) // Executar apenas uma vez quando o componente monta
  useEffect(() => {
    if (timeLeft <= 0) {
      handleClose()
      return
    }

    const timer = setTimeout(() => {
      setTimeLeft(prev => prev - 1)
    }, 1000)

    return () => clearTimeout(timer)
  }, [timeLeft])

  // Resetar o contador quando o mouse entra
  const handleMouseEnter = useCallback(() => {
    setTimeLeft(10) // Reseta para 10 segundos quando o mouse entra
  }, [])

  // Iniciar contagem regressiva quando o mouse sai
  const handleMouseLeave = useCallback(() => {
    setTimeLeft(5) // Volta para 5 segundos quando o mouse sai
  }, [])

  const handleClose = useCallback((e) => {
    if (e) e.stopPropagation()
    setIsExiting(true)
    setTimeout(() => {
      onClose(toast.id)
    }, 300)
  }, [onClose, toast.id])

  const handleAction = useCallback((e) => {
    e.stopPropagation()
    if (toast.url_acao) {
      router.push(toast.url_acao)
      handleClose(e)
    }
  }, [toast.url_acao, handleClose, router])

  const getIcon = () => {
    switch (toast.tipo) {
      case 'success':
        return '✅'
      case 'info':
        return 'ℹ️'
      case 'warning':
        return '⚠️'
      case 'critical':
        return '🔴'
      case 'financeiro':
        return '💰'
      case 'reserva':
        return '🏨'
      default:
        return '📌'
    }
  }

  const getBgColor = () => {
    switch (toast.tipo) {
      case 'success':
        return 'bg-green-50 border-l-4 border-green-500'
      case 'info':
        return 'bg-blue-50 border-l-4 border-blue-500'
      case 'warning':
      case 'financeiro':
        return 'bg-yellow-50 border-l-4 border-yellow-500'
      case 'critical':
        return 'bg-red-50 border-l-4 border-red-500'
      case 'reserva':
        return 'bg-indigo-50 border-l-4 border-indigo-500'
      default:
        return 'bg-gray-50 border-l-4 border-gray-500'
    }
  }

  const getTextColor = () => {
    switch (toast.tipo) {
      case 'success':
        return 'text-green-800'
      case 'info':
        return 'text-blue-800'
      case 'warning':
      case 'financeiro':
        return 'text-yellow-800'
      case 'critical':
        return 'text-red-800'
      case 'reserva':
        return 'text-indigo-800'
      default:
        return 'text-gray-800'
    }
  }

  // Renderizar dados adicionais se disponíveis
  const renderAdditionalData = () => {
    if (!toast.dados_adicionais) return null

    return (
      <div className="mt-2 text-xs space-y-1">
        {toast.dados_adicionais.codigo_reserva && (
          <div className="flex">
            <span className="font-medium text-gray-600 w-20">Código:</span>
            <span className="text-gray-800">{toast.dados_adicionais.codigo_reserva}</span>
          </div>
        )}
        {toast.dados_adicionais.quarto_numero && (
          <div className="flex">
            <span className="font-medium text-gray-600 w-20">Quarto:</span>
            <span className="text-gray-800">{toast.dados_adicionais.quarto_numero}</span>
          </div>
        )}
        {toast.dados_adicionais.checkin_previsto && (
          <div className="flex">
            <span className="font-medium text-gray-600 w-20">Check-in:</span>
            <span className="text-gray-800">{toast.dados_adicionais.checkin_previsto}</span>
          </div>
        )}
        {toast.dados_adicionais.valor_total > 0 && (
          <div className="flex">
            <span className="font-medium text-gray-600 w-20">Total:</span>
            <span className="font-semibold text-gray-900">
              {formatCurrency(toast.dados_adicionais.valor_total)}
            </span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      className={`
        ${getBgColor()}
        rounded-r-lg shadow-lg p-4 mb-3 w-full max-w-md
        transition-all duration-300 ease-in-out transform
        ${isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'}
        cursor-pointer hover:shadow-md
      `}
      onClick={handleAction}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      role="button"
      tabIndex={0}
      onKeyPress={(e) => e.key === 'Enter' && handleAction(e)}
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl flex-shrink-0 mt-0.5">{getIcon()}</span>
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start">
            <h4 className={`font-semibold ${getTextColor()} text-sm mb-1`}>
              {toast.titulo}
            </h4>
            <span className="text-xs text-gray-400">
              {timeLeft}s
            </span>
          </div>
          
          <p className="text-gray-700 text-sm leading-relaxed">
            {toast.mensagem}
          </p>
          
          {renderAdditionalData()}
          
          <div className="mt-2 flex items-center justify-between">
            {toast.categoria && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-white/50 text-gray-800">
                {toast.categoria}
              </span>
            )}
            
            {toast.url_acao && (
              <button
                onClick={handleAction}
                className="text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
              >
                Ver detalhes →
              </button>
            )}
          </div>
        </div>
        
        <button
          onClick={handleClose}
          className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0 ml-2"
          aria-label="Fechar"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  )
}
