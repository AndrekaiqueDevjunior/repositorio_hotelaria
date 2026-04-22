'use client'

import { useState, useEffect } from 'react'

export default function Cronometro() {
  const [tempo, setTempo] = useState({ horas: 0, minutos: 0, segundos: 0 })

  useEffect(() => {
    const inicio = Date.now()

    const intervalo = setInterval(() => {
      const agora = Date.now()
      const diferenca = agora - inicio

      const horas = Math.floor(diferenca / (1000 * 60 * 60))
      const minutos = Math.floor((diferenca % (1000 * 60 * 60)) / (1000 * 60))
      const segundos = Math.floor((diferenca % (1000 * 60)) / 1000)

      setTempo({ horas, minutos, segundos })
    }, 1000)

    return () => clearInterval(intervalo)
  }, [])

  const formatarNumero = (numero) => numero.toString().padStart(2, '0')

  return (
    <div className="bg-real-blue text-real-white p-6 rounded-lg shadow-premium flex flex-col items-center justify-center min-h-[200px]">
      <h3 className="text-xl font-bold mb-4 text-center">Tempo de Operação</h3>
      <div className="text-4xl font-mono font-bold text-center">
        {formatarNumero(tempo.horas)}:{formatarNumero(tempo.minutos)}:{formatarNumero(tempo.segundos)}
      </div>
      <p className="text-sm mt-2 opacity-80 text-center">"Reserve nas próximas 72 horas e ganhe +3 pontos extras"🔥</p>
    </div>
  )
}
