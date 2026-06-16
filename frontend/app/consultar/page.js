'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft,
  ArrowRight,
  Crown,
  LockKeyhole,
  Search,
  ShieldCheck,
  User,
} from 'lucide-react'
import GoldParticles from '@/components/GoldParticles'

export default function ConsultarJornadaReal() {
  const router = useRouter()
  const [cpf, setCpf] = useState('')
  const [error, setError] = useState('')

  const formatCPF = (value) => {
    const numbers = value.replace(/\D/g, '').slice(0, 11)

    if (numbers.length <= 3) return numbers
    if (numbers.length <= 6) return `${numbers.slice(0, 3)}.${numbers.slice(3)}`
    if (numbers.length <= 9) {
      return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`
    }

    return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9)}`
  }

  const handleSubmit = (event) => {
    event.preventDefault()

    const cpfLimpo = cpf.replace(/\D/g, '')
    if (cpfLimpo.length !== 11) {
      setError('Digite um CPF válido.')
      return
    }

    setError('')
    router.push(`/consultar-pontos?cpf=${cpfLimpo}`)
  }

  return (
    <main className="cpf-page">
      <GoldParticles />

      <section className="cpf-shell">
        <header className="cpf-header">
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
            className="cpf-logo"
          />
        </header>

        <section className="cpf-intro" aria-labelledby="cpf-title">
          <h1 id="cpf-title">
            Consulte sua
            <br />
            Jornada Real
          </h1>

          <div className="title-divider">
            <span />
            <Crown size={22} strokeWidth={1.7} />
            <span />
          </div>

          <p>
            Descubra o quanto você já avançou
            <br />
            na sua Jornada Real.
          </p>
        </section>

        <form className="cpf-card" onSubmit={handleSubmit}>
          <div className="search-orb" aria-hidden="true">
            <Search size={48} strokeWidth={1.8} />
          </div>

          <label htmlFor="cpf">Digite seu CPF para continuar</label>

          <div className="cpf-input-wrap">
            <User size={22} strokeWidth={1.7} aria-hidden="true" />
            <input
              id="cpf"
              type="text"
              inputMode="numeric"
              autoComplete="off"
              value={cpf}
              onChange={(event) => {
                setCpf(formatCPF(event.target.value))
                setError('')
              }}
              placeholder="000.000.000-00"
              maxLength={14}
              aria-invalid={Boolean(error)}
            />
          </div>

          {error && <p className="cpf-error">{error}</p>}

          <button type="submit" className="submit-button">
            <span>Ver minha jornada</span>
            <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
            <ArrowRight size={24} strokeWidth={1.9} />
          </button>

          <p className="privacy-note">
            <LockKeyhole size={13} strokeWidth={2} />
            Seus dados estão protegidos conosco.
          </p>
        </form>

        <div className="hotel-showcase" aria-hidden="true" />

        <article className="privacy-card">
          <div className="privacy-icon">
            <ShieldCheck size={34} strokeWidth={1.8} />
          </div>
          <div>
            <h2>Segurança e Privacidade</h2>
            <p>
              Suas informações são utilizadas apenas para consulta da sua Jornada
              Real.
            </p>
          </div>
        </article>
      </section>

      <style jsx global>{`
        .cpf-page {
          --gold: #f6c637;
          --gold-soft: #ffe38a;
          --page-x: clamp(18px, 5vw, 28px);
          min-height: 100svh;
          overflow-x: hidden;
          color: #fff4dd;
          background:
            radial-gradient(circle at 50% 33%, rgba(180, 104, 17, 0.18), transparent 14rem),
            radial-gradient(circle at 50% 78%, rgba(247, 198, 55, 0.16), transparent 18rem),
            #020302;
          font-family: 'Playfair Display', serif;
          isolation: isolate;
        }

        .cpf-page::before {
          content: '';
          position: fixed;
          inset: 0;
          z-index: -3;
          background:
            radial-gradient(circle at 0% 64%, rgba(246, 198, 55, 0.2) 0 1px, transparent 2px),
            radial-gradient(circle at 100% 74%, rgba(246, 198, 55, 0.18) 0 1px, transparent 2px),
            linear-gradient(180deg, #020302 0%, #030303 42%, #050402 100%);
          background-size: 16px 16px, 18px 18px, auto;
          opacity: 0.75;
        }

        .cpf-page::after {
          content: '';
          position: fixed;
          inset: 0;
          z-index: -2;
          pointer-events: none;
          background:
            linear-gradient(180deg, rgba(0, 0, 0, 0.98) 0%, rgba(0, 0, 0, 0.9) 28%, rgba(0, 0, 0, 0.32) 56%, rgba(0, 0, 0, 0.38) 74%, rgba(0, 0, 0, 0.95) 100%),
            radial-gradient(ellipse at 50% 58%, rgba(3, 3, 2, 0) 0%, rgba(0, 0, 0, 0.28) 48%, rgba(0, 0, 0, 0.92) 100%);
        }

        body:has(.cpf-page) button[aria-label^=Abrir][aria-label*=configura],
        body:has(.cpf-page) nextjs-portal {
          display: none;
        }

        .cpf-shell {
          position: relative;
          z-index: 30;
          width: min(100% - (var(--page-x) * 2), 430px);
          min-height: 100svh;
          margin: 0 auto;
          padding: 12px 0 28px;
        }

        .cpf-header {
          display: grid;
          grid-template-columns: 42px 1fr 42px;
          align-items: start;
          min-height: 102px;
        }

        .back-button {
          width: 36px;
          height: 36px;
          display: grid;
          place-items: center;
          color: var(--gold);
          background: rgba(0, 0, 0, 0.28);
          border: 1.5px solid var(--gold);
          border-radius: 50%;
          box-shadow: 0 0 14px rgba(246, 198, 55, 0.16);
          cursor: pointer;
        }

        .cpf-logo {
          width: clamp(222px, 65vw, 282px);
          height: auto;
          justify-self: center;
          filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.86));
        }

        .cpf-intro {
          margin-top: 2px;
          text-align: center;
          text-shadow: 0 3px 12px rgba(0, 0, 0, 0.92);
        }

        .cpf-intro h1 {
          margin: 0;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(2.35rem, 10.5vw, 3.35rem);
          font-weight: 700;
          line-height: 0.94;
          text-transform: uppercase;
        }

        .title-divider {
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          align-items: center;
          gap: 10px;
          width: min(276px, 76vw);
          margin: 14px auto 10px;
          color: var(--gold);
        }

        .title-divider span {
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(246, 198, 55, 0.72), transparent);
        }

        .cpf-intro p {
          margin: 0 auto;
          color: #f5efe6;
          font-size: clamp(0.98rem, 4vw, 1.12rem);
          line-height: 1.35;
        }

        .cpf-card {
          position: relative;
          margin: 22px auto 0;
          padding: 22px 18px 17px;
          border: 1.5px solid rgba(246, 198, 55, 0.88);
          border-radius: 20px;
          background:
            linear-gradient(180deg, rgba(255, 226, 138, 0.06), rgba(0, 0, 0, 0.72)),
            rgba(9, 8, 6, 0.72);
          box-shadow:
            0 0 26px rgba(246, 198, 55, 0.2),
            inset 0 0 28px rgba(246, 198, 55, 0.08),
            0 22px 42px rgba(0, 0, 0, 0.42);
          text-align: center;
          backdrop-filter: blur(5px);
        }

        .cpf-card::before {
          content: '';
          position: absolute;
          top: -1px;
          left: 50%;
          width: 44%;
          height: 1px;
          transform: translateX(-50%);
          background: linear-gradient(90deg, transparent, #fff0ad, transparent);
          box-shadow: 0 0 14px rgba(255, 230, 150, 0.95);
        }

        .search-orb {
          width: 78px;
          height: 78px;
          display: grid;
          place-items: center;
          margin: 0 auto 13px;
          color: var(--gold);
          border: 1.5px solid var(--gold);
          border-radius: 50%;
          background:
            radial-gradient(circle at 35% 30%, rgba(255, 238, 163, 0.2), transparent 38%),
            rgba(0, 0, 0, 0.28);
          box-shadow:
            inset 0 0 18px rgba(246, 198, 55, 0.22),
            0 0 22px rgba(246, 198, 55, 0.3);
        }

        .cpf-card label {
          display: block;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(0.98rem, 4vw, 1.16rem);
          font-weight: 700;
          text-transform: uppercase;
        }

        .cpf-input-wrap {
          display: flex;
          align-items: center;
          gap: 12px;
          height: 52px;
          margin-top: 13px;
          padding: 0 14px;
          color: var(--gold);
          border: 1.5px solid var(--gold);
          border-radius: 9px;
          background: rgba(4, 4, 3, 0.54);
          box-shadow: inset 0 0 14px rgba(246, 198, 55, 0.08);
        }

        .cpf-input-wrap input {
          width: 100%;
          min-width: 0;
          color: #fff1c5;
          background: transparent;
          border: 0;
          outline: 0;
          font-family: 'Cinzel', serif;
          font-size: clamp(1rem, 4vw, 1.16rem);
          letter-spacing: 0;
        }

        .cpf-input-wrap input::placeholder {
          color: rgba(255, 241, 197, 0.48);
        }

        .cpf-error {
          margin: 10px 0 0;
          color: #ffb1a8;
          font-size: 0.9rem;
          font-weight: 700;
        }

        .submit-button {
          width: 100%;
          min-height: 52px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 14px;
          margin-top: 15px;
          color: #170f06;
          background: linear-gradient(180deg, #ffe27b 0%, #e0a125 56%, #b46b06 100%);
          border: 1px solid #ffeaa4;
          border-radius: 14px;
          box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.55),
            0 12px 22px rgba(0, 0, 0, 0.42),
            0 0 18px rgba(246, 198, 55, 0.22);
          font-family: 'Cinzel', serif;
          font-size: clamp(0.84rem, 3.5vw, 0.98rem);
          font-weight: 700;
          text-transform: uppercase;
          cursor: pointer;
        }

        .submit-button svg {
          flex: 0 0 auto;
        }

        .privacy-note {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin: 12px 0 0;
          color: var(--gold);
          font-size: clamp(0.72rem, 3vw, 0.84rem);
          line-height: 1.2;
        }

        .hotel-showcase {
          position: relative;
          width: min(500px, 132vw);
          height: clamp(430px, 120vw, 570px);
          margin: -48px auto -20px;
          overflow: hidden;
          background-image: url('/images/background-cpf-atual.png');
          background-repeat: no-repeat;
          background-position: 68% bottom;
          background-size: 128% auto;
          filter: brightness(0.88) drop-shadow(0 18px 28px rgba(0, 0, 0, 0.7));
          -webkit-mask-image: linear-gradient(180deg, transparent 0%, #000 12%, #000 86%, transparent 100%);
          mask-image: linear-gradient(180deg, transparent 0%, #000 12%, #000 86%, transparent 100%);
          pointer-events: none;
        }

        .hotel-showcase::before,
        .hotel-showcase::after {
          content: '';
          position: absolute;
          inset: 0;
          z-index: 2;
          pointer-events: none;
        }

        .hotel-showcase::before {
          background:
            linear-gradient(180deg, rgba(0, 0, 0, 0.32) 0%, rgba(0, 0, 0, 0) 28%, rgba(0, 0, 0, 0) 72%, rgba(0, 0, 0, 0.48) 100%),
            linear-gradient(90deg, #020302 0%, rgba(2, 3, 2, 0) 18%, rgba(2, 3, 2, 0) 82%, #020302 100%);
        }

        .hotel-showcase::after {
          background: radial-gradient(ellipse at 50% 62%, rgba(246, 198, 55, 0.1) 0%, transparent 48%, rgba(0, 0, 0, 0.58) 94%);
        }

        .privacy-card {
          display: grid;
          grid-template-columns: 56px 1fr;
          gap: 14px;
          align-items: center;
          margin: -1px auto 0;
          padding: 16px;
          border: 1.3px solid rgba(246, 198, 55, 0.78);
          border-radius: 12px;
          background: rgba(7, 7, 5, 0.8);
          box-shadow: 0 0 20px rgba(246, 198, 55, 0.13);
          backdrop-filter: blur(4px);
        }

        .privacy-icon {
          width: 48px;
          height: 58px;
          display: grid;
          place-items: center;
          color: var(--gold);
          background: rgba(246, 198, 55, 0.08);
          clip-path: polygon(50% 0%, 90% 18%, 90% 70%, 50% 100%, 10% 70%, 10% 18%);
        }

        .privacy-card h2 {
          margin: 0 0 4px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(0.95rem, 3.8vw, 1.08rem);
          font-weight: 700;
          text-transform: uppercase;
        }

        .privacy-card p {
          margin: 0;
          color: #fff4dd;
          font-size: clamp(0.82rem, 3.25vw, 0.94rem);
          line-height: 1.28;
        }

        @media (max-width: 390px) {
          .cpf-page {
            --page-x: 14px;
          }

          .cpf-shell {
            padding-top: 10px;
          }

          .cpf-header {
            min-height: 96px;
          }

          .cpf-logo {
            width: 232px;
          }

          .cpf-card {
            margin-top: 18px;
          }

          .hotel-showcase {
            width: min(462px, 134vw);
            height: clamp(398px, 119vw, 495px);
            background-position: 76% bottom;
          }
        }

        @media (max-width: 360px) {
          .cpf-page {
            --page-x: 12px;
          }

          .back-button {
            width: 34px;
            height: 34px;
          }

          .cpf-intro h1 {
            font-size: 2.22rem;
          }

          .search-orb {
            width: 72px;
            height: 72px;
          }

          .cpf-card {
            padding: 18px 15px 15px;
          }

          .submit-button {
            gap: 9px;
          }

          .privacy-card {
            grid-template-columns: 50px 1fr;
            padding: 14px;
          }
        }

        @media (min-width: 700px) {
          .cpf-shell {
            width: min(430px, calc(100% - 40px));
          }
        }
      `}</style>
    </main>
  )
}
