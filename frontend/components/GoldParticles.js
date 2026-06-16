'use client'

import { useEffect, useRef } from 'react'

export default function GoldParticles() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return undefined

    const ctx = canvas.getContext('2d')
    if (!ctx) return undefined

    let particles = []
    let animationFrameId

    const resizeCanvas = () => {
      const pixelRatio = window.devicePixelRatio || 1

      canvas.width = window.innerWidth * pixelRatio
      canvas.height = window.innerHeight * pixelRatio
      canvas.style.width = `${window.innerWidth}px`
      canvas.style.height = `${window.innerHeight}px`
      ctx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0)
    }

    class Particle {
      constructor() {
        this.reset(true)
      }

      reset(startBelow = false) {
        this.x = Math.random() * window.innerWidth
        this.y = startBelow
          ? window.innerHeight + Math.random() * 220
          : Math.random() * window.innerHeight
        this.size = Math.random() * 3 + 1
        this.speedY = Math.random() * 1 + 0.3
        this.opacity = Math.random() * 0.5 + 0.3
      }

      update() {
        this.y -= this.speedY

        if (this.y < -10) {
          this.reset(true)
          this.y = window.innerHeight + 10
        }
      }

      draw() {
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(212, 175, 55, ${this.opacity})`
        ctx.shadowColor = '#D4AF37'
        ctx.shadowBlur = 15
        ctx.fill()
      }
    }

    const init = () => {
      particles = []
      for (let i = 0; i < 120; i += 1) {
        particles.push(new Particle())
      }
    }

    const handleResize = () => {
      resizeCanvas()
      init()
    }

    const animate = () => {
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)
      particles.forEach((particle) => {
        particle.update()
        particle.draw()
      })
      animationFrameId = requestAnimationFrame(animate)
    }

    resizeCanvas()
    init()
    animate()

    window.addEventListener('resize', handleResize)

    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-20" />
}
