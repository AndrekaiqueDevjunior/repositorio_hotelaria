'use client'

import { useEffect, useRef } from 'react'

/*
 * Reveal no scroll — movimento seco, uma vez só.
 *
 * O elemento é renderizado no servidor já com o estado "pending" e o
 * <noscript> em JornadaBase devolve a visibilidade quando não há JS.
 * Se o navegador não tiver IntersectionObserver, ou se o hóspede pediu
 * menos movimento, o conteúdo aparece imediatamente.
 */
export default function Reveal({ as: Tag = 'div', delay = 0, className = '', children, ...rest }) {
  const ref = useRef(null)

  useEffect(() => {
    const node = ref.current
    if (!node) return

    const show = () => node.setAttribute('data-jr-reveal', 'in')

    const semMovimento =
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (semMovimento || typeof IntersectionObserver === 'undefined') {
      show()
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return
          observer.unobserve(entry.target)
          if (delay) window.setTimeout(show, delay)
          else show()
        })
      },
      { rootMargin: '0px 0px -12% 0px', threshold: 0.08 }
    )

    observer.observe(node)
    return () => observer.disconnect()
  }, [delay])

  return (
    <Tag
      ref={ref}
      data-jr-reveal="pending"
      className={`jr-reveal ${className}`.trim()}
      {...rest}
    >
      {children}
    </Tag>
  )
}
