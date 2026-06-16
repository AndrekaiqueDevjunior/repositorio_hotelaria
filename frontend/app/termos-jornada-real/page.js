'use client'

import Link from 'next/link'
import { ChevronLeft } from 'lucide-react'
import GoldParticles from '@/components/GoldParticles'

const terms = [
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
    <main className="terms-page">
      <div className="overlay" />
      <GoldParticles />

      <Link href="/entrar-jornada-real" className="back-button" aria-label="Voltar">
        <ChevronLeft size={38} strokeWidth={2.2} />
      </Link>

      <section className="terms-shell">
        <img
          src="/images/logo-jornada-real.png"
          alt="Hotel Real Cabo Frio - Jornada Real"
          className="brand"
        />

        <article className="terms-card">
          <h1>Termos da Jornada Real</h1>
          <p className="intro">
            Ao marcar “Concordo”, o hóspede declara que leu e aceita as regras abaixo:
          </p>

          <ol>
            {terms.map((term, index) => (
              <li key={term}>
                <strong>{index + 1}.</strong> {term}
              </li>
            ))}
          </ol>

          <Link href="/entrar-jornada-real" className="return-button">
            Voltar
            <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
          </Link>
        </article>
      </section>

      <style jsx global>{`
        button[aria-label="Abrir configurações de acessibilidade"] {
          display: none !important;
        }
      `}</style>

      <style jsx>{`
        .terms-page {
          min-height: 100vh;
          position: relative;
          overflow-x: hidden;
          background:
            radial-gradient(circle at 50% 10%, rgba(255, 205, 72, 0.15), transparent 20%),
            linear-gradient(180deg, #080706 0%, #040403 100%);
          color: #f8ecd0;
        }

        .overlay {
          position: absolute;
          inset: 0;
          background:
            linear-gradient(rgba(8, 5, 3, 0.62), rgba(8, 5, 3, 0.74)),
            url('/images/background-jornada-entrada.png') center/cover no-repeat;
        }

        .back-button {
          position: fixed;
          left: 20px;
          top: 22px;
          z-index: 40;
          width: 64px;
          height: 64px;
          border-radius: 50%;
          border: 1px solid rgba(212, 175, 55, 0.65);
          color: #f0bf3c;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(0, 0, 0, 0.24);
          box-shadow: 0 0 22px rgba(212, 175, 55, 0.18);
        }

        .terms-shell {
          position: relative;
          z-index: 20;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 32px 18px;
        }

        .brand {
          width: min(360px, 72vw);
          height: auto;
          margin-bottom: 16px;
          filter: drop-shadow(0 0 18px rgba(212, 175, 55, 0.34));
        }

        .terms-card {
          width: min(860px, 100%);
          border-radius: 18px;
          border: 2px solid rgba(212, 175, 55, 0.72);
          background: rgba(10, 6, 4, 0.88);
          padding: 28px 26px 30px;
          box-shadow:
            inset 0 0 18px rgba(212, 175, 55, 0.06),
            0 0 36px rgba(0, 0, 0, 0.32);
        }

        .terms-card h1 {
          margin: 0 0 14px;
          text-align: center;
          color: #f4d471;
          font-family: 'Cinzel', serif;
          font-size: clamp(30px, 5vw, 42px);
          text-shadow: 0 0 18px rgba(212, 175, 55, 0.26);
        }

        .intro {
          margin: 0 0 18px;
          text-align: center;
          color: #fff0ca;
          font-size: 20px;
          line-height: 1.45;
        }

        ol {
          margin: 0;
          padding-left: 0;
          list-style: none;
          display: grid;
          gap: 14px;
        }

        li {
          color: #f7ecd2;
          font-size: 18px;
          line-height: 1.55;
          padding: 14px 16px;
          border-radius: 12px;
          border: 1px solid rgba(212, 175, 55, 0.22);
          background: rgba(255, 255, 255, 0.02);
        }

        li strong {
          color: #f2c84b;
        }

        .return-button {
          margin: 72px auto 0;
          min-height: 56px;
          width: min(240px, 100%);
          border-radius: 999px;
          border: 1px solid rgba(255, 239, 176, 0.45);
          background: linear-gradient(180deg, #ffe89a 0%, #e7b938 55%, #bf7d0e 100%);
          color: #181006;
          font-family: 'Cinzel', serif;
          font-size: 17px;
          font-weight: 700;
          display: flex;
          align-items: center;
          justify-content: center;
          text-decoration: none;
          box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.36),
            0 12px 24px rgba(0, 0, 0, 0.34),
            0 0 22px rgba(212, 175, 55, 0.22);
        }

        @media (max-width: 640px) {
          .return-button {
            margin-top: 84px;
          }
        }
      `}</style>
    </main>
  )
}
