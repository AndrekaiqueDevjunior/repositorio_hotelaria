'use client'

import { ArrowLeft, Mail, Phone } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function Header() {
  const router = useRouter()

  return (
    <header className="relative z-40 border-b border-[#b9821b]/35 bg-black/42 backdrop-blur-[2px]">
      <div className="mx-auto grid w-full max-w-[820px] grid-cols-[72px_minmax(0,1fr)_72px] items-start px-4 py-5 sm:grid-cols-[88px_minmax(0,1fr)_88px] sm:px-8 sm:py-7">
        <button
          type="button"
          aria-label="Voltar"
          onClick={() => router.push('/entrar-jornada-real')}
          className="mt-1 grid h-16 w-16 place-items-center rounded-full border border-white/15 bg-black/24 text-white/80 shadow-[inset_0_0_14px_rgba(255,255,255,0.04)] transition hover:border-[#e5b84a]/60 hover:text-[#e5b84a]"
        >
          <ArrowLeft size={34} strokeWidth={1.6} />
        </button>

        <div className="min-w-0 justify-self-center text-center">
          <img
            src="/images/logo-jornada-real.png"
            alt="Hotel Real Cabo Frio"
            className="mx-auto h-auto w-[230px] max-w-full object-contain drop-shadow-[0_8px_18px_rgba(0,0,0,0.9)] sm:w-[330px]"
          />
          <div className="mx-auto mt-4 w-fit max-w-full space-y-3 font-serif text-[0.76rem] uppercase tracking-wide text-[#f4ead2] sm:text-[1.08rem]">
            <p className="flex items-center justify-center gap-4">
              <Phone size={22} className="shrink-0 text-[#d7a52c] drop-shadow-[0_0_8px_rgba(215,165,44,0.7)]" />
              <span>(22) 2648-5900</span>
            </p>
            <p className="flex items-center justify-center gap-4 break-all leading-snug">
              <Mail size={22} className="shrink-0 text-[#d7a52c] drop-shadow-[0_0_8px_rgba(215,165,44,0.7)]" />
              <span>contato@hotelrealcabofrio.com.br</span>
            </p>
          </div>
        </div>

        <div aria-hidden="true" />
      </div>
    </header>
  )
}
