// Som de notificação de pagamento aprovado/reserva
export const playNotificationSound = () => {
  try {
    // Criar áudio context
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    
    // Criar um som de "caixa registradora" ou "notificação"
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    // Frequências para um som agradável de notificação
    const frequencies = [523.25, 659.25, 783.99] // Dó, Mi, Sol (acorde maior)
    
    frequencies.forEach((freq, index) => {
      setTimeout(() => {
        oscillator.frequency.setValueAtTime(freq, audioContext.currentTime)
        oscillator.type = 'sine'
        
        // Envelope para som suave
        gainNode.gain.setValueAtTime(0, audioContext.currentTime)
        gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01)
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3)
      }, index * 100)
    })
    
    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + 0.4)
    
  } catch (error) {
    console.log('Erro ao reproduzir som de notificação:', error)
    // Fallback: tentar usar áudio pré-carregado se disponível
    try {
      const audio = new Audio('/sounds/notification.mp3')
      audio.volume = 0.5
      audio.play().catch(e => console.log('Fallback de áudio falhou:', e))
    } catch (e) {
      console.log('Fallback de áudio não disponível')
    }
  }
}
