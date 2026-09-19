'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CalendarCheck,
  Clock,
  Crown,
  Gift,
  LockKeyhole,
  ShieldCheck,
  Star,
  Truck,
  UserX,
  Users,
} from 'lucide-react'
import '../jornada-real.css'
import Reveal from '@/components/jornada/Reveal'
import LuzPonteiro from '@/components/jornada/LuzPonteiro'
import BotaoSom from '@/components/jornada/BotaoSom'
import JornadaNav from '@/components/jornada/JornadaNav'
import { Fleurao } from '@/components/jornada/Ornamentos'

// As quatro suítes da Jornada Real. Dupla e Real pontuam igual de propósito
// — não é erro de dado, é a regra vigente do programa.
const suites = [
  { nome: 'Suíte Luxo', pontos: 1 },
  { nome: 'Suíte Master', pontos: 2 },
  { nome: 'Suíte Dupla', pontos: 3 },
  { nome: 'Suíte Real', pontos: 3 },
]

const regras = [
  { Icone: CalendarCheck, texto: 'Pontos liberados após o check-out.' },
  { Icone: Clock, texto: 'Pode levar até 48h para aparecer.' },
  { Icone: UserX, texto: 'Cancelamentos não geram pontos.' },
  {
    Icone: AlertTriangle,
    texto: 'Os pontos poderão ser cancelados em casos de fraude, estorno, chargeback ou inconsistências.',
  },
  { Icone: Gift, texto: 'Prêmios podem variar conforme disponibilidade.' },
  {
    Icone: Users,
    texto: 'O hóspede declara que as informações fornecidas são verdadeiras e se responsabiliza por sua atualização.',
  },
  { Icone: LockKeyhole, texto: 'Seus dados são usados apenas para sua experiência.' },
  {
    Icone: Truck,
    texto: 'O tempo de entrega do prêmio pode variar conforme localidade, estoque e disponibilidade do parceiro logístico.',
  },
]

export default function EntrarJornadaReal() {
  const router = useRouter()
  const [aceitouTermos, setAceitouTermos] = useState(false)

  return (
    <main className="jr jr-entrar-pagina">
      <LuzPonteiro densidade={2} />

      <header className="jr-barra">
        <div className="jr-shell jr-barra__interno">
          <button
            type="button"
            className="jr-barra__voltar"
            aria-label="Voltar"
            onClick={() => router.push('/')}
          >
            <ArrowLeft size={18} strokeWidth={1.9} />
          </button>

          <div className="jr-barra__marca">
            <img src="/images/logo-jornada-real.png" alt="Jornada Real" />
          </div>

          <div className="jr-barra__acoes">
            <BotaoSom />
          </div>
        </div>
      </header>

      <section className="jr-cena jr-entrar" aria-label="Entrar na Jornada Real">
        <div className="jr-shell">
          <Reveal className="jr-cena__cabeca">
            <h1 className="jr-cena__titulo jr-ouro-metal">
              Como começa sua Jornada Real
            </h1>
            <Fleurao largura={260} />
            <p className="jr-lede">
              Entenda como o programa funciona e comece a conquistar experiências únicas.
            </p>
          </Reveal>

          <div className="jr-entrar__grade">
            <div>
              <Reveal className="jr-entrar__bloco">
                <h2 className="jr-painel__titulo">
                  <Crown size={17} aria-hidden="true" />
                  Como acumular pontos
                </h2>

                <ul className="jr-entrar__suites">
                  {suites.map((suite) => (
                    <li className="jr-entrar__linha" key={suite.nome}>
                      <span className="jr-entrar__nome">{suite.nome}</span>
                      <span className="jr-entrar__pontos">
                        <span className="jr-numeral">{suite.pontos}</span>
                        <span className="jr-entrar__pontos-rotulo">
                          {suite.pontos === 1 ? 'ponto / diária' : 'pontos / diária'}
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>

                <div className="jr-entrar__nota">
                  <CalendarCheck size={18} strokeWidth={1.9} aria-hidden="true" />
                  <span>Seus pontos são liberados após o check-out.</span>
                </div>
              </Reveal>
            </div>

            <div>
              <Reveal delay={80} className="jr-entrar__bloco">
                <h2 className="jr-painel__titulo">
                  <ShieldCheck size={18} strokeWidth={1.8} aria-hidden="true" />
                  Regras da Jornada Real
                </h2>

                <ul className="jr-entrar__regras">
                  {regras.map((regra) => (
                    <li className="jr-entrar__regra" key={regra.texto}>
                      <regra.Icone size={19} strokeWidth={1.8} aria-hidden="true" />
                      <p>{regra.texto}</p>
                    </li>
                  ))}
                </ul>

                <div className="jr-entrar__nota">
                  <Star size={18} strokeWidth={1.8} aria-hidden="true" />
                  <span>
                    Seus pontos são válidos dentro da Jornada Real e não expiram durante sua
                    participação ativa.
                  </span>
                </div>
              </Reveal>
            </div>
          </div>

          <Reveal delay={140}>
            <label className="jr-entrar__termos">
              <input
                type="checkbox"
                checked={aceitouTermos}
                onChange={(event) => setAceitouTermos(event.target.checked)}
              />
              <span>Li e concordo com todos os termos e regras da Jornada Real.</span>
            </label>

            <div className="jr-entrar__acao">
              <button
                type="button"
                className="jr-btn"
                disabled={!aceitouTermos}
                onClick={() => router.push('/reservar')}
              >
                <Crown size={20} strokeWidth={1.7} aria-hidden="true" />
                <span>Começar agora</span>
                <ArrowRight size={20} strokeWidth={1.9} aria-hidden="true" />
              </button>

              <p className="jr-entrar__privacidade">
                <LockKeyhole size={13} strokeWidth={2} aria-hidden="true" />
                Seus dados estão protegidos conosco.
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      <JornadaNav atual="/entrar-jornada-real" />
    </main>
  )
}
