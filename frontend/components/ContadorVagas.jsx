'use client'

import { useState, useEffect } from 'react'

export default function ContadorVagas() {
  const [vagas, setVagas] = useState({
    total: 50,
    disponiveis: 0,
    ocupadas: 0,
    manutencao: 0
  })

  useEffect(() => {
    // Simulação de dados - substituir com API real
    const carregarVagas = () => {
      const ocupadas = Math.floor(Math.random() * 35) + 10
      const manutencao = Math.floor(Math.random() * 5)
      const disponiveis = vagas.total - ocupadas - manutencao

      setVagas({
        total: vagas.total,
        disponiveis,
        ocupadas,
        manutencao
      })
    }

    carregarVagas()
    const intervalo = setInterval(carregarVagas, 30000) // Atualiza a cada 30 segundos

    return () => clearInterval(intervalo)
  }, [])

  const getCorStatus = (disponiveis) => {
    if (disponiveis === 0) return 'text-danger-600'
    if (disponiveis < 10) return 'text-warning-600'
    return 'text-success-600'
  }

  const getMensagemStatus = (disponiveis) => {
    if (disponiveis === 0) return 'Lotado'
    if (disponiveis < 10) return 'Últimas Vagas'
    return 'Disponível'
  }

  return (
    <div className="bg-white border border-neutral-200 rounded-lg shadow-premium p-6">
      <h3 className="text-xl font-bold text-real-blue mb-4">Status das Vagas</h3>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center p-3 bg-success-50 rounded-lg">
          <div className={`text-3xl font-bold ${getCorStatus(vagas.disponiveis)}`}>
            {vagas.disponiveis}
          </div>
          <div className="text-sm text-neutral-600">Disponíveis</div>
        </div>
        
        <div className="text-center p-3 bg-danger-50 rounded-lg">
          <div className="text-3xl font-bold text-danger-600">
            {vagas.ocupadas}
          </div>
          <div className="text-sm text-neutral-600">Ocupadas</div>
        </div>
      </div>

      <div className="text-center p-3 bg-warning-50 rounded-lg mb-4">
        <div className="text-xl font-bold text-warning-600">
          {vagas.manutencao}
        </div>
        <div className="text-sm text-neutral-600">Manutenção</div>
      </div>

      <div className="border-t pt-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-neutral-600">Total de Vagas:</span>
          <span className="font-bold text-real-blue">{vagas.total}</span>
        </div>
        
        <div className="w-full bg-neutral-200 rounded-full h-3 overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-success-500 to-success-600 transition-all duration-500"
            style={{ width: `${(vagas.disponiveis / vagas.total) * 100}%` }}
          />
        </div>
        
        <div className="text-center mt-2">
          <span className={`text-sm font-semibold ${getCorStatus(vagas.disponiveis)}`}>
            {getMensagemStatus(vagas.disponiveis)}
          </span>
        </div>
      </div>
    </div>
  )
}
