/**
 * Frontend Component para Comprovação de Pagamentos
 * 
 * Componente React para upload e validação de comprovantes.
 */

'use client'
import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { api } from '../../lib/api'
import { TipoComprovante, TIPO_COMPROVANTE_LABELS } from '../../lib/constants/enums'

const ComprovanteUpload = ({ pagamentoId, onUploadSuccess }) => {
  const [loading, setLoading] = useState(false)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [observacoes, setObservacoes] = useState('')
  const [valorConfirmado, setValorConfirmado] = useState('')
  const [tipoComprovante, setTipoComprovante] = useState(TipoComprovante.PIX)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      // Validar tamanho (max 10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        toast.error('Arquivo muito grande. Máximo 10MB')
        return
      }

      // Validar tipo
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
      if (!allowedTypes.includes(selectedFile.type)) {
        toast.error('Apenas imagens (JPG, PNG) e PDF são permitidos')
        return
      }

      setFile(selectedFile)
      
      // Criar preview
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreview(e.target.result)
      }
      reader.readAsDataURL(selectedFile)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!file) {
      toast.error('Selecione um arquivo')
      return
    }

    setLoading(true)
    
    try {
      // Converter arquivo para base64
      const base64 = await new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result.split(',')[1])
        reader.readAsDataURL(file)
      })

      const payload = {
        pagamento_id: pagamentoId,
        tipo_comprovante: tipoComprovante,
        arquivo_base64: base64,
        nome_arquivo: file.name,
        observacoes: observacoes || null,
        valor_confirmado: valorConfirmado ? parseFloat(valorConfirmado) : null
      }

      const response = await api.post('/comprovantes/upload', payload)
      
      toast.success('Comprovante enviado com sucesso! Aguardando validação.')
      setFile(null)
      setPreview(null)
      setObservacoes('')
      setValorConfirmado('')
      
      if (onUploadSuccess) {
        onUploadSuccess(response.data)
      }
      
    } catch (error) {
      console.error('Erro ao enviar comprovante:', error)
      toast.error(error.response?.data?.detail || 'Erro ao enviar comprovante')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold mb-4">Enviar Comprovante</h3>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Tipo de Comprovante */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tipo de Comprovante
          </label>
          <select
            value={tipoComprovante}
            onChange={(e) => setTipoComprovante(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {Object.entries(TIPO_COMPROVANTE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Upload do Arquivo */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Arquivo do Comprovante
          </label>
          <input
            type="file"
            onChange={handleFileChange}
            accept="image/jpeg,image/png,image/jpg,application/pdf"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Formatos: JPG, PNG, PDF (máx. 10MB)
          </p>
        </div>

        {/* Preview */}
        {preview && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Preview
            </label>
            <div className="border border-gray-300 rounded-md p-2">
              {file.type === 'application/pdf' ? (
                <div className="flex items-center justify-center h-32 bg-gray-100">
                  <span className="text-gray-500">📄 PDF: {file.name}</span>
                </div>
              ) : (
                <img 
                  src={preview} 
                  alt="Preview" 
                  className="max-w-full h-32 object-contain mx-auto"
                />
              )}
            </div>
          </div>
        )}

        {/* Valor Confirmado */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Valor Confirmado (Opcional)
          </label>
          <input
            type="number"
            step="0.01"
            value={valorConfirmado}
            onChange={(e) => setValorConfirmado(e.target.value)}
            placeholder="0,00"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Observações */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Observações
          </label>
          <textarea
            value={observacoes}
            onChange={(e) => setObservacoes(e.target.value)}
            placeholder="Adicione observações sobre este pagamento..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Botão de Envio */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Enviando...' : 'Enviar Comprovante'}
        </button>
      </form>
    </div>
  )
}

export default ComprovanteUpload
