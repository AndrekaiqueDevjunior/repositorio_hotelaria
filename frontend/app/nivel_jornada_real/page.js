'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Check, ChevronLeft, Crown, Gift, Leaf, Percent, Star, User, X } from 'lucide-react'
import GoldParticles from '@/components/GoldParticles'
import { api } from '@/lib/api'

const levels = [
  {
    key: 'essencia',
    label: 'Essência',
    min: 0,
    max: 49,
    range: '0 a 50 pontos',
    icon: Leaf,
    benefits: ['Entrada na Jornada Real', 'Acompanhamento dos seus pontos', 'Acesso aos prêmios iniciais'],
  },
  {
    key: 'experiencia',
    label: 'Experiência',
    min: 50,
    max: 89,
    range: '50 a 90 pontos',
    icon: Star,
    benefits: ['Prioridade no atendimento', 'Ofertas e experiências exclusivas', '+20% de pontos por reserva'],
  },
  {
    key: 'real',
    label: 'Real',
    min: 90,
    max: Infinity,
    range: '90+ pontos',
    icon: Crown,
    benefits: ['Nível máximo da Jornada Real', 'Prêmios mais exclusivos', '+40% de pontos por reserva'],
  },
]

const crest = '/images/brasao-hotel-real-transparente.png?v=4'
const clamp = (value, min, max) => Math.min(Math.max(value, min), max)
const firstNumber = (...values) => {
  for (const value of values) {
    const parsed = Number(value)
    if (Number.isFinite(parsed)) return parsed
  }

  return 0
}

const withCpfParam = (href, cpf) => {
  if (!cpf) return href

  const separator = href.includes('?') ? '&' : '?'
  return `${href}${separator}cpf=${encodeURIComponent(cpf)}`
}

const normalizeLoyaltyData = (data) => {
  const programa = data?.programa_pontos || {}

  return {
    customerName: data?.customer_name || data?.customerName || data?.cliente?.nome || data?.cliente_nome,
    levelPoints: firstNumber(
      data?.lifetime_points,
      data?.lifetimePoints,
      data?.total_pontos_nivel,
      programa?.total_pontos_nivel,
      data?.redeemable_points,
      data?.saldo_atual,
      data?.saldo_pontos,
      data?.saldo
    ),
  }
}

function getLevel(points) {
  return levels.find((level) => points >= level.min && points <= level.max) || levels[0]
}

function getNextLevel(currentLevel) {
  const index = levels.findIndex((level) => level.key === currentLevel.key)
  return levels[index + 1] || null
}

export default function NivelJornadaReal() {
  const params = useSearchParams()
  const [showLevelDialog, setShowLevelDialog] = useState(false)
  const [loyaltyData, setLoyaltyData] = useState(null)
  const cpf = (params.get('cpf') || params.get('documento') || '').replace(/\D/g, '')
  const name = loyaltyData?.customerName || 'Hóspede Real'
  const points = loyaltyData ? loyaltyData.levelPoints : 72
  const previousPoints = points
  const forceCelebrate = params.get('celebrar') === '1' || params.get('up') === '1'

  useEffect(() => {
    let isMounted = true

    const loadLoyalty = async () => {
      if (!cpf) {
        setLoyaltyData(null)
        return
      }

      try {
        const response = await api.get(`/customers/${cpf}/loyalty`)

        if (isMounted) {
          setLoyaltyData(normalizeLoyaltyData(response.data))
        }
      } catch (primaryError) {
        try {
          const response = await api.get(`/pontos/consultar/${cpf}`)

          if (isMounted) {
            setLoyaltyData(normalizeLoyaltyData(response.data))
          }
        } catch (error) {
          if (isMounted) {
            setLoyaltyData(null)
          }
        }
      }
    }

    loadLoyalty()

    return () => {
      isMounted = false
    }
  }, [cpf])

  const currentLevel = getLevel(points)
  const CurrentLevelIcon = currentLevel.icon
  const previousLevel = getLevel(previousPoints)
  const nextLevel = getNextLevel(currentLevel)
  const didLevelUp = forceCelebrate || currentLevel.key !== previousLevel.key

  const goal = nextLevel ? nextLevel.min : points
  const levelStart = currentLevel.min
  const levelEnd = nextLevel ? nextLevel.min : points
  const levelProgress = nextLevel ? clamp(((points - levelStart) / (levelEnd - levelStart)) * 100, 0, 100) : 100
  const fullJourneyProgress = clamp((points / 90) * 100, 0, 100)
  const missing = nextLevel ? Math.max(goal - points, 0) : 0

  return (
    <main className="level-page">
      <GoldParticles />

      <Link href={withCpfParam('/consultar-pontos', cpf)} className="back-button" aria-label="Voltar">
        <ChevronLeft size={42} strokeWidth={2.2} />
      </Link>

      <section className="level-shell">
        <header className="brand">
          <img src="/images/logo-jornada-real.png" alt="Hotel Real Cabo Frio - Jornada Real" />
        </header>

        <button className="level-reveal-button" type="button" onClick={() => setShowLevelDialog(true)}>
          <span>
            <Crown size={24} fill="currentColor" />
          </span>
          <strong>{didLevelUp ? 'Ver novo nível desbloqueado' : 'Ver meu nível e benefícios'}</strong>
          <small>Nível {currentLevel.label} • {points} pts</small>
        </button>

        {showLevelDialog && (
          <section className="level-dialog" role="dialog" aria-modal="true" aria-labelledby="celebration-title">
            <button className="dialog-close" type="button" onClick={() => setShowLevelDialog(false)} aria-label="Fechar">
              <X size={24} strokeWidth={2.4} />
            </button>

            <section className="celebration-card" aria-labelledby="celebration-title">
            <h1 id="celebration-title">
              <span>{didLevelUp ? `Parabéns, ${name}!` : `Olá, ${name}!`}</span>
              {didLevelUp ? 'Você subiu de nível!' : 'Seu nível na Jornada Real'}
            </h1>

            <div className="level-orb" aria-hidden="true">
              <Crown className="orb-crown" size={76} fill="currentColor" strokeWidth={1.2} />
              <CurrentLevelIcon className="level-orb-icon" size={112} fill="currentColor" strokeWidth={1.3} />
            </div>

            <p className="level-unlocked">
              {didLevelUp ? 'Você agora é' : 'Você está no'} NÍVEL {currentLevel.label}!
            </p>
            <p className="celebration-copy">
              {didLevelUp
                ? 'Novos benefícios foram desbloqueados para a sua jornada.'
                : 'Veja seus benefícios ativos e o próximo nível da sua jornada.'}
            </p>

            <div className="mini-track" aria-label="Níveis da Jornada Real">
              {levels.map((level) => {
                const Icon = level.icon
                const isCurrent = level.key === currentLevel.key
                const isDone = points >= level.min && !isCurrent

                return (
                  <article className={isCurrent ? 'current' : isDone ? 'done' : ''} key={level.key}>
                    <div>
                      <Icon size={28} fill={isCurrent ? 'currentColor' : 'none'} strokeWidth={1.7} />
                    </div>
                    <h2>{level.label}</h2>
                    <p>{level.range}</p>
                    <span>{isDone || isCurrent ? <Check size={15} strokeWidth={3} /> : ''}</span>
                  </article>
                )
              })}
            </div>

            <section className="benefits-card" aria-labelledby="benefits-title">
              <div>
                <h2 id="benefits-title">
                  {didLevelUp ? 'Novos benefícios desbloqueados!' : 'Benefícios do seu nível'}
                </h2>
                {currentLevel.benefits.map((benefit, index) => {
                  const icons = [User, Star, Percent]
                  const Icon = icons[index] || Gift

                  return (
                    <p key={benefit}>
                      <Icon size={22} fill="currentColor" strokeWidth={1.8} />
                      {benefit}
                    </p>
                  )
                })}
              </div>

              <div className="gift-box" aria-hidden="true">
                <span />
                <img src={crest} alt="" />
              </div>
            </section>
          </section>
          </section>
        )}

        <section className="progress-card" aria-labelledby="progress-title">
          <h2 id="progress-title">
            <Star size={18} fill="currentColor" />
            Seu progresso de nível
            <Star size={18} fill="currentColor" />
          </h2>

          <div className="level-map">
            {levels.map((level) => {
              const Icon = level.icon
              const isCurrent = level.key === currentLevel.key

              return (
                <article className={isCurrent ? 'active' : ''} key={level.key}>
                  <div className={`level-medal ${level.key}`}>
                    <Icon size={28} fill={isCurrent ? 'currentColor' : 'none'} strokeWidth={1.7} />
                  </div>
                  <h3>{level.label}</h3>
                  <p>{level.range}</p>
                </article>
              )
            })}
          </div>

          <div className="progress-bar" aria-hidden="true">
            <span style={{ width: `${fullJourneyProgress}%` }} />
            <i style={{ left: `${fullJourneyProgress}%` }}>
              <Star size={16} fill="currentColor" />
            </i>
          </div>

          <div className="points-summary">
            <Star size={30} fill="currentColor" />
            <p>
              <strong>{points}</strong> / {nextLevel ? goal : points} pontos
              <span>
                {nextLevel
                  ? `Faltam ${missing} pontos para o próximo nível`
                  : 'Você chegou ao nível máximo da Jornada Real'}
              </span>
            </p>
          </div>
        </section>

        <section className="points-card">
          <p>Seus pontos atuais</p>
          <strong>
            <Star size={36} fill="currentColor" />
            {points} pts
          </strong>

          <div className="next-progress">
            <span>{nextLevel ? `Faltam ${missing} pontos para o nível ${nextLevel.label}` : 'Nível máximo conquistado'}</span>
            <div>
              <i style={{ width: `${levelProgress}%` }} />
            </div>
            <small>{nextLevel ? `${points} / ${goal}` : `${points} / ${points}`}</small>
          </div>
        </section>

        <section className="actions">
          <p>
            <Crown size={24} fill="currentColor" />
            Cada estadia te leva mais longe.
            <br />
            O topo te espera!
          </p>

          <Link href={withCpfParam('/consultar-pontos', cpf)} className="primary-button">
            Continuar minha jornada
            <img className="jr-button-crest" src={crest} alt="" aria-hidden="true" />
          </Link>

          <Link href={withCpfParam('/resgate_dos_premios?premio=tecnologia-real', cpf)} className="secondary-button">
            <Gift size={22} fill="currentColor" />
            Ver meus benefícios
            <img className="jr-button-crest" src={crest} alt="" aria-hidden="true" />
          </Link>
        </section>
      </section>

      <style jsx global>{`
        body:has(.level-page) button[aria-label^=Abrir][aria-label*=configura],
        body:has(.level-page) nextjs-portal {
          display: none;
        }
      `}</style>

      <style jsx global>{`
        .level-page {
          --gold: #f6c637;
          --gold-soft: #ffe08a;
          --purple: #b46cff;
          min-height: 100svh;
          overflow-x: hidden;
          color: #fff1d6;
          background:
            radial-gradient(circle at 50% 22%, rgba(246, 198, 55, 0.14), transparent 16rem),
            radial-gradient(circle at 50% 42%, rgba(255, 190, 21, 0.1), transparent 18rem),
            #020302;
          font-family: 'Playfair Display', Georgia, serif;
        }

        .level-page::before {
          content: '';
          position: fixed;
          inset: 0;
          pointer-events: none;
          background:
            radial-gradient(circle at 13% 16%, rgba(246, 198, 55, 0.2) 0 1px, transparent 2px),
            radial-gradient(circle at 80% 35%, rgba(246, 198, 55, 0.16) 0 1px, transparent 2px),
            radial-gradient(circle at 35% 80%, rgba(246, 198, 55, 0.14) 0 1px, transparent 2px);
          background-size: 18px 18px, 22px 22px, 26px 26px;
          opacity: 0.74;
        }

        .back-button {
          position: fixed;
          left: clamp(12px, 4vw, 24px);
          top: clamp(14px, 4vw, 24px);
          z-index: 10;
          width: 56px;
          height: 56px;
          display: grid;
          place-items: center;
          border: 1.5px solid rgba(246, 198, 55, 0.68);
          border-radius: 50%;
          color: var(--gold);
          background: rgba(0, 0, 0, 0.28);
          box-shadow: 0 0 18px rgba(246, 198, 55, 0.18);
        }

        .level-shell {
          position: relative;
          z-index: 20;
          width: min(100% - 18px, 430px);
          margin: 0 auto;
          padding: 14px 0 28px;
        }

        .brand {
          display: grid;
          place-items: center;
          min-height: 128px;
          padding: 0 56px;
        }

        .brand img {
          width: min(280px, 72vw);
          height: auto;
          filter: drop-shadow(0 7px 18px rgba(0, 0, 0, 0.82));
        }

        .level-reveal-button {
          width: min(100%, 360px);
          min-height: 76px;
          display: grid;
          grid-template-columns: 52px 1fr;
          align-items: center;
          column-gap: 12px;
          margin: 0 auto 14px;
          padding: 12px 16px;
          border: 1px solid rgba(246, 198, 55, 0.76);
          border-radius: 12px;
          color: var(--gold-soft);
          text-align: left;
          background:
            radial-gradient(circle at 18% 50%, rgba(246, 198, 55, 0.18), transparent 5rem),
            rgba(5, 4, 3, 0.82);
          box-shadow: 0 0 22px rgba(246, 198, 55, 0.16);
          cursor: pointer;
        }

        .level-reveal-button span {
          grid-row: span 2;
          width: 52px;
          height: 52px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          color: #140b03;
          background: linear-gradient(180deg, #ffe18d, #d9991c);
          box-shadow: 0 0 18px rgba(246, 198, 55, 0.35);
        }

        .level-reveal-button strong {
          align-self: end;
          font-family: 'Cinzel', serif;
          font-size: 0.95rem;
          line-height: 1.15;
          text-transform: uppercase;
        }

        .level-reveal-button small {
          align-self: start;
          color: #fff1d6;
          font-size: 0.82rem;
        }

        .level-dialog {
          position: fixed;
          inset: 0;
          z-index: 80;
          overflow-y: auto;
          padding: 18px 9px 28px;
          background:
            radial-gradient(circle at 50% 22%, rgba(246, 198, 55, 0.2), transparent 18rem),
            #020302;
        }

        .level-dialog .celebration-card {
          width: min(100%, 430px);
          margin: 72px auto 0;
        }

        .dialog-close {
          position: fixed;
          top: 18px;
          right: 18px;
          z-index: 90;
          width: 46px;
          height: 46px;
          display: grid;
          place-items: center;
          border: 1px solid rgba(246, 198, 55, 0.72);
          border-radius: 50%;
          color: var(--gold);
          background: rgba(0, 0, 0, 0.64);
          box-shadow: 0 0 18px rgba(246, 198, 55, 0.2);
          cursor: pointer;
        }

        .celebration-card,
        .progress-card,
        .points-card,
        .benefits-card {
          border: 1px solid rgba(246, 198, 55, 0.64);
          background:
            radial-gradient(circle at 50% 0%, rgba(246, 198, 55, 0.09), transparent 12rem),
            rgba(5, 4, 3, 0.82);
          box-shadow:
            inset 0 0 18px rgba(246, 198, 55, 0.04),
            0 0 24px rgba(0, 0, 0, 0.32);
        }

        .celebration-card {
          padding: 22px 18px 18px;
          border-radius: 18px;
          text-align: center;
          margin-bottom: 14px;
        }

        .celebration-card h1 {
          margin: 0;
          color: var(--gold-soft);
          font-family: 'Cinzel', serif;
          font-size: clamp(2.1rem, 9vw, 3rem);
          line-height: 1.08;
          text-shadow: 0 0 20px rgba(246, 198, 55, 0.36);
        }

        .celebration-card h1 span {
          display: block;
          font-size: clamp(1.45rem, 6vw, 2rem);
          margin-bottom: 8px;
        }

        .level-orb {
          position: relative;
          width: 246px;
          height: 246px;
          display: grid;
          place-items: center;
          margin: 64px auto 16px;
          color: #f7ca3e;
          border: 4px solid var(--gold);
          border-radius: 50%;
          background:
            radial-gradient(circle, rgba(255, 207, 66, 0.12), transparent 58%),
            #060604;
          box-shadow:
            0 0 0 10px rgba(246, 198, 55, 0.06),
            0 0 50px rgba(246, 198, 55, 0.52);
        }

        .level-orb::before {
          content: '';
          position: absolute;
          inset: -58px;
          z-index: -1;
          background: repeating-conic-gradient(from 0deg, rgba(246, 198, 55, 0.34) 0 2deg, transparent 2deg 7deg);
          border-radius: 50%;
          opacity: 0.85;
          filter: blur(0.4px);
        }

        .orb-crown {
          position: absolute;
          top: -66px;
          color: var(--gold);
          filter: drop-shadow(0 0 12px rgba(246, 198, 55, 0.78));
        }

        .level-unlocked {
          width: min(100%, 300px);
          margin: 8px auto 16px;
          padding: 10px 12px;
          border: 1px solid rgba(246, 198, 55, 0.7);
          border-radius: 10px;
          color: var(--gold-soft);
          font-family: 'Cinzel', serif;
          font-size: 1.05rem;
          font-weight: 700;
          text-transform: uppercase;
        }

        .celebration-copy {
          margin: 0 0 20px;
          color: #fff5df;
          font-size: 1.28rem;
          line-height: 1.25;
        }

        .mini-track {
          position: relative;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
          margin: 12px 0 18px;
        }

        .mini-track::before {
          content: '';
          position: absolute;
          top: 30px;
          left: 18%;
          right: 18%;
          height: 6px;
          border-radius: 999px;
          background: linear-gradient(90deg, #7a4b16, var(--gold), #7a4b16);
          box-shadow: 0 0 16px rgba(246, 198, 55, 0.45);
        }

        .mini-track article {
          position: relative;
          z-index: 1;
          text-align: center;
        }

        .mini-track article div,
        .level-medal {
          width: 62px;
          height: 62px;
          display: grid;
          place-items: center;
          margin: 0 auto 8px;
          border: 2px solid var(--gold);
          border-radius: 50%;
          color: var(--gold);
          background: rgba(17, 11, 4, 0.86);
        }

        .mini-track article.current div,
        .level-map article.active .level-medal {
          color: #f8e9ff;
          border-color: var(--purple);
          background: radial-gradient(circle at 45% 30%, rgba(255, 255, 255, 0.2), rgba(96, 43, 130, 0.9));
          box-shadow: 0 0 24px rgba(180, 108, 255, 0.55);
        }

        .mini-track h2,
        .level-map h3 {
          margin: 0 0 4px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 0.78rem;
          text-transform: uppercase;
        }

        .mini-track p,
        .level-map p {
          margin: 0;
          color: #fff3dd;
          font-size: 0.7rem;
          line-height: 1.15;
        }

        .mini-track article > span {
          display: grid;
          place-items: center;
          width: 24px;
          height: 24px;
          margin: 8px auto 0;
          color: white;
          border-radius: 50%;
          background: rgba(246, 198, 55, 0.14);
        }

        .mini-track article.done > span {
          background: #20a955;
        }

        .mini-track article.current > span {
          color: white;
          background: #20a955;
          box-shadow: 0 0 15px rgba(32, 169, 85, 0.55);
        }

        .benefits-card {
          display: grid;
          grid-template-columns: 1fr 108px;
          gap: 14px;
          align-items: center;
          padding: 16px;
          border-radius: 12px;
          text-align: left;
        }

        .benefits-card h2 {
          margin: 0 0 12px;
          color: var(--gold-soft);
          font-family: 'Cinzel', serif;
          font-size: 1.1rem;
        }

        .benefits-card p {
          display: flex;
          align-items: center;
          gap: 10px;
          margin: 8px 0 0;
          color: #fff4dc;
          font-size: 0.9rem;
          line-height: 1.2;
        }

        .benefits-card p svg {
          color: var(--gold);
          flex: 0 0 auto;
        }

        .gift-box {
          position: relative;
          width: 104px;
          height: 104px;
          border-radius: 10px;
          background:
            linear-gradient(90deg, transparent 42%, #d99419 42% 58%, transparent 58%),
            linear-gradient(0deg, transparent 42%, #d99419 42% 58%, transparent 58%),
            linear-gradient(135deg, #17120b, #060604);
          box-shadow: 0 0 24px rgba(246, 198, 55, 0.22);
        }

        .gift-box span {
          position: absolute;
          top: -16px;
          left: 50%;
          width: 54px;
          height: 28px;
          transform: translateX(-50%);
          border-radius: 50%;
          background: linear-gradient(135deg, #ffe38b, #b36e09);
          box-shadow: 0 0 18px rgba(246, 198, 55, 0.35);
        }

        .gift-box img {
          position: absolute;
          left: 50%;
          bottom: 8px;
          width: 34px;
          height: 42px;
          object-fit: contain;
          transform: translateX(-50%);
        }

        .progress-card,
        .points-card {
          padding: 16px 14px;
          border-radius: 8px;
          margin-top: 14px;
        }

        .progress-card h2 {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 9px;
          margin: 0 0 20px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 1.02rem;
          text-transform: uppercase;
        }

        .level-map {
          position: relative;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
        }

        .level-map::before {
          content: '';
          position: absolute;
          top: 31px;
          left: 15%;
          right: 15%;
          height: 5px;
          border-radius: 999px;
          background: linear-gradient(90deg, var(--gold), var(--purple), var(--gold));
          box-shadow: 0 0 14px rgba(180, 108, 255, 0.4);
        }

        .level-map article {
          position: relative;
          z-index: 2;
          text-align: center;
        }

        .level-medal.essencia {
          color: var(--gold);
        }

        .level-medal.real {
          color: var(--gold);
        }

        .progress-bar {
          position: relative;
          height: 13px;
          margin: 18px 10px 16px;
          border: 1px solid rgba(246, 198, 55, 0.72);
          border-radius: 999px;
          background: rgba(0, 0, 0, 0.45);
        }

        .progress-bar span {
          display: block;
          height: 100%;
          border-radius: inherit;
          background: linear-gradient(90deg, #884bd8, #c786ff, #e3b15b);
          box-shadow: 0 0 12px rgba(180, 108, 255, 0.55);
        }

        .progress-bar i {
          position: absolute;
          top: 50%;
          width: 26px;
          height: 26px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          color: white;
          background: linear-gradient(180deg, #ffe08a, #c98311);
          transform: translate(-50%, -50%);
        }

        .points-summary {
          width: min(260px, 80vw);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          margin: 0 auto;
          padding: 12px;
          color: #fff4df;
          border: 1px solid rgba(246, 198, 55, 0.72);
          border-radius: 12px;
          background: rgba(0, 0, 0, 0.42);
        }

        .points-summary svg {
          color: var(--purple);
          flex: 0 0 auto;
        }

        .points-summary p {
          margin: 0;
          font-size: 1rem;
          line-height: 1.18;
        }

        .points-summary strong {
          color: var(--purple);
          font-family: 'Cinzel', serif;
          font-size: 1.45rem;
        }

        .points-summary span {
          display: block;
          font-size: 0.72rem;
        }

        .points-card {
          text-align: center;
          border-radius: 12px;
        }

        .points-card > p {
          margin: 0 0 6px;
          color: #fff3df;
          font-size: 0.95rem;
        }

        .points-card > strong {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 2rem;
          line-height: 1;
        }

        .next-progress {
          margin-top: 14px;
          padding: 12px;
          border: 1px solid rgba(246, 198, 55, 0.25);
          border-radius: 10px;
          background: rgba(0, 0, 0, 0.28);
        }

        .next-progress span,
        .next-progress small {
          display: block;
          color: #fff4d8;
          font-size: 0.86rem;
        }

        .next-progress div {
          height: 13px;
          margin: 10px 0 8px;
          border: 1px solid rgba(246, 198, 55, 0.6);
          border-radius: 999px;
          overflow: hidden;
          background: rgba(0, 0, 0, 0.45);
        }

        .next-progress i {
          display: block;
          height: 100%;
          border-radius: inherit;
          background: linear-gradient(90deg, #ffe78e, #e0a91e);
          box-shadow: 0 0 14px rgba(246, 198, 55, 0.42);
        }

        .actions {
          text-align: center;
          padding: 14px 0 0;
        }

        .actions p {
          margin: 0 0 12px;
          color: #fff1d2;
          font-size: 1.2rem;
          line-height: 1.24;
        }

        .actions p svg {
          color: var(--gold);
          margin-right: 8px;
          vertical-align: -3px;
        }

        .primary-button,
        .secondary-button {
          width: min(100%, 320px);
          min-height: 54px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          margin: 0 auto 10px;
          border-radius: 10px;
          font-family: 'Cinzel', serif;
          font-weight: 700;
          text-decoration: none;
        }

        .primary-button {
          color: #160d04;
          border: 1px solid #ffe799;
          background: linear-gradient(180deg, #ffe08a, #d9981b 60%, #a75f05);
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.38);
          text-transform: uppercase;
        }

        .secondary-button {
          color: var(--gold);
          border: 1px solid rgba(246, 198, 55, 0.68);
          background: rgba(0, 0, 0, 0.44);
        }

        @media (max-width: 370px) {
          .brand {
            min-height: 112px;
            padding-inline: 48px;
          }

          .level-orb {
            width: 210px;
            height: 210px;
          }

          .mini-track article div,
          .level-medal {
            width: 54px;
            height: 54px;
          }

          .benefits-card {
            grid-template-columns: 1fr;
          }

          .gift-box {
            margin: 0 auto;
          }
        }
      `}</style>
    </main>
  )
}
