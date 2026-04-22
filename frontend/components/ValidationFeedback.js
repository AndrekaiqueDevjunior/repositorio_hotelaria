/**
 * Componente de Feedback de Validação
 * Exibe erros de validação de forma amigável
 */

import { AlertCircle, CheckCircle } from 'lucide-react';

/**
 * Mensagens de erro amigáveis
 */
const MENSAGENS_AMIGAVEIS = {
  // CPF
  'CPF inválido': 'CPF inválido. Verifique os números digitados.',
  'CPF deve ter 11 dígitos': 'CPF deve ter 11 dígitos.',
  'dígito verificador incorreto': 'CPF inválido. Os dígitos verificadores estão incorretos.',
  
  // Datas
  'Data de check-in não pode ser no passado': 'A data de check-in deve ser hoje ou no futuro.',
  'Data de check-out deve ser posterior ao check-in': 'A data de saída deve ser depois da data de entrada.',
  'Reserva não pode exceder 30 dias': 'Reservas podem ter no máximo 30 dias.',
  
  // Disponibilidade
  'não disponível': 'Este quarto não está disponível nas datas selecionadas.',
  'Conflito com reservas': 'Já existe uma reserva para este quarto neste período.',
  
  // Status
  'Não é possível cancelar reserva com hóspede já hospedado': 'Não é possível cancelar uma reserva em andamento.',
  'Não é possível cancelar reserva já finalizada': 'Esta reserva já foi finalizada.',
  'Check-in só pode ser feito em reservas confirmadas': 'A reserva precisa estar confirmada para fazer check-in.',
  'Check-out só pode ser feito em reservas com status HOSPEDADO': 'Só é possível fazer check-out de hóspedes que já fizeram check-in.',
  
  // Pagamento
  'Valor do pagamento deve ser maior que zero': 'O valor do pagamento deve ser maior que zero.',
  'Valor do pagamento excede o limite permitido': 'O valor excede o limite de R$ 100.000.',
  'Método de pagamento inválido': 'Selecione um método de pagamento válido.',
  'já existe': 'Esta operação já foi processada anteriormente.',
  
  // Pontos
  'Saldo insuficiente': 'Saldo de pontos insuficiente para esta operação.',
  'Quantidade de pontos deve ser maior que zero': 'A quantidade de pontos deve ser maior que zero.',
  
  // Genérico
  'já em andamento': 'Esta operação já está sendo processada. Aguarde...',
  'Outro processo está criando': 'Outra pessoa está fazendo esta operação. Tente novamente em alguns segundos.'
};

/**
 * Traduzir mensagem de erro técnica para amigável
 */
function traduzirErro(mensagemTecnica) {
  if (!mensagemTecnica) return 'Ocorreu um erro. Tente novamente.';
  
  // Procurar correspondência parcial
  for (const [chave, mensagemAmigavel] of Object.entries(MENSAGENS_AMIGAVEIS)) {
    if (mensagemTecnica.toLowerCase().includes(chave.toLowerCase())) {
      return mensagemAmigavel;
    }
  }
  
  // Se não encontrou, retornar mensagem original (pode ser já amigável)
  return mensagemTecnica;
}

/**
 * Componente de Feedback Inline
 */
export function ValidationFeedback({ error, success, className = '' }) {
  if (!error && !success) return null;

  const mensagem = error ? traduzirErro(error) : success;
  const isError = !!error;

  return (
    <div
      className={`
        flex items-start gap-2 p-3 rounded-lg text-sm
        ${isError ? 'bg-red-50 text-red-800 border border-red-200' : 'bg-green-50 text-green-800 border border-green-200'}
        ${className}
      `}
    >
      <div className="flex-shrink-0 mt-0.5">
        {isError ? (
          <AlertCircle className="w-4 h-4" />
        ) : (
          <CheckCircle className="w-4 h-4" />
        )}
      </div>
      <div className="flex-1">{mensagem}</div>
    </div>
  );
}

/**
 * Componente de Feedback de Campo
 */
export function FieldError({ error, className = '' }) {
  if (!error) return null;

  return (
    <p className={`text-sm text-red-600 mt-1 ${className}`}>
      {traduzirErro(error)}
    </p>
  );
}

/**
 * Modal de Confirmação de Duplicação
 */
export function DuplicateConfirmModal({ isOpen, onClose, onConfirm, operacao }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <AlertCircle className="w-6 h-6 text-yellow-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Operação Duplicada
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Parece que você já realizou esta operação recentemente:
            </p>
            <div className="bg-gray-50 rounded p-3 mb-4">
              <p className="text-sm font-medium text-gray-900">{operacao}</p>
            </div>
            <p className="text-sm text-gray-600">
              Deseja continuar mesmo assim?
            </p>
          </div>
        </div>
        
        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Continuar
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Indicador de Operação em Andamento
 */
export function OperationInProgress({ message = 'Processando...' }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4">
        <div className="flex items-center gap-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <div>
            <p className="font-medium text-gray-900">{message}</p>
            <p className="text-sm text-gray-600 mt-1">Aguarde um momento...</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export { traduzirErro };
