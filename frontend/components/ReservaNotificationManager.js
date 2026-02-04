'use client'
import { useState, useEffect, useCallback, useRef } from 'react'
import { useToast } from '../contexts/ToastContext'
import { api } from '../lib/api'
import { playNotificationSound } from '../sounds/notification-sound'

export default function ReservaNotificationManager() {
  const { addToast } = useToast()
  const [lastReservaId, setLastReservaId] = useState(null)
  const [lastNotificationCheck, setLastNotificationCheck] = useState(new Date().toISOString())
  const [isLoading, setIsLoading] = useState(false)
  const [errorCount, setErrorCount] = useState(0)
  const [isPollingEnabled, setIsPollingEnabled] = useState(true)
  const intervalsRef = useRef({ notification: null, reservation: null })

  // Função para verificar notificações do servidor
  const checkServerNotifications = useCallback(async () => {
    if (isLoading || !isPollingEnabled) return
    
    setIsLoading(true)
    try {
      // Buscar notificações não lidas do servidor
      const res = await api.get('/notificacoes', {
        params: {
          lida: false,
          atualizada_apos: lastNotificationCheck,
          limit: 10,
          order_by: 'data_criacao:desc'
        }
      })

      if (res.data && res.data.data && res.data.data.length > 0) {
        // Atualizar a data da última verificação
        setLastNotificationCheck(new Date().toISOString())
        
        // Processar cada notificação recebida
        res.data.data.forEach(notificacao => {
          // Verificar se já exibimos esta notificação
          const notificationKey = `notif-${notificacao.id}`
          if (sessionStorage.getItem(notificationKey)) return
          
          // Marcar como exibida
          sessionStorage.setItem(notificationKey, 'true')
          
          // Adicionar ao toast com som e mensagem detalhada
          playNotificationSound() // Tocar som de notificação
          
          addToast({
            id: `notif-${notificacao.id}`,
            titulo: notificacao.titulo,
            mensagem: notificacao.mensagem,
            tipo: notificacao.tipo || 'info',
            categoria: notificacao.categoria || 'sistema',
            url_acao: notificacao.urlAcao,
            reserva_id: notificacao.reservaId,
            pagamento_id: notificacao.pagamentoId,
            dados_adicionais: notificacao.dadosAdicionais
          })
        })
      }
      
      // Resetar contador de erros em caso de sucesso
      setErrorCount(0)
    } catch (error) {
      console.error('Erro ao verificar notificações do servidor:', error)
      
      // Incrementar contador de erros
      setErrorCount(prev => {
        const newCount = prev + 1
        
        // Se houver muitos erros consecutivos, desabilitar polling temporariamente
        if (newCount >= 5) {
          console.warn('Muitos erros consecutivos. Desabilitando polling por 5 minutos.')
          setIsPollingEnabled(false)
          
          // Reabilitar após 5 minutos
          setTimeout(() => {
            setIsPollingEnabled(true)
            setErrorCount(0)
          }, 300000)
        }
        
        return newCount
      })
    } finally {
      setIsLoading(false)
    }
  }, [addToast, isLoading, lastNotificationCheck, isPollingEnabled])

  // Função para verificar novas reservas (para compatibilidade)
  const checkNewReservations = useCallback(async () => {
    if (!isPollingEnabled) return
    
    try {
      const res = await api.get('/reservas/ultimas', {
        params: {
          limit: 1,
          status: 'CONFIRMADA,CHECKIN,EM_ANDAMENTO',
          order_by: 'data_criacao:desc'
        }
      })

      if (res.data && res.data.data && res.data.data.length > 0) {
        const latestReserva = res.data.data[0]
        
        if (!lastReservaId || latestReserva.id > lastReservaId) {
          setLastReservaId(latestReserva.id)
          
          if (lastReservaId !== null) {
            // Tocar som de nova reserva
            playNotificationSound()
            
            // Formatar data do check-in
            const checkinDate = new Date(latestReserva.checkin_previsto)
            const dataFormatada = checkinDate.toLocaleDateString('pt-BR', {
              day: '2-digit',
              month: '2-digit',
              year: 'numeric'
            })
            
            addToast({
              id: `reserva-${latestReserva.id}`,
              titulo: '🏨 Nova Reserva Confirmada!',
              mensagem: `Foi feita uma reserva no dia ${dataFormatada}, o responsável que reservou foi ${latestReserva.cliente_nome || 'Cliente'}, para o cliente ${latestReserva.cliente_nome || latestReserva.responsavel_nome || 'Não informado'}`,
              tipo: 'success',
              categoria: 'reserva',
              url_acao: `/reservas/${latestReserva.id}`,
              reserva_id: latestReserva.id,
              dados_adicionais: {
                codigo_reserva: latestReserva.codigo_reserva,
                quarto_numero: latestReserva.quarto_numero,
                checkin_previsto: dataFormatada,
                valor_total: latestReserva.valor_diaria * (latestReserva.num_diarias || 1)
              }
            })
          }
        }
      }
      
      // Resetar contador de erros em caso de sucesso
      setErrorCount(0)
    } catch (error) {
      console.error('Erro ao verificar novas reservas:', error)
      
      // Incrementar contador de erros
      setErrorCount(prev => {
        const newCount = prev + 1
        
        // Se houver muitos erros consecutivos, desabilitar polling temporariamente
        if (newCount >= 5) {
          console.warn('Muitos erros consecutivos. Desabilitando polling por 5 minutos.')
          setIsPollingEnabled(false)
          
          // Reabilitar após 5 minutos
          setTimeout(() => {
            setIsPollingEnabled(true)
            setErrorCount(0)
          }, 300000)
        }
        
        return newCount
      })
    }
  }, [addToast, lastReservaId, isPollingEnabled])

  // Configurar os intervalos de verificação
  useEffect(() => {
    // Limpar intervalos existentes antes de criar novos
    if (intervalsRef.current.notification) {
      clearInterval(intervalsRef.current.notification)
    }
    if (intervalsRef.current.reservation) {
      clearInterval(intervalsRef.current.reservation)
    }
    
    // Verificar imediatamente ao montar
    checkServerNotifications()
    checkNewReservations()
    
    // Configurar intervalos apenas se polling estiver habilitado
    if (isPollingEnabled) {
      // Verificar notificações do servidor a cada 2 minutos (aumentado de 1 minuto)
      intervalsRef.current.notification = setInterval(checkServerNotifications, 120000)
      
      // Verificar reservas a cada 1 minuto (aumentado de 30 segundos)
      intervalsRef.current.reservation = setInterval(checkNewReservations, 60000)
    }
    
    // Limpar intervalos ao desmontar
    return () => {
      if (intervalsRef.current.notification) {
        clearInterval(intervalsRef.current.notification)
      }
      if (intervalsRef.current.reservation) {
        clearInterval(intervalsRef.current.reservation)
      }
    }
  }, [isPollingEnabled])

  return null // Este componente não renderiza nada
}
