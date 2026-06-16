'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CalendarCheck,
  Check,
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
import GoldParticles from '@/components/GoldParticles'

const suites = [
  {
    name: 'Suite Luxo',
    image: '/images/suites/suite-luxo.png',
    points: '1',
    label: 'ponto',
  },
  {
    name: 'Suite Master',
    image: '/images/suites/suite-master.png',
    points: '2',
    label: 'pontos',
  },
  {
    name: 'Suite Dupla',
    image: '/images/suites/suite-dupla.png',
    points: '3',
    label: 'pontos',
  },
  {
    name: 'Suite Real',
    image: '/images/background-jornada-real.jpeg',
    points: '3',
    label: 'pontos',
  },
]

const rules = [
  {
    icon: CalendarCheck,
    text: 'Pontos liberados após o check-out.',
  },
  {
    icon: Clock,
    text: 'Pode levar até 48h para aparecer.',
  },
  {
    icon: UserX,
    text: 'Cancelamentos não geram pontos.',
  },
  {
    icon: AlertTriangle,
    text: 'Os pontos poderão ser cancelados em casos de fraude, estorno, chargeback ou inconsistências.',
  },
  {
    icon: Gift,
    text: 'Prêmios podem variar conforme disponibilidade.',
  },
  {
    icon: Users,
    text: 'O hóspede declara que as informações fornecidas são verdadeiras e se responsabiliza por sua atualização.',
  },
  {
    icon: LockKeyhole,
    text: 'Seus dados são usados apenas para sua experiência.',
  },
  {
    icon: Truck,
    text: 'O tempo de entrega do prêmio pode variar conforme localidade, estoque e disponibilidade do parceiro logístico.',
  },
]

export default function EntrarJornadaReal() {
  const router = useRouter()
  const [acceptedTerms, setAcceptedTerms] = useState(false)

  return (
    <main className="entry-page">
      <GoldParticles />

      <section className="entry-shell">
        <header className="entry-header">
          <button
            type="button"
            className="back-button"
            aria-label="Voltar"
            onClick={() => router.push('/')}
          >
            <ArrowLeft size={22} strokeWidth={1.9} />
          </button>

          <img
            src="/images/logo-jornada-real.png"
            alt="Hotel Real Cabo Frio"
            className="entry-logo"
          />
        </header>

        <section className="entry-card" aria-labelledby="entry-title">
          <div className="entry-hero">
            <h1 id="entry-title">Jornada Real</h1>
            <p>
              Entenda como funciona o programa
              <br />
              e comece a conquistar experiências únicas.
            </p>
            <div className="hero-divider">
              <span />
              <Crown size={20} strokeWidth={1.7} />
              <span />
            </div>
          </div>

          <section className="points-section" aria-labelledby="points-title">
            <div className="section-heading">
              <span className="heading-icon">
                <span>$</span>
              </span>
              <h2 id="points-title">Como acumular pontos</h2>
            </div>

            <div className="suite-grid">
              {suites.map((suite, index) => (
                <article className="suite-card" key={suite.name}>
                  <div className="suite-name">
                    <span>{suite.name.split(' ')[0]}</span>
                    <strong>{suite.name.split(' ')[1]}</strong>
                  </div>
                  <img src={suite.image} alt={suite.name} />
                  <div className="points-badge">{index === 3 ? 3 : index + 1}</div>
                  <p>
                    <em>Ganhe</em>
                    <strong>{suite.points}</strong>
                    <span>{suite.label}</span>
                    <small>por diária</small>
                  </p>
                </article>
              ))}
            </div>

            <div className="auto-credit">
              <span>
                <Check size={20} strokeWidth={2} />
              </span>
              <p>
                Seus pontos são liberados após o check-out.
              </p>
            </div>
          </section>

          <section className="rules-section" aria-labelledby="rules-title">
            <div className="section-heading">
              <ShieldCheck size={20} strokeWidth={1.8} />
              <h2 id="rules-title">Regras da Jornada Real</h2>
            </div>

            <div className="rules-list">
              {rules.map((rule, index) => {
                const Icon = rule.icon
                return (
                  <article className="rule-item" key={rule.text}>
                    <div className="rule-icon">
                      <Icon size={24} strokeWidth={1.8} />
                    </div>
                    <span className="rule-number">{index + 1}</span>
                    <p>{rule.text}</p>
                  </article>
                )
              })}
            </div>

            <div className="validity-note">
              <Star size={24} strokeWidth={1.8} />
              <p>
                Seus pontos são válidos dentro da Jornada Real
                <br />
                e não expiram durante sua participação ativa.
              </p>
              <Crown className="note-crown" size={42} strokeWidth={1.4} />
            </div>
          </section>

          <section className="terms-section" aria-labelledby="terms-title">
            <div className="section-heading compact">
              <CalendarCheck size={18} strokeWidth={1.8} />
              <h2 id="terms-title">Aceite os termos</h2>
            </div>

            <label className="terms-check">
              <input
                type="checkbox"
                checked={acceptedTerms}
                onChange={(event) => setAcceptedTerms(event.target.checked)}
              />
              <span>Li e concordo com todos os termos e regras da Jornada Real.</span>
            </label>
          </section>

          <button
            type="button"
            disabled={!acceptedTerms}
            onClick={() => router.push('/reservar')}
            className="start-button"
          >
            <Crown size={32} strokeWidth={1.6} />
            <span>Começar agora</span>
            <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
            <ArrowRight size={26} strokeWidth={1.9} />
          </button>

          <p className="privacy-note">
            <LockKeyhole size={13} strokeWidth={2} />
            Seus dados estão protegidos conosco.
          </p>
        </section>
      </section>

      <style jsx global>{`
        .entry-page {
          --gold: #f6c637;
          --gold-soft: #ffe08a;
          --panel: rgba(5, 5, 4, 0.82);
          --line: rgba(246, 198, 55, 0.64);
          min-height: 100svh;
          overflow-x: hidden;
          color: #fff1d6;
          background:
            radial-gradient(circle at 50% 0%, rgba(143, 82, 12, 0.16), transparent 22rem),
            radial-gradient(circle at 50% 75%, rgba(246, 198, 55, 0.1), transparent 18rem),
            #020302;
          font-family: 'Playfair Display', serif;
        }

        body:has(.entry-page) button[aria-label^=Abrir][aria-label*=configura],
        body:has(.entry-page) nextjs-portal {
          display: none;
        }

        .entry-page::before {
          content: '';
          position: fixed;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          background:
            radial-gradient(circle at 0% 64%, rgba(246, 198, 55, 0.2) 0 1px, transparent 2px),
            radial-gradient(circle at 100% 76%, rgba(246, 198, 55, 0.18) 0 1px, transparent 2px);
          background-size: 17px 17px, 19px 19px;
          opacity: 0.48;
        }

        .entry-shell {
          position: relative;
          z-index: 30;
          width: min(100% - 10px, 430px);
          margin: 0 auto;
          padding: 6px 0 10px;
        }

        .entry-header {
          display: grid;
          grid-template-columns: 38px 1fr 38px;
          align-items: start;
          min-height: 82px;
        }

        .back-button {
          width: 34px;
          height: 34px;
          display: grid;
          place-items: center;
          color: var(--gold);
          background: rgba(0, 0, 0, 0.24);
          border: 1.4px solid var(--gold);
          border-radius: 50%;
          box-shadow: 0 0 14px rgba(246, 198, 55, 0.17);
          cursor: pointer;
        }

        .entry-logo {
          width: clamp(188px, 54vw, 230px);
          height: auto;
          justify-self: center;
          filter: drop-shadow(0 5px 14px rgba(0, 0, 0, 0.86));
        }

        .entry-card {
          margin-top: -6px;
          padding: 9px 9px 12px;
          border: 1.4px solid rgba(176, 114, 16, 0.68);
          border-radius: 16px;
          background:
            linear-gradient(180deg, rgba(255, 216, 96, 0.04), rgba(0, 0, 0, 0.76)),
            rgba(0, 0, 0, 0.72);
          box-shadow:
            0 0 26px rgba(246, 198, 55, 0.15),
            inset 0 0 30px rgba(246, 198, 55, 0.06);
        }

        .entry-hero {
          text-align: center;
        }

        .entry-hero h1 {
          margin: 0;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(2.55rem, 12vw, 3.38rem);
          font-weight: 700;
          line-height: 0.95;
          text-transform: uppercase;
          text-shadow:
            0 2px 3px rgba(0, 0, 0, 0.95),
            0 0 14px rgba(246, 198, 55, 0.52);
        }

        .entry-hero p {
          margin: 6px auto 0;
          color: #fff5df;
          font-size: clamp(0.84rem, 3.1vw, 0.98rem);
          line-height: 1.25;
        }

        .hero-divider {
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          align-items: center;
          gap: 8px;
          width: min(170px, 48vw);
          margin: 7px auto 0;
          color: var(--gold);
        }

        .hero-divider span {
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(246, 198, 55, 0.74), transparent);
        }

        .section-heading {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 8px 0 6px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          text-transform: uppercase;
        }

        .section-heading h2 {
          margin: 0;
          font-size: clamp(0.85rem, 3.3vw, 1rem);
          font-weight: 700;
        }

        .section-heading::after {
          content: '';
          flex: 1;
          height: 1px;
          background: linear-gradient(90deg, rgba(246, 198, 55, 0.72), transparent);
        }

        .section-heading.compact {
          margin-top: 9px;
        }

        .heading-icon {
          width: 24px;
          height: 24px;
          display: grid;
          place-items: center;
          border: 1px solid var(--gold);
          border-radius: 50%;
          color: var(--gold);
          font-family: Georgia, serif;
          font-size: 0.86rem;
          font-weight: 700;
        }

        .suite-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 4px;
        }

        .suite-card {
          position: relative;
          overflow: hidden;
          min-height: 160px;
          border: 1px solid rgba(246, 198, 55, 0.72);
          border-radius: 5px;
          background: #050505;
          text-align: center;
          box-shadow: inset 0 0 14px rgba(246, 198, 55, 0.05);
        }

        .suite-name {
          height: 34px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          color: var(--gold);
          background: linear-gradient(180deg, #130c04, #020202);
          border-bottom: 1px solid rgba(246, 198, 55, 0.46);
          font-family: 'Cinzel', serif;
          font-size: clamp(0.56rem, 2.55vw, 0.7rem);
          line-height: 1.05;
          text-transform: uppercase;
        }

        .suite-name strong {
          font-size: 1.05em;
        }

        .suite-card img {
          width: 100%;
          height: 78px;
          display: block;
          object-fit: cover;
          filter: saturate(0.95) contrast(1.07);
        }

        .points-badge {
          position: relative;
          z-index: 2;
          width: 30px;
          height: 30px;
          display: grid;
          place-items: center;
          margin: -15px auto 2px;
          color: #1c1204;
          background: linear-gradient(180deg, #ffe27e, #d99317);
          border: 1px solid #ffe08a;
          border-radius: 50%;
          font-family: 'Cinzel', serif;
          font-size: 1.1rem;
          font-weight: 700;
          box-shadow: 0 0 12px rgba(246, 198, 55, 0.32);
        }

        .suite-card p {
          margin: 0 0 5px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          line-height: 1;
          text-transform: lowercase;
        }

        .suite-card p strong,
        .suite-card p span,
        .suite-card p small,
        .suite-card p em {
          display: block;
        }

        .suite-card p em {
          color: #fff5df;
          font-size: 0.62rem;
          font-style: normal;
        }

        .suite-card p strong {
          font-size: 0.84rem;
        }

        .suite-card p span {
          font-size: 0.72rem;
          font-weight: 700;
        }

        .suite-card p small {
          color: #fff5df;
          font-size: 0.65rem;
        }

        .auto-credit,
        .validity-note,
        .terms-check,
        .rule-item {
          border: 1px solid rgba(154, 94, 12, 0.82);
          background: rgba(9, 8, 6, 0.78);
          box-shadow: inset 0 0 15px rgba(246, 198, 55, 0.04);
        }

        .auto-credit {
          display: grid;
          grid-template-columns: 36px 1fr;
          gap: 8px;
          align-items: center;
          margin-top: 6px;
          padding: 7px 8px;
          border-radius: 8px;
        }

        .auto-credit span {
          width: 25px;
          height: 25px;
          display: grid;
          place-items: center;
          justify-self: center;
          color: var(--gold);
          border: 1.2px solid var(--gold);
          border-radius: 50%;
        }

        .auto-credit p {
          margin: 0;
          color: #fff3dc;
          font-size: clamp(0.72rem, 2.8vw, 0.86rem);
          line-height: 1.22;
        }

        .auto-credit strong {
          color: var(--gold);
        }

        .rules-list {
          display: grid;
          gap: 4px;
        }

        .rule-item {
          display: grid;
          grid-template-columns: 31px 22px 1fr;
          gap: 7px;
          align-items: center;
          min-height: 42px;
          padding: 5px 7px;
          border-radius: 7px;
        }

        .rule-icon {
          display: grid;
          place-items: center;
          color: var(--gold);
        }

        .rule-number {
          width: 21px;
          height: 21px;
          display: grid;
          place-items: center;
          color: #1b1104;
          background: linear-gradient(180deg, #ffe27d, #d28b12);
          border-radius: 50%;
          font-family: 'Cinzel', serif;
          font-size: 0.72rem;
          font-weight: 700;
        }

        .rule-item p {
          margin: 0;
          color: #fff2d9;
          font-size: clamp(0.63rem, 2.55vw, 0.76rem);
          line-height: 1.16;
        }

        .validity-note {
          position: relative;
          display: grid;
          grid-template-columns: 38px 1fr;
          gap: 8px;
          align-items: center;
          min-height: 44px;
          margin-top: 5px;
          padding: 6px 8px;
          border-radius: 8px;
          color: var(--gold);
          overflow: hidden;
        }

        .validity-note p {
          margin: 0;
          color: var(--gold);
          font-size: clamp(0.76rem, 3vw, 0.86rem);
          line-height: 1.18;
          font-weight: 700;
        }

        .note-crown {
          position: absolute;
          right: 9px;
          bottom: 1px;
          color: rgba(246, 198, 55, 0.16);
        }

        .terms-check {
          display: grid;
          grid-template-columns: 22px 1fr;
          gap: 9px;
          align-items: center;
          padding: 8px 11px;
          border-radius: 7px;
          color: #fff2d9;
          cursor: pointer;
        }

        .terms-check input {
          width: 18px;
          height: 18px;
          margin: 0;
          appearance: none;
          display: grid;
          place-items: center;
          border: 1.4px solid #fff2d1;
          border-radius: 2px;
          background: rgba(0, 0, 0, 0.34);
          cursor: pointer;
        }

        .terms-check input:focus,
        .terms-check input:focus-visible {
          outline: 1px solid var(--gold);
          outline-offset: 2px;
        }

        .terms-check input:checked {
          border-color: var(--gold);
          background: linear-gradient(180deg, #ffe27e, #c57d0b);
        }

        .terms-check input:checked::after {
          content: '';
          width: 9px;
          height: 5px;
          transform: rotate(-45deg);
          border-left: 2px solid #1c1204;
          border-bottom: 2px solid #1c1204;
        }

        .terms-check span {
          font-size: clamp(0.7rem, 2.9vw, 0.84rem);
          line-height: 1.2;
        }

        .start-button {
          width: 100%;
          min-height: 52px;
          display: grid;
          grid-template-columns: 34px 1fr 34px 28px;
          align-items: center;
          gap: 5px;
          margin-top: 8px;
          padding: 0 13px;
          color: #160f05;
          background: linear-gradient(180deg, #ffe27e 0%, #d99a1b 58%, #ad6706 100%);
          border: 1px solid #ffe799;
          border-radius: 18px;
          box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.58),
            0 11px 22px rgba(0, 0, 0, 0.46),
            0 0 18px rgba(246, 198, 55, 0.22);
          font-family: 'Cinzel', serif;
          font-size: clamp(0.72rem, 3vw, 0.92rem);
          font-weight: 700;
          text-transform: uppercase;
          cursor: pointer;
          transition: opacity 160ms ease, transform 160ms ease;
        }

        .start-button span {
          white-space: nowrap;
        }

        .start-button:not(:disabled):hover {
          transform: translateY(-1px);
        }

        .start-button:disabled {
          cursor: not-allowed;
          opacity: 0.58;
          filter: grayscale(0.3);
        }

        .start-button svg:first-child {
          color: rgba(83, 54, 6, 0.5);
          fill: rgba(83, 54, 6, 0.16);
        }

        .privacy-note {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          margin: 7px 0 0;
          color: var(--gold);
          font-size: clamp(0.68rem, 2.7vw, 0.78rem);
        }

        @media (max-width: 370px) {
          .entry-shell {
            width: min(100% - 6px, 430px);
          }

          .entry-card {
            padding: 8px 7px 10px;
          }

          .suite-grid {
            gap: 3px;
          }

          .suite-card {
            min-height: 154px;
          }

          .suite-card img {
            height: 72px;
          }

          .rule-item {
            grid-template-columns: 28px 20px 1fr;
            gap: 5px;
            padding-inline: 5px;
          }

          .start-button {
            grid-template-columns: 30px 1fr 28px 24px;
            padding-inline: 8px;
            font-size: 0.7rem;
          }
        }

        @media (min-width: 700px) and (max-width: 899px) {
          .entry-shell {
            width: min(430px, calc(100% - 24px));
          }
        }

        @media (min-width: 900px) {
          .entry-page {
            background:
              radial-gradient(circle at 18% 12%, rgba(143, 82, 12, 0.18), transparent 28rem),
              radial-gradient(circle at 82% 22%, rgba(246, 198, 55, 0.1), transparent 26rem),
              radial-gradient(circle at 50% 84%, rgba(92, 36, 145, 0.12), transparent 30rem),
              #020302;
          }

          .entry-shell {
            width: min(1180px, calc(100% - 64px));
            padding: 20px 0 28px;
          }

          .entry-header {
            min-height: 98px;
            grid-template-columns: 48px 1fr 48px;
            align-items: center;
          }

          .back-button {
            width: 40px;
            height: 40px;
          }

          .entry-logo {
            width: clamp(250px, 21vw, 340px);
          }

          .entry-card {
            display: grid;
            grid-template-columns: minmax(0, 1.08fr) minmax(0, 0.92fr);
            gap: 18px;
            margin-top: 0;
            padding: 24px;
            border-radius: 18px;
          }

          .entry-hero,
          .terms-section,
          .start-button,
          .privacy-note {
            grid-column: 1 / -1;
          }

          .entry-hero {
            max-width: 760px;
            margin: 0 auto 2px;
          }

          .entry-hero h1 {
            font-size: clamp(3.2rem, 5.2vw, 5.4rem);
          }

          .entry-hero p {
            font-size: 1.08rem;
          }

          .points-section {
            grid-column: 1;
          }

          .rules-section {
            grid-column: 2;
          }

          .section-heading {
            margin-top: 0;
          }

          .section-heading h2 {
            font-size: 1.02rem;
          }

          .suite-grid {
            gap: 10px;
          }

          .suite-card {
            min-height: 238px;
            border-radius: 10px;
          }

          .suite-name {
            height: 48px;
            font-size: 0.78rem;
          }

          .suite-card img {
            height: 120px;
          }

          .points-badge {
            width: 40px;
            height: 40px;
            margin-top: -20px;
            font-size: 1.35rem;
          }

          .suite-card p em {
            font-size: 0.72rem;
          }

          .suite-card p strong {
            font-size: 1.02rem;
          }

          .suite-card p span {
            font-size: 0.84rem;
          }

          .suite-card p small {
            font-size: 0.74rem;
          }

          .auto-credit,
          .validity-note {
            min-height: 58px;
            margin-top: 10px;
            padding: 10px 12px;
            border-radius: 10px;
          }

          .rules-list {
            gap: 8px;
          }

          .rule-item {
            min-height: 58px;
            padding: 9px 11px;
            border-radius: 10px;
          }

          .rule-item p {
            font-size: 0.84rem;
          }

          .terms-section {
            width: min(720px, 100%);
            justify-self: center;
          }

          .terms-check {
            min-height: 50px;
            padding: 11px 14px;
          }

          .start-button {
            width: min(420px, 100%);
            justify-self: center;
            min-height: 56px;
            margin-top: 0;
          }
        }
      `}</style>
    </main>
  )
}
