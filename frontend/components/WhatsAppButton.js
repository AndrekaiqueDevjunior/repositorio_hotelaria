'use client'
import { useState } from 'react'

export default function WhatsAppButton({ 
  clienteNome = 'Cliente',
  clienteCPF = '',
  clienteRG = '',
  premioNome = 'Prêmio',
  pontosUsados = 0,
  codigoResgate = '',
  endereco = {
    rua: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    estado: '',
    cep: ''
  },
  className = '',
  onNeedAddress = null
}) {
  const [loading, setLoading] = useState(false)
  const [showAddressForm, setShowAddressForm] = useState(false)
  const [formData, setFormData] = useState({
    rua: endereco.rua || '',
    numero: endereco.numero || '',
    complemento: endereco.complemento || '',
    bairro: endereco.bairro || '',
    cidade: endereco.cidade || 'Cabo Frio',
    estado: endereco.estado || 'RJ',
    cep: endereco.cep || '',
    rg: clienteRG || ''
  })

  const handleWhatsAppClick = () => {
    // Verificar se tem endereço completo
    if (!formData.rua || !formData.numero || !formData.cidade || !formData.cep || !formData.rg) {
      setShowAddressForm(true)
      return
    }
    
    enviarWhatsApp()
  }

  const enviarWhatsApp = () => {
    setLoading(true)
    
    // Número do WhatsApp do Hotel Real Cabo Frio
    const numeroWhatsApp = '5522264859 00'.replace(/\s/g, '')
    
    // Endereço completo formatado
    const enderecoCompleto = `${formData.rua}, ${formData.numero}${formData.complemento ? ' - ' + formData.complemento : ''}
${formData.bairro}
${formData.cidade}/${formData.estado}
CEP: ${formData.cep}`
    
    // Mensagem formatada com TODOS os dados necessários
    const mensagem = `🎁 *RESGATE DE PRÊMIO - PROGRAMA DE FIDELIDADE*

👤 *DADOS DO CLIENTE*
Nome: ${clienteNome}
CPF: ${clienteCPF}
RG: ${formData.rg}

📦 *DADOS DO PRÊMIO*
Prêmio: ${premioNome}
Pontos Utilizados: ${pontosUsados}
Código de Resgate: *${codigoResgate}*

📍 *ENDEREÇO PARA ENTREGA*
${enderecoCompleto}

✉️ *SOLICITAÇÃO*
Gostaria de confirmar o resgate e saber sobre a entrega (Correios/SEDEX).`

    // Codificar mensagem para URL
    const mensagemCodificada = encodeURIComponent(mensagem)
    
    // Gerar link do WhatsApp
    const linkWhatsApp = `https://wa.me/${numeroWhatsApp}?text=${mensagemCodificada}`
    
    // Abrir WhatsApp em nova aba
    window.open(linkWhatsApp, '_blank')
    
    setShowAddressForm(false)
    setTimeout(() => setLoading(false), 1000)
  }

  const handleFormChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const formatCEP = (value) => {
    const numbers = value.replace(/\D/g, '')
    if (numbers.length <= 8) {
      return numbers.replace(/(\d{5})(\d)/, '$1-$2')
    }
    return numbers.slice(0, 8).replace(/(\d{5})(\d)/, '$1-$2')
  }

  return (
    <>
      <button
        onClick={handleWhatsAppClick}
        disabled={loading}
        className={`
          inline-flex items-center justify-center gap-2 px-6 py-3
          bg-green-600 hover:bg-green-700 
          text-white font-semibold rounded-lg
          transition-all duration-200
          disabled:opacity-50 disabled:cursor-not-allowed
          shadow-md hover:shadow-lg
          ${className}
        `}
      >
        {/* Ícone WhatsApp */}
        <svg 
          className="w-5 h-5" 
          fill="currentColor" 
          viewBox="0 0 24 24"
        >
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
        
        {loading ? 'Abrindo WhatsApp...' : '📦 Solicitar Entrega via WhatsApp'}
      </button>

      {/* Modal de Formulário de Endereço */}
      {showAddressForm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-6 text-white flex-shrink-0">
              <h3 className="text-2xl font-bold text-center">📦 Dados para Entrega</h3>
              <p className="text-sm text-center mt-2 text-green-100">Preencha seus dados completos para receber o prêmio</p>
            </div>

            {/* Conteúdo */}
            <div className="p-6 flex-1 overflow-y-auto">
              <div className="space-y-4">
                {/* RG */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    RG *
                  </label>
                  <input
                    type="text"
                    value={formData.rg}
                    onChange={(e) => handleFormChange('rg', e.target.value)}
                    placeholder="00.000.000-0"
                    className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-green-500 focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>

                {/* Rua */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Rua/Avenida *
                  </label>
                  <input
                    type="text"
                    value={formData.rua}
                    onChange={(e) => handleFormChange('rua', e.target.value)}
                    placeholder="Ex: Rua das Flores"
                    className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-green-500 focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>

                {/* Número e Complemento */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Número *
                    </label>
                    <input
                      type="text"
                      value={formData.numero}
                      onChange={(e) => handleFormChange('numero', e.target.value)}
                      placeholder="123"
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-green-500 focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Complemento
                    </label>
                    <input
                      type="text"
                      value={formData.complemento}
                      onChange={(e) => handleFormChange('complemento', e.target.value)}
                      placeholder="Apto 101"
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-green-500 focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                </div>

                {/* Bairro */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Bairro *
                  </label>
                  <input
                    type="text"
                    value={formData.bairro}
                    onChange={(e) => handleFormChange('bairro', e.target.value)}
                    placeholder="Ex: Centro"
                    className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-green-500 focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>

                {/* Cidade e Estado */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Cidade *
                    </label>
                    <input
                      type="text"
                      value={formData.cidade}
                      onChange={(e) => handleFormChange('cidade', e.target.value)}
                      placeholder="Cabo Frio"
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-green-500 focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Estado *
                    </label>
                    <input
                      type="text"
                      value={formData.estado}
                      onChange={(e) => handleFormChange('estado', e.target.value.toUpperCase())}
                      placeholder="RJ"
                      maxLength={2}
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-green-500 focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white uppercase"
                      required
                    />
                  </div>
                </div>

                {/* CEP */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    CEP *
                  </label>
                  <input
                    type="text"
                    value={formData.cep}
                    onChange={(e) => handleFormChange('cep', formatCEP(e.target.value))}
                    placeholder="00000-000"
                    maxLength={9}
                    className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-green-500 focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>

                {/* Aviso */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    📦 <strong>Importante:</strong> Estes dados serão enviados para a equipe do hotel organizar a entrega via Correios/SEDEX.
                  </p>
                </div>
              </div>

              {/* Botões */}
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowAddressForm(false)}
                  className="flex-1 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg font-semibold hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={enviarWhatsApp}
                  disabled={!formData.rua || !formData.numero || !formData.cidade || !formData.cep || !formData.rg}
                  className="flex-1 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ✉️ Enviar para WhatsApp
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
