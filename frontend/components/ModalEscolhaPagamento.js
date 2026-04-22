'use client'

import { useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../lib/api'
import UploadComprovanteModal from './UploadComprovanteModal'

/**
 * Modal de Escolha de Forma de Pagamento
 * Apresenta as opções: PIX, Cartão Online, Pagamento no Balcão
 */
export default function ModalEscolhaPagamento({ reserva, onClose, onSuccess }) {
  const [metodoPagamento, setMetodoPagamento] = useState(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [pagamentoCriado, setPagamentoCriado] = useState(null)

  const opcoesPagamento = [
    {
      id: 'pix',
      nome: 'PIX',
      icon: '📱',
      descricao: 'Pagamento instantâneo via PIX',
      disponivel: true,
      action: 'pix'
    },
    {
      id: 'cartao_online',
      nome: 'Cartão Online',
      icon: '💳',
      descricao: 'Pagamento com cartão de crédito/débito',
      disponivel: true,
      action: 'cielo'
    },
    {
      id: 'balcao',
      nome: 'Pagamento no Balcão',
      icon: '🏪',
      descricao: 'Pagamento presencial (dinheiro, cartão na maquininha)',
      disponivel: true,
      action: 'comprovante'
    }
  ]

  const handleEscolha = async (opcao) => {
    setMetodoPagamento(opcao.id)

    if (opcao.action === 'comprovante') {
      try {
        if (!reserva?.id) {
          toast.error('Reserva inválida. Recarregue a página e tente novamente.')
          return
        }

        const valor = Number(reserva?.valor_total || reserva?.valor_previsto || 0)
        if (!valor || Number.isNaN(valor)) {
          toast.error('Valor da reserva inválido. Recarregue a página e tente novamente.')
          return
        }

        const pagamentoPayload = {
          reserva_id: parseInt(reserva.id),
          valor: valor,
          metodo: 'na_chegada'
        }

        const res = await api.post('/pagamentos', pagamentoPayload)
        setPagamentoCriado(res.data)

        // Abrir modal de upload de comprovante
        setShowUploadModal(true)
      } catch (err) {
        console.error('Erro ao criar pagamento (balcão):', err)
        toast.error(err.response?.data?.detail || 'Erro ao iniciar pagamento no balcão')
      }
    } else if (opcao.action === 'pix') {
      toast.info('🚧 Integração PIX em desenvolvimento')
      // TODO: Implementar fluxo PIX
    } else if (opcao.action === 'cielo') {
      toast.info('🚧 Integração Cielo em desenvolvimento')
      // TODO: Implementar fluxo Cielo
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0)
  }

  if (showUploadModal) {
    return (
      <UploadComprovanteModal
        reserva={reserva}
        pagamento={pagamentoCriado || { valor: reserva.valor_total || reserva.valor_previsto }}
        onClose={() => {
          setShowUploadModal(false)
          setPagamentoCriado(null)
          onClose()
        }}
        onSuccess={() => {
          setShowUploadModal(false)
          setPagamentoCriado(null)
          if (onSuccess) onSuccess()
        }}
      />
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-green-800 text-white p-6 rounded-t-lg">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">💰 Escolha a Forma de Pagamento</h2>
              <p className="text-green-100">
                Reserva: {reserva?.codigo_reserva || `#${reserva?.id}`}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        {/* Valor Total */}
        <div className="bg-blue-50 p-6 border-b-2 border-blue-200">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">Valor Total da Reserva</p>
            <p className="text-4xl font-bold text-blue-600">
              {formatCurrency(reserva?.valor_total || reserva?.valor_previsto)}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              {reserva?.num_diarias} diária(s) × {formatCurrency(reserva?.valor_diaria)}
            </p>
          </div>
        </div>

        {/* Opções de Pagamento */}
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Selecione como deseja pagar:
          </h3>

          <div className="space-y-4">
            {opcoesPagamento.map((opcao) => (
              <button
                key={opcao.id}
                onClick={() => handleEscolha(opcao)}
                disabled={!opcao.disponivel}
                className={`w-full p-6 rounded-lg border-2 transition-all text-left ${
                  opcao.disponivel
                    ? 'border-gray-300 hover:border-green-500 hover:shadow-lg cursor-pointer'
                    : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-50'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="text-4xl">{opcao.icon}</div>
                  <div className="flex-1">
                    <h4 className="text-xl font-bold text-gray-800 mb-1">
                      {opcao.nome}
                    </h4>
                    <p className="text-gray-600">{opcao.descricao}</p>
                    
                    {/* Destaque especial para Balcão */}
                    {opcao.id === 'balcao' && (
                      <div className="mt-3 bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
                        <p className="text-sm text-yellow-800">
                          <strong>⚠️ Importante:</strong> Você precisará enviar o comprovante de pagamento
                          para aprovação do administrador antes de fazer o check-in.
                        </p>
                      </div>
                    )}

                    {!opcao.disponivel && (
                      <span className="inline-block mt-2 px-3 py-1 bg-gray-200 text-gray-600 rounded-full text-xs font-medium">
                        Em breve
                      </span>
                    )}
                  </div>
                  
                  {opcao.disponivel && (
                    <div className="text-green-600 text-2xl">→</div>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Informações Adicionais */}
          <div className="mt-6 bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-blue-700">
                  <strong>Dica:</strong> Para pagamento no balcão, você pode pagar em dinheiro, 
                  débito ou crédito na maquininha. Após o pagamento, tire uma foto do comprovante 
                  e envie para aprovação.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Botão Cancelar */}
        <div className="p-6 bg-gray-50 rounded-b-lg border-t">
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 font-medium transition-colors"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}
