'use client'
import { useState } from 'react'
import { api } from '../../../lib/api'
import { Search, Filter, Download, Eye, AlertTriangle, CheckCircle, X, Clock, CreditCard, User, Calendar, TrendingUp, TrendingDown } from 'lucide-react'
import { toast } from 'react-toastify'

export default function AnaliseDetalhada({ clienteId, onClose }) {
  const [loading, setLoading] = useState(false)
  const [analise, setAnalise] = useState(null)
  const [historico, setHistorico] = useState([])
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({
    periodo: '30d',
    tipo_risco: 'todos',
    status: 'todos'
  })

  useEffect(() => {
    if (clienteId) {
      carregarAnaliseCompleta()
    }
  }, [clienteId])

  const carregarAnaliseCompleta = async () => {
    setLoading(true)
    try {
      // Carregar análise atual do cliente
      const res = await api.get(`/antifraude/analisar/${clienteId}`)
      setAnalise(res.data)

      // Carregar histórico de transações
      const histRes = await api.get(`/antifraude/historico/${clienteId}`)
      setHistorico(histRes.data?.historico || [])
    } catch (error) {
      console.error('Erro ao carregar análise:', error)
      toast.error('Erro ao carregar análise detalhada')
    } finally {
      setLoading(false)
    }
  }

  const getRiscoColor = (score) => {
    if (score >= 70) return 'text-red-600'
    if (score >= 40) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getRiscoIcon = (score) => {
    if (score >= 70) return <AlertTriangle className="w-5 h-5" />
    if (score >= 40) return <Shield className="w-5 h-5" />
    return <CheckCircle className="w-5 h-5" />
  }

  const getRiscoText = (score) => {
    if (score >= 70) return 'ALTO RISCO'
    if (score >= 40) return 'MÉDIO RISCO'
    return 'BAIXO RISCO'
  }

  const getRecomendacaoIcon = (risco) => {
    switch (risco) {
      case 'ALTO':
        return <X className="w-4 h-4 text-red-600" />
      case 'MÉDIO':
        return <Eye className="w-4 h-4 text-yellow-600" />
      case 'BAIXO':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      default:
        return <CheckCircle className="w-4 h-4 text-gray-600" />
    }
  }

  const executarAcaoManual = async (acao, clienteId) => {
    try {
      setLoading(true)
      
      let endpoint = ''
      switch (acao) {
        case 'aprovar':
          endpoint = `/antifraude/aprovar-manual/${clienteId}`
          break
        case 'recusar':
          endpoint = `/antifraude/recusar/${clienteId}`
          break
        case 'investigar':
          endpoint = `/antifraude/investigar/${clienteId}`
          break
        default:
          return
      }

      const res = await api.post(endpoint)
      
      if (res.data.success) {
        toast.success(`Ação "${acao}" executada com sucesso`)
        carregarAnaliseCompleta()
      } else {
        toast.error(res.data.error || 'Erro ao executar ação')
      }
    } catch (error) {
      console.error('Erro ao executar ação manual:', error)
      toast.error('Erro ao executar ação manual')
    } finally {
      setLoading(false)
    }
  }

  const exportarRelatorio = async () => {
    try {
      setLoading(true)
      const res = await api.get(`/antifraude/relatorio/${clienteId}`)
      
      if (res.data.success) {
        // Criar blob e download
        const blob = new Blob([res.data.relatorio], { type: 'text/plain' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `relatorio_antifraude_cliente_${cliente_id}_${new Date().toISOString().split('T')[0]}.txt`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
        toast.success('Relatório exportado com sucesso')
      }
    } catch (error) {
      console.error('Erro ao exportar relatório:', error)
      toast.error('Erro ao exportar relatório')
    } finally {
      setLoading(false)
    }
  }

  if (!analise && loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2 text-gray-600">Carregando análise...</span>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-xl p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Análise Detalhada</h2>
          <p className="text-gray-600">Cliente #{clienteId}</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Score de Risco */}
      {analise && (
        <div className="mb-6 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-l-4 border-indigo-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Score de Risco</h3>
              <p className="text-sm text-gray-600">Avaliação completa do perfil</p>
            </div>
            <div className={`text-3xl font-bold ${getRiscoColor(analise.score)}`}>
              {analise.score}/100
            </div>
          </div>
          <div className="mt-4 flex items-center space-x-4">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
              analise.risco === 'ALTO' ? 'bg-red-100 text-red-800' :
              analise.risco === 'MÉDIO' ? 'bg-yellow-100 text-yellow-800' :
              'bg-green-100 text-green-800'
            }`}>
              {getRiscoIcon(analise.score)}
              <span className="font-medium">{getRiscoText(analise.score)}</span>
            </div>
            <div className="text-sm text-gray-600">
              Recomendação: {analise.recomendacao}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => executarAcaoManual('aprovar', clienteId)}
                className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                disabled={analise.aprovacao_automatica}
              >
                Aprovar Manual
              </button>
              <button
                onClick={() => executarAcaoManual('investigar', clienteId)}
                className="px-3 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700"
              >
                Investigar
              </button>
              <button
                onClick={() => executarAcaoManual('recusar', clienteId)}
                className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Recusar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Alertas Detalhadas */}
      {analise && analise.alertas && analise.alertas.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🚨 Alertas Detectadas</h3>
          <div className="space-y-3">
            {analise.alertas.map((alerta, index) => (
              <div key={index} className="p-4 border-l-4 border-orange-200 bg-orange-50 rounded-r-lg">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="w-5 h-5 text-orange-600 mt-1" />
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{alerta}</h4>
                    <p className="text-sm text-gray-600 mt-1">{analise.detalhes_alertas[alerta] || 'Detalhes não disponíveis'}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Métricas do Cliente */}
      {analise && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <User className="w-4 h-4 text-gray-600" />
              <h4 className="font-medium text-gray-900">Total Reservas</h4>
            </div>
            <div className="text-2xl font-bold text-gray-900">{analise.total_reservas}</div>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <CreditCard className="w-4 h-4 text-gray-600" />
              <h4 className="font-medium text-gray-900">Canceladas</h4>
            </div>
            <div className="text-2xl font-bold text-red-600">{analise.reservas_canceladas}</div>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <TrendingUp className="w-4 h-4 text-gray-600" />
              <h4 className="font-medium text-gray-900">Taxa Cancelamento</h4>
            </div>
            <div className="text-2xl font-bold text-orange-600">{analise.taxa_cancelamento}%</div>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Clock className="w-4 h-4 text-gray-600" />
              <h4 className="font-medium text-gray-900">Reservas Recentes</h4>
            </div>
            <div className="text-2xl font-bold text-blue-600">{analise.reservas_recentes}</div>
          </div>
        </div>
      )}

      {/* Histórico de Transações */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">📊 Histórico de Transações</h3>
          <button
            onClick={exportarRelatorio}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            disabled={loading}
          >
            <Download className="w-4 h-4" />
            Exportar Relatório
          </button>
        </div>
        
        {historico.length > 0 ? (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="p-3 text-left">Data</th>
                  <th className="p-3 text-left">Tipo</th>
                  <th>Score</th>
                  <th>Valor</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {historico.map((item, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="p-3 text-sm">
                      {new Date(item.data).toLocaleString('pt-BR')}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        item.tipo === 'ALTO' ? 'bg-red-100 text-red-800' :
                        item.tipo === 'MÉDIO' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {item.tipo}
                      </span>
                    </td>
                    <td className="p-3 font-mono">
                      <span className={getRiscoColor(item.score)}>
                        {item.score}
                      </span>
                    </td>
                    <td className="p-3 font-semibold">
                      R$ {item.valor?.toFixed(2)}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        item.status === 'APROVADO' ? 'bg-green-100 text-green-800' :
                        item.status === 'RECUSADO' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p>Nenhum histórico encontrado</p>
          </div>
        )}
      </div>
    </div>
  )
}
