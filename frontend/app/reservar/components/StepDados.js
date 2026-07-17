'use client'

import { ShieldCheck } from 'lucide-react'
import { formatCPF, formatTelefone, onlyDigits } from '../utils/formatters'
import { isValidCPF, isValidEmail, isValidTelefone } from '../utils/validators'
import { getSuiteDescription } from '../utils/suites'

export default function StepDados({
  hospedeData,
  onUpdateField,
  quartoSelecionado,
  numDiarias,
  customerAuth,
  onBuscarCpf,
  onCriarCadastro,
  onEnviarOtp,
  onValidarOtp,
  authLoading,
  isAuthenticated,
  onVoltar,
  onContinuar
}) {
  const canEditCustomerFields = customerAuth.status === 'idle' || customerAuth.status === 'not_found'
  const cpfLimpo = onlyDigits(hospedeData.documento)
  const telefoneLimpo = onlyDigits(hospedeData.telefone)

  const authBadge = {
    idle: { label: 'Pendente', className: 'border-blue-200 bg-blue-100 text-blue-800' },
    not_found: { label: 'Novo cadastro', className: 'border-amber-200 bg-amber-100 text-amber-800' },
    found: { label: 'Cadastro localizado', className: 'border-blue-200 bg-blue-100 text-blue-800' },
    otp_sent: { label: 'Código enviado', className: 'border-purple-200 bg-purple-100 text-purple-800' },
    verified: { label: 'Autenticado', className: 'border-green-200 bg-green-100 text-green-800' },
  }[customerAuth.status] || { label: 'Pendente', className: 'border-blue-200 bg-blue-100 text-blue-800' }

  const suiteInfo = getSuiteDescription(quartoSelecionado?.tipo)

  return (
    <div className="bg-white rounded-2xl shadow-2xl overflow-hidden text-gray-900">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6">
        <h2 className="text-xl font-bold text-white sm:text-2xl">📝 Seus Dados</h2>
        <p className="text-blue-100">Autentique seu cadastro para liberar a reserva</p>
      </div>

      {/* Resumo do Quarto */}
      <div className="bg-blue-50 p-4 border-b flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">Quarto selecionado</p>
          <p className="font-bold text-blue-800">
            {suiteInfo.titulo} - Quarto {quartoSelecionado.numero}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-600">{numDiarias} {numDiarias === 1 ? 'diária' : 'diárias'}</p>
          <p className="font-bold text-green-600">R$ {quartoSelecionado.preco_total.toFixed(2)}</p>
        </div>
      </div>

      <div className="p-6 space-y-4">
        {/* Autenticação */}
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-gray-800">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-start gap-3">
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-blue-600 text-white">
                <ShieldCheck size={24} strokeWidth={1.8} />
              </span>
              <div>
                <h3 className="font-bold text-blue-900">Autenticação do cadastro</h3>
                <p className="text-sm text-blue-800">
                  O código é enviado para o WhatsApp do cadastro e vincula esta reserva ao CPF.
                </p>
              </div>
            </div>
            <span className={`w-fit rounded-full border px-3 py-1 text-xs font-bold uppercase ${authBadge.className}`}>
              {authBadge.label}
            </span>
          </div>

          {/* CPF Input */}
          <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">CPF *</span>
              <input
                type="text"
                placeholder="000.000.000-00"
                value={hospedeData.documento}
                onChange={(e) => onUpdateField('documento', formatCPF(e.target.value))}
                disabled={customerAuth.status !== 'idle' && customerAuth.status !== 'not_found'}
                className="w-full rounded-lg border-2 border-gray-200 p-3 focus:border-blue-400 focus:outline-none disabled:bg-gray-100 disabled:text-gray-500"
                maxLength={14}
              />
            </label>
            <div className="flex items-end gap-2">
              <button
                type="button"
                onClick={onBuscarCpf}
                disabled={authLoading || customerAuth.status !== 'idle'}
                className="min-h-[48px] rounded-lg bg-blue-600 px-5 font-bold text-white transition-all hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {authLoading && customerAuth.status === 'idle' ? 'Consultando...' : 'Consultar'}
              </button>
            </div>
          </div>

          {/* CPF não encontrado */}
          {customerAuth.status === 'not_found' && (
            <div className="mt-4 rounded-lg border border-amber-200 bg-white p-4 text-gray-900">
              <p className="text-sm text-amber-800">
                CPF não cadastrado. Preencha nome, email e telefone abaixo para criar o cadastro antes do OTP.
              </p>
              <button
                type="button"
                onClick={onCriarCadastro}
                disabled={authLoading}
                className="mt-3 rounded-lg bg-amber-500 px-5 py-3 font-bold text-white transition-all hover:bg-amber-600 disabled:opacity-50"
              >
                {authLoading ? 'Criando cadastro...' : 'Criar cadastro'}
              </button>
            </div>
          )}

          {/* Cliente encontrado */}
          {customerAuth.customer && customerAuth.status !== 'verified' && (
            <div className="mt-4 rounded-lg border border-blue-200 bg-white p-4 text-gray-900">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-bold text-gray-900">{customerAuth.customer.nome_completo}</p>
                  <p className="text-sm text-gray-600">
                    WhatsApp cadastrado: {formatTelefone(customerAuth.customer.telefone || '') || 'telefone indisponível'}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={onEnviarOtp}
                  disabled={authLoading}
                  className="rounded-lg bg-blue-600 px-5 py-3 font-bold text-white transition-all hover:bg-blue-700 disabled:opacity-50"
                >
                  {customerAuth.status === 'otp_sent' ? 'Reenviar código' : 'Enviar código'}
                </button>
              </div>

              {/* OTP Input */}
              {customerAuth.status === 'otp_sent' && (
                <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,220px)_auto]">
                  <input
                    type="text"
                    inputMode="numeric"
                    placeholder="000000"
                    value={customerAuth.otpCode}
                    onChange={(e) => {
                      const digits = onlyDigits(e.target.value).slice(0, 6)
                      onUpdateField('otpCode', digits)
                    }}
                    className="rounded-lg border-2 border-gray-200 p-3 text-center text-xl font-bold tracking-[0.2em] focus:border-blue-400 focus:outline-none"
                    maxLength={6}
                  />
                  <button
                    type="button"
                    onClick={onValidarOtp}
                    disabled={authLoading}
                    className="rounded-lg bg-green-600 px-5 py-3 font-bold text-white transition-all hover:bg-green-700 disabled:opacity-50"
                  >
                    {authLoading ? 'Validando...' : 'Validar código'}
                  </button>
                </div>
              )}
            </div>
          )}

          {isAuthenticated && (
            <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-4 text-sm font-medium text-green-800">
              Cadastro autenticado. Você já pode revisar os dados da reserva e continuar.
            </div>
          )}
        </div>

        {/* Dados do Hóspede */}
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-gray-700 font-medium mb-1">Nome Completo *</label>
            <input
              type="text"
              placeholder="Como está no documento"
              value={hospedeData.nome_completo}
              onChange={(e) => onUpdateField('nome_completo', e.target.value)}
              disabled={!canEditCustomerFields}
              className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none disabled:bg-gray-100 disabled:text-gray-500"
            />
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-1">Email *</label>
            <input
              type="email"
              placeholder="seu@email.com"
              value={hospedeData.email}
              onChange={(e) => onUpdateField('email', e.target.value)}
              disabled={!canEditCustomerFields}
              className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none disabled:bg-gray-100 disabled:text-gray-500"
            />
            <p className="text-xs text-gray-500 mt-1">Enviaremos a confirmação para este email</p>
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-1">Telefone *</label>
            <input
              type="text"
              placeholder="(00) 00000-0000"
              value={hospedeData.telefone}
              onChange={(e) => onUpdateField('telefone', formatTelefone(e.target.value))}
              disabled={!canEditCustomerFields}
              className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none disabled:bg-gray-100 disabled:text-gray-500"
              maxLength={15}
            />
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-1">Adultos</label>
            <select
              value={hospedeData.num_hospedes}
              onChange={(e) => onUpdateField('num_hospedes', parseInt(e.target.value))}
              className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none"
            >
              {[1, 2, 3, 4].map(n => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-1">Crianças (0-12 anos)</label>
            <select
              value={hospedeData.num_criancas}
              onChange={(e) => onUpdateField('num_criancas', parseInt(e.target.value))}
              className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none"
            >
              {[0, 1, 2, 3].map(n => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-gray-700 font-medium mb-1">Observações (opcional)</label>
          <textarea
            placeholder="Solicitações especiais, preferências, restrições alimentares..."
            value={hospedeData.observacoes}
            onChange={(e) => onUpdateField('observacoes', e.target.value)}
            className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none resize-none"
            rows={3}
          />
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
            onClick={onContinuar}
            disabled={!isAuthenticated}
            className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition-all disabled:cursor-not-allowed disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isAuthenticated ? 'Continuar →' : 'Autentique para continuar'}
            <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}
