'use client'
import { useState } from 'react'
import WhatsAppButton from './WhatsAppButton'

/**
 * Exemplo de uso do botão WhatsApp para resgates de prêmios
 * 
 * Este componente pode ser integrado em:
 * - Modal de confirmação de resgate
 * - Página de detalhes do prêmio
 * - Lista de prêmios disponíveis
 */
export default function PremioWhatsAppExample({ premio, cliente }) {
  const [showWhatsApp, setShowWhatsApp] = useState(false)

  // Gerar código de resgate único
  const codigoResgate = `RES-${Date.now().toString().slice(-6)}`

  return (
    <div className="space-y-4">
      {/* Card do Prêmio */}
      <div className="glass-card p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-neutral-900 dark:text-white">
              {premio?.nome || 'Prêmio Exemplo'}
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
              {premio?.descricao || 'Descrição do prêmio'}
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-primary-600">
              {premio?.preco_em_pontos || 0} pts
            </div>
          </div>
        </div>

        {/* Informações do Cliente */}
        <div className="border-t border-neutral-200 dark:border-neutral-700 pt-4 mb-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-neutral-500 dark:text-neutral-400">Cliente:</span>
              <p className="font-medium text-neutral-900 dark:text-white">
                {cliente?.nome || 'Seu Nome'}
              </p>
            </div>
            <div>
              <span className="text-neutral-500 dark:text-neutral-400">Endereço:</span>
              <p className="font-medium text-neutral-900 dark:text-white">
                {cliente?.endereco || 'Cabo Frio/RJ'}
              </p>
            </div>
          </div>
        </div>

        {/* Botões de Ação */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Botão Resgate Normal */}
          <button
            onClick={() => setShowWhatsApp(!showWhatsApp)}
            className="flex-1 btn-secondary"
          >
            {showWhatsApp ? '❌ Cancelar' : '🎁 Resgatar Prêmio'}
          </button>
        </div>

        {/* Botão WhatsApp (aparece após clicar em Resgatar) */}
        {showWhatsApp && (
          <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border-2 border-green-200 dark:border-green-800">
            <div className="flex items-start gap-3 mb-3">
              <div className="flex-shrink-0 w-10 h-10 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-green-900 dark:text-green-100 mb-1">
                  Resgatar via WhatsApp
                </h4>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Clique no botão abaixo para enviar uma mensagem automática com os detalhes do resgate.
                </p>
              </div>
            </div>

            {/* Botão WhatsApp */}
            <WhatsAppButton
              clienteNome={cliente?.nome || 'Cliente'}
              premioNome={premio?.nome || 'Prêmio'}
              pontosUsados={premio?.preco_em_pontos || 0}
              codigoResgate={codigoResgate}
              clienteEndereco={cliente?.endereco || 'Cabo Frio/RJ'}
              className="w-full"
            />

            <p className="text-xs text-green-600 dark:text-green-400 mt-2 text-center">
              💬 Número: +55 11 96802-9600
            </p>
          </div>
        )}
      </div>

      {/* Instruções de Uso */}
      <div className="glass-card p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-2">
          <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium mb-1">Como funciona:</p>
            <ol className="list-decimal list-inside space-y-1 text-blue-700 dark:text-blue-300">
              <li>Clique em "Resgatar Prêmio"</li>
              <li>Clique em "Resgatar via WhatsApp"</li>
              <li>O WhatsApp abrirá com a mensagem pronta</li>
              <li>Envie a mensagem e aguarde o contato</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  )
}
