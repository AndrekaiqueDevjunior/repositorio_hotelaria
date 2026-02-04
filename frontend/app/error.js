'use client'

import { useEffect } from 'react'

export default function GlobalError({ error, reset }) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div style={{ maxWidth: 520, width: '100%', textAlign: 'center' }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Erro inesperado</h1>
        <p style={{ marginBottom: 16 }}>Ocorreu um erro ao carregar esta página.</p>
        <button
          type="button"
          onClick={() => reset()}
          style={{ padding: '10px 16px', borderRadius: 8, border: '1px solid #0b3b6e', background: '#0b3b6e', color: '#fff' }}
        >
          Tentar novamente
        </button>
      </div>
    </div>
  )
}
