'use client'
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../lib/api'
import ToastNotification from '../components/ToastNotification'

const ToastContext = createContext()

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const [lastNotificationId, setLastNotificationId] = useState(null)
  const [userProfile, setUserProfile] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [lastCheck, setLastCheck] = useState(new Date().toISOString())

  // Obter perfil do usuário
  useEffect(() => {
    const getUserProfile = () => {
      try {
        const user = localStorage.getItem('user')
        if (user) {
          const userData = JSON.parse(user)
          setUserProfile(userData.perfil)
        }
      } catch (error) {
        console.error('Erro ao obter perfil do usuário:', error)
      }
    }

    getUserProfile()
  }, [])

  // Função para verificar notificações do servidor
  const checkServerNotifications = useCallback(async () => {
    if (isLoading || !userProfile) return
    
    setIsLoading(true)
    try {
      // Buscar notificações não lidas e recentes
      const res = await api.get('/notificacoes', {
        params: {
          lida: false,
          perfil: userProfile,
          atualizada_apos: lastCheck,
          limit: 10,
          order_by: 'data_criacao:desc'
        }
      })

      if (res.data && res.data.data) {
        const notificacoes = res.data.data
        
        // Atualizar a data da última verificação
        setLastCheck(new Date().toISOString())
        
        // Processar cada notificação recebida
        notificacoes.forEach(notif => {
          // Verificar se já exibimos esta notificação
          const notificationKey = `notif-${notif.id}`
          if (sessionStorage.getItem(notificationKey)) return
          
          // Marcar como exibida
          sessionStorage.setItem(notificationKey, 'true')
          
          // Adicionar ao toast
          addToast({
            id: `notif-${notif.id}`,
            titulo: notif.titulo,
            mensagem: notif.mensagem,
            tipo: notif.tipo || 'info',
            categoria: notif.categoria || 'sistema',
            url_acao: notif.urlAcao,
            reserva_id: notif.reservaId,
            pagamento_id: notif.pagamentoId,
            dados_adicionais: notif.dadosAdicionais
          })
          
          // Atualizar o último ID de notificação
          if (!lastNotificationId || notif.id > lastNotificationId) {
            setLastNotificationId(notif.id)
          }
        })
      }
    } catch (error) {
      // Silenciar erros de autenticação
      if (error.response?.status !== 401) {
        console.error('Erro ao verificar notificações:', error)
      }
    } finally {
      setIsLoading(false)
    }
  }, [userProfile, isLoading, lastCheck, lastNotificationId])

  // Configurar polling para notificações
  useEffect(() => {
    // Verificar a cada 30 segundos
    const interval = setInterval(checkServerNotifications, 30000)
    
    // Verificar imediatamente ao montar
    checkServerNotifications()
    
    return () => clearInterval(interval)
  }, [checkServerNotifications])

  // Função para tocar som de notificação
  const playNotificationSound = (tipo) => {
    try {
      // Criar contexto de áudio
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)
      
      // Configurar som baseado no tipo
      switch (tipo) {
        case 'critical':
          // Som de alerta (grave e urgente)
          oscillator.frequency.value = 200
          gainNode.gain.value = 0.3
          oscillator.start()
          oscillator.stop(audioContext.currentTime + 0.2)
          break
        case 'warning':
          // Som de aviso (médio)
          oscillator.frequency.value = 400
          gainNode.gain.value = 0.2
          oscillator.start()
          oscillator.stop(audioContext.currentTime + 0.15)
          break
        case 'success':
          // Som de sucesso (agudo e curto)
          oscillator.frequency.value = 600
          gainNode.gain.value = 0.15
          oscillator.start()
          oscillator.stop(audioContext.currentTime + 0.1)
          break
        case 'info':
        default:
          // Som suave (info)
          oscillator.frequency.value = 500
          gainNode.gain.value = 0.1
          oscillator.start()
          oscillator.stop(audioContext.currentTime + 0.08)
          break
      }
    } catch (error) {
      // Silenciar erros de áudio (navegadores antigos)
      console.log('Som de notificação não suportado')
    }
  }

  const addToast = (toast) => {
    const toastWithId = {
      ...toast,
      id: toast.id || Date.now() + Math.random()
    }
    setToasts(prev => [...prev, toastWithId])
    
    // Tocar som
    playNotificationSound(toast.tipo)
  }

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      
      {/* Container de Toasts - Canto inferior direito */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end pointer-events-none">
        <div className="pointer-events-auto">
          {toasts.map(toast => (
            <ToastNotification
              key={toast.id}
              toast={toast}
              onClose={removeToast}
            />
          ))}
        </div>
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast deve ser usado dentro de ToastProvider')
  }
  return context
}
