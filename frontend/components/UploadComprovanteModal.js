'use client'

import { useState } from 'react'
import { api } from '../lib/api'
import { toast } from 'react-toastify'
import { TipoComprovante, TIPO_COMPROVANTE_LABELS } from '../lib/constants/enums'

export default function UploadComprovanteModal({ pagamento, reserva, onClose, onSuccess }) {
  const [uploading, setUploading] = useState(false)
  const [tipoComprovante, setTipoComprovante] = useState('DINHEIRO')
  const [observacoes, setObservacoes] = useState('')
  const [arquivo, setArquivo] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [showFullScreen, setShowFullScreen] = useState(false)

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Validar tipo de arquivo
    const validTypes = [
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/webp',
      'image/heic',
      'image/heif',
      'application/pdf'
    ]

    const name = (file.name || '').toLowerCase()
    const ext = name.includes('.') ? name.split('.').pop() : ''
    const validExts = ['jpg', 'jpeg', 'png', 'webp', 'heic', 'heif', 'pdf']

    const typeOk = file.type ? validTypes.includes(file.type) : true
    const extOk = ext ? validExts.includes(ext) : true

    if (!typeOk || !extOk) {
      toast.error('Tipo de arquivo inválido. Use JPG, PNG, WEBP, HEIC/HEIF ou PDF')
      return
    }

    // Validar tamanho (máximo 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Arquivo muito grande. Tamanho máximo: 5MB')
      return
    }

    setArquivo(file)

    // Criar preview se for imagem ou PDF
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreviewUrl(reader.result)
      }
      reader.readAsDataURL(file)
    } else if (file.type === 'application/pdf') {
      // Para PDFs, criar preview também
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreviewUrl(reader.result)
      }
      reader.readAsDataURL(file)
    } else {
      setPreviewUrl(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!arquivo) {
      toast.error('Selecione um arquivo')
      return
    }

    setUploading(true)

    try {
      // Converter arquivo para base64
      const reader = new FileReader()
      reader.onloadend = async () => {
        const base64String = reader.result.split(',')[1]

        const pagamentoId = pagamento?.id ? parseInt(pagamento.id) : null
        if (!pagamentoId) {
          toast.error('Pagamento inválido. Recarregue a página e tente novamente.')
          setUploading(false)
          return
        }

        // CORREÇÃO: Usar endpoint correto e schema alinhado com backend
        const dados = {
          pagamento_id: pagamentoId,
          tipo_comprovante: tipoComprovante,  // Enum correto
          arquivo_base64: base64String,
          nome_arquivo: arquivo.name,
          observacoes: observacoes || undefined,  // undefined remove o campo se vazio
          valor_confirmado: pagamento?.valor ? parseFloat(pagamento.valor) : undefined
        }
        
        // Remover campos undefined para não enviar ao backend
        Object.keys(dados).forEach(key => dados[key] === undefined && delete dados[key])
        
        console.log('[UPLOAD] Enviando dados:', {
          ...dados,
          arquivo_base64: `${dados.arquivo_base64.substring(0, 50)}... (${dados.arquivo_base64.length} chars)`
        })

        try {
          // Endpoint correto: POST /comprovantes/upload
          const response = await api.post('/comprovantes/upload', dados)
          
          toast.success('✅ Comprovante enviado! Status: EM ANÁLISE')
          toast.info('📋 Aguarde a aprovação do administrador para liberar o check-in')
          
          if (onSuccess) {
            onSuccess()
          }
          
          onClose()
        } catch (error) {
          console.error('Erro ao enviar comprovante:', error)
          toast.error(error.response?.data?.detail || 'Erro ao enviar comprovante')
        } finally {
          setUploading(false)
        }
      }

      reader.onerror = () => {
        toast.error('Erro ao ler arquivo')
        setUploading(false)
      }

      reader.readAsDataURL(arquivo)
    } catch (error) {
      console.error('Erro:', error)
      toast.error('Erro ao processar arquivo')
      setUploading(false)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-t-lg">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">📤 Upload de Comprovante</h2>
              <p className="text-blue-100">Reserva: {reserva?.codigo_reserva || `#${reserva?.id}`}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-2xl"
              disabled={uploading}
            >
              ×
            </button>
          </div>
        </div>

        {/* Conteúdo */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Informações do Pagamento */}
          <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-200">
            <h3 className="font-semibold text-gray-800 mb-2">💰 Informações do Pagamento</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Valor</p>
                <p className="text-xl font-bold text-blue-600">
                  {formatCurrency(pagamento?.valor)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800">
                  {pagamento?.status || 'PENDENTE'}
                </span>
              </div>
            </div>
          </div>

          {/* Tipo de Comprovante */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tipo de Comprovante *
            </label>
            <select
              value={tipoComprovante}
              onChange={(e) => setTipoComprovante(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              {Object.entries(TIPO_COMPROVANTE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Upload de Arquivo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Comprovante (Foto ou PDF) *
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
              <input
                type="file"
                accept="image/jpeg,image/jpg,image/png,image/webp,image/heic,image/heif,application/pdf"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
                disabled={uploading}
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer flex flex-col items-center"
              >
                {previewUrl ? (
                  <div className="mb-4 relative">
                    {arquivo?.type === 'application/pdf' ? (
                      // Preview para PDF
                      <div className="border-2 border-gray-300 rounded-lg p-4 bg-gray-50">
                        <div className="flex items-center justify-center mb-2">
                          <svg
                            className="w-16 h-16 text-red-500 mr-3"
                            fill="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M10,19L12,15H9V10H15V15L13,19H10Z" />
                          </svg>
                          <div className="text-left">
                            <p className="font-medium text-gray-800">PDF Selecionado</p>
                            <p className="text-sm text-gray-600">{arquivo.name}</p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault()
                            setShowFullScreen(true)
                          }}
                          className="w-full mt-2 bg-blue-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors flex items-center justify-center"
                        >
                          🔍 Visualizar PDF
                        </button>
                      </div>
                    ) : (
                      // Preview para imagem
                      <img
                        src={previewUrl}
                        alt="Preview"
                        className="max-h-48 rounded-lg shadow-md cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={(e) => {
                          e.preventDefault()
                          setShowFullScreen(true)
                        }}
                      />
                    )}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault()
                        setShowFullScreen(true)
                      }}
                      className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-lg text-xs hover:bg-opacity-70 transition-all"
                    >
                      🔍 Ampliar
                    </button>
                  </div>
                ) : (
                  <div className="mb-4">
                    <svg
                      className="w-16 h-16 text-gray-400 mx-auto"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                  </div>
                )}
                <p className="text-sm text-gray-600">
                  {arquivo ? (
                    <span className="font-medium text-blue-600">{arquivo.name}</span>
                  ) : (
                    <>
                      Clique para selecionar ou arraste o arquivo
                      <br />
                      <span className="text-xs text-gray-500">
                        JPG, PNG, WEBP, HEIC/HEIF ou PDF (máx. 5MB)
                      </span>
                    </>
                  )}
                </p>
              </label>
            </div>
          </div>

          {/* Observações */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Observações (opcional)
            </label>
            <textarea
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ex: Pagamento recebido no balcão às 14h30"
              disabled={uploading}
            />
          </div>

          {/* Informações Importantes */}
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-yellow-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  <strong>Importante:</strong> O comprovante será analisado pela equipe administrativa.
                  Você receberá uma notificação quando for aprovado ou se houver alguma pendência.
                </p>
              </div>
            </div>
          </div>

          {/* Botões */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 font-medium transition-colors"
              disabled={uploading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={uploading || !arquivo}
            >
              {uploading ? (
                <span className="flex items-center justify-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Enviando...
                </span>
              ) : (
                '📤 Enviar Comprovante'
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Modal de Visualização em Tela Cheia */}
      {showFullScreen && previewUrl && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-95 flex items-center justify-center z-[60]"
          onClick={() => setShowFullScreen(false)}
        >
          <div className="relative w-full h-full flex items-center justify-center p-4">
            {/* Botão Fechar */}
            <button
              onClick={() => setShowFullScreen(false)}
              className="absolute top-4 right-4 bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg font-medium transition-all z-10"
            >
              ✕ Fechar
            </button>

            {/* Instruções */}
            <div className="absolute top-4 left-4 bg-white bg-opacity-20 text-white px-4 py-2 rounded-lg text-sm z-10">
              💡 {arquivo?.type === 'application/pdf' 
                ? 'Use o visualizador de PDF para navegar pelas páginas' 
                : 'Clique na imagem para dar zoom | Use scroll do mouse para ampliar/reduzir'
              }
            </div>

            {/* Conteúdo (Imagem ou PDF) */}
            {arquivo?.type === 'application/pdf' ? (
              // Visualizador de PDF
              <div className="w-full h-full flex items-center justify-center p-4">
                <iframe
                  src={previewUrl}
                  title="Comprovante PDF"
                  className="w-full h-full max-w-6xl max-h-[90vh] border-0 rounded-lg shadow-2xl bg-white"
                  style={{ minHeight: '80vh' }}
                />
              </div>
            ) : (
              // Imagem com Zoom
              <img
                src={previewUrl}
                alt="Comprovante - Visualização Completa"
                className="max-w-full max-h-full object-contain cursor-zoom-in hover:scale-105 transition-transform"
                style={{
                  imageRendering: 'high-quality'
                }}
                onClick={(e) => {
                  e.stopPropagation()
                  // Criar visualização com zoom adicional
                  const img = e.target
                  if (img.style.transform === 'scale(2)') {
                    img.style.transform = 'scale(1)'
                    img.style.cursor = 'zoom-in'
                  } else {
                    img.style.transform = 'scale(2)'
                    img.style.cursor = 'zoom-out'
                  }
                }}
              />
            )}

            {/* Nome do arquivo */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-white bg-opacity-20 text-white px-4 py-2 rounded-lg text-sm">
              📄 {arquivo?.name}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
