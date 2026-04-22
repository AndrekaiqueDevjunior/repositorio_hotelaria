'use client'
import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { api } from '../../../lib/api'
import { toast } from 'react-toastify'

export default function VoucherPage() {
  const params = useParams()
  const router = useRouter()
  const codigo = params.codigo
  const [voucher, setVoucher] = useState(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    if (codigo) {
      carregarVoucher()
    }
  }, [codigo])

  const carregarVoucher = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/vouchers/${codigo}`)
      
      if (response.data && response.data.data) {
        setVoucher(response.data.data)
      } else {
        toast.error('Voucher não encontrado')
        router.push('/reservas')
      }
    } catch (error) {
      console.error('Erro ao carregar voucher:', error)
      toast.error('Erro ao carregar voucher')
      router.push('/reservas')
    } finally {
      setLoading(false)
    }
  }

  const baixarPDF = async () => {
    try {
      setDownloading(true)
      
      const response = await api.get(`/vouchers/${codigo}/pdf`, {
        responseType: 'blob'
      })

      // Criar URL para download
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      
      // Criar link e fazer download
      const link = document.createElement('a')
      link.href = url
      link.download = `voucher_${codigo}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // Limpar URL
      window.URL.revokeObjectURL(url)
      
      toast.success('PDF baixado com sucesso!')
    } catch (error) {
      console.error('Erro ao baixar PDF:', error)
      toast.error('Erro ao baixar PDF')
    } finally {
      setDownloading(false)
    }
  }

  const imprimirPDF = async () => {
    try {
      setDownloading(true)
      
      const response = await api.get(`/vouchers/${codigo}/pdf`, {
        responseType: 'blob'
      })

      // Criar URL para impressão
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      
      // Abrir em nova janela para impressão
      const printWindow = window.open(url, '_blank')
      
      if (printWindow) {
        printWindow.onload = () => {
          printWindow.print()
        }
      } else {
        toast.error('Não foi possível abrir janela de impressão')
      }
      
      toast.success('Preparando impressão...')
    } catch (error) {
      console.error('Erro ao imprimir PDF:', error)
      toast.error('Erro ao imprimir PDF')
    } finally {
      setDownloading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'EMITIDO': return 'bg-green-100 text-green-800 border-green-300'
      case 'CHECKIN_REALIZADO': return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'FINALIZADO': return 'bg-gray-100 text-gray-800 border-gray-300'
      case 'CANCELADO': return 'bg-red-100 text-red-800 border-red-300'
      default: return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando voucher...</p>
        </div>
      </div>
    )
  }

  if (!voucher) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Voucher não encontrado</p>
          <button 
            onClick={() => router.push('/reservas')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Voltar para Reservas
          </button>
        </div>
      </div>
    )
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
            
            <div className="flex space-x-3">
              <button
                onClick={baixarPDF}
                disabled={downloading}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {downloading ? 'Baixando...' : 'Baixar PDF'}
              </button>
              
              <button
                onClick={imprimirPDF}
                disabled={downloading}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                {downloading ? 'Preparando...' : 'Imprimir'}
              </button>
            </div>
          </div>
          
          <h1 className="text-2xl font-bold text-gray-800">Voucher de Reserva</h1>
        </div>

        {/* Voucher Principal */}
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
            <p className="text-sm text-gray-500 mt-2">📍 Av. do Mar, 1234 - Cabo Frio, RJ</p>
            <p className="text-sm text-gray-500">📞 (22) 1234-5678 | 📧 contato@hotelreal.com.br</p>
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

          {/* Status */}
          <div className="flex justify-center mb-8">
            <span className={`px-6 py-3 rounded-full text-lg font-bold border-2 ${getStatusColor(voucher.status)}`}>
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
      </div>
    </div>
  )
}
