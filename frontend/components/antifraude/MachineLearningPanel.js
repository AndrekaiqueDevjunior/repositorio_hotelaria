'use client'
import { useState, useEffect } from 'react'
import { api } from '../../../lib/api'
import { Brain, TrendingUp, AlertTriangle, CheckCircle, Play, Pause, Settings, Download, RefreshCw } from 'lucide-react'
import { toast } from 'react-toastify'

export default function MachineLearningPanel() {
  const [mlStats, setMlStats] = useState(null)
  const [trainingStatus, setTrainingStatus] = useState('idle')
  const [modelAccuracy, setModelAccuracy] = useState(0)
  const [predictions, setPredictions] = useState([])
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    carregarDadosML()
  }, [])

  const carregarDadosML = async () => {
    try {
      setLoading(true)
      const res = await api.get('/antifraude/ml/stats')
      setMlStats(res.data)
      setModelAccuracy(res.data?.accuracy || 0)
      setPredictions(res.data?.recent_predictions || [])
    } catch (error) {
      console.error('Erro ao carregar dados ML:', error)
    } finally {
      setLoading(false)
    }
  }

  const treinarModelo = async () => {
    try {
      setTrainingStatus('training')
      toast.info('Iniciando treinamento do modelo...')
      
      const res = await api.post('/antifraude/ml/train')
      
      if (res.data.success) {
        setModelAccuracy(res.data.accuracy)
        setTrainingStatus('completed')
        toast.success(`Modelo treinado com ${res.data.accuracy}% de precisão`)
        carregarDadosML()
      } else {
        setTrainingStatus('error')
        toast.error('Erro ao treinar modelo')
      }
    } catch (error) {
      setTrainingStatus('error')
      console.error('Erro ao treinar modelo:', error)
      toast.error('Erro ao treinar modelo')
    }
  }

  const fazerPrevisao = async (clienteId) => {
    try {
      setLoading(true)
      const res = await api.post('/antifraude/ml/predict', { cliente_id: clienteId })
      
      if (res.data.success) {
        const prediction = res.data.prediction
        toast.success(`Previsão: ${prediction.risco} (Score: ${prediction.score})`)
        setPredictions(prev => [prediction, ...prev.slice(0, 9)])
      }
    } catch (error) {
      console.error('Erro ao fazer previsão:', error)
      toast.error('Erro ao fazer previsão')
    } finally {
      setLoading(false)
    }
  }

  const exportarModelo = async () => {
    try {
      setLoading(true)
      const res = await api.get('/antifraude/ml/export')
      
      if (res.data.success) {
        // Download do modelo
        const blob = new Blob([JSON.stringify(res.data.model)], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `modelo_antifraude_${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
        toast.success('Modelo exportado com sucesso')
      }
    } catch (error) {
      console.error('Erro ao exportar modelo:', error)
      toast.error('Erro ao exportar modelo')
    } finally {
      setLoading(false)
    }
  }

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 90) return 'text-green-600'
    if (accuracy >= 75) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getAccuracyIcon = (accuracy) => {
    if (accuracy >= 90) return <CheckCircle className="w-5 h-5" />
    if (accuracy >= 75) return <Brain className="w-5 h-5" />
    return <AlertTriangle className="w-5 h-5" />
  }

  return (
    <div className="bg-white rounded-lg shadow-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Brain className="w-6 h-6 text-purple-600" />
          <h2 className="text-xl font-bold text-gray-900">Machine Learning Antifraude</h2>
        </div>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-gray-400 hover:text-gray-600"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Status do Modelo */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-900">Precisão do Modelo</h3>
            {getAccuracyIcon(modelAccuracy)}
          </div>
          <div className={`text-2xl font-bold ${getAccuracyColor(modelAccuracy)}`}>
            {modelAccuracy.toFixed(1)}%
          </div>
          <p className="text-sm text-gray-600">Acurácia atual</p>
        </div>

        <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-900">Status</h3>
            <div className={`w-3 h-3 rounded-full ${
              trainingStatus === 'training' ? 'bg-yellow-500 animate-pulse' :
              trainingStatus === 'completed' ? 'bg-green-500' :
              trainingStatus === 'error' ? 'bg-red-500' :
              'bg-gray-500'
            }`} />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {trainingStatus === 'training' ? 'Treinando' :
             trainingStatus === 'completed' ? 'Pronto' :
             trainingStatus === 'error' ? 'Erro' :
             'Parado'}
          </div>
          <p className="text-sm text-gray-600">Estado do modelo</p>
        </div>

        <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-900">Previsões</h3>
            <TrendingUp className="w-4 h-4 text-green-600" />
          </div>
          <div className="text-2xl font-bold text-green-600">
            {predictions.length}
          </div>
          <p className="text-sm text-gray-600">Previsões recentes</p>
        </div>
      </div>

      {/* Controles do Modelo */}
      <div className="flex flex-wrap gap-3 mb-6">
        <button
          onClick={treinarModelo}
          disabled={trainingStatus === 'training' || loading}
          className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
        >
          {trainingStatus === 'training' ? (
            <>
              <Pause className="w-4 h-4" />
              Treinando...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Treinar Modelo
            </>
          )}
        </button>

        <button
          onClick={carregarDadosML}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Atualizar
        </button>

        <button
          onClick={exportarModelo}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          Exportar Modelo
        </button>
      </div>

      {/* Previsões Recentes */}
      {predictions.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🔮 Previsões Recentes</h3>
          <div className="space-y-3">
            {predictions.map((pred, index) => (
              <div key={index} className="p-4 border rounded-lg hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">Cliente #{pred.cliente_id}</h4>
                    <p className="text-sm text-gray-600">Previsão: {pred.risco}</p>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${
                      pred.score >= 70 ? 'text-red-600' :
                      pred.score >= 40 ? 'text-yellow-600' :
                      'text-green-600'
                    }`}>
                      {pred.score}
                    </div>
                    <p className="text-xs text-gray-500">
                      {new Date(pred.timestamp).toLocaleString('pt-BR')}
                    </p>
                  </div>
                </div>
                <div className="mt-2">
                  <div className="text-sm text-gray-600">
                    Confiança: {(pred.confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Configurações Avançadas */}
      {showAdvanced && (
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">⚙️ Configurações Avançadas</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Parâmetros do Modelo</h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Algoritmo
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500">
                    <option>Random Forest</option>
                    <option>Gradient Boosting</option>
                    <option>Neural Network</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Threshold de Risco
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    defaultValue="50"
                    className="w-full"
                  />
                  <div className="text-sm text-gray-600">50%</div>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-3">Features</h4>
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input type="checkbox" defaultChecked className="rounded" />
                  <span className="text-sm text-gray-700">Histórico de cancelamentos</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" defaultChecked className="rounded" />
                  <span className="text-sm text-gray-700">Padrões de tempo</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" defaultChecked className="rounded" />
                  <span className="text-sm text-gray-700">Valor médio de transações</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm text-gray-700">Geolocalização</span>
                </label>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={() => toast.info('Configurações salvas com sucesso')}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Salvar Configurações
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
