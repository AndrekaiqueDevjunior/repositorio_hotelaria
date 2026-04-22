'use client'
import { useState, useEffect } from 'react'
import { api } from '../../lib/api'
import Link from 'next/link'

export default function PortalCliente() {
  const [cpf, setCpf] = useState('')
  const [loading, setLoading] = useState(false)
  const [clienteData, setClienteData] = useState(null)
  const [premios, setPremios] = useState([])
  const [loadingPremios, setLoadingPremios] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [resgateModal, setResgateModal] = useState(false)
  const [premioSelecionado, setPremioSelecionado] = useState(null)

  // Prêmios específicos do Hotel Real Cabo Frio
  const PREMIOS_ESPECIFICOS = [
    {
      id: 1,
      nome: "1 diária suíte luxo",
      descricao: "Diária gratuita na suíte luxo para 2 pessoas",
      categoria: "DIARIA",
      preco_em_rp: 20,
      imagem_url: "/images/premio-diaria-luxo.jpg",
      estoque: 50
    },
    {
      id: 2,
      nome: "Cafeteira",
      descricao: "Cafeteira elétrica de alta qualidade",
      categoria: "ELETRONICO",
      preco_em_rp: 35,
      imagem_url: "/images/premio-cafeteira.jpg",
      estoque: 25
    },
    {
      id: 3,
      nome: "Luminária carregador",
      descricao: "Luminária com porta USB para carregamento",
      categoria: "ELETRONICO",
      preco_em_rp: 25,
      imagem_url: "/images/premio-luminaria.jpg",
      estoque: 30
    },
    {
      id: 4,
      nome: "iPhone 16",
      descricao: "iPhone 16 128GB - Última geração",
      categoria: "ELETRONICO",
      preco_em_rp: 100,
      imagem_url: "/images/premio-iphone.jpg",
      estoque: 5
    }
  ]

  const formatarCPF = (valor) => {
    const numeros = valor.replace(/\D/g, '')
    if (numeros.length <= 11) {
      return numeros
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})$/, '$1-$2')
    }
    return numeros
      .replace(/(\d{2})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1/$2')
      .replace(/(\d{4})(\d{1,2})$/, '$1-$2')
  }

  const handleCpfChange = (e) => {
    const formatted = formatarCPF(e.target.value)
    setCpf(formatted)
  }

  const consultarPontos = async (e) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')
    
    const cpfLimpo = cpf.replace(/\D/g, '')
    
    if (!cpfLimpo || (cpfLimpo.length !== 11 && cpfLimpo.length !== 14)) {
      setError('CPF/CNPJ inválido. Digite 11 dígitos (CPF) ou 14 dígitos (CNPJ).')
      return
    }

    try {
      setLoading(true)
      const res = await api.get(`/pontos/consultar/${cpfLimpo}`)
      setClienteData(res.data)
      setSuccessMessage('Dados carregados com sucesso!')
    } catch (error) {
      console.error('Erro ao consultar pontos:', error)
      setError(
        error.response?.data?.detail || 
        'Erro ao consultar pontos. Verifique o CPF/CNPJ e tente novamente.'
      )
    } finally {
      setLoading(false)
    }
  }

  const carregarPremios = async () => {
    try {
      setLoadingPremios(true)
      const res = await api.get('/premios')
      setPremios(res.data)
    } catch (error) {
      console.error('Erro ao carregar prêmios:', error)
      // Fallback para prêmios específicos
      setPremios(PREMIOS_ESPECIFICOS)
    } finally {
      setLoadingPremios(false)
    }
  }

  const resgatarPremio = async (premio) => {
    if (!clienteData) {
      setError('Consulte seus pontos primeiro!')
      return
    }

    if (clienteData.saldo < premio.preco_em_rp) {
      setError(`Saldo insuficiente! Você tem ${clienteData.saldo} RP, mas precisa de ${premio.preco_em_rp} RP.`)
      return
    }

    try {
      setLoading(true)
      const res = await api.post('/premios/resgatar-publico', {
        premio_id: premio.id,
        cliente_documento: cpf.replace(/\D/g, ''),
        observacoes: 'Resgate via portal do cliente'
      })

      setSuccessMessage(`🎉 Prêmio "${premio.nome}" resgatado com sucesso!`)
      setResgateModal(false)
      
      // Atualizar saldo do cliente
      setClienteData(prev => ({
        ...prev,
        saldo: prev.saldo - premio.preco_em_rp
      }))

      // Atualizar estoque do prêmio
      setPremios(prev => prev.map(p => 
        p.id === premio.id 
          ? { ...p, estoque: p.estoque - 1 }
          : p
      ))

    } catch (error) {
      console.error('Erro ao resgatar prêmio:', error)
      setError(
        error.response?.data?.detail || 
        'Erro ao resgatar prêmio. Tente novamente.'
      )
    } finally {
      setLoading(false)
    }
  }

  const abrirModalResgate = (premio) => {
    setPremioSelecionado(premio)
    setResgateModal(true)
    setError('')
  }

  const fecharModalResgate = () => {
    setResgateModal(false)
    setPremioSelecionado(null)
  }

  useEffect(() => {
    carregarPremios()
  }, [])

  const getCategoriaIcon = (categoria) => {
    switch (categoria) {
      case 'DIARIA': return '🏨'
      case 'ELETRONICO': return '📱'
      case 'SERVICO': return '🛠️'
      case 'VALE': return '🎫'
      default: return '🎁'
    }
  }

  const getCategoriaColor = (categoria) => {
    switch (categoria) {
      case 'DIARIA': return 'from-blue-500 to-cyan-500'
      case 'ELETRONICO': return 'from-purple-500 to-pink-500'
      case 'SERVICO': return 'from-green-500 to-emerald-500'
      case 'VALE': return 'from-yellow-500 to-orange-500'
      default: return 'from-gray-500 to-gray-600'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 dark:from-gray-900 dark:via-purple-900 dark:to-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-pink-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white text-lg font-bold">🏨</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Hotel Real Cabo Frio
                </h1>
                <p className="text-sm text-purple-600 dark:text-purple-400">
                  Portal do Cliente - Pontos RP
                </p>
              </div>
            </div>
            <Link
              href="/login"
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
            >
              Área Restrita
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="text-6xl mb-4">💎</div>
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Portal do Cliente
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Consulte seus pontos RP e resgate prêmios exclusivos
          </p>
        </div>

        {/* Formulário de Consulta */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 mb-8">
          <form onSubmit={consultarPontos} className="space-y-6">
            <div>
              <label htmlFor="cpf" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                CPF ou CNPJ
              </label>
              <input
                type="text"
                id="cpf"
                value={cpf}
                onChange={handleCpfChange}
                placeholder="000.000.000-00"
                maxLength={18}
                className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-purple-500 focus:ring-purple-500 focus:ring-2 focus:ring-opacity-50 dark:bg-gray-700 dark:text-white text-lg"
                disabled={loading}
              />
            </div>

            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">⚠️</span>
                  <p className="text-red-800 dark:text-red-200">{error}</p>
                </div>
              </div>
            )}

            {successMessage && (
              <div className="bg-green-50 dark:bg-green-900/20 border-2 border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">✅</span>
                  <p className="text-green-800 dark:text-green-200">{successMessage}</p>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !cpf}
              className="w-full py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold text-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin mr-3" />
                  Consultando...
                </span>
              ) : (
                '🔍 Consultar Meus Pontos'
              )}
            </button>
          </form>
        </div>

        {/* Dados do Cliente */}
        {clienteData && (
          <div className="space-y-8 animate-fade-in">
            {/* Card de Saldo */}
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-2xl shadow-xl p-8">
              <div className="text-center">
                <div className="text-5xl mb-4">👤</div>
                <h3 className="text-2xl font-bold mb-2">{clienteData.cliente.nome}</h3>
                <p className="text-purple-100 mb-6">CPF/CNPJ: {formatarCPF(clienteData.cliente.documento)}</p>
                
                <div className="bg-white/20 backdrop-blur-sm rounded-xl p-6">
                  <p className="text-sm uppercase tracking-wide mb-2 opacity-90">Seu Saldo RP</p>
                  <p className="text-6xl font-bold">{clienteData.saldo}</p>
                  <p className="text-xl mt-2">pontos RP</p>
                </div>
              </div>
            </div>

            {/* Catálogo de Prêmios */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
                <span className="text-3xl mr-3">🎁</span>
                Catálogo de Prêmios
              </h3>
              
              {loadingPremios ? (
                <div className="text-center py-12">
                  <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-gray-600 dark:text-gray-400">Carregando prêmios...</p>
                </div>
              ) : premios.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {premios.map((premio) => (
                    <div key={premio.id} className="bg-gray-50 dark:bg-gray-700 rounded-xl overflow-hidden hover:shadow-lg transition-shadow">
                      {/* Imagem do Prêmio */}
                      <div className={`h-32 bg-gradient-to-br ${getCategoriaColor(premio.categoria)} flex items-center justify-center`}>
                        <span className="text-5xl">{getCategoriaIcon(premio.categoria)}</span>
                      </div>
                      
                      {/* Informações */}
                      <div className="p-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white mb-2">{premio.nome}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                          {premio.descricao || 'Prêmio exclusivo do Hotel Real Cabo Frio'}
                        </p>
                        
                        {/* Estoque */}
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            Estoque: {premio.estoque}
                          </span>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            premio.estoque > 10 
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                              : premio.estoque > 0
                              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                              : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                          }`}>
                            {premio.estoque > 10 ? 'Disponível' : premio.estoque > 0 ? 'Últimas unidades' : 'Esgotado'}
                          </span>
                        </div>
                        
                        {/* Preço e Botão */}
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                              {premio.preco_em_rp}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">pontos RP</p>
                          </div>
                          <button
                            onClick={() => abrirModalResgate(premio)}
                            disabled={premio.estoque <= 0 || clienteData.saldo < premio.preco_em_rp}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                              premio.estoque <= 0 || clienteData.saldo < premio.preco_em_rp
                                ? 'bg-gray-200 text-gray-400 cursor-not-allowed dark:bg-gray-600 dark:text-gray-500'
                                : 'bg-purple-600 text-white hover:bg-purple-700'
                            }`}
                          >
                            {premio.estoque <= 0 ? 'Esgotado' : 
                             clienteData.saldo < premio.preco_em_rp ? 'Saldo insuficiente' : 
                             'Resgatar'}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  <div className="text-6xl mb-4">📭</div>
                  <p>Nenhum prêmio disponível no momento</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Modal de Resgate */}
        {resgateModal && premioSelecionado && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Confirmar Resgate
              </h3>
              
              <div className="mb-6">
                <div className={`h-20 bg-gradient-to-br ${getCategoriaColor(premioSelecionado.categoria)} rounded-lg flex items-center justify-center mb-4`}>
                  <span className="text-4xl">{getCategoriaIcon(premioSelecionado.categoria)}</span>
                </div>
                
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">{premioSelecionado.nome}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {premioSelecionado.descricao || 'Prêmio exclusivo do Hotel Real Cabo Frio'}
                </p>
                
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700 dark:text-gray-300">Custo em pontos:</span>
                    <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {premioSelecionado.preco_em_rp} RP
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-gray-700 dark:text-gray-300">Seu saldo atual:</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {clienteData?.saldo || 0} RP
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-purple-200 dark:border-purple-700">
                    <span className="text-gray-700 dark:text-gray-300">Saldo após resgate:</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {(clienteData?.saldo || 0) - premioSelecionado.preco_em_rp} RP
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={fecharModalResgate}
                  className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  Cancelar
                </button>
                <button
                  onClick={() => resgatarPremio(premioSelecionado)}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      Processando...
                    </span>
                  ) : (
                    'Confirmar Resgate'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Informações do Programa */}
        {!clienteData && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 mt-8">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center">
              💎 Como Funcionam os Pontos RP
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="text-center p-6 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
                <div className="text-4xl mb-3">🏨</div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Suíte Luxo</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  2 diárias R$ 600-700 = 3 RP
                </p>
              </div>
              <div className="text-center p-6 bg-pink-50 dark:bg-pink-900/20 rounded-xl">
                <div className="text-4xl mb-3">🛏️</div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Suíte Dupla</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  2 diárias R$ 1200-1400 = 4 RP
                </p>
              </div>
              <div className="text-center p-6 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                <div className="text-4xl mb-3">👑</div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Suíte Master</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  2 diárias R$ 800-900 = 4 RP
                </p>
              </div>
              <div className="text-center p-6 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl">
                <div className="text-4xl mb-3">👑</div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Suíte Real</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  2 diárias R$ 1000-1200 = 5 RP
                </p>
              </div>
            </div>
            
            <div className="mt-8 text-center">
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">🎁 Prêmios Disponíveis</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                  <span className="text-2xl">🏨</span>
                  <p className="text-sm font-medium mt-1">1 diária luxo</p>
                  <p className="text-xs text-purple-600 dark:text-purple-400">20 RP</p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                  <span className="text-2xl">☕</span>
                  <p className="text-sm font-medium mt-1">Cafeteira</p>
                  <p className="text-xs text-purple-600 dark:text-purple-400">35 RP</p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                  <span className="text-2xl">💡</span>
                  <p className="text-sm font-medium mt-1">Luminária</p>
                  <p className="text-xs text-purple-600 dark:text-purple-400">25 RP</p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                  <span className="text-2xl">📱</span>
                  <p className="text-sm font-medium mt-1">iPhone 16</p>
                  <p className="text-xs text-purple-600 dark:text-purple-400">100 RP</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-gray-600 dark:text-gray-400 text-sm">
            © 2026 Hotel Real Cabo Frio - Programa de Fidelidade RP
          </p>
        </div>
      </div>
    </div>
  )
}
