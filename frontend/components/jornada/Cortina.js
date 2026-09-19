'use client'

import { useEffect, useRef, useState } from 'react'

/*
 * Cortina de veludo.
 *
 * Cobre a cena e abre quando ela entra na tela — o gesto de revelar o prêmio.
 * Abre uma vez só; depois de aberta não fecha mais no scroll de volta.
 * Com prefers-reduced-motion o CSS já nasce aberto e o JS não anima nada.
 */
export default function Cortina({ children, className = '' }) {
  const ref = useRef(null)
  const [aberta, setAberta] = useState(false)

  useEffect(() => {
    const node = ref.current
    if (!node) return

    const semMovimento =
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (semMovimento || typeof IntersectionObserver === 'undefined') {
      setAberta(true)
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return
          observer.unobserve(entry.target)
          window.setTimeout(() => setAberta(true), 220)
        })
      },
      { threshold: 0.3 }
    )

    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return (
    <div ref={ref} className={`jr-palco ${className}`.trim()}>
      {children}

      <div className="jr-cortina" data-jr-cortina={aberta ? 'aberta' : 'fechada'} aria-hidden="true">
        <div className="jr-cortina__folha jr-cortina__folha--esq" />
        <div className="jr-cortina__folha jr-cortina__folha--dir" />
        <div className="jr-cortina__sanefa" />
      </div>
    </div>
  )
}
