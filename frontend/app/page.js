'use client'

import Link from 'next/link'
import GoldParticles from '@/components/GoldParticles'

const benefits = [
  {
    title: 'O retorno do sonho',
    text: 'Porque algumas histórias merecem continuação!',
    image: '/images/premios/o-retorno-do-sonho.png',
  },
  {
    title: 'Rituais do Real',
    text: 'Transforme rotina em prazer!',
    image: '/images/premios/rituais-do-real.png',
  },
  {
    title: 'Tecnologia Real',
    text: 'Registre cada conquista',
    image: '/images/premios/tecnologia-real.png',
  },
]

export default function JornadaReal() {
  return (
    <div className="relative min-h-screen w-full bg-black text-white overflow-hidden">
      <div className="absolute inset-0">
        <img
          src="/images/background-jornada-real.jpeg"
          alt="Hotel Real"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-black/60" />
      </div>

      <GoldParticles />

      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center text-center px-5 py-8 md:py-6">
        <div className="mb-9 w-full max-w-[760px]">
          <img
            src="/images/logo-jornada-real.png"
            alt="Hotel Real Cabo Frio - Jornada Real"
            className="mx-auto h-auto w-full drop-shadow-[0_0_18px_rgba(250,204,21,0.25)]"
          />
        </div>

        <p className="gold-text-glow mt-2 text-5xl md:text-7xl font-playfair italic text-yellow-300">
          O sonho é Real
        </p>

        <div className="grid md:grid-cols-3 gap-10 mt-16 w-full max-w-[1500px]">
          {benefits.map((benefit) => (
            <div className="text-center" key={benefit.title}>
              <div className="h-60 md:h-80 rounded-xl border border-yellow-500/30 bg-black/40 backdrop-blur-md shadow-2xl shadow-black/30 flex items-center justify-center overflow-hidden">
                <img src={benefit.image} alt={benefit.title} className="h-full w-full object-contain" />
              </div>
              <h3 className={`${benefit.title === 'O retorno do sonho' || benefit.title === 'Rituais do Real' || benefit.title === 'Tecnologia Real' ? 'gold-text-glow ' : ''}mt-8 text-yellow-300 font-playfair italic text-5xl mb-5`}>
                {benefit.title}
              </h3>
              <p className="text-gray-200 text-2xl leading-relaxed">
                {benefit.text}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-16 flex flex-col items-center">
          <h1 className="gold-text-glow font-greatVibes text-6xl md:text-8xl text-yellow-300">
            Jornada Real
          </h1>
          <p className="mt-6 text-3xl md:text-4xl font-semibold text-gray-100 drop-shadow">
            Reserve, acumule, conquiste!
          </p>

          <Link
            href="/entrar-jornada-real"
            className="mt-9 bg-gradient-to-r from-yellow-400 to-yellow-600 text-black font-semibold px-14 py-6 rounded-full text-2xl shadow-lg hover:scale-105 transition-all duration-300"
          >
            Entrar na Jornada Real
          </Link>

          <p className="mt-6 text-2xl text-gray-200 font-semibold italic">ou</p>

          <Link
            href="/consultar-pontos"
            className="mt-6 bg-gradient-to-r from-yellow-400 to-yellow-600 text-black font-semibold px-14 py-6 rounded-full text-2xl shadow-lg hover:scale-105 transition-all duration-300"
          >
            Consultar minha Jornada Real
          </Link>
        </div>
      </div>

      <div className="absolute inset-x-0 bottom-0 h-[46vh] pointer-events-none bg-[radial-gradient(ellipse_at_center,rgba(0,0,0,0.78)_0%,rgba(0,0,0,0.5)_38%,rgba(0,0,0,0.2)_66%,transparent_100%)] blur-2xl" />
      <div className="absolute inset-x-0 bottom-0 h-[34vh] pointer-events-none bg-[radial-gradient(ellipse_at_center,rgba(212,175,55,0.16)_0%,rgba(165,115,20,0.08)_42%,transparent_72%)] blur-xl" />

      <style jsx>{`
        .gold-text-glow {
          color: #f8d66d;
          text-shadow:
            0 2px 3px rgba(0, 0, 0, 0.75),
            0 0 6px rgba(255, 244, 190, 0.95),
            0 0 14px rgba(255, 214, 90, 0.9),
            0 0 30px rgba(212, 175, 55, 0.85),
            0 0 56px rgba(212, 135, 20, 0.65),
            0 0 82px rgba(150, 95, 8, 0.45);
        }
      `}</style>
    </div>
  )
}
