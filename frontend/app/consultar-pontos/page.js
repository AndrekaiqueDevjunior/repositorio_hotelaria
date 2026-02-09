'use client'
import { useState, useEffect } from 'react'
import { api } from '../../lib/api'
import Link from 'next/link'
import Script from 'next/script'
import WhatsAppButton from '../../components/WhatsAppButton'

const RECAPTCHA_SITE_KEY = process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || ''

async function getRecaptchaToken(action) {
  if (!RECAPTCHA_SITE_KEY) return null
  if (typeof window === 'undefined') return null

  const grecaptcha = window.grecaptcha
  if (!grecaptcha?.ready || !grecaptcha?.execute) return null

  await new Promise((resolve) => {
    try {
      grecaptcha.ready(resolve)
    } catch {
      resolve()
    }
  })

  try {
    return await grecaptcha.execute(RECAPTCHA_SITE_KEY, { action })
  } catch {
    return null
  }
}

// Componente para mostrar catálogo completo de prêmios
function PremiosCatalogo({ saldoAtual, clienteNome, clienteEndereco }) {
  const [premios, setPremios] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadPremios = async () => {
      try {
        const res = await api.get('/premios')
        setPremios(Array.isArray(res.data) ? res.data : [])
      } catch (error) {
        console.error('Erro ao carregar prêmios:', error)
      } finally {
        setLoading(false)
      }
    }
    loadPremios()
  }, [])

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-gray-500 dark:text-gray-400 mt-4">Carregando prêmios...</p>
      </div>
    )
  }

  if (premios.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        <div className="text-6xl mb-4">📦</div>
        <p>Nenhum prêmio disponível no momento</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {premios.map((premio) => {
        const pontosFaltantes = premio.preco_em_pontos - saldoAtual
        const podeResgatar = saldoAtual >= premio.preco_em_pontos
        
        return (
          <div
            key={premio.id}
            className={`rounded-xl overflow-hidden border-2 transition-shadow hover:shadow-lg ${
              podeResgatar
                ? 'bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200 dark:border-green-800'
                : 'bg-gradient-to-br from-gray-50 to-slate-50 dark:from-gray-800/20 dark:to-slate-800/20 border-gray-200 dark:border-gray-700'
            }`}
          >
            {/* Imagem do Prêmio */}
            <div className="relative h-32 sm:h-48 bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30">
              {premio.imagem_url ? (
                <img
                  src={premio.imagem_url}
                  alt={premio.nome}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.style.display = 'none'
                    e.target.nextElementSibling.style.display = 'flex'
                  }}
                />
              ) : null}
              <div 
                className={`${premio.imagem_url ? 'hidden' : 'flex'} absolute inset-0 items-center justify-center text-6xl`}
                style={{ display: premio.imagem_url ? 'none' : 'flex' }}
              >
                {podeResgatar ? '🏆' : '🎁'}
              </div>
              {podeResgatar && (
                <div className="absolute top-2 right-2 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg">
                  ✓ Disponível
                </div>
              )}
            </div>

            {/* Conteúdo */}
            <div className="p-6">
              <h4 className="font-bold text-gray-900 dark:text-white text-lg mb-2 text-center">
                {premio.nome}
              </h4>
              {premio.descricao && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 text-center line-clamp-2">
                  {premio.descricao}
                </p>
              )}
              <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3 text-center mt-4">
                <p className={`text-2xl font-bold ${
                  podeResgatar 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-gray-700 dark:text-gray-300'
                }`}>
                  {premio.preco_em_pontos} pontos
                </p>
                {podeResgatar ? (
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1 font-semibold">
                    ✓ Você pode resgatar!
                  </p>
                ) : (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Faltam {pontosFaltantes} pontos
                  </p>
                )}
              </div>

              {/* Botão WhatsApp */}
              {podeResgatar && (
                <div className="mt-4">
                  <WhatsAppButton
                    clienteNome={clienteNome || 'Cliente'}
                    clienteCPF={formatarCPF(resultado?.cliente?.documento || '')}
                    premioNome={premio.nome}
                    pontosUsados={premio.preco_em_pontos}
                    codigoResgate={`RES-${premio.id}-${Date.now().toString().slice(-6)}`}
                    className="w-full text-sm py-2"
                  />
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default function ConsultarPontos() {
  const [cpf, setCpf] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState('')
  
  // Estados para resgate de prêmios
  const [showResgateModal, setShowResgateModal] = useState(false)
  const [premioSelecionado, setPremioSelecionado] = useState(null)
  const [observacoes, setObservacoes] = useState('')
  const [resgatando, setResgatando] = useState(false)
  const [resgateSuccess, setResgateSuccess] = useState(null)

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

  const handleConsultar = async (e) => {
    e.preventDefault()
    setError('')
    setResultado(null)
    setResgateSuccess(null)
    
    const cpfLimpo = cpf.replace(/\D/g, '')
    
    if (!cpfLimpo || (cpfLimpo.length !== 11 && cpfLimpo.length !== 14)) {
      setError('CPF/CNPJ inválido. Digite 11 dígitos (CPF) ou 14 dígitos (CNPJ).')
      return
    }

    try {
      setLoading(true)
      const recaptchaToken = await getRecaptchaToken('consultar_pontos')
      const res = await api.get(
        `/pontos/consultar/${cpfLimpo}`,
        recaptchaToken
          ? { headers: { 'X-Recaptcha-Token': recaptchaToken, 'X-Recaptcha-Action': 'consultar_pontos' } }
          : undefined
      )
      setResultado(res.data)
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

  const abrirModalResgate = (premio) => {
    setPremioSelecionado(premio)
    setObservacoes('')
    setShowResgateModal(true)
  }

  const fecharModalResgate = () => {
    setShowResgateModal(false)
    setPremioSelecionado(null)
    setObservacoes('')
  }

  const confirmarResgate = async () => {
    if (!premioSelecionado || !resultado?.cliente?.documento) return

    try {
      setResgatando(true)
      const recaptchaToken = await getRecaptchaToken('resgatar_premio_publico')
      const res = await api.post(
        '/premios/resgatar-publico',
        {
          premio_id: premioSelecionado.id,
          cliente_documento: resultado.cliente.documento,
          observacoes: observacoes || null
        },
        recaptchaToken
          ? { headers: { 'X-Recaptcha-Token': recaptchaToken, 'X-Recaptcha-Action': 'resgatar_premio_publico' } }
          : undefined
      )

      setResgateSuccess(res.data)
      setShowResgateModal(false)
      
      // Recarregar dados
      const cpfLimpo = resultado.cliente.documento
      const recaptchaTokenConsulta = await getRecaptchaToken('consultar_premios')
      const resAtualizado = await api.get(
        `/premios/consulta/${cpfLimpo}`,
        recaptchaTokenConsulta
          ? { headers: { 'X-Recaptcha-Token': recaptchaTokenConsulta, 'X-Recaptcha-Action': 'consultar_premios' } }
          : undefined
      )
      setResultado(resAtualizado.data)
    } catch (error) {
      console.error('Erro ao resgatar prêmio:', error)
      alert(error.response?.data?.detail || 'Erro ao resgatar prêmio. Tente novamente.')
    } finally {
      setResgatando(false)
    }
  }

  const getTipoTransacaoColor = (tipo) => {
    switch (tipo) {
      case 'CREDITO':
      case 'GANHO':
        return 'text-green-600 font-bold'
      case 'DEBITO':
      case 'RESGATE':
        return 'text-red-600 font-bold'
      case 'AJUSTE':
      case 'AJUSTE_MANUAL':
        return 'text-blue-600 font-bold'
      case 'ESTORNO':
        return 'text-orange-600 font-bold'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 dark:from-gray-900 dark:via-purple-900 dark:to-gray-900">
      {RECAPTCHA_SITE_KEY ? (
        <Script
          src={`https://www.google.com/recaptcha/api.js?render=${RECAPTCHA_SITE_KEY}`}
          strategy="afterInteractive"
        />
      ) : null}
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
                  Programa de Fidelidade
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
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="text-6xl mb-4">💎</div>
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Consulte Seus Pontos
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Digite seu CPF ou CNPJ para verificar seu saldo de pontos e histórico de transações
          </p>
        </div>

        {/* Formulário de Consulta */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-4 sm:p-8 mb-8">
          <form onSubmit={handleConsultar} className="space-y-6">
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
                className="w-full px-4 py-3 sm:py-4 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-purple-500 focus:ring-purple-500 focus:ring-2 focus:ring-opacity-50 dark:bg-gray-700 dark:text-white text-base sm:text-lg"
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

            <button
              type="submit"
              disabled={loading || !cpf}
              className="w-full py-3 sm:py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold text-base sm:text-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin mr-3" />
                  Consultando...
                </span>
              ) : (
                '🔍 Consultar Pontos'
              )}
            </button>
          </form>
        </div>

        {/* Resultado da Consulta */}
        {resultado && (
          <div className="space-y-6 animate-fade-in">
            {/* Card de Saldo */}
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-2xl shadow-xl p-8">
              <div className="text-center">
                <div className="text-5xl mb-4">👤</div>
                <h3 className="text-2xl font-bold mb-2">{resultado.cliente.nome}</h3>
                <p className="text-purple-100 mb-2">CPF/CNPJ: {formatarCPF(resultado.cliente.documento)}</p>
                
                {/* Badge de Verificação */}
                <div className="inline-flex items-center gap-1 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-semibold mb-6">
                  <span>✓</span>
                  <span>Cliente Verificado</span>
                </div>
                
                <div className="bg-white/20 backdrop-blur-sm rounded-xl p-6">
                  <p className="text-sm uppercase tracking-wide mb-2 opacity-90">Saldo Disponível</p>
                  <p className="text-6xl font-bold">{resultado.saldo_pontos || resultado.saldo || 0}</p>
                  <p className="text-xl mt-2">pontos</p>
                </div>
                
                {/* Aviso Anti-Fraude */}
                <div className="mt-4 bg-yellow-500/20 border border-yellow-300/30 rounded-lg p-3">
                  <p className="text-xs text-yellow-100">
                    🔒 Seus resgates são protegidos e validados pela recepção
                  </p>
                </div>
              </div>
            </div>

            {/* Prêmios - Seção Unificada */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
                <span className="text-3xl mr-3">🎁</span>
                Catálogo de Prêmios
              </h3>
              
              {/* Prêmios Disponíveis */}
              {resultado.premios_disponiveis && resultado.premios_disponiveis.length > 0 && (
                <div className="mb-8">
                  <h4 className="text-lg font-semibold text-green-600 dark:text-green-400 mb-4 flex items-center">
                    <span className="mr-2">✅</span>
                    Você pode resgatar agora
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {resultado.premios_disponiveis.map((premio) => (
                      <div
                        key={premio.id}
                        className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-2 border-green-200 dark:border-green-800 rounded-xl overflow-hidden hover:shadow-lg transition-shadow"
                      >
                        <div className="relative h-32 sm:h-48 bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/30">
                          {premio.imagem_url ? (
                            <img
                              src={premio.imagem_url}
                              alt={premio.nome}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                e.target.style.display = 'none'
                                e.target.nextElementSibling.style.display = 'flex'
                              }}
                            />
                          ) : null}
                          <div 
                            className={`${premio.imagem_url ? 'hidden' : 'flex'} absolute inset-0 items-center justify-center text-6xl`}
                          >
                            🏆
                          </div>
                          <div className="absolute top-2 right-2 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg">
                            ✓ Disponível
                          </div>
                        </div>
                        <div className="p-6">
                          <h4 className="font-bold text-gray-900 dark:text-white text-lg mb-2 text-center">
                            {premio.nome}
                          </h4>
                          {premio.descricao && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 text-center line-clamp-2">
                              {premio.descricao}
                            </p>
                          )}
                          <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3 text-center">
                            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                              {premio.preco_em_pontos} pontos
                            </p>
                            <p className="text-xs text-green-600 dark:text-green-400 mt-1 font-semibold">
                              ✓ Disponível para resgate
                            </p>
                          </div>
                          <div className="mt-4 space-y-2">
                            {/* Validação de Saldo Visível */}
                            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-2 text-center">
                              <p className="text-xs text-green-700 dark:text-green-300">
                                ✓ Saldo suficiente: {resultado?.saldo_pontos || 0} pts
                              </p>
                            </div>
                            <button
                              onClick={() => abrirModalResgate(premio)}
                              className="w-full py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg hover:shadow-xl"
                            >
                              🎁 Resgatar Agora
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Prêmios Próximos */}
              {resultado.premios_proximos && resultado.premios_proximos.length > 0 && (
                <div className="mb-8">
                  <h4 className="text-lg font-semibold text-orange-600 dark:text-orange-400 mb-4 flex items-center">
                    <span className="mr-2">🎯</span>
                    Quase lá! Continue acumulando
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {resultado.premios_proximos.map((premio) => (
                      <div
                        key={premio.id}
                        className="bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border-2 border-yellow-200 dark:border-yellow-800 rounded-xl overflow-hidden"
                      >
                        <div className="relative h-32 sm:h-48 bg-gradient-to-br from-yellow-100 to-orange-100 dark:from-yellow-900/30 dark:to-orange-900/30">
                          {premio.imagem_url ? (
                            <img
                              src={premio.imagem_url}
                              alt={premio.nome}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                e.target.style.display = 'none'
                                e.target.nextElementSibling.style.display = 'flex'
                              }}
                            />
                          ) : null}
                          <div 
                            className={`${premio.imagem_url ? 'hidden' : 'flex'} absolute inset-0 items-center justify-center text-6xl`}
                          >
                            ⭐
                          </div>
                          <div className="absolute top-2 right-2 bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg">
                            Quase lá!
                          </div>
                        </div>
                        <div className="p-6">
                          <h4 className="font-bold text-gray-900 dark:text-white text-lg mb-2 text-center">
                            {premio.nome}
                          </h4>
                          {premio.descricao && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 text-center line-clamp-2">
                              {premio.descricao}
                            </p>
                          )}
                          <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3 text-center">
                            <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                              {premio.preco_em_pontos} pontos
                            </p>
                            <p className="text-sm text-orange-600 dark:text-orange-400 mt-1 font-semibold">
                              Faltam {premio.pontos_faltantes} pontos
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Todos os Prêmios (quando não há disponíveis nem próximos) */}
              {(!resultado.premios_disponiveis || resultado.premios_disponiveis.length === 0) &&
               (!resultado.premios_proximos || resultado.premios_proximos.length === 0) && (
                <div>
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                    <p className="text-blue-800 dark:text-blue-200 text-center">
                      💡 <strong>Acumule pontos</strong> no hotel para resgatar prêmios incríveis!
                    </p>
                  </div>
                  
                  <h4 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center">
                    <span className="mr-2">🎁</span>
                    Prêmios disponíveis no programa
                  </h4>
                  
                  {/* Buscar todos os prêmios via API */}
                  <PremiosCatalogo 
                    saldoAtual={resultado.saldo_pontos || 0}
                    clienteNome={resultado.cliente?.nome || 'Cliente'}
                    clienteEndereco={resultado.cliente?.endereco || 'Cabo Frio/RJ'}
                  />
                </div>
              )}
            </div>

            {/* Prêmios Próximos */}
            {resultado.premios_proximos && resultado.premios_proximos.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
                  <span className="text-3xl mr-3">🎯</span>
                  Prêmios Próximos
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {resultado.premios_proximos.map((premio) => (
                    <div
                      key={premio.id}
                      className="bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border-2 border-yellow-200 dark:border-yellow-800 rounded-xl p-6"
                    >
                      <div className="text-4xl mb-3 text-center">⭐</div>
                      <h4 className="font-bold text-gray-900 dark:text-white text-lg mb-2 text-center">
                        {premio.nome}
                      </h4>
                      {premio.descricao && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 text-center">
                          {premio.descricao}
                        </p>
                      )}
                      <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3 text-center">
                        <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                          {premio.preco_em_pontos} pontos
                        </p>
                        <p className="text-sm text-orange-600 dark:text-orange-400 mt-1 font-semibold">
                          Faltam {premio.pontos_faltantes} pontos
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Histórico de Transações */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
                <span className="text-3xl mr-3">📊</span>
                Histórico Recente
              </h3>
              
              {resultado.historico && resultado.historico.length > 0 ? (
                <div className="space-y-4">
                  {resultado.historico.map((transacao, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:shadow-md transition-shadow"
                    >
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 dark:text-white">
                          {transacao.reserva_codigo || `Transação #${transacao.id}`}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {new Date(transacao.created_at).toLocaleDateString('pt-BR', {
                            day: '2-digit',
                            month: 'long',
                            year: 'numeric'
                          })}
                        </div>
                        <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {transacao.origem} • {transacao.tipo}
                        </div>
                      </div>
                      <div className="text-right ml-4">
                        <span className={`text-xl ${getTipoTransacaoColor(transacao.tipo)}`}>
                          {transacao.pontos > 0 ? '+' : ''}{transacao.pontos} pts
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  <div className="text-6xl mb-4">📭</div>
                  <p>Nenhuma transação encontrada</p>
                </div>
              )}
            </div>

            {/* Botão Nova Consulta */}
            <div className="text-center">
              <button
                onClick={() => {
                  setResultado(null)
                  setCpf('')
                  setError('')
                }}
                className="px-8 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
              >
                🔄 Nova Consulta
              </button>
            </div>
          </div>
        )}

        {/* Informações do Programa */}
        {!resultado && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-4 sm:p-8 mt-8">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center">
              💎 Como funciona a jornada Real 👑
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              <div className="text-center p-6 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
                <div className="text-4xl mb-3">🏨</div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Reserve</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Reserve sua hospedagem diretamente com o hotel e comece a participar do nosso Programa de Pontos.
                </p>
              </div>
              <div className="text-center p-6 bg-pink-50 dark:bg-pink-900/20 rounded-xl">
                <div className="text-4xl mb-3">💰</div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Acumule</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Quanto melhor a suíte, mais rápido você avança.
                </p>
              </div>
              <div className="text-center p-6 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                <div className="text-4xl mb-3">🎁</div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Conquiste</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Troque seus pontos por prêmios, diárias grátis e chegue ao prêmio máximo: um iPhone exclusivo.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal de Confirmação de Resgate */}
      {showResgateModal && premioSelecionado && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 p-4 sm:p-6 text-white flex-shrink-0">
              <h3 className="text-xl sm:text-2xl font-bold text-center">Confirmar Resgate</h3>
            </div>

            {/* Conteúdo */}
            <div className="p-4 sm:p-6 flex-1 overflow-y-auto">
              {/* Imagem do Prêmio */}
              <div className="mb-4">
                {premioSelecionado.imagem_url ? (
                  <img
                    src={premioSelecionado.imagem_url}
                    alt={premioSelecionado.nome}
                    className="w-full h-32 sm:h-48 object-cover rounded-lg"
                    onError={(e) => {
                      e.target.style.display = 'none'
                      e.target.nextElementSibling.style.display = 'flex'
                    }}
                  />
                ) : null}
                <div 
                  className={`${premioSelecionado.imagem_url ? 'hidden' : 'flex'} w-full h-32 sm:h-48 bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30 rounded-lg items-center justify-center text-4xl sm:text-6xl`}
                >
                  🏆
                </div>
              </div>

              {/* Info do Prêmio */}
              <div className="text-center mb-6">
                <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  {premioSelecionado.nome}
                </h4>
                {premioSelecionado.descricao && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    {premioSelecionado.descricao}
                  </p>
                )}
              </div>

              {/* Validação Anti-Fraude */}
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-300 dark:border-yellow-700 rounded-lg p-4 mb-4">
                <div className="flex items-start gap-2">
                  <span className="text-2xl">🔒</span>
                  <div>
                    <p className="font-semibold text-yellow-800 dark:text-yellow-200 mb-1">Validação de Segurança</p>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300">
                      Este resgate será registrado com código único e validado pela recepção.
                    </p>
                  </div>
                </div>
              </div>

              {/* Resumo de Pontos */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Saldo atual:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {resultado?.saldo_pontos || 0} pontos
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Custo do prêmio:</span>
                  <span className="font-semibold text-red-600 dark:text-red-400">
                    -{premioSelecionado.preco_em_pontos} pontos
                  </span>
                </div>
                <div className="border-t border-gray-300 dark:border-gray-600 pt-2 flex justify-between">
                  <span className="font-semibold text-gray-900 dark:text-white">Novo saldo:</span>
                  <span className="font-bold text-green-600 dark:text-green-400">
                    {(resultado?.saldo_pontos || 0) - premioSelecionado.preco_em_pontos} pontos
                  </span>
                </div>
              </div>

              {/* Campo de Observações */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Observações (opcional)
                </label>
                <textarea
                  value={observacoes}
                  onChange={(e) => setObservacoes(e.target.value)}
                  placeholder="Ex: Prefiro retirar pela manhã..."
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  rows="3"
                />
              </div>

              {/* Botões */}
              <div className="flex gap-2 sm:gap-3 mt-auto pt-4">
                <button
                  onClick={fecharModalResgate}
                  disabled={resgatando}
                  className="flex-1 py-2 sm:py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg font-semibold hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 text-sm sm:text-base"
                >
                  Cancelar
                </button>
                <button
                  onClick={confirmarResgate}
                  disabled={resgatando}
                  className="flex-1 py-2 sm:py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg disabled:opacity-50 text-sm sm:text-base"
                >
                  {resgatando ? (
                    <span className="flex items-center justify-center">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      Resgatando...
                    </span>
                  ) : (
                    '✓ Confirmar Resgate'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Sucesso */}
      {resgateSuccess && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header de Sucesso */}
            <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-4 sm:p-6 text-white text-center flex-shrink-0">
              <div className="text-4xl sm:text-6xl mb-3">🎉</div>
              <h3 className="text-xl sm:text-2xl font-bold">Resgate Realizado!</h3>
            </div>

            {/* Conteúdo */}
            <div className="p-4 sm:p-6 flex-1 overflow-y-auto">
              <div className="text-center mb-6">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Seu prêmio foi resgatado com sucesso!
                </p>
                
                {/* Código de Retirada Seguro */}
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border-2 border-purple-200 dark:border-purple-800 rounded-xl p-6 mb-4">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <span className="text-2xl">🔐</span>
                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">Código de Retirada Seguro</p>
                  </div>
                  <p className="text-3xl font-bold text-purple-600 dark:text-purple-400 tracking-wider text-center">
                    RES-{String(resgateSuccess.data?.resgate_id || '000000').padStart(6, '0')}
                  </p>
                  <p className="text-xs text-center text-gray-500 dark:text-gray-400 mt-2">
                    ⚠️ Apresente este código + documento com foto
                  </p>
                </div>

                {/* Informações */}
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4 text-left space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Prêmio:</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {resgateSuccess.data?.premio?.nome}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Pontos utilizados:</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {resgateSuccess.data?.pontos_usados} pontos
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Novo saldo:</span>
                    <span className="font-semibold text-green-600 dark:text-green-400">
                      {resgateSuccess.data?.novo_saldo} pontos
                    </span>
                  </div>
                </div>

                {/* Instruções */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    <strong>📍 Como retirar:</strong><br />
                    Apresente este código na recepção do Hotel Real Cabo Frio para retirar seu prêmio.
                  </p>
                </div>
              </div>

              {/* Botões */}
              <div className="space-y-3">
                {/* Botão WhatsApp */}
                <WhatsAppButton
                  clienteNome={resultado?.cliente?.nome || 'Cliente'}
                  clienteCPF={formatarCPF(resultado?.cliente?.documento || '')}
                  premioNome={resgateSuccess.data?.premio?.nome || 'Prêmio'}
                  pontosUsados={resgateSuccess.data?.pontos_usados || 0}
                  codigoResgate={`RES-${String(resgateSuccess.data?.resgate_id || '000000').padStart(6, '0')}`}
                  className="w-full"
                />
                
                <button
                  onClick={() => window.print()}
                  className="w-full py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors"
                >
                  🖨️ Imprimir Comprovante
                </button>
                <button
                  onClick={() => setResgateSuccess(null)}
                  className="w-full py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg font-semibold hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-gray-600 dark:text-gray-400 text-sm">
            © 2026 Hotel Real Cabo Frio - Todos os direitos reservados
          </p>
        </div>
      </div>
    </div>
  )
}
