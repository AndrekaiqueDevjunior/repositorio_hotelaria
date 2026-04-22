'use client'
import { useState } from 'react'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import Link from 'next/link'
import { api } from '../../lib/api'

export default function Consultar() {
  const [tab, setTab] = useState('reserva') // reserva ou pontos
  const [loading, setLoading] = useState(false)
  
  // Consulta de reserva
  const [codigoReserva, setCodigoReserva] = useState('')
  const [reservaEncontrada, setReservaEncontrada] = useState(null)
  
  // Consulta de pontos
  const [cpf, setCpf] = useState('')
  const [pontosEncontrados, setPontosEncontrados] = useState(null)
  
  // Buscar reserva
  const buscarReserva = async () => {
    if (!codigoReserva.trim()) {
      toast.warning('Digite o código da reserva')
      return
    }
    
    setLoading(true)
    setReservaEncontrada(null)
    
    try {
      // Tentar diferentes formatos de código
      const codigosParaTestar = [
        codigoReserva.trim(),
        codigoReserva.trim().replace('WEB-', 'RCF-'),
        codigoReserva.trim().replace('RCF-', 'WEB-')
      ]
      
      let reservaEncontrada = null
      let ultimoErro = null
      
      for (const codigo of codigosParaTestar) {
        try {
          const res = await api.get(`/public/reservas/${codigo}`)
          const data = res.data
          
          if (data.success) {
            reservaEncontrada = data.reserva
            setReservaEncontrada(data.reserva)
            toast.success('Reserva encontrada!')
            break
          } else {
            ultimoErro = data.detail || 'Reserva não encontrada'
          }
        } catch (error) {
          ultimoErro = 'Erro ao buscar reserva'
        }
      }
      
      if (!reservaEncontrada) {
        toast.error(ultimoErro || 'Reserva não encontrada')
      }
    } catch (error) {
      console.error('Erro:', error)
      toast.error('Erro ao buscar reserva')
    } finally {
      setLoading(false)
    }
  }
  
  // Buscar pontos
  const buscarPontos = async () => {
    const cpfLimpo = cpf.replace(/\D/g, '')
    if (cpfLimpo.length !== 11) {
      toast.warning('Digite um CPF válido')
      return
    }
    
    setLoading(true)
    setPontosEncontrados(null)
    
    try {
      const res = await api.get(`/public/pontos/${cpfLimpo}`)
      const data = res.data
      
      if (data.success) {
        setPontosEncontrados(data)
        toast.success('Pontos encontrados!')
      } else {
        toast.error(data.detail || 'Cliente não encontrado')
      }
    } catch (error) {
      console.error('Erro:', error)
      toast.error('Erro ao buscar pontos')
    } finally {
      setLoading(false)
    }
  }
  
  // Formatar CPF
  const formatCPF = (value) => {
    const numbers = value.replace(/\D/g, '').substring(0, 11)
    if (numbers.length <= 3) return numbers
    if (numbers.length <= 6) return `${numbers.slice(0, 3)}.${numbers.slice(3)}`
    if (numbers.length <= 9) return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`
    return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9)}`
  }
  
  // Status badge
  const getStatusBadge = (status) => {
    const configs = {
      'PENDENTE': { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pendente' },
      'HOSPEDADO': { bg: 'bg-green-100', text: 'text-green-800', label: 'Hospedado' },
      'CHECKED_OUT': { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Finalizado' },
      'CANCELADO': { bg: 'bg-red-100', text: 'text-red-800', label: 'Cancelado' }
    }
    const config = configs[status] || { bg: 'bg-gray-100', text: 'text-gray-800', label: status }
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-800 to-blue-900">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/reservar" className="flex items-center gap-3">
            <span className="text-4xl">🏨</span>
            <div>
              <h1 className="text-2xl font-bold text-white">Hotel Real</h1>
              <p className="text-yellow-400 text-sm">Cabo Frio</p>
            </div>
          </Link>
          <Link
            href="/reservar"
            className="px-4 py-2 bg-yellow-400 text-blue-900 rounded-lg font-medium hover:bg-yellow-300 transition-all"
          >
            🏨 Fazer Reserva
          </Link>
        </div>
      </header>
      
      <main className="max-w-2xl mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b">
            <button
              onClick={() => { setTab('reserva'); setReservaEncontrada(null) }}
              className={`flex-1 py-4 font-medium transition-all ${
                tab === 'reserva' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              📋 Consultar Reserva
            </button>
            <button
              onClick={() => { setTab('pontos'); setPontosEncontrados(null) }}
              className={`flex-1 py-4 font-medium transition-all ${
                tab === 'pontos' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              🎯 Consultar Pontos
            </button>
          </div>
          
          {/* Consulta de Reserva */}
          {tab === 'reserva' && (
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Consultar sua Reserva</h2>
              <p className="text-gray-600 mb-6">Digite o código da reserva que você recebeu por email.</p>
              
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="Ex: WEB-20241217-000001 ou RCF-202512-000001"
                  value={codigoReserva}
                  onChange={(e) => setCodigoReserva(e.target.value.toUpperCase())}
                  className="flex-1 p-4 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:outline-none text-lg font-mono"
                />
                <button
                  onClick={buscarReserva}
                  disabled={loading}
                  className="px-6 py-4 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-all disabled:opacity-50"
                >
                  {loading ? '⏳' : '🔍'} Buscar
                </button>
              </div>
              
              {/* Resultado da reserva */}
              {reservaEncontrada && (
                <div className="mt-8 border-t pt-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-bold text-gray-800">Detalhes da Reserva</h3>
                    {getStatusBadge(reservaEncontrada.status)}
                  </div>
                  
                  <div className="bg-blue-50 p-4 rounded-xl mb-4">
                    <p className="text-sm text-gray-600">Código</p>
                    <p className="text-xl font-bold text-blue-600 font-mono">{reservaEncontrada.codigo}</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-500">Hóspede</p>
                      <p className="font-medium">{reservaEncontrada.cliente_nome}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-500">Acomodação</p>
                      <p className="font-medium">{reservaEncontrada.tipo_suite} - Quarto {reservaEncontrada.quarto_numero}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-500">Check-in Previsto</p>
                      <p className="font-medium">{new Date(reservaEncontrada.checkin_previsto).toLocaleDateString('pt-BR')}</p>
                      <p className="text-xs text-gray-400">às 12:00</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-500">Check-out Previsto</p>
                      <p className="font-medium">{new Date(reservaEncontrada.checkout_previsto).toLocaleDateString('pt-BR')}</p>
                      <p className="text-xs text-gray-400">até 11:00</p>
                    </div>
                  </div>
                  
                  {/* Financeiro */}
                  <div className="mt-4 bg-green-50 p-4 rounded-xl">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-600">Diárias</span>
                      <span className="font-medium">{reservaEncontrada.num_diarias} x R$ {reservaEncontrada.valor_diaria.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center pt-2 border-t">
                      <span className="text-gray-700 font-medium">Valor Total</span>
                      <span className="font-bold text-lg text-green-600">R$ {reservaEncontrada.valor_total.toFixed(2)}</span>
                    </div>
                  </div>
                  
                  
                  {/* Instruções */}
                  <div className="mt-4 bg-blue-50 p-4 rounded-lg text-sm">
                    <p className="font-medium text-blue-900 mb-2">📋 Informações Importantes:</p>
                    <ul className="space-y-1 text-blue-800">
                      <li>• Check-in: 12:00 | Check-out: 11:00</li>
                      <li>• Apresente documento de identidade e CPF</li>
                      <li>• Contato: (22) 2648-5900</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Consulta de Pontos */}
          {tab === 'pontos' && (
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Consultar seus Pontos</h2>
              <p className="text-gray-600 mb-6">Digite seu CPF para verificar seu saldo de pontos.</p>
              
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="000.000.000-00"
                  value={cpf}
                  onChange={(e) => setCpf(formatCPF(e.target.value))}
                  className="flex-1 p-4 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:outline-none text-lg"
                  maxLength={14}
                />
                <button
                  onClick={buscarPontos}
                  disabled={loading}
                  className="px-6 py-4 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-all disabled:opacity-50"
                >
                  {loading ? '⏳' : '🔍'} Buscar
                </button>
              </div>
              
              {/* Resultado dos pontos */}
              {pontosEncontrados && (
                <div className="mt-8 border-t pt-6">
                  <div className="text-center mb-6">
                    <p className="text-gray-600">Olá,</p>
                    <p className="text-xl font-bold text-gray-800">{pontosEncontrados.cliente.nome}</p>
                    <p className="text-sm text-gray-500">CPF: {pontosEncontrados.cliente.documento}</p>
                  </div>
                  
                  {/* Saldo de pontos */}
                  <div className="bg-gradient-to-r from-yellow-400 to-yellow-500 p-6 rounded-xl text-center">
                    <p className="text-yellow-900">Seu saldo de pontos</p>
                    <p className="text-5xl font-bold text-yellow-900">{pontosEncontrados.pontos.saldo}</p>
                    <p className="text-yellow-800 text-sm mt-1">pontos</p>
                  </div>
                  
                  {/* Histórico recente */}
                  {pontosEncontrados.pontos.historico_recente.length > 0 && (
                    <div className="mt-6">
                      <h4 className="font-medium text-gray-700 mb-3">Últimas movimentações</h4>
                      <div className="space-y-2">
                        {pontosEncontrados.pontos.historico_recente.map((item, i) => (
                          <div key={i} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <div>
                              <p className="font-medium text-gray-800">{item.origem}</p>
                              <p className="text-sm text-gray-500">{item.data}</p>
                            </div>
                            <span className={`font-bold ${item.tipo === 'GANHO' ? 'text-green-600' : 'text-red-600'}`}>
                              {item.tipo === 'GANHO' ? '+' : '-'}{item.pontos}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Info sobre pontos */}
                  <div className="mt-6 bg-blue-50 p-4 rounded-lg text-sm text-blue-800">
                    <p className="font-medium mb-2">💡 Como ganhar mais pontos?</p>
                    <ul className="space-y-1">
                      <li>• Hospede-se conosco e ganhe 10 pontos por diária</li>
                      <li>• Suítes Master: 15 pontos por diária</li>
                      <li>• Suítes Real: 20 pontos por diária</li>
                      <li>• Troque seus pontos por descontos e upgrades!</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Links rápidos */}
        <div className="mt-8 text-center">
          <Link
            href="/reservar"
            className="inline-block px-8 py-3 bg-yellow-400 text-blue-900 rounded-lg font-bold hover:bg-yellow-300 transition-all"
          >
            🏨 Fazer Nova Reserva
          </Link>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="bg-blue-950 text-white/80 py-8 mt-12">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <p className="text-sm">Hotel Real Cabo Frio</p>
          <p className="text-sm mt-1">📞 (22) 2648-5900 | 📧 contato@hotelrealcabofrio.com.br</p>
        </div>
      </footer>
      
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="colored"
      />
    </div>
  )
}

