'use client'

/**
 * Badge de Status para Reservas
 * Mostra o estado atual da reserva com cores e ícones apropriados
 */

export default function StatusBadge({ status }) {
  const getStatusConfig = (status) => {
    const configs = {
      'PENDENTE_PAGAMENTO': {
        label: 'Aguardando Pagamento',
        icon: '⏳',
        color: 'bg-yellow-100 text-yellow-800 border-yellow-300'
      },
      'AGUARDANDO_COMPROVANTE': {
        label: 'Aguardando Comprovante',
        icon: '📤',
        color: 'bg-orange-100 text-orange-800 border-orange-300'
      },
      'EM_ANALISE': {
        label: 'Em Análise',
        icon: '🔍',
        color: 'bg-blue-100 text-blue-800 border-blue-300'
      },
      'PAGA_APROVADA': {
        label: 'Pago Aprovado',
        icon: '✅',
        color: 'bg-green-100 text-green-800 border-green-300'
      },
      'PAGA_REJEITADA': {
        label: 'Pagamento Rejeitado',
        icon: '❌',
        color: 'bg-red-100 text-red-800 border-red-300'
      },
      'CHECKIN_LIBERADO': {
        label: 'Check-in Liberado',
        icon: '🟢',
        color: 'bg-purple-100 text-purple-800 border-purple-300'
      },
      'CHECKIN_REALIZADO': {
        label: 'Check-in Realizado',
        icon: '🏨',
        color: 'bg-indigo-100 text-indigo-800 border-indigo-300'
      },
      'CHECKOUT_REALIZADO': {
        label: 'Check-out Realizado',
        icon: '✔️',
        color: 'bg-gray-100 text-gray-800 border-gray-300'
      },
      'CANCELADA': {
        label: 'Cancelada',
        icon: '🚫',
        color: 'bg-red-100 text-red-800 border-red-300'
      },
      'NO_SHOW': {
        label: 'No Show',
        icon: '👻',
        color: 'bg-gray-100 text-gray-800 border-gray-300'
      },
      // Aliases legados
      'PENDENTE': {
        label: 'Pendente',
        icon: '⏳',
        color: 'bg-yellow-100 text-yellow-800 border-yellow-300'
      },
      'CONFIRMADA': {
        label: 'Confirmada',
        icon: '✅',
        color: 'bg-green-100 text-green-800 border-green-300'
      },
      'HOSPEDADO': {
        label: 'Hospedado',
        icon: '🏨',
        color: 'bg-indigo-100 text-indigo-800 border-indigo-300'
      }
    }

    return configs[status] || {
      label: status || 'Desconhecido',
      icon: '❓',
      color: 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const config = getStatusConfig(status)

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border-2 ${config.color}`}>
      <span className="text-sm">{config.icon}</span>
      <span>{config.label}</span>
    </span>
  )
}

/**
 * Badge de Status Financeiro
 */
export function StatusFinanceiroBadge({ status }) {
  const getStatusConfig = (status) => {
    const configs = {
      'AGUARDANDO_PAGAMENTO': {
        label: 'Aguardando',
        icon: '💰',
        color: 'bg-yellow-100 text-yellow-800'
      },
      'SINAL_PAGO': {
        label: 'Sinal Pago',
        icon: '💵',
        color: 'bg-blue-100 text-blue-800'
      },
      'PAGO_TOTAL': {
        label: 'Pago',
        icon: '✅',
        color: 'bg-green-100 text-green-800'
      },
      'ESTORNADO': {
        label: 'Estornado',
        icon: '↩️',
        color: 'bg-red-100 text-red-800'
      },
      'DEVEDOR': {
        label: 'Devedor',
        icon: '⚠️',
        color: 'bg-orange-100 text-orange-800'
      }
    }

    return configs[status] || {
      label: status || 'N/A',
      icon: '❓',
      color: 'bg-gray-100 text-gray-800'
    }
  }

  const config = getStatusConfig(status)

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${config.color}`}>
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </span>
  )
}

/**
 * Tooltip com explicação do status
 */
export function StatusTooltip({ status }) {
  const getTooltip = (status) => {
    const tooltips = {
      'PENDENTE_PAGAMENTO': 'Reserva criada. Cliente precisa escolher forma de pagamento.',
      'AGUARDANDO_COMPROVANTE': 'Cliente escolheu "Pagamento no balcão". Aguardando upload do comprovante.',
      'EM_ANALISE': 'Comprovante enviado. Aguardando validação do administrador.',
      'PAGA_APROVADA': 'Comprovante aprovado. Pagamento confirmado.',
      'PAGA_REJEITADA': 'Comprovante rejeitado. Cliente precisa enviar novo comprovante.',
      'CHECKIN_LIBERADO': '✅ Pagamento OK. Check-in pode ser realizado.',
      'CHECKIN_REALIZADO': 'Check-in realizado. Hóspede no hotel.',
      'CHECKOUT_REALIZADO': 'Check-out realizado. Hospedagem finalizada.',
      'CANCELADA': 'Reserva cancelada.',
      'NO_SHOW': 'Cliente não compareceu no check-in.'
    }

    return tooltips[status] || 'Status desconhecido'
  }

  return (
    <div className="group relative inline-block">
      <span className="cursor-help text-gray-400 hover:text-gray-600">ℹ️</span>
      <div className="invisible group-hover:visible absolute z-10 w-64 p-2 mt-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg -left-24">
        {getTooltip(status)}
      </div>
    </div>
  )
}
