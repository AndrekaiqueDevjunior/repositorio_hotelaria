'use client'

import Link from 'next/link'
import GoldParticles from '@/components/GoldParticles'

const suites = [
  { name: 'Suite Luxo', points: '1 ponto por diária' },
  { name: 'Suite Master', points: '2 pontos por diária' },
  { name: 'Suite Dupla', points: '3 pontos por diária' },
  { name: 'Suite Real', points: '3 pontos por diária' },
]

export default function EntrarJornadaReal() {
  return (
    <main className="relative min-h-screen w-full overflow-hidden bg-black text-white">
      <div className="absolute inset-0">
        <img
          src="/images/background-jornada-entrada.png"
          alt="Hotel Real Cabo Frio"
          className="h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-black/58" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(95,58,28,0.22)_0%,rgba(24,12,16,0.5)_46%,rgba(0,0,0,0.82)_100%)]" />
        <div className="absolute inset-y-0 left-0 w-48 bg-gradient-to-r from-yellow-200/20 via-yellow-900/10 to-transparent blur-xl" />
        <div className="absolute inset-y-0 right-0 w-48 bg-gradient-to-l from-yellow-200/20 via-yellow-900/10 to-transparent blur-xl" />
      </div>

      <GoldParticles />

      <section className="relative z-30 flex min-h-screen flex-col items-center justify-center px-6 py-8 text-center">
        <img
          src="/images/logo-jornada-real.png"
          alt="Hotel Real Cabo Frio - Jornada Real"
          className="h-auto w-full max-w-[470px] drop-shadow-[0_0_26px_rgba(212,175,55,0.4)]"
        />

        <div className="mt-5 w-full max-w-[790px] rounded-xl border-2 border-[#d4af37]/75 bg-[#0b0504] px-12 py-12 shadow-[0_0_42px_rgba(212,175,55,0.22),inset_0_0_18px_rgba(212,175,55,0.08)]">
          <h1 className="gold-title font-cinzel text-3xl font-semibold tracking-wide text-[#f3d474]">
            Como funciona a Jornada Real!
          </h1>

          <div className="mt-9 grid grid-cols-1 gap-6 sm:grid-cols-2">
            {suites.map((suite) => (
              <div
                key={suite.name}
                className="rounded-lg border border-[#d4af37]/40 bg-[#180d09] px-8 py-6 shadow-[inset_0_0_14px_rgba(212,175,55,0.04)]"
              >
                <h2 className="font-playfair text-xl text-[#f2d48b]">{suite.name}</h2>
                <p className="mt-4 font-playfair text-xl text-[#fff4d2]">
                  • {suite.points}
                </p>
              </div>
            ))}
          </div>

          <p className="mt-10 font-cinzel text-lg font-bold uppercase leading-relaxed tracking-wide text-[#f6dc8d]">
            *Você acumula pontos na Jornada Real
            <br />
            * Pontos creditados somente após o check-out!
          </p>

          <Link
            href="/reservar"
            className="mt-10 inline-flex min-h-[74px] w-full max-w-[500px] items-center justify-center rounded-full border border-yellow-100/40 bg-gradient-to-b from-[#ffe89a] via-[#e7b938] to-[#bf7d0e] px-12 py-6 font-cinzel text-xl font-bold uppercase tracking-wide text-black shadow-[0_12px_24px_rgba(0,0,0,0.38),0_0_28px_rgba(212,175,55,0.22)] transition-transform duration-300 hover:scale-[1.03]"
          >
            Começar minha Jornada Real
          </Link>
        </div>
      </section>

      <style jsx>{`
        .gold-title {
          text-shadow:
            0 1px 2px rgba(0, 0, 0, 0.9),
            0 0 10px rgba(212, 175, 55, 0.55),
            0 0 22px rgba(212, 175, 55, 0.3);
        }
      `}</style>
    </main>
  )
}
