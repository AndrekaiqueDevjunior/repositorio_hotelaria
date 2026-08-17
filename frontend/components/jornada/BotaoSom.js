'use client'

import { useEffect, useState } from 'react'
import { alternarSom, somLigado } from './som'

/*
 * Liga e desliga os efeitos sonoros.
 *
 * O estado inicial só é lido depois da montagem: o valor mora no
 * localStorage, e ler no servidor deixaria o HTML divergindo do cliente.
 */
export default function BotaoSom() {
  const [ligado, setLigado] = useState(true)
  const [montado, setMontado] = useState(false)

  useEffect(() => {
    setLigado(somLigado())
    setMontado(true)
  }, [])

  const alternar = () => setLigado(alternarSom())

  return (
    <button
      type="button"
      className="jr-som"
      onClick={alternar}
      aria-pressed={montado ? ligado : undefined}
      aria-label={ligado ? 'Desligar os sons' : 'Ligar os sons'}
      title={ligado ? 'Desligar os sons' : 'Ligar os sons'}
    >
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M4 9.5h3.2L12 5.4v13.2L7.2 14.5H4z"
          fill="currentColor"
        />
        {ligado ? (
          <>
            <path d="M15.6 9.1a4 4 0 0 1 0 5.8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            <path d="M18.2 6.6a7.6 7.6 0 0 1 0 10.8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          </>
        ) : (
          <path d="M16 9.6l5 4.8M21 9.6l-5 4.8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        )}
      </svg>
      <span>{ligado ? 'Som' : 'Mudo'}</span>
    </button>
  )
}
