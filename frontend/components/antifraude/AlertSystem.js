'use client'
import { useState, useEffect } from 'react'
import { api } from '../../../lib/api'
import { Bell, AlertTriangle, Shield, X, CheckCircle } from 'lucide-react'
import { toast } from 'react-toastify'

export default function AlertSystem({ onAlertaRecebida }) {
  const [alertas, setAlertas] = useState([])
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [showAlerts, setShowAlerts] = useState(true)

  useEffect(() => {
    // Polling para novas alertas a cada 30 segundos
    const interval = setInterval(() => {
      carregarAlertas()
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const carregarAlertas = async () => {
    try {
      const res = await api.get('/antifraude/alertas-ativas')
      if (res.data.success) {
        const novasAlertas = res.data.alertas || []
        
        // Verificar se há alertas novas
        if (novasAlertas.length > 0) {
          // Notificar sobre novas alertas
          novasAlertas.forEach(alerta => {
            if (soundEnabled) {
              // Reproduzir som de notificação (se implementado)
              tocarSomNotificacao()
            }
            
            // Mostrar toast
            toast.warning(`⚠️ Alerta Antifraude: ${alerta.titulo}`, {
              position: 'top-right',
              autoClose: 5000,
              onClick: () => {
                // Redirecionar para detalhes da alerta
                window.open(`/dashboard/antifraude?alerta=${alerta.id}`)
              }
            })
            
            // Callback para notificar componente pai
            if (onAlertaRecebida) {
              onAlertaRecebida(alerta)
            }
          })
          
          setAlertas(prev => [...novasAlertas, ...prev])
        }
      }
    } catch (error) {
      console.error('Erro ao carregar alertas:', error)
    }
  }

  const tocarSomNotificacao = () => {
    // Implementar som de notificação
    try {
      const audio = new Audio('/sounds/alert.mp3')
      audio.play().catch(e => console.log('Erro ao tocar som:', e))
    } catch (e) {
      console.log('Arquivo de som não encontrado:', e)
    }
  }

  const marcarAlertaComoLida = async (alertaId) => {
    try {
      await api.patch(`/antifraude/alertas/${alertaId}/marcar-lida`)
      
      setAlertas(prev => prev.filter(a => a.id !== alertaId))
      toast.success('Alerta marcada como lida')
    } catch (error) {
      console.error('Erro ao marcar alerta como lida:', error)
      toast.error('Erro ao marcar alerta como lida')
    }
  }

  const descartarAlerta = async (alertaId) => {
    try {
      await api.delete(`/antifraude/alertas/${alertaId}`)
      
      setAlertas(prev => prev.filter(a => a.id !== alertaId))
      toast.success('Alerta descartada com sucesso')
    } catch (error) {
      console.error('Erro ao descartar alerta:', error)
      toast.error('Erro ao descartar alerta')
    }
  }

  const getAlertaIcon = (tipo) => {
    switch (tipo) {
      case 'ALTO':
        return <AlertTriangle className="w-5 h-5 text-red-600" />
      case 'MEDIO':
        return <Shield className="w-5 h-5 text-yellow-600" />
      case 'BAIXO':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      default:
        return <Bell className="w-5 h-5 text-gray-600" />
    }
  }

  const getAlertaColor = (tipo) => {
    switch (tipo) {
      case 'ALTO':
        return 'border-red-200 bg-red-50'
      case 'MEDIO':
        return 'border-yellow-200 bg-yellow-50'
      case 'BAIXO':
        return 'border-green-200 bg-green-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  return (
    <div className="fixed top-4 right-4 z-50 w-96 max-h-96 overflow-hidden">
      {/* Botão de Notificações */}
      <div className="relative">
        <button
          onClick={() => setShowAlerts(!showAlerts)}
          className="relative p-2 bg-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200"
        >
          <Bell className={`w-5 h-5 ${alertas.length > 0 ? 'text-red-600 animate-pulse' : 'text-gray-600'}`} />
          {alertas.length > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {alertas.length}
            </span>
          )}
        </button>
      </div>

      {/* Dropdown de Alertas */}
      {showAlerts && (
        <div className="absolute top-12 right-0 w-full bg-white rounded-lg shadow-xl border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-800">Alertas Antifraude</h4>
              <button
                onClick={() => setShowAlerts(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <div className="max-h-64 overflow-y-auto">
            {alertas.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                <Bell className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p>Nenhuma alerta ativa</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {alertas.map((alerta) => (
                  <div
                    key={alerta.id}
                    className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${getAlertaColor(alerta.tipo)}`}
                    onClick={() => {
                      // Redirecionar para detalhes
                      window.open(`/dashboard/antifraude?alerta=${alerta.id}`)
                    }}
                  >
                    <div className="flex items-start space-x-3">
                      {getAlertaIcon(alerta.tipo)}
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <h5 className="font-medium text-gray-900">{alerta.titulo}</h5>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            alerta.tipo === 'ALTO' ? 'bg-red-100 text-red-800' :
                            alerta.tipo === 'MEDIO' ? 'bg-yellow-100 text-yellow-800' :
                            alerta.tipo === 'BAIXO' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {alerta.tipo}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{alerta.mensagem}</p>
                        <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                          <span>{new Date(alerta.data_criacao).toLocaleString('pt-BR')}</span>
                          <div className="flex space-x-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                marcarAlertaComoLida(alerta.id)
                              }}
                              className="text-blue-600 hover:text-blue-800"
                            >
                              Marcar lida
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                descartarAlerta(alerta.id)
                              }}
                              className="text-red-600 hover:text-red-800"
                            >
                              Descartar
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
