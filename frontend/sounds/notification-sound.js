// Som de notificação de pagamento aprovado/reserva
export const playNotificationSound = () => {
  try {
    // Tentar reproduzir som de sistema primeiro (mais compatível)
    const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT')
    audio.volume = 0.5
    audio.play().catch(e => {
      console.log('Fallback 1 falhou, tentando Web Audio API...')
      playWebAudioSound()
    })
    
  } catch (error) {
    console.log('Erro ao reproduzir som de notificação:', error)
    playWebAudioSound()
  }
}

// Web Audio API fallback
const playWebAudioSound = () => {
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    // Frequências para um som de "dinheiro/caixa"
    const frequencies = [523.25, 659.25, 783.99, 1046.50] // Dó, Mi, Sol, Dó agudo
    
    frequencies.forEach((freq, index) => {
      setTimeout(() => {
        oscillator.frequency.setValueAtTime(freq, audioContext.currentTime)
        oscillator.type = 'sine'
        
        gainNode.gain.setValueAtTime(0, audioContext.currentTime)
        gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01)
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2)
      }, index * 80)
    })
    
    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + 0.4)
    
  } catch (error) {
    console.log('Web Audio API falhou também:', error)
    // Último fallback: tentar áudio pré-carregado
    try {
      const audio = new Audio('/sounds/notification.mp3')
      audio.volume = 0.5
      audio.play().catch(e => console.log('Todos os fallbacks de áudio falharam'))
    } catch (e) {
      console.log('Nenhum método de áudio disponível')
    }
  }
}
