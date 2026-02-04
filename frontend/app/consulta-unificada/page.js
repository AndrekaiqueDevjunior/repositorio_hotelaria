'use client'
import { useState, useEffect } from 'react'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import Link from 'next/link'
import { api } from '../../lib/api'

export default function ConsultaUnificada() {
  const [abaAtiva, setAbaAtiva] = useState('codigo') // codigo ou documento
  const [loading, setLoading] = useState(false)
  
  // Estado para consulta por código
  const [codigo, setCodigo] = useState('')
  const [resultado, setResultado] = useState(null)
  const [sugestoes, setSugestoes] = useState([])
  
  // Estado para consulta por documento
  const [documento, setDocumento] = useState('')
  const [resultadoDocumento, setResultadoDocumento] = useState(null)
  
  // Estado para ajuda
  const [formatos, setFormatos] = useState(null)

  useEffect(() => {
    carregarFormatos()
  }, [])

  const carregarFormatos = async () => {
    try {
      const response = await api.get('/public/consulta/ajuda/formatos')
      if (response.data.success) {
        setFormatos(response.data.data)
      }
    } catch (error) {
      console.error('Erro ao carregar formatos:', error)
    }
  }

  const buscarPorCodigo = async () => {
    if (!codigo.trim()) {
      toast.warning('Digite um código para consultar')
      return
    }
    
    setLoading(true)
    setResultado(null)
    setSugestoes([])
    
    try {
      const response = await api.get(`/public/consulta/${codigo.trim()}`)
      
      if (response.data.success && response.data.data) {
        setResultado(response.data.data)
        toast.success('Código encontrado!')
      } else {
        setSugestoes(response.data.sugestoes || [])
        toast.error(response.data.mensagem || 'Código não encontrado')
      }
    } catch (error) {
      console.error('Erro:', error)
      toast.error('Erro ao buscar código')
      setSugestoes(['Tente novamente em alguns instantes'])
    } finally {
      setLoading(false)
    }
  }

  const buscarPorDocumento = async () => {
    const documentoLimpo = documento.replace(/\D/g, '')
    if (documentoLimpo.length !== 11) {
      toast.warning('Digite um CPF válido (11 números)')
      return
    }
    
    setLoading(true)
    setResultadoDocumento(null)
    
    try {
      const response = await api.get(`/public/consulta/documento/${documentoLimpo}`)
      
      if (response.data.success) {
        setResultadoDocumento(response.data.data)
        toast.success(`Encontradas ${response.data.data.total_reservas} reservas!`)
      } else {
        toast.error(response.data.mensagem || 'Nenhuma reserva encontrada')
      }
    } catch (error) {
      console.error('Erro:', error)
      toast.error('Erro ao buscar reservas')
    } finally {
      setLoading(false)
    }
  }

  const formatarCPF = (value) => {
    const numbers = value.replace(/\D/g, '').substring(0, 11)
    if (numbers.length <= 3) return numbers
    if (numbers.length <= 6) return `${numbers.slice(0, 3)}.${numbers.slice(3)}`
    if (numbers.length <= 9) return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`
    return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9)}`
  }

  const getStatusBadge = (status) => {
    const cores = {
      'EMITIDO': 'bg-green-100 text-green-800',
      'CHECKIN_REALIZADO': 'bg-blue-100 text-blue-800',
      'FINALIZADO': 'bg-gray-100 text-gray-800',
      'CANCELADO': 'bg-red-100 text-red-800',
      'CONFIRMADA': 'bg-yellow-100 text-yellow-800',
      'PAGO': 'bg-green-100 text-green-800',
      'PENDENTE': 'bg-orange-100 text-orange-800',
      'CHECKED_OUT': 'bg-purple-100 text-purple-800'
    }
    return cores[status] || 'bg-gray-100 text-gray-800'
  }

  const getTipoIcon = (tipo) => {
    return tipo === 'VOUCHER' ? '🎫' : '📋'
  }

  const baixarPDF = async (codigo) => {
    try {
      const response = await api.get(`/vouchers/${codigo}/pdf`, {
        responseType: 'blob'
      })
      
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      
      const link = document.createElement('a')
      link.href = url
      link.download = `voucher_${codigo}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      window.URL.revokeObjectURL(url)
      toast.success('PDF baixado com sucesso!')
    } catch (error) {
      console.error('Erro ao baixar PDF:', error)
      toast.error('Erro ao baixar PDF')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Cabeçalho */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Consulta Unificada</h1>
              <p className="text-gray-600 mt-1">Busque vouchers e reservas em um único lugar</p>
            </div>
            <Link 
              href="/"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              ← Voltar
            </Link>
          </div>

          {/* Abas */}
          <div className="flex border-b">
            <button
              onClick={() => setAbaAtiva('codigo')}
              className={`px-4 py-2 font-medium ${
                abaAtiva === 'codigo'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              📄 Consultar por Código
            </button>
            <button
              onClick={() => setAbaAtiva('documento')}
              className={`px-4 py-2 font-medium ${
                abaAtiva === 'documento'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              👤 Consultar por CPF
            </button>
            <button
              onClick={() => setAbaAtiva('ajuda')}
              className={`px-4 py-2 font-medium ${
                abaAtiva === 'ajuda'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              ❓ Formatos
            </button>
          </div>
        </div>

        {/* Aba: Consulta por Código */}
        {abaAtiva === 'codigo' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Código do Voucher ou Reserva
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value.toUpperCase())}
                  placeholder="Digite o código (ex: HR-2025-000001 ou UYUN2KLU)"
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && buscarPorCodigo()}
                />
                <button
                  onClick={buscarPorCodigo}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Buscando...' : '🔍 Consultar'}
                </button>
              </div>
            </div>

            {/* Sugestões */}
            {sugestoes.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-yellow-800 mb-2">💡 Sugestões:</h3>
                <ul className="space-y-1 text-yellow-700">
                  {sugestoes.map((sugestao, index) => (
                    <li key={index} className="flex items-start">
                      <span className="mr-2">•</span>
                      <span>{sugestao}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Resultado */}
            {resultado && (
              <div className="space-y-6">
                {/* Cabeçalho do Resultado */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{getTipoIcon(resultado.tipo)}</span>
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900">{resultado.codigo}</h2>
                        <p className="text-sm text-gray-600">Tipo: {resultado.tipo}</p>
                      </div>
                    </div>
                    <span className={`px-4 py-2 rounded-full text-sm font-bold ${getStatusBadge(resultado.status)}`}>
                      {resultado.status.replace('_', ' ')}
                    </span>
                  </div>

                  {/* Links Cruzados */}
                  {resultado.links && (
                    <div className="flex gap-3 mt-4">
                      {resultado.links.pdf_voucher && (
                        <button
                          onClick={() => baixarPDF(resultado.codigo)}
                          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                        >
                          📄 Baixar PDF
                        </button>
                      )}
                      {resultado.links.reserva && (
                        <Link
                          href={`/voucher/view?codigo=${resultado.codigo}`}
                          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                        >
                          👁️ Ver Voucher
                        </Link>
                      )}
                    </div>
                  )}
                </div>

                {/* Informações do Cliente */}
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">👤 Dados do Hóspede</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Nome</p>
                      <p className="font-medium">{resultado.cliente.nome_completo}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Email</p>
                      <p className="font-medium">{resultado.cliente.email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Telefone</p>
                      <p className="font-medium">{resultado.cliente.telefone}</p>
                    </div>
                  </div>
                </div>

                {/* Informações da Reserva */}
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">🏨 Dados da Reserva</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Quarto</p>
                      <p className="font-medium">{resultado.quarto.numero} - {resultado.quarto.tipo_suite}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Diárias</p>
                      <p className="font-medium">{resultado.datas.num_diarias} diárias</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Check-in</p>
                      <p className="font-medium">
                        {new Date(resultado.datas.checkin_previsto).toLocaleString('pt-BR')}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Check-out</p>
                      <p className="font-medium">
                        {new Date(resultado.datas.checkout_previsto).toLocaleString('pt-BR')}
                      </p>
                    </div>
                    <div className="md:col-span-2">
                      <p className="text-sm text-gray-600 mb-1">Valor Total</p>
                      <p className="font-bold text-xl text-green-600">
                        R$ {resultado.valores.valor_total.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Pagamentos */}
                {resultado.pagamentos && resultado.pagamentos.length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">💳 Pagamentos</h3>
                    <div className="space-y-3">
                      {resultado.pagamentos.map((pagamento) => (
                        <div key={pagamento.id} className="border-l-4 border-green-500 pl-4">
                          <div className="flex justify-between items-center">
                            <div>
                              <p className="font-medium">{pagamento.metodo}</p>
                              <p className="text-sm text-gray-600">
                                {new Date(pagamento.data).toLocaleString('pt-BR')}
                              </p>
                            </div>
                            <div className="text-right">
                              <span className={`px-2 py-1 rounded text-xs font-bold ${getStatusBadge(pagamento.status)}`}>
                                {pagamento.status}
                              </span>
                              <p className="font-semibold">R$ {pagamento.valor.toFixed(2)}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Instruções */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-900 mb-3">📋 Instruções para Check-in</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="font-medium text-blue-800">🕐 Horários</p>
                      <p className="text-blue-700">Check-in: {resultado.instrucoes.horario_checkin}</p>
                      <p className="text-blue-700">Check-out: {resultado.instrucoes.horario_checkout}</p>
                    </div>
                    <div>
                      <p className="font-medium text-blue-800">📋 Documentos</p>
                      <p className="text-blue-700">{resultado.instrucoes.documentos}</p>
                    </div>
                    <div className="md:col-span-2">
                      <p className="font-medium text-blue-800">📞 Contato</p>
                      <p className="text-blue-700">{resultado.instrucoes.contato}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Aba: Consulta por Documento */}
        {abaAtiva === 'documento' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                CPF do Hóspede
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={formatCPF(documento)}
                  onChange={(e) => setDocumento(e.target.value)}
                  placeholder="Digite o CPF (ex: 123.456.789-01)"
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  maxLength={14}
                />
                <button
                  onClick={buscarPorDocumento}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Buscando...' : '🔍 Consultar'}
                </button>
              </div>
            </div>

            {/* Resultado Documento */}
            {resultadoDocumento && (
              <div className="space-y-6">
                {/* Dados do Cliente */}
                <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">👤 Cliente</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Nome</p>
                      <p className="font-medium">{resultadoDocumento.cliente.nome_completo}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Email</p>
                      <p className="font-medium">{resultadoDocumento.cliente.email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Telefone</p>
                      <p className="font-medium">{resultadoDocumento.cliente.telefone}</p>
                    </div>
                  </div>
                </div>

                {/* Reservas */}
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    📋 Reservas Encontradas ({resultadoDocumento.total_reservas})
                  </h3>
                  <div className="space-y-4">
                    {resultadoDocumento.reservas.map((reserva) => (
                      <div key={reserva.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <p className="font-semibold text-gray-900">{reserva.codigo_reserva}</p>
                            <p className="text-sm text-gray-600">Quarto {reserva.quarto_numero} - {reserva.tipo_suite}</p>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-bold ${getStatusBadge(reserva.status)}`}>
                            {reserva.status.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-gray-600">Check-in:</p>
                            <p className="font-medium">
                              {new Date(reserva.checkin_previsto).toLocaleDateString('pt-BR')}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">Check-out:</p>
                            <p className="font-medium">
                              {new Date(reserva.checkout_previsto).toLocaleDateString('pt-BR')}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">Valor:</p>
                            <p className="font-medium text-green-600">
                              R$ {(reserva.valor_diaria * reserva.num_diarias).toFixed(2)}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">Diárias:</p>
                            <p className="font-medium">{reserva.num_diarias}</p>
                          </div>
                        </div>
                        {reserva.voucher_relacionado && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-sm text-gray-600 mb-1">Voucher Relacionado:</p>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{reserva.voucher_relacionado.codigo}</span>
                              <span className={`px-2 py-1 rounded text-xs ${getStatusBadge(reserva.voucher_relacionado.status)}`}>
                                {reserva.voucher_relacionado.status}
                              </span>
                              <button
                                onClick={() => {
                                  setCodigo(reserva.voucher_relacionado.codigo)
                                  setAbaAtiva('codigo')
                                }}
                                className="text-blue-600 hover:text-blue-800 text-sm"
                              >
                                Ver voucher →
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Aba: Ajuda */}
        {abaAtiva === 'ajuda' && formatos && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">📖 Formatos Suportados</h2>
            
            <div className="space-y-8">
              {formatos.formatos_suportados.map((formato, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-6">
                  <div className="mb-4">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{formato.tipo === 'VOUCHER' ? '🎫' : '📋'}</span>
                      <h3 className="text-xl font-semibold text-gray-900">{formato.tipo}</h3>
                      <code className="px-3 py-1 bg-gray-100 rounded text-sm">{formato.formato}</code>
                    </div>
                    <p className="text-gray-600 mb-3">{formato.descricao}</p>
                    <div className="bg-gray-50 rounded p-3">
                      <p className="text-sm font-medium text-gray-700 mb-2">Características:</p>
                      <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                        {formato.caracteristicas.map((carac, i) => (
                          <li key={i}>{carac}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="mt-3">
                      <p className="text-sm font-medium text-gray-700 mb-1">Exemplo:</p>
                      <code className="px-3 py-1 bg-blue-100 text-blue-800 rounded">{formato.exemplo}</code>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Dicas Úteis */}
            <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-yellow-800 mb-3">💡 Dicas Úteis</h3>
              <ul className="space-y-2 text-yellow-700">
                {formatos.dicas_uteis.map((dica, index) => (
                  <li key={index} className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>{dica}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Exemplos Reais */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">📝 Exemplos de Uso</h3>
              <div className="space-y-4">
                {formatos.exemplos_reais.map((exemplo, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-gray-900">{exemplo.situacao}</h4>
                      <code className="px-2 py-1 bg-gray-100 rounded text-sm">{exemplo.codigo}</code>
                    </div>
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Onde encontrar:</span> {exemplo.onde_encontrar}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <ToastContainer position="top-right" />
      </div>
    </div>
  )
}
