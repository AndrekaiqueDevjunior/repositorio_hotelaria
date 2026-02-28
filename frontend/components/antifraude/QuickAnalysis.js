'use client'
import { useState } from 'react'
import { api } from '../../../lib/api'
import { Search, AlertTriangle, CheckCircle, Shield, Clock, TrendingUp, User, CreditCard } from 'lucide-react'
import { toast } from 'react-toastify'

export default function QuickAnalysis() {
  const [searchTerm, setSearchTerm] = useState('')
  const [searchType, setSearchType] = useState('cpf')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [selectedResult, setSelectedResult] = useState(null)
  const [showDetails, setShowDetails] = useState(false)

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      toast.warning('Digite um CPF, email ou ID do cliente')
      return
    }

    setLoading(true)
    try {
      let endpoint = ''
      switch (searchType) {
        case 'cpf':
          endpoint = `/antifraude/buscar-cpf/${searchTerm}`
          break
        case 'email':
          endpoint = `/antifraude/buscar-email/${searchTerm}`
          break
        case 'id':
          endpoint = `/antifraude/analisar/${searchTerm}`
          break
        default:
          endpoint = `/antifraude/buscar/${searchTerm}`
      }

      const res = await api.get(endpoint)
      
      if (res.data.success) {
        if (Array.isArray(res.data.data)) {
          setResults(res.data.data)
        } else {
          setResults([res.data])
        }
      } else {
        toast.error(res.data.error || 'Nenhum resultado encontrado')
        setResults([])
      }
    } catch (error) {
      console.error('Erro na busca:', error)
      toast.error('Erro ao buscar informações')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (score) => {
    if (score >= 70) return 'text-red-600 bg-red-50 border-red-200'
    if (score >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-green-600 bg-green-50 border-green-200'
  }

  const getRiskIcon = (score) => {
    if (score >= 70) return <AlertTriangle className="w-4 h-4" />
    if (score >= 40) return <Shield className="w-4 h-4" />
    return <CheckCircle className="w-4 h-4" />
  }

  const getRiskText = (score) => {
    if (score >= 70) return 'ALTO RISCO'
    if (score >= 40) return 'MÉDIO RISCO'
    return 'BAIXO RISCO'
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-xl p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900">🔍 Análise Rápida</h2>
        <p className="text-gray-600">Verifique o risco de clientes em tempo real</p>
      </div>

      {/* Search Interface */}
      <div className="mb-6">
        <div className="flex space-x-3">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  searchType === 'cpf' ? 'Digite o CPF (ex: 12345678900)' :
                  searchType === 'email' ? 'Digite o email' :
                  'Digite o ID do cliente'
                }
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
          
          <select
            value={searchType}
            onChange={(e) => setSearchType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="cpf">CPF</option>
            <option value="email">Email</option>
            <option value="id">ID Cliente</option>
          </select>
          
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              'Buscar'
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <h3 className="font-semibold text-gray-900">Resultados ({results.length})</h3>
          
          {results.map((result, index) => (
            <div
              key={index}
              className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${getRiskColor(result.score)}`}
              onClick={() => {
                setSelectedResult(result)
                setShowDetails(true)
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getRiskIcon(result.score)}
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {result.nome || `Cliente #${result.cliente_id}`}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {result.documento || result.email || `ID: ${result.cliente_id}`}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold">{result.score}</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-white/50">
                      {getRiskText(result.score)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">
                    Score de risco
                  </p>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
                <div className="flex items-center space-x-2">
                  <CreditCard className="w-3 h-3 text-gray-500" />
                  <span>{result.total_reservas || 0} reservas</span>
                </div>
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-3 h-3 text-gray-500" />
                  <span>{result.taxa_cancelamento || 0}% cancelamento</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="w-3 h-3 text-gray-500" />
                  <span>{result.pagamentos_recusados || 0} recusados</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* No Results */}
      {!loading && results.length === 0 && searchTerm && (
        <div className="text-center py-8 text-gray-500">
          <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p>Nenhum resultado encontrado para "{searchTerm}"</p>
          <p className="text-sm text-gray-400 mt-2">
            Verifique se os dados estão corretos
          </p>
        </div>
      )}

      {/* Details Modal */}
      {showDetails && selectedResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">Detalhes da Análise</h3>
              <button
                onClick={() => setShowDetails(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            {/* Risk Score */}
            <div className={`p-4 rounded-lg mb-4 ${getRiskColor(selectedResult.score)}`}>
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-gray-900">Score de Risco</h4>
                  <p className="text-sm text-gray-600">Avaliação completa</p>
                </div>
                <div className="text-3xl font-bold">
                  {selectedResult.score}/100
                </div>
              </div>
              <div className="mt-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium bg-white/50`}>
                  {getRiskText(selectedResult.score)}
                </span>
              </div>
            </div>

            {/* Alerts */}
            {selectedResult.alertas && selectedResult.alertas.length > 0 && (
              <div className="mb-4">
                <h4 className="font-semibold text-gray-900 mb-2">🚨 Alertas Detectadas</h4>
                <div className="space-y-2">
                  {selectedResult.alertas.map((alerta, index) => (
                    <div key={index} className="p-3 bg-orange-50 border-l-4 border-orange-200 rounded-r">
                      <p className="text-sm text-gray-700">{alerta}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <h5 className="font-medium text-gray-900">Total Reservas</h5>
                <p className="text-2xl font-bold text-gray-900">{selectedResult.total_reservas}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <h5 className="font-medium text-gray-900">Canceladas</h5>
                <p className="text-2xl font-bold text-red-600">{selectedResult.reservas_canceladas}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <h5 className="font-medium text-gray-900">Taxa Cancelamento</h5>
                <p className="text-2xl font-bold text-orange-600">{selectedResult.taxa_cancelamento}%</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <h5 className="font-medium text-gray-900">Pagamentos Recusados</h5>
                <p className="text-2xl font-bold text-red-600">{selectedResult.pagamentos_recusados}</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-3">
              <button
                onClick={() => {
                  toast.success('Ação executada com sucesso')
                  setShowDetails(false)
                }}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Aprovar Manual
              </button>
              <button
                onClick={() => {
                  toast.info('Investigação iniciada')
                  setShowDetails(false)
                }}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
              >
                Investigar
              </button>
              <button
                onClick={() => {
                  toast.error('Transação recusada')
                  setShowDetails(false)
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Recusar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
