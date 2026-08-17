'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import '../jornada-real.css'
import Reveal from '@/components/jornada/Reveal'
import LuzPonteiro from '@/components/jornada/LuzPonteiro'
import BotaoSom from '@/components/jornada/BotaoSom'
import { Fleurao } from '@/components/jornada/Ornamentos'

const termos = [
  'Pontos liberados após o check-out.',
  'Pode levar até 48h para aparecer.',
  'Cancelamentos não geram pontos.',
  'Os pontos são pessoais, vinculados ao cadastro do hóspede, intransferíveis e sem conversão em dinheiro, salvo regra expressa de campanha específica.',
  'O hotel poderá cancelar pontos lançados indevidamente em caso de fraude, abuso, erro operacional, estorno, chargeback, reembolso ou descumprimento deste termo.',
  'Prêmios podem variar conforme disponibilidade.',
  'O hóspede declara que as informações fornecidas são verdadeiras e se responsabiliza por sua atualização.',
  'Seus dados são usados apenas para sua experiência.',
  'Este termo não exclui nem limita direitos assegurados pela legislação aplicável.',
]

export default function TermosJornadaReal() {
  return (
    <main className="jr jr-termos-pagina">
      <LuzPonteiro densidade={2} />

      <header className="jr-barra">
        <div className="jr-shell jr-barra__interno">
          <Link href="/entrar-jornada-real" className="jr-barra__voltar" aria-label="Voltar">
            <ArrowLeft size={18} strokeWidth={1.9} />
          </Link>

          <div className="jr-barra__marca">
            <img src="/images/logo-jornada-real.png" alt="Jornada Real" />
          </div>

          <div className="jr-barra__acoes">
            <BotaoSom />
          </div>
        </div>
      </header>

      <section className="jr-cena jr-termos" aria-label="Termos da Jornada Real">
        <div className="jr-shell jr-shell--estreito">
          <Reveal className="jr-cena__cabeca">
            <h1 className="jr-cena__titulo jr-ouro-metal">Termos da Jornada Real</h1>
            <Fleurao largura={260} />
            <p className="jr-lede">
              Ao marcar &ldquo;Concordo&rdquo;, o hóspede declara que leu e aceita as regras abaixo.
            </p>
          </Reveal>

          <ol className="jr-termos__lista">
            {termos.map((termo, indice) => (
              <Reveal as="li" key={termo} delay={indice * 40} className="jr-termos__item">
                <span>{String(indice + 1).padStart(2, '0')}</span>
                <p>{termo}</p>
              </Reveal>
            ))}
          </ol>

          <div className="jr-niveis-pagina__acao">
            <Link href="/entrar-jornada-real" className="jr-btn jr-btn--contorno">
              Voltar
            </Link>
          </div>
        </div>
      </section>
    </main>
  )
}
