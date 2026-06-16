'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  ArrowRight,
  Bell,
  Coffee,
  Crown,
  Gift,
  Home,
  Leaf,
  Menu,
  Star,
  TrendingUp,
  User,
} from 'lucide-react'
import GoldParticles from '@/components/GoldParticles'
import { api } from '@/lib/api'

const rewardDefaults = [
  {
    name: 'Tecnologia Real',
    points: 90,
    image: '/images/premios/tecnologia-real.png',
    badge: 'Mais disputado',
    footer: '+Prêmio mais disputado',
    slug: 'tecnologia-real',
  },
  {
    name: 'Rituais do Real',
    points: 35,
    image: '/images/premios/rituais-do-real.png',
    footer: 'Transforme sua rotina em experiência',
    slug: 'rituais-do-real',
  },
  {
    name: 'O Retorno do Sonho',
    points: 25,
    image: '/images/premios/o-retorno-do-sonho.png',
    badge: 'Último restante!',
    footer: '1 diária com hidro + champanhe cortesia',
    slug: 'o-retorno-do-sonho',
  },
]

const slugify = (value) =>
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')

const resolveImageUrl = (imageUrl) => {
  if (!imageUrl) return ''
  if (/^https?:\/\//i.test(imageUrl)) return imageUrl

  const apiBase = process.env.NEXT_PUBLIC_API_URL || ''

  if (imageUrl.startsWith('/media') && /^https?:\/\//i.test(apiBase)) {
    return `${new URL(apiBase).origin}${imageUrl}`
  }

  return imageUrl
}

const toFiniteNumber = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

const firstNumber = (...values) => {
  for (const value of values) {
    const number = toFiniteNumber(value)
    if (number !== null) return number
  }

  return 0
}

const clampPercent = (value) => Math.max(0, Math.min(firstNumber(value), 100))

const getApiErrorMessage = (error, fallback) => {
  const data = error.response?.data

  if (typeof data === 'string') return data
  if (typeof data?.detail === 'string') return data.detail
  if (typeof data?.message === 'string') return data.message
  if (Array.isArray(data?.detail)) return data.detail.map((item) => item.msg || item.message).filter(Boolean).join(', ')

  return fallback
}

const withCpfParam = (href, cpf) => {
  if (!cpf) return href

  const separator = href.includes('?') ? '&' : '?'
  return `${href}${separator}cpf=${encodeURIComponent(cpf)}`
}

const normalizeLoyaltyData = (data) => {
  const programa = data?.programa_pontos || {}
  const barraNivel = data?.barra_nivel || programa?.barra_nivel || {}
  const barraPremios = data?.barra_premios || programa?.barra_premios || {}
  const redeemablePoints = firstNumber(
    data?.redeemable_points,
    data?.redeemablePoints,
    data?.saldo_atual,
    data?.saldo_pontos,
    data?.saldo,
    programa?.saldo_atual
  )
  const lifetimePoints = firstNumber(
    data?.lifetime_points,
    data?.lifetimePoints,
    data?.total_pontos_nivel,
    programa?.total_pontos_nivel,
    redeemablePoints
  )

  return {
    ...data,
    customer_id: data?.customer_id || data?.cliente_id || programa?.cliente_id,
    customer_name: data?.customer_name || data?.customerName || data?.cliente?.nome || data?.cliente_nome,
    document: data?.document || data?.documento || data?.cliente?.documento,
    lifetime_points: lifetimePoints,
    redeemable_points: redeemablePoints,
    total_redeemed_points: firstNumber(data?.total_redeemed_points, programa?.total_resgatado),
    current_level: data?.current_level || programa?.nivel,
    current_level_name: data?.current_level_name || programa?.nivel?.nome,
    next_level: data?.next_level || barraNivel?.proximo_nivel,
    next_level_points: firstNumber(data?.next_level_points, barraNivel?.meta, 90),
    missing_to_next_level: firstNumber(data?.missing_to_next_level, barraNivel?.faltam_pontos),
    level_progress: firstNumber(data?.level_progress, barraNivel?.percentual),
    next_reward: data?.next_reward || programa?.proximo_premio,
    reward_goal_points: firstNumber(data?.reward_goal_points, barraPremios?.meta),
    missing_to_next_reward: firstNumber(data?.missing_to_next_reward, barraPremios?.faltam_pontos),
    reward_progress: firstNumber(data?.reward_progress, barraPremios?.percentual),
    barra_nivel: barraNivel,
    barra_premios: barraPremios,
    programa_pontos: programa,
  }
}

const fallbackLoyaltyData = normalizeLoyaltyData({
  is_fallback: true,
  customer_name: 'Hóspede Real',
  redeemable_points: 0,
  lifetime_points: 0,
  next_level_points: 90,
  missing_to_next_level: 90,
  level_progress: 0,
  reward_goal_points: 0,
  missing_to_next_reward: 0,
  reward_progress: 0,
})

const normalizeReward = (premio) => {
  const slug = premio.slug || slugify(premio.nome)
  const defaults = rewardDefaults.find((item) => item.slug === slug) || {}

  return {
    ...defaults,
    id: premio.id,
    name: premio.nome || defaults.name || 'Prêmio Real',
    points: premio.preco_em_pontos ?? premio.preco_em_rp ?? defaults.points ?? 0,
    image: resolveImageUrl(premio.imagem_url || premio.imagemUrl) || defaults.image || '',
    footer: premio.descricao || defaults.footer || 'Prêmio exclusivo da Jornada Real',
    slug,
  }
}

const navItems = [
  { icon: Home, label: 'Início', href: '/' },
  { icon: TrendingUp, label: 'Minha Jornada', href: '/consultar-pontos' },
  { icon: Gift, label: 'Prêmios', href: '/resgate_dos_premios' },
  { icon: User, label: 'Perfil', href: '/entrar-jornada-real' },
]

export default function ConsultarPontos() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [apiRewards, setApiRewards] = useState([])
  const [isLoadingRewards, setIsLoadingRewards] = useState(true)
  const [loyaltyData, setLoyaltyData] = useState(fallbackLoyaltyData)
  const [isLoadingLoyalty, setIsLoadingLoyalty] = useState(false)
  const [loyaltyError, setLoyaltyError] = useState(null)
  const cpf = (searchParams.get('cpf') || searchParams.get('documento') || '').replace(/\D/g, '')

  const currentPoints = firstNumber(
    loyaltyData?.redeemable_points,
    loyaltyData?.redeemablePoints,
    loyaltyData?.saldo_atual,
    loyaltyData?.saldo_pontos
  )
  const lifetimePoints = firstNumber(
    loyaltyData?.lifetime_points,
    loyaltyData?.lifetimePoints,
    loyaltyData?.total_pontos_nivel,
    currentPoints
  )
  const nextLevelPoints = firstNumber(
    loyaltyData?.next_level_points,
    loyaltyData?.nextLevelPoints,
    loyaltyData?.barra_nivel?.meta,
    90
  )
  const missingToLevel = firstNumber(
    loyaltyData?.missing_to_next_level,
    loyaltyData?.missingToNextLevel,
    loyaltyData?.barra_nivel?.faltam_pontos,
    Math.max(nextLevelPoints - lifetimePoints, 0)
  )
  const levelProgress = clampPercent(
    loyaltyData?.level_progress ??
      loyaltyData?.levelProgress ??
      loyaltyData?.barra_nivel?.percentual ??
      (nextLevelPoints > 0 ? (lifetimePoints / nextLevelPoints) * 100 : 0)
  )
  const rewardProgress = clampPercent(
    loyaltyData?.reward_progress ??
      loyaltyData?.rewardProgress ??
      loyaltyData?.barra_premios?.percentual
  )
  const rewardGoalPoints = firstNumber(
    loyaltyData?.reward_goal_points,
    loyaltyData?.rewardGoalPoints,
    loyaltyData?.barra_premios?.meta
  )
  const missingToReward = firstNumber(
    loyaltyData?.missing_to_next_reward,
    loyaltyData?.missingToNextReward,
    loyaltyData?.barra_premios?.faltam_pontos
  )
  const customerName = loyaltyData?.customer_name || loyaltyData?.customerName || 'Hóspede Real'
  const isFallbackLoyalty = Boolean(loyaltyData?.is_fallback)
  const rewardSummary = rewardGoalPoints > 0 ? `${Math.min(currentPoints, rewardGoalPoints)}/${rewardGoalPoints}` : `${currentPoints}`
  const rewardSummaryLabel = rewardGoalPoints > 0 ? 'pontos para o próximo prêmio' : 'pontos disponíveis'
  const rewardProgressText =
    isFallbackLoyalty
      ? 'Consulte seu CPF para ver seus prêmios disponíveis'
      : missingToReward > 0
      ? `Faltam ${missingToReward} pontos para o próximo prêmio`
      : 'Você já tem pontos para resgatar experiências'
  const levelProgressText =
    isFallbackLoyalty
      ? 'Consulte seu CPF para carregar seu nível'
      : missingToLevel > 0
      ? `Faltam ${missingToLevel} pontos para o próximo nível`
      : 'Nível máximo alcançado'
  const levelPageUrl = useMemo(() => {
    return withCpfParam('/nivel_jornada_real', cpf)
  }, [cpf])

  useEffect(() => {
    let isMounted = true

    const loadRewards = async () => {
      try {
        const response = await api.get('/premios')
        const premios = Array.isArray(response.data) ? response.data : []

        if (isMounted) {
          setApiRewards(premios.map(normalizeReward))
        }
      } catch (error) {
        if (isMounted) {
          setApiRewards([])
        }
      } finally {
        if (isMounted) {
          setIsLoadingRewards(false)
        }
      }
    }

    loadRewards()

    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    let isMounted = true

    const loadLoyalty = async () => {
      if (!cpf) {
        // Redireciona para a tela de entrada de CPF
        router.push('/consultar')
        return
      }

      setIsLoadingLoyalty(true)
      setLoyaltyError(null)

      try {
        const response = await api.get(`/customers/${cpf}/loyalty`)

        if (isMounted) {
          setLoyaltyData(normalizeLoyaltyData(response.data))
          setLoyaltyError(null)
        }
      } catch (primaryError) {
        try {
          const response = await api.get(`/pontos/consultar/${cpf}`)

          if (isMounted) {
            setLoyaltyData(normalizeLoyaltyData(response.data))
            setLoyaltyError(null)
          }
        } catch (error) {
          if (isMounted) {
            setLoyaltyData(fallbackLoyaltyData)
            setLoyaltyError(getApiErrorMessage(error, getApiErrorMessage(primaryError, 'CPF não encontrado.')))
          }
        }
      } finally {
        if (isMounted) {
          setIsLoadingLoyalty(false)
        }
      }
    }

    loadLoyalty()

    return () => {
      isMounted = false
    }
  }, [cpf])

  const rewards = useMemo(() => {
    if (!apiRewards.length) return rewardDefaults

    const apiSlugs = new Set(apiRewards.map((reward) => reward.slug))
    const missingDefaults = rewardDefaults.filter((reward) => !apiSlugs.has(reward.slug))

    return [...apiRewards, ...missingDefaults]
  }, [apiRewards])

  return (
    <main className="points-page">
      <GoldParticles />

      <section className="points-shell">
        <header className="points-header">
          <button className="round-action" type="button" aria-label="Abrir menu">
            <Menu size={24} strokeWidth={1.8} />
          </button>

          <img
            className="points-logo"
            src="/images/logo-jornada-real.png"
            alt="Hotel Real Cabo Frio"
          />

          <button className="round-action bell-action" type="button" aria-label="Notificações">
            <Bell size={23} strokeWidth={1.8} />
            <span />
          </button>
        </header>

        {isLoadingLoyalty && (
          <section className="loading-indicator">
            <p>Carregando seus dados da Jornada Real...</p>
          </section>
        )}

        {loyaltyError && !isLoadingLoyalty && cpf && (
          <section className="error-indicator">
            <p>{loyaltyError}</p>
            <button type="button" onClick={() => router.push('/consultar')}>
              Voltar e tentar novamente
            </button>
          </section>
        )}

        {loyaltyData && (
          <>
        <section className="welcome-card">
          <div>
            <p>Você está quase lá 👑</p>
            <h1>
              {customerName} <Crown size={18} strokeWidth={1.6} />
            </h1>
            <span>
              Você está evoluindo na Jornada Real
              <br />
              e conquistando experiências únicas!
            </span>
          </div>

          <aside className="current-points-card">
            <strong>Pontos atuais</strong>
            <div>
              <Crown size={32} strokeWidth={1.5} />
              <span>{currentPoints}</span>
            </div>
            <small>pontos</small>
          </aside>
        </section>

        <section className="level-card card">
          <h2>
            <Star size={17} fill="currentColor" />
            Seu progresso de nível
            <Star size={17} fill="currentColor" />
          </h2>

          <div className="level-map">
            <article>
              <div className="level-medal essence">
                <Leaf size={26} strokeWidth={1.7} />
              </div>
              <h3>Essência</h3>
              <p>0 a 50 pontos</p>
            </article>

            <article>
              <div className="level-medal experience">
                <Star size={26} fill="currentColor" strokeWidth={1.4} />
              </div>
              <h3>Experiência</h3>
              <p>50 a 90 pontos</p>
            </article>

            <article>
              <div className="level-medal real">
                <Crown size={28} strokeWidth={1.7} />
              </div>
              <h3>Real</h3>
              <p>90+ pontos</p>
            </article>
          </div>

          <div className="level-line" aria-hidden="true">
            <span />
          </div>

          <div className="level-progress">
            <div className="level-fill" style={{ width: `${levelProgress}%` }} />
            <div className="level-marker" style={{ left: `${levelProgress}%` }}>
              <Star size={16} fill="currentColor" />
            </div>
          </div>

          <div className="level-summary">
            <Star size={25} fill="currentColor" />
            <p>
              <strong>{lifetimePoints}</strong> / {nextLevelPoints} pontos
              <span>{levelProgressText}</span>
            </p>
          </div>

          <button
            type="button"
            className="level-page-button"
            onClick={() => router.push(levelPageUrl)}
          >
            <span>Ver tela de níveis</span>
            <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
            <ArrowRight size={18} strokeWidth={1.9} />
          </button>
        </section>

        <section className="reward-progress card">
          <h2>
            <Crown size={18} />
            Seu progresso de prêmios
            <Crown size={18} />
          </h2>

          <div className="reward-progress-row">
            <div className="reward-bar">
              <span style={{ width: `${rewardProgress}%` }} />
              <i style={{ left: `${rewardProgress}%` }} />
            </div>

            <aside>
              <Crown size={36} strokeWidth={1.6} />
              <strong>{rewardSummary}</strong>
              <small>{rewardSummaryLabel}</small>
            </aside>
          </div>

          <p>{rewardProgressText}</p>
        </section>

        <section className="exclusive-section">
          <h2>
            <Crown size={20} />
            Prêmios exclusivos
            <Crown size={20} />
          </h2>
          <p>Escolha seu próximo objetivo e transforme sua estadia em conquistas.</p>

          <div className="reward-grid">
            {rewards.map((reward) => (
              <article
                className="reward-card"
                key={reward.slug || reward.name}
                onClick={() => router.push(withCpfParam(`/resgate_dos_premios?premio=${reward.slug}`, cpf))}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    router.push(withCpfParam(`/resgate_dos_premios?premio=${reward.slug}`, cpf))
                  }
                }}
              >
                {reward.badge && <span className="reward-badge">{reward.badge}</span>}
                {reward.image ? (
                  <img src={reward.image} alt={reward.name} />
                ) : (
                  <div className="reward-image-empty">
                    <Gift size={28} strokeWidth={1.6} />
                    <span>
                      {isLoadingRewards ? 'Carregando imagem' : 'Imagem não cadastrada'}
                    </span>
                  </div>
                )}
                <div>
                  <h3>{reward.name}</h3>
                  <p>
                    <Crown size={17} strokeWidth={1.7} />
                    <strong>{reward.points}</strong> pontos
                  {reward.slug === 'tecnologia-real' && <span className="points-tag">• Mais disputado</span>}
                  </p>
                  <small>{reward.footer}</small>
                </div>
              </article>
            ))}
          </div>

          <button
            type="button"
            className="all-rewards"
            onClick={() => router.push(withCpfParam('/resgate_dos_premios', cpf))}
          >
            <span>
              <Coffee size={19} strokeWidth={1.8} />
              Escolher meu prêmio
            </span>
            <img className="jr-button-crest all-rewards-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
            <ArrowRight size={19} strokeWidth={1.9} />
          </button>
        </section>
          </>
        )}

        <nav className="bottom-nav" aria-label="Navegação principal">
          {navItems.map((item, index) => {
            const Icon = item.icon
            return (
              <button
                type="button"
                className={index === 0 ? 'active' : ''}
                key={item.label}
                onClick={() => router.push(
                  ['Minha Jornada', 'Prêmios'].includes(item.label)
                    ? withCpfParam(item.href, cpf)
                    : item.href
                )}
              >
                <Icon size={26} strokeWidth={1.8} />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>
      </section>

      <style jsx global>{`
        .points-page {
          --gold: #f6c637;
          --gold-soft: #ffe08a;
          --amber: #c57a0d;
          --purple: #a65aff;
          min-height: 100svh;
          overflow-x: hidden;
          color: #fff3dd;
          background:
            radial-gradient(circle at 50% 0%, rgba(142, 83, 10, 0.16), transparent 24rem),
            radial-gradient(circle at 50% 68%, rgba(111, 50, 160, 0.12), transparent 18rem),
            #020302;
          font-family: 'Playfair Display', serif;
        }

        body:has(.points-page) button[aria-label^=Abrir][aria-label*=configura],
        body:has(.points-page) nextjs-portal {
          display: none;
        }

        .points-page::before {
          content: '';
          position: fixed;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          background:
            radial-gradient(circle at 0% 68%, rgba(246, 198, 55, 0.2) 0 1px, transparent 2px),
            radial-gradient(circle at 100% 78%, rgba(246, 198, 55, 0.16) 0 1px, transparent 2px);
          background-size: 17px 17px, 19px 19px;
          opacity: 0.4;
        }

        .points-shell {
          position: relative;
          z-index: 30;
          width: min(100% - 12px, 430px);
          margin: 0 auto;
          padding: 8px 0 10px;
        }

        .points-header {
          display: grid;
          grid-template-columns: 42px 1fr 42px;
          align-items: start;
          min-height: 72px;
        }

        .round-action {
          position: relative;
          width: 36px;
          height: 36px;
          display: grid;
          place-items: center;
          color: var(--gold);
          background: rgba(0, 0, 0, 0.38);
          border: 1.2px solid rgba(246, 198, 55, 0.48);
          border-radius: 50%;
          box-shadow: inset 0 0 12px rgba(246, 198, 55, 0.06);
          cursor: pointer;
        }

        .bell-action {
          justify-self: end;
        }

        .bell-action span {
          position: absolute;
          top: 3px;
          right: 3px;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--gold);
        }

        .points-logo {
          width: clamp(210px, 61vw, 255px);
          justify-self: center;
          filter: drop-shadow(0 6px 14px rgba(0, 0, 0, 0.86));
        }

        .loading-indicator,
        .error-indicator {
          margin: 10px 0;
          padding: 16px;
          color: #fff5df;
          border: 1.2px solid rgba(168, 99, 10, 0.72);
          border-radius: 8px;
          background:
            linear-gradient(180deg, rgba(255, 219, 117, 0.05), rgba(0, 0, 0, 0.78)),
            rgba(5, 5, 4, 0.82);
          box-shadow:
            0 0 20px rgba(246, 198, 55, 0.12),
            inset 0 0 24px rgba(246, 198, 55, 0.04);
          text-align: center;
        }

        .loading-indicator p,
        .error-indicator p {
          margin: 0;
          font-size: 0.88rem;
          line-height: 1.35;
        }

        .error-indicator button {
          min-height: 38px;
          margin-top: 12px;
          padding: 0 16px;
          color: #160d04;
          border: 1px solid #ffe799;
          border-radius: 8px;
          background: linear-gradient(180deg, #ffe08a, #d9981b 60%, #a75f05);
          font-family: 'Cinzel', serif;
          font-size: 0.72rem;
          font-weight: 800;
          text-transform: uppercase;
          cursor: pointer;
        }

        .card,
        .welcome-card,
        .bottom-nav {
          border: 1.2px solid rgba(168, 99, 10, 0.72);
          background:
            linear-gradient(180deg, rgba(255, 219, 117, 0.04), rgba(0, 0, 0, 0.78)),
            rgba(5, 5, 4, 0.78);
          box-shadow:
            0 0 20px rgba(246, 198, 55, 0.12),
            inset 0 0 24px rgba(246, 198, 55, 0.04);
        }

        .welcome-card {
          display: grid;
          grid-template-columns: 1fr 130px;
          gap: 16px;
          align-items: stretch;
          padding: 16px;
          border-radius: 12px;
        }

        .welcome-card p {
          margin: 0 0 4px;
          font-size: 0.82rem;
          color: #fff7e9;
        }

        .welcome-card h1 {
          display: flex;
          align-items: center;
          gap: 7px;
          margin: 0 0 12px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 1.25rem;
          line-height: 1.1;
          text-transform: uppercase;
        }

        .welcome-card span {
          display: block;
          color: #fff4dc;
          font-size: 0.8rem;
          line-height: 1.32;
        }

        .current-points-card {
          min-height: 110px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          gap: 6px;
          padding: 14px 12px;
          border: 1px solid rgba(246, 198, 55, 0.62);
          border-radius: 14px;
          background:
            radial-gradient(circle at 50% 26%, rgba(246, 198, 55, 0.12), transparent 45%),
            rgba(9, 7, 5, 0.76);
        }

        .current-points-card strong {
          color: #fff7e9;
          font-family: 'Cinzel', serif;
          font-size: 0.62rem;
          text-transform: uppercase;
        }

        .current-points-card div {
          display: flex;
          align-items: center;
          gap: 9px;
          margin-top: 8px;
          color: var(--gold);
        }

        .current-points-card div span {
          color: #fff8ee;
          font-family: 'Cinzel', serif;
          font-size: 2.35rem;
          font-weight: 700;
          line-height: 1;
        }

        .current-points-card small {
          color: var(--gold);
          font-size: 0.96rem;
        }

        .card {
          margin-top: 14px;
          padding: 14px 14px 16px;
          border-radius: 12px;
        }

        .card h2,
        .exclusive-section h2 {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin: 0;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(1rem, 4.2vw, 1.18rem);
          text-align: center;
          text-transform: uppercase;
        }

        .level-map {
          position: relative;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
          margin-top: 16px;
        }

        .level-map::before {
          content: '';
          position: absolute;
          top: 31px;
          left: 16%;
          right: 16%;
          height: 3px;
          background: linear-gradient(90deg, var(--gold), var(--purple), var(--gold));
          box-shadow: 0 0 12px rgba(166, 90, 255, 0.5);
        }

        .level-map article {
          position: relative;
          z-index: 2;
          text-align: center;
        }

        .level-medal {
          width: 62px;
          height: 62px;
          display: grid;
          place-items: center;
          margin: 0 auto 7px;
          border-radius: 50%;
          border: 2px solid var(--gold);
          color: var(--gold);
          background: radial-gradient(circle at 35% 28%, rgba(255, 238, 170, 0.18), rgba(72, 44, 8, 0.78));
          box-shadow: 0 0 18px rgba(246, 198, 55, 0.25);
        }

        .level-medal.experience {
          border-color: #c17bff;
          color: #dfb4ff;
          background: radial-gradient(circle at 35% 28%, rgba(255, 255, 255, 0.2), rgba(88, 44, 122, 0.82));
          box-shadow: 0 0 20px rgba(166, 90, 255, 0.42);
        }

        .level-map h3 {
          margin: 0 0 3px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 0.76rem;
          text-transform: uppercase;
        }

        .level-map article:nth-child(2) h3 {
          color: #c17bff;
        }

        .level-map p {
          margin: 0;
          color: #fff4df;
          font-size: 0.68rem;
        }

        .level-line {
          height: 1px;
          margin: 12px 24px 8px;
          background: linear-gradient(90deg, var(--gold), var(--purple), var(--gold));
          opacity: 0.8;
        }

        .level-progress {
          position: relative;
          height: 13px;
          margin: 0 12px;
          border: 1px solid rgba(246, 198, 55, 0.72);
          border-radius: 999px;
          background: rgba(5, 4, 3, 0.88);
          box-shadow: inset 0 0 10px rgba(246, 198, 55, 0.08);
        }

        .level-fill {
          height: 100%;
          border-radius: 999px;
          background: linear-gradient(90deg, #7a3bd6, #ce8cff, #e3b15b);
          box-shadow: 0 0 12px rgba(166, 90, 255, 0.55);
        }

        .level-marker {
          position: absolute;
          top: 50%;
          width: 24px;
          height: 24px;
          display: grid;
          place-items: center;
          transform: translate(-50%, -50%);
          color: #fff7df;
          background: linear-gradient(180deg, #ffe38a, #b76b08);
          border-radius: 50%;
          box-shadow: 0 0 12px rgba(246, 198, 55, 0.4);
        }

        .level-summary {
          width: min(280px, 85vw);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 14px;
          margin: 16px auto 0;
          padding: 12px 16px;
          color: #fff4df;
          border: 1px solid rgba(246, 198, 55, 0.62);
          border-radius: 12px;
          background: rgba(8, 7, 5, 0.78);
        }

        .level-summary svg {
          color: #c17bff;
        }

        .level-summary p {
          margin: 0;
          font-size: 1rem;
          line-height: 1.2;
        }

        .level-summary strong {
          color: #c17bff;
          font-family: 'Cinzel', serif;
          font-size: 1.35rem;
        }

        .level-summary span {
          display: block;
          font-size: 0.72rem;
        }

        .level-page-button {
          width: min(100%, 292px);
          min-height: 42px;
          display: grid;
          grid-template-columns: 1fr 32px 18px;
          align-items: center;
          gap: 8px;
          margin: 12px auto 0;
          padding: 0 12px 0 18px;
          color: #160d04;
          border: 1px solid #ffe799;
          border-radius: 10px;
          background: linear-gradient(180deg, #ffe08a, #d9981b 60%, #a75f05);
          box-shadow: 0 8px 18px rgba(0, 0, 0, 0.3);
          font-family: 'Cinzel', serif;
          font-size: 0.78rem;
          font-weight: 800;
          text-transform: uppercase;
          cursor: pointer;
        }

        .level-page-button span {
          text-align: center;
        }

        .reward-progress {
          padding-bottom: 10px;
        }

        .reward-progress-row {
          display: grid;
          grid-template-columns: 1fr 88px;
          gap: 12px;
          align-items: center;
          margin-top: 13px;
        }

        .reward-bar {
          position: relative;
          height: 13px;
          border: 1px solid rgba(166, 94, 13, 0.74);
          border-radius: 999px;
          background: #050403;
          overflow: visible;
        }

        .reward-bar span {
          display: block;
          height: 100%;
          border-radius: 999px;
          background: linear-gradient(90deg, #ffe17c, #d58d18);
          box-shadow: 0 0 12px rgba(246, 198, 55, 0.35);
        }

        .reward-bar i {
          position: absolute;
          top: 50%;
          width: 18px;
          height: 18px;
          transform: translate(-50%, -50%);
          border-radius: 50%;
          background: linear-gradient(180deg, #fff0a7, #d69016);
          box-shadow: 0 0 8px rgba(246, 198, 55, 0.4);
        }

        .reward-progress aside {
          min-height: 70px;
          display: grid;
          grid-template-columns: 32px 1fr;
          align-items: center;
          column-gap: 7px;
          padding: 8px;
          color: var(--gold);
          border: 1px solid rgba(246, 198, 55, 0.52);
          border-radius: 10px;
          background: rgba(8, 7, 5, 0.78);
        }

        .reward-progress aside strong {
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 1.4rem;
          line-height: 0.9;
        }

        .reward-progress aside small {
          grid-column: 2;
          color: #fff3dd;
          font-size: 0.58rem;
          line-height: 1.1;
        }

        .reward-progress > p {
          margin: 4px 0 0;
          color: #fff3dd;
          font-size: 0.74rem;
        }

        .exclusive-section {
          margin-top: 12px;
        }

        .exclusive-section > p {
          margin: 3px 0 10px;
          color: #fff3dd;
          font-size: 0.83rem;
          text-align: center;
        }

        .reward-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
        }

        .reward-card {
          position: relative;
          overflow: hidden;
          min-height: 235px;
          border: 1.2px solid var(--gold);
          border-radius: 10px;
          background:
            radial-gradient(circle at 50% 18%, rgba(246, 198, 55, 0.12), transparent 42%),
            rgba(7, 6, 4, 0.88);
          box-shadow: 0 0 14px rgba(246, 198, 55, 0.14);
          cursor: pointer;
        }

        .reward-badge {
          position: absolute;
          top: 0;
          left: 0;
          z-index: 2;
          padding: 4px 7px;
          color: #110b03;
          background: linear-gradient(180deg, #ffe589, #d18a12);
          border-bottom-right-radius: 8px;
          font-family: 'Cinzel', serif;
          font-size: 0.55rem;
          font-weight: 700;
          text-transform: uppercase;
        }

        .reward-card img {
          width: 100%;
          height: 135px;
          display: block;
          object-fit: cover;
          filter: saturate(1.04) contrast(1.08);
        }

        .reward-card:first-child img,
        .reward-card:nth-child(2) img {
          object-fit: contain;
          padding: 8px;
          background:
            radial-gradient(circle at 50% 42%, rgba(246, 198, 55, 0.2), transparent 58%),
            #050403;
        }

        .reward-image-empty {
          height: 135px;
          display: grid;
          place-items: center;
          gap: 7px;
          padding: 14px;
          color: var(--gold);
          background:
            radial-gradient(circle at 50% 42%, rgba(246, 198, 55, 0.2), transparent 58%),
            #050403;
          text-align: center;
        }

        .reward-image-empty span {
          max-width: 95px;
          color: #fff0d2;
          font-size: 0.62rem;
          line-height: 1.15;
        }

        .reward-card > div {
          padding: 8px;
        }

        .reward-card h3 {
          min-height: 30px;
          margin: 0 0 5px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 0.74rem;
          line-height: 1.12;
          text-transform: uppercase;
        }

        .reward-card p {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 4px;
          margin: 0;
          color: #fff4df;
          font-size: 0.88rem;
        }

        .reward-card p svg {
          color: var(--gold);
        }

        .reward-card p strong {
          color: #fff4df;
          font-family: 'Cinzel', serif;
          font-size: 1.08rem;
        }

        .points-tag {
          color: var(--gold);
          font-size: 0.64rem;
          font-weight: 700;
          text-transform: uppercase;
        }

        .reward-card small {
          display: block;
          margin-top: 5px;
          color: #fff4df;
          font-size: 0.62rem;
          line-height: 1.22;
        }

        .all-rewards {
          width: 100%;
          min-height: 42px;
          display: grid;
          grid-template-columns: 34px 1fr 34px 19px;
          align-items: center;
          column-gap: 8px;
          margin-top: 10px;
          padding: 0 15px;
          color: var(--gold);
          border: 1px solid rgba(246, 198, 55, 0.58);
          border-radius: 8px;
          background: rgba(7, 6, 4, 0.84);
          font-family: 'Cinzel', serif;
          font-size: 0.78rem;
          font-weight: 700;
          text-transform: uppercase;
          cursor: pointer;
        }

        .all-rewards span {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          grid-column: 1 / 3;
        }

        .all-rewards-crest {
          justify-self: end;
        }

        .bottom-nav {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          min-height: 62px;
          margin-top: 10px;
          border-radius: 8px;
        }

        .bottom-nav button {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 3px;
          color: rgba(255, 243, 221, 0.64);
          background: transparent;
          border: 0;
          font-family: 'Cinzel', serif;
          font-size: 0.55rem;
          text-transform: uppercase;
          cursor: pointer;
        }

        .bottom-nav button.active {
          color: var(--gold);
        }

        .bottom-nav button.active svg {
          fill: var(--gold);
          filter: drop-shadow(0 0 8px rgba(246, 198, 55, 0.5));
        }

        @media (max-width: 370px) {
          .points-shell {
            width: min(100% - 8px, 430px);
          }

          .welcome-card {
            grid-template-columns: 1fr 106px;
            padding: 12px;
          }

          .current-points-card div span {
            font-size: 2.05rem;
          }

          .reward-card {
            min-height: 222px;
          }

          .reward-card img {
            height: 122px;
          }
        }

        @media (min-width: 900px) {
          .points-page {
            background:
              radial-gradient(circle at 18% 12%, rgba(142, 83, 10, 0.18), transparent 26rem),
              radial-gradient(circle at 82% 24%, rgba(111, 50, 160, 0.16), transparent 24rem),
              radial-gradient(circle at 50% 88%, rgba(246, 198, 55, 0.08), transparent 28rem),
              #020302;
          }

          .points-shell {
            width: min(1180px, calc(100% - 64px));
            display: grid;
            grid-template-columns: minmax(320px, 0.92fr) minmax(0, 1.45fr);
            gap: 18px;
            padding: 20px 0 24px;
          }

          .points-header,
          .loading-indicator,
          .error-indicator,
          .exclusive-section,
          .bottom-nav {
            grid-column: 1 / -1;
          }

          .points-header {
            min-height: 92px;
            align-items: center;
          }

          .points-logo {
            width: clamp(250px, 22vw, 330px);
          }

          .welcome-card {
            grid-column: 1;
            align-self: start;
            min-height: 190px;
            grid-template-columns: minmax(0, 1fr) 148px;
            gap: 16px;
            padding: 22px;
            border-radius: 12px;
          }

          .welcome-card h1 {
            font-size: 1.65rem;
          }

          .welcome-card span {
            font-size: 0.95rem;
          }

          .current-points-card {
            min-height: 136px;
          }

          .level-card {
            grid-column: 2;
            grid-row: 2 / span 2;
            margin-top: 0;
            padding: 22px;
            border-radius: 12px;
          }

          .reward-progress {
            grid-column: 1;
            margin-top: 0;
            padding: 18px;
            border-radius: 12px;
          }

          .card h2,
          .exclusive-section h2 {
            font-size: 1.35rem;
          }

          .level-map {
            gap: 18px;
            margin-top: 24px;
          }

          .level-medal {
            width: 76px;
            height: 76px;
          }

          .level-map h3 {
            font-size: 0.9rem;
          }

          .level-map p {
            font-size: 0.78rem;
          }

          .level-summary {
            width: min(100%, 380px);
            margin-top: 20px;
          }

          .exclusive-section {
            margin-top: 0;
          }

          .exclusive-section > p {
            margin: 6px 0 16px;
            font-size: 0.98rem;
          }

          .reward-grid {
            gap: 16px;
          }

          .reward-card {
            min-height: 330px;
            border-radius: 14px;
          }

          .reward-card img,
          .reward-image-empty {
            height: 198px;
          }

          .reward-card > div {
            padding: 14px;
          }

          .reward-card h3 {
            min-height: auto;
            font-size: 1rem;
          }

          .reward-card small {
            font-size: 0.78rem;
          }

          .all-rewards {
            width: min(420px, 100%);
            justify-self: center;
            margin: 16px auto 0;
          }

          .bottom-nav {
            min-height: 70px;
            margin-top: 0;
            border-radius: 14px;
          }
        }
      `}</style>
    </main>
  )
}
