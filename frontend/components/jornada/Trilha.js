'use client'

import { useEffect, useRef, useState } from 'react'

/*
 * Trilha dos quatro passos.
 *
 * Um trilho dourado atravessa os postos e se desenha conforme a cena sobe na
 * tela. Cada posto acende quando o fio chega nele — o avanço da página imita
 * o avanço na Jornada.
 *
 * Sem JS ou com prefers-reduced-motion o trilho nasce cheio e todos os postos
 * acesos, para o conteúdo nunca depender da animação.
 */
export default function Trilha({ passos }) {
  const ref = useRef(null)
  const [progresso, setProgresso] = useState(1)

  useEffect(() => {
    const node = ref.current
    if (!node) return

    const semMovimento =
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (semMovimento) return

    let pendente = false

    const medir = () => {
      pendente = false
      const caixa = node.getBoundingClientRect()
      const altura = window.innerHeight
      // começa quando o bloco entra a 82% da tela, termina quando passa de 42%
      const inicio = altura * 0.82
      const fim = altura * 0.42
      const bruto = (inicio - caixa.top) / (inicio - fim)
      setProgresso(Math.min(1, Math.max(0, bruto)))
    }

    const aoRolar = () => {
      if (pendente) return
      pendente = true
      window.requestAnimationFrame(medir)
    }

    setProgresso(0)
    medir()
    window.addEventListener('scroll', aoRolar, { passive: true })
    window.addEventListener('resize', aoRolar)
    return () => {
      window.removeEventListener('scroll', aoRolar)
      window.removeEventListener('resize', aoRolar)
    }
  }, [])

  return (
    <div className="jr-trilha" ref={ref} style={{ '--jr-p': progresso }}>
      <div className="jr-trilha__rail" aria-hidden="true">
        <span className="jr-trilha__fio" />
      </div>

      <ol className="jr-trilha__postos">
        {passos.map((passo, indice) => {
          // o posto acende quando o fio passa pelo centro dele
          const limite = (indice + 0.55) / passos.length
          const aceso = progresso >= limite
          return (
            <li className="jr-trilha__posto" key={passo.numeral} data-aceso={aceso ? 'sim' : 'nao'}>
              <span className="jr-trilha__marca" aria-hidden="true">
                <span className="jr-trilha__numeral">{passo.numeral}</span>
              </span>
              <div className="jr-trilha__corpo">
                <h3 className="jr-trilha__titulo">{passo.titulo}</h3>
                <p className="jr-texto jr-trilha__texto">{passo.texto}</p>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
