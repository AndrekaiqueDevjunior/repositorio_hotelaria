'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '../../lib/api'

export default function VoucherViewPage() {
  const router = useRouter()
  const [codigo, setCodigo] = useState('')
  const [voucher, setVoucher] = useState(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const buscarVoucher = async () => {
    if (!codigo.trim()) {
      alert('Digite o código do voucher')
      return
    }

    try {
      setLoading(true)
      const response = await api.get(`/vouchers/${codigo.toUpperCase()}`)
      
      if (response.data && response.data.data) {
        setVoucher(response.data.data)
      } else {
        alert('Voucher não encontrado')
        setVoucher(null)
      }
    } catch (error) {
      console.error('Erro ao buscar voucher:', error)
      alert('Voucher não encontrado ou erro ao buscar')
      setVoucher(null)
    } finally {
      setLoading(false)
    }
  }

  const baixarPDF = async () => {
    if (!voucher) return
    
    try {
      setDownloading(true)
      
      const response = await api.get(`/vouchers/${voucher.codigo}/pdf`, {
        responseType: 'blob'
      })

      // Criar URL para download
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      
      // Criar link e fazer download
      const link = document.createElement('a')
      link.href = url
      link.download = `voucher_${voucher.codigo}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // Limpar URL
      window.URL.revokeObjectURL(url)
      
      alert('PDF baixado com sucesso!')
    } catch (error) {
      console.error('Erro ao baixar PDF:', error)
      alert('Erro ao baixar PDF')
    } finally {
      setDownloading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'EMITIDO': return 'bg-green-100 text-green-800'
      case 'CHECKIN_REALIZADO': return 'bg-blue-100 text-blue-800'
      case 'FINALIZADO': return 'bg-gray-100 text-gray-800'
      case 'CANCELADO': return 'bg-red-100 text-red-800'
      default: return 'bg-yellow-100 text-yellow-800'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Cabeçalho */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <button 
              onClick={() => router.push('/reservas')}
              className="flex items-center text-gray-600 hover:text-gray-800"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Voltar para Reservas
            </button>
            
            <h1 className="text-2xl font-bold text-gray-800">Consulta de Voucher</h1>
          </div>
          
          {/* Busca */}
          <div className="flex gap-3">
            <input
              type="text"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder="Digite o código do voucher (ex: HR-2024-000001)"
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyPress={(e) => e.key === 'Enter' && buscarVoucher()}
            />
            <button
              onClick={buscarVoucher}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Buscando...' : 'Buscar'}
            </button>
          </div>
        </div>

        {/* Resultado */}
        {voucher && (
          <div className="bg-white rounded-lg shadow-sm border p-8">
            {/* Cabeçalho do Hotel */}
            <div className="text-center mb-8">
              <div className="flex items-center justify-center mb-4">
                <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-2xl font-bold">🏨</span>
                </div>
              </div>
              <h2 className="text-3xl font-bold text-blue-900 mb-2">Hotel Real</h2>
              <p className="text-gray-600">Cabo Frio - Sistema de Gestão</p>
            </div>

            {/* Código do Voucher - CENTRALIZADO E DESTACADO */}
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 border-4 border-blue-300 rounded-xl p-8 text-center mb-8">
              <p className="text-lg text-blue-800 font-semibold mb-3">VOUCHER DE CONFIRMAÇÃO</p>
              <div className="bg-white rounded-lg p-6 shadow-inner">
                <p className="text-5xl font-bold text-blue-900 tracking-wider">{voucher.codigo}</p>
              </div>
              <p className="text-sm text-blue-700 mt-4">
                Emitido em: {new Date(voucher.dataEmissao).toLocaleString('pt-BR')}
              </p>
            </div>

            {/* Botões de Ação */}
            <div className="flex justify-center gap-3 pt-4">
              <button
                onClick={() => window.open(`/consulta-unificada?codigo=${voucher.codigo}`, '_blank')}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
              >
                🔍 Consulta Unificada
              </button>
              <button
                onClick={() => window.open(`/consulta-unificada?codigo=${voucher.reserva.codigoReserva}`, '_blank')}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
              >
                📋 Ver Reserva
              </button>
              <button
                onClick={baixarPDF}
                disabled={downloading}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
              >
                {downloading ? 'Baixando...' : 'Baixar PDF'}
              </button>
            </div>

            {/* Status */}
            <div className="flex justify-center mb-8">
              <span className={`px-6 py-3 rounded-full text-lg font-bold ${getStatusColor(voucher.status)}`}>
                {voucher.status.replace('_', ' ')}
              </span>
            </div>

            {/* Dados da Reserva */}
            <div className="mb-8">
              <h3 className="text-xl font-bold text-gray-800 mb-4 border-b pb-2">DADOS DA RESERVA</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm text-gray-600 mb-1">Código Reserva</p>
                  <p className="font-semibold text-gray-800">{voucher.reserva.codigoReserva}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm text-gray-600 mb-1">Hóspede</p>
                  <p className="font-semibold text-gray-800">{voucher.reserva.clienteNome}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm text-gray-600 mb-1">Tipo Suíte</p>
                  <p className="font-semibold text-gray-800">{voucher.reserva.tipoSuite}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm text-gray-600 mb-1">Quarto</p>
                  <p className="font-semibold text-gray-800">{voucher.reserva.quartoNumero}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm text-gray-600 mb-1">Check-in</p>
                  <p className="font-semibold text-gray-800">
                    {new Date(voucher.reserva.checkinPrevisto).toLocaleString('pt-BR')}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm text-gray-600 mb-1">Check-out</p>
                  <p className="font-semibold text-gray-800">
                    {new Date(voucher.reserva.checkoutPrevisto).toLocaleString('pt-BR')}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded md:col-span-2">
                  <p className="text-sm text-gray-600 mb-1">Valor Total</p>
                  <p className="font-semibold text-green-600 text-xl">
                    R$ {Number(voucher.reserva.valorTotal || 0).toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            {/* Dados do Hóspede */}
            {voucher.reserva.cliente && (
              <div className="mb-8">
                <h3 className="text-xl font-bold text-gray-800 mb-4 border-b pb-2">DADOS COMPLETOS DO HÓSPEDE</h3>
                <div className="bg-blue-50 p-6 rounded-lg">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Nome Completo</p>
                      <p className="font-medium text-gray-800">{voucher.reserva.cliente.nomeCompleto}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Email</p>
                      <p className="font-medium text-gray-800">{voucher.reserva.cliente.email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Telefone</p>
                      <p className="font-medium text-gray-800">{voucher.reserva.cliente.telefone}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Controle de Acesso */}
            <div className="mb-8">
              <h3 className="text-xl font-bold text-gray-800 mb-4 border-b pb-2">CONTROLE DE ACESSO</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-green-50 p-4 rounded">
                  <p className="text-sm text-gray-600 mb-1">Emissão</p>
                  <p className="font-semibold text-green-700">
                    {new Date(voucher.dataEmissao).toLocaleString('pt-BR')}
                  </p>
                </div>
                <div className="bg-blue-50 p-4 rounded">
                  <p className="text-sm text-gray-600 mb-1">Check-in</p>
                  <p className="font-semibold text-blue-700">
                    {voucher.checkinRealizadoEm 
                      ? `✓ ${new Date(voucher.checkinRealizadoEm).toLocaleString('pt-BR')}`
                      : '⏳ Aguardando check-in'
                    }
                  </p>
                </div>
                <div className="bg-purple-50 p-4 rounded">
                  <p className="text-sm text-gray-600 mb-1">Check-out</p>
                  <p className="font-semibold text-purple-700">
                    {voucher.checkoutRealizadoEm 
                      ? `✓ ${new Date(voucher.checkoutRealizadoEm).toLocaleString('pt-BR')}`
                      : '⏳ Aguardando check-out'
                    }
                  </p>
                </div>
              </div>
            </div>

            {/* Instruções */}
            <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-6">
              <h4 className="text-lg font-bold text-yellow-800 mb-3">📋 INSTRUÇÕES IMPORTANTES</h4>
              <ul className="space-y-2 text-yellow-700">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Este voucher é válido apenas para a reserva identificada acima</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Apresente este voucher no momento do check-in</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>O código do voucher deve ser informado na recepção</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Documentação necessária: RG/CPF e comprovante de pagamento</span>
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
