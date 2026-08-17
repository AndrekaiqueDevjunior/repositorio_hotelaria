'use client'

import { useEffect, useState } from 'react'
import { demoAtivo } from '@/lib/demo-mock'

/*
 * Faixa do modo demonstração.
 *
 * Fica no layout raiz para valer em qualquer tela — a pessoa que testa entra
 * pela home e navega livre, sem recolocar `?demo=1` a cada link.
 *
 * Chamar demoAtivo() aqui também é o que LIGA o modo: ele grava a marca na
 * sessão. Sem isso, o modo só ligaria quando alguma tela fizesse a primeira
 * chamada de API — e telas sem chamada nenhuma ficariam de fora.
 *
 * Estilo inline de propósito: este componente entra em páginas que não
 * carregam o CSS da Jornada (área administrativa), e não pode depender dele.
 */
export default function FaixaDemo() {
  const [ativo, setAtivo] = useState(false)

  useEffect(() => setAtivo(demoAtivo()), [])

  if (!ativo) return null

  return (
    <div
      role="status"
      style={{
        position: 'relative',
        zIndex: 60,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '6px 16px',
        padding: '9px 20px',
        borderBottom: '1px solid rgba(205, 155, 64, 0.4)',
        background: 'rgba(94, 62, 8, 0.55)',
        color: '#f0d68f',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        fontSize: '0.75rem',
        letterSpacing: '0.04em',
        textAlign: 'center',
      }}
    >
      <b style={{ color: '#fff6de', fontWeight: 600 }}>Modo demonstração</b>
      <span style={{ color: 'rgba(239, 230, 210, 0.7)' }}>
        Dados fictícios · CPF 111.444.777-35 · código: qualquer 6 dígitos
      </span>
      <a
        href="?demo=0"
        style={{ color: '#f0d68f', textDecoration: 'underline', textUnderlineOffset: 3 }}
      >
        sair
      </a>
    </div>
  )
}
