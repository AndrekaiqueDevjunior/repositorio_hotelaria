'use client'
import { useEffect, useState } from 'react'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { api } from '../../../lib/api'
import ProtectedRoute from '../../../components/ProtectedRoute'

function PontosRPContent() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [loading, setLoading] = useState(false)
  const [clientes, setClientes] = useState([])
  const [clienteId, setClienteId] = useState(null)
  const [clienteNome, setClienteNome] = useState('')
  
  // Estados do Sistema RP
  const [saldoRP, setSaldoRP] = useState({
    saldo_rp: 0,
    diarias_pendentes: 0,
    total_ganhos: 0,
    total_gastos: 0,
    primeira_vez: true
  })
  const [historicoRP, setHistoricoRP] = useState([])
  const [premiosRP, setPremiosRP] = useState([])
  const [regrasRP, setRegrasRP] = useState(null)
  
  // Carregar clientes ao iniciar
  useEffect(() => {
    loadClientes()
    loadRegrasRP()
  }, [])

  useEffect(() => {
    if (clienteId) {
      if (activeTab === 'dashboard' || activeTab === 'historico') {
        loadSaldoRP()
        loadHistoricoRP()
      }
      if (activeTab === 'premios') {
        loadPremiosRP()
      }
    }
  }, [activeTab, clienteId])

  const loadClientes = async () => {
    try {
      setLoading(true)
      const res = await api.get('/clientes')
      const clientesData = res.data.clientes || res.data
      
      if (clientesData && clientesData.length > 0) {
        setClientes(clientesData)
        setClienteId(clientesData[0].id)
        setClienteNome(clientesData[0].nome_completo)
      } else {
        toast.error('Nenhum cliente encontrado')
      }
    } catch (error) {
      toast.error('Erro ao carregar clientes: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const loadSaldoRP = async () => {
    if (!clienteId) return
    
    try {
      const res = await api.get(`/pontos/saldo/${clienteId}`)
      // Adaptar resposta do sistema unificado para formato RP
      setSaldoRP({
        saldo_rp: res.data.saldo || 0,
        diarias_pendentes: 0,
        total_ganhos: 0,
        total_gastos: 0,
        primeira_vez: true
      })
    } catch (error) {
      console.error('Erro ao carregar saldo RP:', error)
      toast.error('Erro ao carregar saldo RP')
    }
  }

  const loadHistoricoRP = async () => {
    if (!clienteId) return
    
    try {
      const res = await api.get(`/pontos/historico/${clienteId}?limit=100`)
      setHistoricoRP(res.data.transacoes || [])
    } catch (error) {
      console.error('Erro ao carregar histórico RP:', error)
      toast.error('Erro ao carregar histórico RP')
    }
  }

  const loadPremiosRP = async () => {
    try {
      // Sistema de prêmios ainda não implementado no backend unificado
      // Por enquanto, retornar array vazio sem notificação
      setPremiosRP([])
    } catch (error) {
      console.error('Erro ao carregar prêmios RP:', error)
      toast.error('Erro ao carregar prêmios RP')
    }
  }

  const loadRegrasRP = async () => {
    try {
      // Regras hardcoded até implementação no backend
      setRegrasRP({
        pontos_por_real: 0.1,
        descricao: "1 ponto para cada R$ 10,00 gastos",
        regras: [
          "Pontos creditados após check-out",
          "Não expiram",
          "Acumulativos por cliente",
          "1 ponto = R$ 10,00 em hospedagem"
        ]
      })
    } catch (error) {
      console.error('Erro ao carregar regras RP:', error)
    }
  }

  const resgatarPremio = async (premioId, premioNome, rpNecessario) => {
    if (saldoRP.saldo_rp < rpNecessario) {
      toast.error('Saldo insuficiente para este resgate')
      return
    }

    if (!confirm(`Confirma o resgate de "${premioNome}" por ${rpNecessario} RP?`)) {
      return
    }

    try {
      setLoading(true)
      const res = await api.post('/pontos-rp/resgatar', {
        cliente_id: clienteId,
        premio_id: premioId
      })

      if (res.data.success) {
        toast.success(`🎉 Resgate realizado! ${premioNome}`)
        loadSaldoRP() // Atualizar saldo
        loadPremiosRP() // Atualizar disponibilidade
      } else {
        toast.error(res.data.error || 'Erro no resgate')
      }
    } catch (error) {
      toast.error('Erro ao processar resgate: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('pt-BR')
  }

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Saldo RP */}
      <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-6 rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold mb-4">💎 Seus Pontos RP</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold">{saldoRP.saldo_rp}</div>
            <div className="text-sm opacity-90">Pontos Disponíveis</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold">{saldoRP.diarias_pendentes}</div>
            <div className="text-sm opacity-90">Diárias Acumuladas</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold">{saldoRP.total_ganhos}</div>
            <div className="text-sm opacity-90">Total Ganho</div>
          </div>
        </div>
      </div>

      {/* Primeira vez no programa */}
      {saldoRP.primeira_vez && (
        <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-800 mb-2">🎉 Bem-vindo ao Programa RP!</h3>
          <p className="text-blue-700">
            Este é seu primeiro acesso ao sistema de pontos. Faça reservas e acumule pontos para trocar por prêmios incríveis!
          </p>
        </div>
      )}

      {/* Histórico Recente */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-semibold mb-4">📈 Histórico Recente</h3>
        {historicoRP.length === 0 ? (
          <p className="text-gray-500">Nenhuma movimentação de pontos ainda.</p>
        ) : (
          <div className="space-y-3">
            {historicoRP.slice(0, 5).map((item) => (
              <div key={item.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <div>
                  <div className="font-medium">Reserva {item.codigo_reserva || item.reserva_id}</div>
                  <div className="text-sm text-gray-600">{item.detalhamento}</div>
                  <div className="text-xs text-gray-500">{formatDate(item.data)}</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-green-600">+{item.pontos_gerados} RP</div>
                  <div className="text-xs text-gray-500">{item.tipo_suite}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )

  const renderHistorico = () => (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-6">📊 Histórico Completo</h2>
      
      {historicoRP.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-6xl mb-4">📈</div>
          <p className="text-gray-500">Nenhuma movimentação ainda.</p>
          <p className="text-sm text-gray-400 mt-2">
            Faça reservas e realize check-outs para começar a acumular pontos!
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {historicoRP.map((item) => (
            <div key={item.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold">Reserva {item.codigo_reserva || item.reserva_id}</span>
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">{item.tipo_suite}</span>
                  </div>
                  <div className="text-sm text-gray-600 mb-2">{item.detalhamento}</div>
                  <div className="text-xs text-gray-500">
                    {item.num_diarias} diárias • {item.diarias_usadas_acumuladas} diárias processadas • {formatDate(item.data)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-green-600">+{item.pontos_gerados}</div>
                  <div className="text-xs text-gray-500">RP</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  const renderPremios = () => {
    const categorias = [...new Set(premiosRP.map(p => p.categoria))]
    
    return (
      <div className="space-y-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">🎁 Catálogo de Prêmios</h2>
            <div className="text-right">
              <div className="text-sm text-gray-500">Seu saldo:</div>
              <div className="text-2xl font-bold text-purple-600">{saldoRP.saldo_rp} RP</div>
            </div>
          </div>
          
          {categorias.map(categoria => (
            <div key={categoria} className="mb-8">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">{categoria}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {premiosRP.filter(p => p.categoria === categoria).map((premio) => (
                  <div key={premio.id} className={`border rounded-lg p-4 ${
                    premio.pode_resgatar ? 'border-green-300 bg-green-50' : 'border-gray-200'
                  }`}>
                    <div className="flex justify-between items-start mb-3">
                      <h4 className="font-semibold">{premio.nome}</h4>
                      <div className="text-right">
                        <div className="font-bold text-purple-600">{premio.rp_necessario} RP</div>
                      </div>
                    </div>
                    
                    {premio.descricao && (
                      <p className="text-sm text-gray-600 mb-3">{premio.descricao}</p>
                    )}
                    
                    <button
                      onClick={() => resgatarPremio(premio.id, premio.nome, premio.rp_necessario)}
                      disabled={!premio.pode_resgatar || loading}
                      className={`w-full py-2 px-4 rounded font-medium ${
                        premio.pode_resgatar 
                          ? 'bg-purple-600 text-white hover:bg-purple-700' 
                          : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      {premio.pode_resgatar ? '🎯 Resgatar' : '🔒 Saldo Insuficiente'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderRegras = () => (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-6">📋 Regras do Programa RP</h2>
      
      {regrasRP ? (
        <div className="space-y-8">
          {/* Regras Gerais */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-800">📌 Regras Gerais</h3>
            <ul className="space-y-2">
              {regrasRP.regras_gerais?.map((regra, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>{regra}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Pontuação por Suite */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-800">🏨 Pontuação por Tipo de Suíte</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(regrasRP.pontuacao_por_suite || {}).map(([tipo, info]) => (
                <div key={tipo} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-semibold">{tipo}</h4>
                    <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm font-bold">
                      {info.pontos_por_2_diarias} RP
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-1">{info.descricao}</p>
                  <p className="text-xs text-gray-500">{info.valor_medio}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Exemplo de Cálculo */}
          {regrasRP.exemplo_calculo && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2 text-blue-800">💡 Exemplo de Cálculo</h3>
              <p className="text-blue-700 mb-1"><strong>Cenário:</strong> {regrasRP.exemplo_calculo.cenario}</p>
              <p className="text-blue-700 mb-1"><strong>Cálculo:</strong> {regrasRP.exemplo_calculo.calculo}</p>
              <p className="text-blue-700 mb-1"><strong>Resultado:</strong> {regrasRP.exemplo_calculo.resultado}</p>
              <p className="text-blue-600 text-sm"><strong>Próxima reserva:</strong> {regrasRP.exemplo_calculo.proxima_reserva}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-8">
          <div className="text-4xl mb-4">📋</div>
          <p className="text-gray-500">Carregando regras...</p>
        </div>
      )}
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">💎 Sistema de Pontos RP</h1>
          
          {/* Seletor de Cliente */}
          <div className="flex items-center gap-4 mb-6">
            <label className="font-medium">Cliente:</label>
            <select
              value={clienteId || ''}
              onChange={(e) => {
                const id = parseInt(e.target.value)
                setClienteId(id)
                const cliente = clientes.find(c => c.id === id)
                setClienteNome(cliente?.nomeCompleto || cliente?.nome_completo || '')
              }}
              className="border border-gray-300 rounded px-3 py-2"
              disabled={loading}
            >
              <option value="">Selecione um cliente</option>
              {clientes.map((cliente) => (
                <option key={cliente.id} value={cliente.id}>
                  {cliente.nomeCompleto || cliente.nome_completo}
                </option>
              ))}
            </select>
            {clienteNome && (
              <span className="text-sm text-gray-600">Cliente selecionado: <strong>{clienteNome}</strong></span>
            )}
          </div>

          {/* Tabs */}
          <div className="flex space-x-1 bg-white p-1 rounded-lg shadow">
            {[
              { key: 'dashboard', label: '📊 Dashboard', icon: '📊' },
              { key: 'historico', label: '📈 Histórico', icon: '📈' },
              { key: 'premios', label: '🎁 Prêmios', icon: '🎁' },
              { key: 'regras', label: '📋 Regras', icon: '📋' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        {!clienteId ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">👆</div>
            <p className="text-gray-500">Selecione um cliente para visualizar os pontos RP</p>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && renderDashboard()}
            {activeTab === 'historico' && renderHistorico()}
            {activeTab === 'premios' && renderPremios()}
            {activeTab === 'regras' && renderRegras()}
          </>
        )}
      </div>

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
      />
    </div>
  )
}

export default function PontosRPPage() {
  return (
    <ProtectedRoute>
      <PontosRPContent />
    </ProtectedRoute>
  )
}
