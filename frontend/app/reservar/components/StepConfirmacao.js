'use client'

export default function StepConfirmacao({
  reservaConfirmada,
  onNovaReserva
}) {
  if (!reservaConfirmada) return null

  const { reserva, instrucoes } = reservaConfirmada

  return (
    <div className="bg-white rounded-2xl shadow-2xl overflow-hidden text-gray-900">
      <div className="bg-gradient-to-r from-green-500 to-green-600 p-8 text-center">
        <div className="text-6xl mb-4">🎉</div>
        <h2 className="text-3xl font-bold text-white">Reserva Confirmada!</h2>
        <p className="text-green-100 mt-2">Sua reserva foi realizada com sucesso</p>
      </div>

      <div className="p-6">
        {/* Código da reserva */}
        <div className="bg-blue-50 p-6 rounded-xl text-center mb-6">
          <p className="text-gray-600 mb-1">Código da Reserva</p>
          <p className="text-3xl font-bold text-blue-600 font-mono">{reserva.codigo}</p>
          <p className="text-sm text-gray-500 mt-2">Guarde este código para consultar sua reserva</p>
        </div>

        {/* Detalhes */}
        <div className="space-y-4 mb-6">
          <h3 className="font-bold text-gray-800 text-lg">📋 Detalhes da Reserva</h3>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Hóspede</p>
              <p className="font-medium">{reserva.cliente}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Acomodação</p>
              <p className="font-medium">{reserva.tipo_suite} - Quarto {reserva.quarto}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Check-in</p>
              <p className="font-medium">{new Date(reserva.checkin).toLocaleDateString('pt-BR')} às 12:00</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Check-out</p>
              <p className="font-medium">{new Date(reserva.checkout).toLocaleDateString('pt-BR')} às 11:00</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Duração</p>
              <p className="font-medium">{reserva.num_diarias} {reserva.num_diarias === 1 ? 'diária' : 'diárias'}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Valor Total</p>
              <p className="font-bold text-green-600 text-xl">
                R$ {Number(reserva.valor_total_com_desconto || reserva.valor_total).toFixed(2)}
              </p>
              {Number(reserva.valor_desconto || 0) > 0 && (
                <p className="text-xs text-green-700">
                  Desconto: R$ {Number(reserva.valor_desconto).toFixed(2)}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Instruções */}
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200 mb-6">
          <h4 className="font-bold text-yellow-800 mb-2">📌 Instruções Importantes</h4>
          <ul className="text-sm text-yellow-800 space-y-1">
            <li>• {instrucoes?.documentos || 'Trazer documentos de identificação'}</li>
            <li>• Check-in a partir das {instrucoes?.checkin_horario || '12:00'}</li>
            <li>• Check-out até as {instrucoes?.checkout_horario || '11:00'}</li>
            <li>• Contato: {instrucoes?.contato || '(22) 2648-5900'}</li>
          </ul>
        </div>

        {/* Ações */}
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={() => window.print()}
            className="flex-1 py-3 border-2 border-blue-600 text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-all flex items-center justify-center gap-2"
          >
            🖨️ Imprimir Comprovante
            <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
          </button>
          <button
            onClick={onNovaReserva}
            className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all flex items-center justify-center gap-2"
          >
            🏨 Nova Reserva
            <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}
