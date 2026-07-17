'use client'

import { formatCurrency } from '../utils/formatters'
import { getSuiteDescription } from '../utils/suites'

export default function StepPagamento({
  hospedeData,
  quartoSelecionado,
  searchData,
  numDiarias,
  valoresReserva,
  pontosEstimados,
  cupomCodigo,
  cupomValidacao,
  cupomLoading,
  onCupomCodigoChange,
  onValidarCupom,
  onVoltar,
  onConfirmarReserva,
  loading
}) {
  const suiteInfo = getSuiteDescription(quartoSelecionado.tipo)

  return (
    <div className="bg-white rounded-2xl shadow-2xl overflow-hidden text-gray-900">
      <div className="bg-gradient-to-r from-green-600 to-green-700 p-6">
        <h2 className="text-xl font-bold text-white sm:text-2xl">💳 Pagamento TEF</h2>
        <p className="text-green-100">O pagamento será processado via Terminal de Pagamento</p>
      </div>

      {/* Resumo da Reserva */}
      <div className="bg-green-50 p-4 border-b">
        <div className="flex justify-between items-center mb-4">
          <div>
            <p className="font-bold text-gray-800">{hospedeData.nome_completo}</p>
            <p className="text-sm text-gray-600">
              {suiteInfo.titulo} - Quarto {quartoSelecionado.numero}
            </p>
            <p className="text-sm text-gray-600">
              {new Date(searchData.data_checkin).toLocaleDateString('pt-BR')} → {new Date(searchData.data_checkout).toLocaleDateString('pt-BR')} ({numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'})
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Total</p>
            <p className="text-2xl font-bold text-green-600">
              {formatCurrency(valoresReserva.total)}
            </p>
            {cupomValidacao?.valido && (
              <p className="text-xs font-semibold text-amber-700">
                Cupom {cupomCodigo} aplicado
              </p>
            )}
          </div>
        </div>

        {/* Pontos Estimados */}
        {pontosEstimados && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
            <p className="font-semibold">👑 Pontos que você vai ganhar nesta reserva (estimativa)</p>
            <div className="mt-1 grid gap-1 sm:grid-cols-3">
              <span>Pontos de nível: {pontosEstimados.pontosN}N</span>
              <span>Pontos de resgate: {pontosEstimados.pontosR}R</span>
              {pontosEstimados.multiplicador > 1 && (
                <span>
                  Bônus nível {pontosEstimados.nivelNome || ''}: {pontosEstimados.multiplicador}x
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="p-6 space-y-4">
        {/* Cupom */}
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <label className="block text-sm font-bold uppercase text-amber-900 mb-2">Cupom ou Convite Real (opcional)</label>
          <div className="mt-2 grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
            <input
              type="text"
              value={cupomCodigo}
              onChange={(e) => onCupomCodigoChange(e.target.value)}
              placeholder="Digite seu cupom"
              className="w-full rounded-lg border-2 border-amber-200 bg-white p-3 font-mono uppercase text-gray-900 focus:border-amber-400 focus:outline-none"
              maxLength={50}
            />
            <button
              type="button"
              onClick={onValidarCupom}
              disabled={cupomLoading || !cupomCodigo}
              className="rounded-lg bg-amber-600 px-5 py-3 font-bold text-white transition-all hover:bg-amber-700 disabled:opacity-50"
            >
              {cupomLoading ? 'Validando...' : 'Validar'}
            </button>
          </div>
          {cupomValidacao && (
            <div className={`mt-3 rounded-lg border p-3 text-sm ${
              cupomValidacao.valido
                ? 'border-green-200 bg-green-50 text-green-800'
                : 'border-red-200 bg-red-50 text-red-700'
            }`}>
              <p className="font-semibold">{cupomValidacao.mensagem}</p>
              {cupomValidacao.valido && (
                <div className="mt-2 grid gap-1 sm:grid-cols-4">
                  <span>Subtotal: {formatCurrency(valoresReserva.subtotal)}</span>
                  <span>Desconto: {valoresReserva.percentualCupom}%</span>
                  <span>Economia: {formatCurrency(valoresReserva.desconto)}</span>
                  <span>Total: {formatCurrency(valoresReserva.total)}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Método de Pagamento TEF */}
        <div className="space-y-3">
          <p className="text-gray-700 font-medium">Forma de Pagamento:</p>
          <div className="p-4 border-2 border-green-500 rounded-xl bg-green-50">
            <div className="flex items-center gap-4">
              <span className="text-4xl">💳</span>
              <div>
                <p className="font-bold text-gray-800">Pagamento via Terminal (TEF)</p>
                <p className="text-sm text-gray-600">A reserva será confirmada após o processamento do pagamento no check-in</p>
              </div>
              <span className="ml-auto text-green-600 font-bold text-2xl">✓</span>
            </div>
          </div>
        </div>

        {/* Informações */}
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <p className="text-yellow-800 text-sm">
            ⚠️ <strong>Importante:</strong> A reserva será processada no check-in via terminal de pagamento (TEF).
            Cancelamentos podem ser feitos até 24h antes do check-in sem custo.
          </p>
        </div>

        {/* Resumo de Valores */}
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Subtotal ({numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'}):</span>
              <span className="font-semibold">{formatCurrency(valoresReserva.subtotal)}</span>
            </div>
            {valoresReserva.desconto > 0 && (
              <div className="flex justify-between text-green-700">
                <span>Desconto:</span>
                <span className="font-semibold">-{formatCurrency(valoresReserva.desconto)}</span>
              </div>
            )}
            <div className="border-t border-gray-300 pt-2 flex justify-between font-bold">
              <span>Total a pagar:</span>
              <span className="text-green-600 text-lg">{formatCurrency(valoresReserva.total)}</span>
            </div>
          </div>
        </div>

        {/* Botões */}
        <div className="flex gap-4 pt-4">
          <button
            onClick={onVoltar}
            className="flex-1 py-3 border-2 border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-all"
          >
            ← Voltar
          </button>
          <button
            onClick={onConfirmarReserva}
            disabled={loading}
            className="flex-1 py-3 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? '⏳ Processando...' : '✅ Confirmar Reserva'}
            <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}
