'use client'

import { useEffect, useRef } from 'react'

/*
 * Rastro de brilho que segue o ponteiro — o efeito de varinha.
 *
 * Cada movimento do mouse solta faíscas douradas que sobem devagar e
 * apagam. Desenhado em canvas com composição aditiva, porque só assim as
 * faíscas somam luz umas sobre as outras em vez de se recortarem.
 *
 * O canvas é fixo do tamanho da viewport e escuta o mouse na janela: assim
 * o efeito vale para a página inteira sem precisar de um canvas do tamanho
 * do documento, que em página longa custaria centenas de MB de memória.
 *
 * Não roda em tela de toque nem com prefers-reduced-motion, e o laço de
 * animação para sozinho quando não há mais faísca viva.
 */

const COR_QUENTE = '255, 244, 214'
const COR_OURO = '214, 168, 74'

export default function LuzPonteiro({ densidade = 2 }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const semEfeito =
      typeof window.matchMedia === 'function' &&
      (window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
        window.matchMedia('(hover: none)').matches)
    if (semEfeito) return

    const ctx = canvas.getContext('2d')
    const faiscas = []
    let dpr = 1
    let rodando = false
    let ultimo = 0

    const medir = () => {
      const largura = window.innerWidth
      const altura = window.innerHeight
      dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = Math.round(largura * dpr)
      canvas.height = Math.round(altura * dpr)
      canvas.style.width = `${largura}px`
      canvas.style.height = `${altura}px`
    }

    const nascer = (x, y) => {
      for (let i = 0; i < densidade; i++) {
        const grande = Math.random() < 0.22
        faiscas.push({
          x: x + (Math.random() - 0.5) * 14,
          y: y + (Math.random() - 0.5) * 14,
          vx: (Math.random() - 0.5) * 0.32,
          vy: -0.14 - Math.random() * 0.34, // sobem, como poeira em suspensão
          raio: grande ? 1.6 + Math.random() * 1.4 : 0.7 + Math.random() * 0.9,
          vida: 0,
          duracao: 620 + Math.random() * 760,
          brilho: grande,
        })
      }
    }

    const desenhar = (agora) => {
      const passo = ultimo ? agora - ultimo : 16
      ultimo = agora

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.save()
      ctx.scale(dpr, dpr)
      ctx.globalCompositeOperation = 'lighter'

      for (let i = faiscas.length - 1; i >= 0; i--) {
        const f = faiscas[i]
        f.vida += passo
        if (f.vida >= f.duracao) {
          faiscas.splice(i, 1)
          continue
        }

        const t = f.vida / f.duracao
        // acende rápido e apaga devagar
        const alfa = t < 0.18 ? t / 0.18 : 1 - (t - 0.18) / 0.82
        f.x += f.vx * passo * 0.06
        f.y += f.vy * passo * 0.06

        const raio = f.raio * (1 - t * 0.35)

        const halo = ctx.createRadialGradient(f.x, f.y, 0, f.x, f.y, raio * 6)
        halo.addColorStop(0, `rgba(${COR_QUENTE}, ${0.5 * alfa})`)
        halo.addColorStop(0.4, `rgba(${COR_OURO}, ${0.22 * alfa})`)
        halo.addColorStop(1, `rgba(${COR_OURO}, 0)`)
        ctx.fillStyle = halo
        ctx.beginPath()
        ctx.arc(f.x, f.y, raio * 6, 0, Math.PI * 2)
        ctx.fill()

        ctx.fillStyle = `rgba(${COR_QUENTE}, ${0.95 * alfa})`
        ctx.beginPath()
        ctx.arc(f.x, f.y, raio, 0, Math.PI * 2)
        ctx.fill()

        // as maiores ganham as quatro pontas da estrela
        if (f.brilho) {
          const braco = raio * 5.5
          ctx.strokeStyle = `rgba(${COR_QUENTE}, ${0.42 * alfa})`
          ctx.lineWidth = 0.8
          ctx.beginPath()
          ctx.moveTo(f.x - braco, f.y)
          ctx.lineTo(f.x + braco, f.y)
          ctx.moveTo(f.x, f.y - braco)
          ctx.lineTo(f.x, f.y + braco)
          ctx.stroke()
        }
      }

      ctx.restore()

      if (faiscas.length) {
        window.requestAnimationFrame(desenhar)
      } else {
        rodando = false
        ultimo = 0
      }
    }

    const ligar = () => {
      if (rodando) return
      rodando = true
      ultimo = 0
      window.requestAnimationFrame(desenhar)
    }

    // coordenadas de viewport: o canvas é fixo, então clientX/clientY servem direto
    const mover = (evento) => {
      nascer(evento.clientX, evento.clientY)
      ligar()
    }

    medir()
    window.addEventListener('mousemove', mover, { passive: true })
    window.addEventListener('resize', medir)

    return () => {
      window.removeEventListener('mousemove', mover)
      window.removeEventListener('resize', medir)
      faiscas.length = 0
    }
  }, [densidade])

  return <canvas ref={canvasRef} className="jr-faiscas" aria-hidden="true" />
}
