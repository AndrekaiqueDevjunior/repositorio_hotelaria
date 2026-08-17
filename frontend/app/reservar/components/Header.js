'use client'

import { ArrowLeft, Mail, Phone } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function Header() {
  const router = useRouter()

  return (
    <header className="jr-reservar__cabeca">
      <div className="jr-shell jr-shell--estreito jr-reservar__cabeca-interno">
        <button
          type="button"
          aria-label="Voltar"
          onClick={() => router.push('/entrar-jornada-real')}
          className="jr-barra__voltar"
        >
          <ArrowLeft size={18} strokeWidth={1.9} />
        </button>

        <div className="jr-reservar__marca">
          <img src="/images/logo-jornada-real.png" alt="Hotel Real Cabo Frio" />

          <div className="jr-reservar__contato">
            <a href="tel:+552226485900">
              <Phone size={15} strokeWidth={1.8} aria-hidden="true" />
              (22) 2648-5900
            </a>
            <a href="mailto:contato@hotelrealcabofrio.com.br">
              <Mail size={15} strokeWidth={1.8} aria-hidden="true" />
              contato@hotelrealcabofrio.com.br
            </a>
          </div>
        </div>

        <span aria-hidden="true" />
      </div>
    </header>
  )
}
