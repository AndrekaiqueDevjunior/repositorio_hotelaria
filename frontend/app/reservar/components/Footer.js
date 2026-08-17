'use client'

import { Mail, MapPin, Phone } from 'lucide-react'
import { Fleurao } from '@/components/jornada/Ornamentos'

export default function Footer() {
  return (
    <footer className="jr-reservar__rodape">
      <div className="jr-shell jr-shell--estreito">
        <p className="jr-reservar__rodape-nome">Hotel Real Cabo Frio</p>
        <p className="jr-reservar__rodape-lema">O sonho é real</p>

        <Fleurao largura={220} />

        <div className="jr-reservar__rodape-dados">
          <span>
            <MapPin size={15} strokeWidth={1.8} aria-hidden="true" />
            Rua Enfermeiro Ricardo Sanches, 22 — Cabo Frio, RJ
          </span>
          <span>
            <Phone size={15} strokeWidth={1.8} aria-hidden="true" />
            (22) 2648-5900
          </span>
          <span>
            <Mail size={15} strokeWidth={1.8} aria-hidden="true" />
            contato@hotelrealcabofrio.com.br
          </span>
        </div>

        <p className="jr-reservar__rodape-legal">
          © {new Date().getFullYear()} Hotel Real Cabo Frio. Todos os direitos reservados.
        </p>
      </div>
    </footer>
  )
}
