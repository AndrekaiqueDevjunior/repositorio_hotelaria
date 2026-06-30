'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  ArrowLeft,
  ArrowRight,
  Clock3,
  Copy,
  Crown,
  Gift,
  Info,
  LockKeyhole,
  ShieldCheck,
  Sparkles,
  Ticket,
} from 'lucide-react'
import GoldParticles from '@/components/GoldParticles'
import { api } from '@/lib/api'

const prizeDefaults = [
  {
    slug: 'tecnologia-real',
    name: 'Tecnologia Real',
    subtitle: 'iPhone 16e',
    points: 90,
    image: '/images/premios/tecnologia-real.png',
    badge: 'Mais disputado',
    status: 'Disponível: 1 restante',
    statusSub: 'Última unidade disponível no momento!',
    aboutTitle: 'Sobre o prêmio',
    about: 'Transforme sua rotina em experiência.',
  },
  {
    slug: 'rituais-do-real',
    name: 'Rituais do Real',
    subtitle: 'Cafeteira Premium',
    points: 35,
    image: '/images/premios/rituais-do-real.png',
    aboutTitle: 'Sobre o prêmio',
    about: 'Transforme sua rotina em experiência.',
  },
  {
    slug: 'o-retorno-do-sonho',
    name: 'O Retorno do Sonho',
    subtitle: '1 diária com hidro + champanhe cortesia',
    points: 25,
    image: '/images/premios/o-retorno-do-sonho.png',
    aboutTitle: 'Sobre o prêmio',
    about: '1 diária com hidro + champanhe cortesia.',
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

const getApiErrorMessage = (error, fallback) => {
  const data = error.response?.data

  if (typeof data === 'string') return data
  if (typeof data?.detail === 'string') return data.detail
  if (typeof data?.message === 'string') return data.message
  if (Array.isArray(data?.detail)) return data.detail.map((item) => item.msg || item.message).filter(Boolean).join(', ')

  return fallback
}

const getRedemptionPayload = (responseData) => responseData?.data || responseData || {}

const getRedemptionCode = (data) =>
  data.redemption_code || data.codigo_resgate || data.codigo || data.code || ''

const getRedemptionExpiry = (data) =>
  data.expires_at || data.expira_em || data.valido_ate || data.expiresAt || null

const getRedemptionStatus = (data) =>
  data.codigo_status || data.code_status || data.status || data.redemption_status || ''

const shouldFallbackToLegacyRedeem = (error) => [404, 405].includes(error.response?.status)

const formatDate = (value) => {
  if (!value) return null

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null

  return date.toLocaleDateString('pt-BR')
}

const withCpfParam = (href, cpf) => {
  if (!cpf) return href

  const separator = href.includes('?') ? '&' : '?'
  return `${href}${separator}cpf=${encodeURIComponent(cpf)}`
}

const normalizePrize = (premio) => {
  const slug = premio.slug || slugify(premio.nome)
  const defaults = prizeDefaults.find((item) => item.slug === slug) || {}
  const points = premio.preco_em_pontos ?? premio.preco_em_rp ?? defaults.points ?? 0
  const stock = premio.estoque ?? premio.quantidade_disponivel

  return {
    ...defaults,
    id: premio.id,
    slug,
    name: premio.nome || defaults.name || 'Prêmio Real',
    subtitle: premio.descricao || defaults.subtitle || 'Experiência exclusiva Hotel Real',
    points,
    image: resolveImageUrl(premio.imagem_url || premio.imagemUrl) || defaults.image || '',
    badge: defaults.badge,
    status:
      stock !== undefined && stock !== null
        ? stock > 0
          ? `Disponível: ${stock} restante${stock === 1 ? '' : 's'}`
          : 'Indisponível no momento'
        : defaults.status,
    statusSub:
      stock !== undefined && stock !== null && stock <= 3 && stock > 0
        ? 'Últimas unidades disponíveis no momento!'
        : defaults.statusSub,
    aboutTitle: defaults.aboutTitle || 'Sobre o prêmio',
    about: premio.descricao || defaults.about || 'Prêmio exclusivo da Jornada Real.',
  }
}

function RoyalCrownMark() {
  return (
    <svg
      className="royal-crown-mark"
      viewBox="0 0 84 58"
      role="img"
      aria-label="Coroa Real"
    >
      <defs>
        <linearGradient id="royalCrownGold" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#fff4a8" />
          <stop offset="35%" stopColor="#f6c637" />
          <stop offset="70%" stopColor="#c57a0d" />
          <stop offset="100%" stopColor="#7a4205" />
        </linearGradient>
        <linearGradient id="royalCrownEdge" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stopColor="#fff8c8" />
          <stop offset="100%" stopColor="#9b5b08" />
        </linearGradient>
        <filter id="royalCrownGlow" x="-35%" y="-45%" width="170%" height="190%">
          <feGaussianBlur stdDeviation="2.4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <path
        d="M9 43 C12 36 12 28 14 18 C20 25 25 30 31 34 C35 25 39 17 42 8 C45 17 49 25 53 34 C59 30 64 25 70 18 C72 28 72 36 75 43 Z"
        fill="url(#royalCrownGold)"
        stroke="url(#royalCrownEdge)"
        strokeWidth="2.2"
        strokeLinejoin="round"
        filter="url(#royalCrownGlow)"
      />
      <path
        d="M17 39 C28 42 56 42 67 39 L64 51 C53 54 31 54 20 51 Z"
        fill="url(#royalCrownGold)"
        stroke="#fff0a6"
        strokeWidth="2.1"
        strokeLinejoin="round"
      />
      <path
        d="M21 45 C32 47 52 47 63 45"
        stroke="#7a4205"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.58"
      />
      <path
        d="M20 38 C27 30 31 25 33 17 M51 17 C53 25 57 30 64 38"
        fill="none"
        stroke="#fff3b0"
        strokeWidth="1.3"
        strokeLinecap="round"
        opacity="0.62"
      />
      <path
        d="M35 35 C38 25 40 17 42 8 C44 17 46 25 49 35"
        fill="none"
        stroke="#fff7c8"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.72"
      />
      <circle cx="14" cy="17" r="4.2" fill="#ffe37a" stroke="#fff8ce" strokeWidth="1.5" />
      <circle cx="42" cy="8" r="4.8" fill="#fff1ad" stroke="#fffbe0" strokeWidth="1.5" />
      <circle cx="70" cy="17" r="4.2" fill="#ffe37a" stroke="#fff8ce" strokeWidth="1.5" />
      <path
        d="M37 43 L42 38 L47 43 L42 48 Z"
        fill="#8d1c7f"
        stroke="#ffe7a0"
        strokeWidth="1.3"
      />
      <circle cx="27" cy="44" r="2.4" fill="#36c8ff" stroke="#fff6c2" strokeWidth="1" />
      <circle cx="57" cy="44" r="2.4" fill="#36c8ff" stroke="#fff6c2" strokeWidth="1" />
      <path d="M24 51 H60" stroke="#fff2a8" strokeWidth="1.2" strokeLinecap="round" opacity="0.6" />
    </svg>
  )
}

export default function ResgateDosPremios() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const selectedSlug = searchParams.get('premio')
  const cpf = (searchParams.get('cpf') || searchParams.get('documento') || '').replace(/\D/g, '')
  const [redeemedPrize, setRedeemedPrize] = useState(null)
  const [apiPrizes, setApiPrizes] = useState([])
  const [isLoadingPrizes, setIsLoadingPrizes] = useState(true)
  const [isRedeeming, setIsRedeeming] = useState(false)
  const [redeemError, setRedeemError] = useState(null)

  useEffect(() => {
    let isMounted = true

    const loadPrizes = async () => {
      try {
        const response = await api.get('/premios')
        const premios = Array.isArray(response.data) ? response.data : []

        if (isMounted) {
          setApiPrizes(premios.map(normalizePrize))
        }
      } catch (error) {
        if (isMounted) {
          setApiPrizes([])
        }
      } finally {
        if (isMounted) {
          setIsLoadingPrizes(false)
        }
      }
    }

    loadPrizes()

    return () => {
      isMounted = false
    }
  }, [])

  const prizes = apiPrizes

  const orderedPrizes = useMemo(() => {
    if (!selectedSlug) return prizes

    const selected = prizes.find((prize) => prize.slug === selectedSlug)
    if (!selected) return prizes

    return [selected, ...prizes.filter((prize) => prize.slug !== selectedSlug)]
  }, [prizes, selectedSlug])

  const handleRedeem = async (prize) => {
    if (isRedeeming) return

    if (!prize.id) {
      setRedeemError('Prêmio ainda não disponível para resgate.')
      return
    }

    if (!cpf) {
      setRedeemError('Consulte seu CPF antes de resgatar um prêmio.')
      return
    }

    setIsRedeeming(true)
    setRedeemError(null)

    try {
      let response

      try {
        response = await api.post('/rewards/redeem', {
          reward_id: prize.id,
          customer_document: cpf,
        })
      } catch (primaryError) {
        if (!shouldFallbackToLegacyRedeem(primaryError)) {
          throw primaryError
        }

        response = await api.post('/premios/resgatar-publico', {
          premio_id: prize.id,
          cliente_documento: cpf,
        })
      }

      const redemption = getRedemptionPayload(response.data)
      const redemptionCode = getRedemptionCode(redemption)

      setRedeemedPrize({
        ...prize,
        code: redemptionCode,
        expiresAt: getRedemptionExpiry(redemption),
        status: getRedemptionStatus(redemption),
      })
    } catch (error) {
      if (error.response?.status === 402) {
        setRedeemError('Saldo insuficiente de pontos.')
      } else if (error.response?.status === 409) {
        setRedeemError('Prêmio sem estoque disponível.')
      } else {
        setRedeemError(getApiErrorMessage(error, 'Erro ao resgatar prêmio.'))
      }
    } finally {
      setIsRedeeming(false)
    }
  }

  const redeemedPrizeExpiresAt = formatDate(redeemedPrize?.expiresAt)
  const isRedeemedCodeActive = ['active', 'ativo'].includes(String(redeemedPrize?.status || '').toLowerCase())

  return (
    <main className="redeem-page">
      <GoldParticles />

      {redeemError && !redeemedPrize && (
        <div className="redeem-error-toast" role="alert">
          <p>{redeemError}</p>
          <button type="button" onClick={() => setRedeemError(null)}>
            Fechar
          </button>
        </div>
      )}

      {!redeemedPrize && (
        <section className="redeem-shell">
          <header className="redeem-header">
            <button
              type="button"
              className="back-button"
              aria-label="Voltar"
              onClick={() => router.push(withCpfParam('/consultar-pontos', cpf))}
            >
              <ArrowLeft size={22} strokeWidth={1.9} />
            </button>

            <img src="/images/logo-jornada-real.png" alt="Hotel Real Cabo Frio" />
          </header>

          <div className="title-area">
            <h1>
              <Crown size={20} />
              Resgatar Prêmio
              <Crown size={20} />
            </h1>
            <p>Escolha seu prêmio e transforme seus pontos em experiências únicas.</p>
          </div>

          <div className="redeem-list">
            {orderedPrizes.map((prize) => (
              <article className="redeem-block" key={prize.slug}>
                <section className="prize-panel">
              <div className="prize-visual">
                {prize.badge && <span className="prize-badge">{prize.badge}</span>}
                {prize.image ? (
                  <img src={prize.image} alt={prize.name} />
                ) : (
                  <div className="prize-image-empty">
                    <Gift size={34} strokeWidth={1.6} />
                    <span>
                      {isLoadingPrizes ? 'Carregando imagem do prêmio' : 'Imagem não cadastrada'}
                    </span>
                  </div>
                )}
                <div className="visual-caption">
                  <h2>{prize.name}</h2>
                  <p>{prize.subtitle}</p>
                </div>
              </div>

              <div className="prize-info">
                <div className="points-line">
                  <Crown size={28} strokeWidth={1.7} />
                  <strong>{prize.points}</strong>
                  <span>pontos</span>
                  {prize.badge && <small>• Mais disputado</small>}
                </div>

                {prize.status && (
                  <article className="info-box status-box">
                    <Clock3 size={20} strokeWidth={1.8} />
                    <div>
                      <h3>{prize.status}</h3>
                      <p>{prize.statusSub}</p>
                    </div>
                  </article>
                )}

                <article className="info-box">
                  <Gift size={21} strokeWidth={1.8} />
                  <div>
                    <h3>{prize.aboutTitle}</h3>
                    <p>{prize.about}</p>
                  </div>
                </article>

                <article className="info-box warning-box">
                  <Sparkles size={21} strokeWidth={1.8} />
                  <p>Ao confirmar, seus pontos serão resgatados e não poderão ser cancelados.</p>
                </article>
              </div>

              <button
                type="button"
                className="confirm-button"
                onClick={() => handleRedeem(prize)}
                disabled={isRedeeming}
              >
                <span>{isRedeeming ? 'Processando...' : 'Confirmar Resgate'}</span>
                <span className="confirm-button-end">
                  <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
                  <ArrowRight size={22} strokeWidth={1.9} />
                </span>
              </button>

              <p className="secure-note">
                <LockKeyhole size={13} strokeWidth={2} />
                Resgate 100% seguro
              </p>
                </section>
              </article>
            ))}
          </div>
        </section>
      )}

      {redeemedPrize && (
        <section className="redeem-success-backdrop" role="dialog" aria-modal="true">
          <div className="success-burst" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>

          <article className="redeem-success-card">
            <div className="success-hero">
              <div className="success-brand">
                <img
                  src="/images/brasao-hotel-real-transparente.png?v=4"
                  alt="Hotel Real Cabo Frio"
                />
              </div>

            </div>

            <p className="success-kicker">
              <Crown size={15} strokeWidth={1.9} />
              Jornada Real
              <Crown size={15} strokeWidth={1.9} />
            </p>

            <h2>Experiência <span>Confirmada</span></h2>
            <p className="success-copy">
              Sua experiência <strong>{redeemedPrize.name}</strong>
              <br />
              foi confirmada com sucesso.
            </p>

            <div className="success-prize">
              {redeemedPrize.image ? (
                <img src={redeemedPrize.image} alt={redeemedPrize.name} />
              ) : (
                <div className="success-prize-empty">
                  <Gift size={24} strokeWidth={1.7} />
                </div>
              )}
              <div>
                <small>{redeemedPrize.name}</small>
                <strong>{redeemedPrize.subtitle}</strong>
                <span>
                  <Sparkles size={14} fill="currentColor" strokeWidth={1.6} />
                  {redeemedPrize.points} pontos utilizados
                </span>
              </div>
            </div>

            <div className="success-code">
              <div className="success-code-label">
                <Ticket size={19} strokeWidth={1.9} />
                <span>Código exclusivo</span>
              </div>

              <div className="success-code-box">
                <strong>{redeemedPrize.code}</strong>
                <button
                  type="button"
                  aria-label="Copiar código"
                  onClick={() => navigator.clipboard?.writeText(redeemedPrize.code)}
                >
                  <Copy size={18} strokeWidth={1.8} />
                </button>
              </div>

              <p>
                <ShieldCheck size={19} strokeWidth={1.9} />
                Apresente este código na recepção para liberar sua experiência exclusiva.
              </p>

              <aside>
                <Info size={18} strokeWidth={2} />
                <span>
                  Seu código é pessoal, intransferível e{' '}
                  {redeemedPrizeExpiresAt ? (
                    <>
                      válido até <strong>{redeemedPrizeExpiresAt}</strong>.
                    </>
                  ) : (
                    <>com validade definida no momento do resgate.</>
                  )}{' '}
                  Resgates são realizados apenas no Hotel Real.
                </span>
              </aside>
              {isRedeemedCodeActive && <small className="success-status">Código ativo</small>}
            </div>

            <div className="success-actions">
              <button type="button" onClick={() => setRedeemedPrize(null)}>
                <Gift size={19} strokeWidth={1.8} />
                Ver outras experiências
                <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
              </button>
              <button type="button" onClick={() => router.push(withCpfParam('/consultar-pontos', cpf))}>
                <Crown size={19} strokeWidth={1.9} />
                Continuar Jornada Real
                <img className="jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
              </button>
            </div>

            <footer className="success-footer">
              <Crown size={22} strokeWidth={1.9} />
              <p>
                Cada estadia te aproxima de novas experiências exclusivas.
                <strong>Continue avançando!</strong>
              </p>
            </footer>
          </article>
        </section>
      )}

      <style jsx global>{`
        .redeem-page {
          --gold: #f6c637;
          --gold-soft: #ffe08a;
          --line: rgba(157, 91, 8, 0.72);
          min-height: 100svh;
          overflow-x: hidden;
          color: #fff2dc;
          background:
            radial-gradient(circle at 50% 0%, rgba(146, 83, 8, 0.16), transparent 20rem),
            radial-gradient(circle at 50% 58%, rgba(92, 36, 145, 0.09), transparent 18rem),
            #020302;
          font-family: 'Playfair Display', serif;
        }

        body:has(.redeem-page) button[aria-label^=Abrir][aria-label*=configura],
        body:has(.redeem-page) nextjs-portal {
          display: none;
        }

        .redeem-error-toast {
          position: fixed;
          z-index: 120;
          top: 14px;
          left: 50%;
          width: min(calc(100% - 28px), 390px);
          display: grid;
          grid-template-columns: 1fr auto;
          align-items: center;
          gap: 10px;
          padding: 10px 12px;
          color: #fff5df;
          border: 1px solid rgba(246, 198, 55, 0.72);
          border-radius: 8px;
          background:
            linear-gradient(180deg, rgba(75, 22, 22, 0.96), rgba(10, 8, 6, 0.96)),
            #130b06;
          box-shadow: 0 12px 32px rgba(0, 0, 0, 0.56);
          transform: translateX(-50%);
        }

        .redeem-error-toast p {
          margin: 0;
          font-size: 0.82rem;
          line-height: 1.28;
        }

        .redeem-error-toast button {
          min-height: 30px;
          padding: 0 10px;
          color: #130d04;
          border: 1px solid #ffe799;
          border-radius: 7px;
          background: linear-gradient(180deg, #ffe07a 0%, #d9981b 58%, #aa6405 100%);
          font-family: 'Cinzel', serif;
          font-size: 0.62rem;
          font-weight: 800;
          text-transform: uppercase;
          cursor: pointer;
        }

        .redeem-shell {
          position: relative;
          z-index: 30;
          width: min(100% - 14px, 430px);
          margin: 0 auto;
          padding: 6px 0 12px;
        }

        .redeem-block {
          padding: 0 8px 10px;
          border-bottom: 1px solid rgba(157, 91, 8, 0.56);
        }

        .redeem-block + .redeem-block {
          margin-top: 12px;
          padding-top: 6px;
        }

        .redeem-list {
          display: grid;
          gap: 12px;
        }

        .redeem-header {
          display: grid;
          grid-template-columns: 38px 1fr 38px;
          align-items: start;
          min-height: 78px;
        }

        .back-button {
          width: 32px;
          height: 32px;
          display: grid;
          place-items: center;
          color: var(--gold);
          background: rgba(0, 0, 0, 0.28);
          border: 1.4px solid rgba(246, 198, 55, 0.74);
          border-radius: 50%;
          cursor: pointer;
        }

        .redeem-header img {
          width: clamp(168px, 50vw, 214px);
          justify-self: center;
          filter: drop-shadow(0 6px 14px rgba(0, 0, 0, 0.86));
        }

        .title-area {
          margin-top: 4px;
          text-align: center;
        }

        .title-area h1 {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          margin: 0;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(1.55rem, 6.6vw, 2.05rem);
          line-height: 1;
          text-transform: uppercase;
        }

        .title-area p {
          margin: 8px 0 10px;
          color: #fff6e8;
          font-size: clamp(0.72rem, 3vw, 0.86rem);
          line-height: 1.2;
        }

        .prize-panel {
          display: grid;
          grid-template-columns: 1.04fr 1fr;
          gap: 8px;
          padding: 8px;
          border: 1.3px solid var(--line);
          border-radius: 10px;
          background:
            radial-gradient(circle at 24% 30%, rgba(246, 198, 55, 0.1), transparent 32%),
            rgba(5, 5, 4, 0.82);
          box-shadow:
            inset 0 0 20px rgba(246, 198, 55, 0.04),
            0 0 18px rgba(246, 198, 55, 0.08);
        }

        .prize-visual {
          position: relative;
          overflow: hidden;
          min-height: 230px;
          border: 1px solid rgba(246, 198, 55, 0.7);
          border-radius: 8px;
          background:
            radial-gradient(circle at 50% 42%, rgba(246, 198, 55, 0.22), transparent 44%),
            #050403;
        }

        .prize-visual::before {
          content: '';
          position: absolute;
          inset: 0;
          background:
            radial-gradient(circle at 52% 42%, transparent 0 30%, rgba(0, 0, 0, 0.3) 64%, rgba(0, 0, 0, 0.88) 100%),
            repeating-conic-gradient(from 0deg at 50% 48%, rgba(246, 198, 55, 0.22) 0deg 2deg, transparent 2deg 10deg);
          opacity: 0.62;
        }

        .prize-visual img {
          position: relative;
          z-index: 1;
          width: 100%;
          height: 173px;
          display: block;
          object-fit: contain;
          padding: 9px;
          filter: drop-shadow(0 12px 18px rgba(0, 0, 0, 0.72));
        }

        .prize-image-empty {
          position: relative;
          z-index: 1;
          height: 173px;
          display: grid;
          place-items: center;
          gap: 8px;
          padding: 16px;
          color: var(--gold);
          text-align: center;
        }

        .prize-image-empty span {
          display: block;
          max-width: 130px;
          color: #fff1d4;
          font-size: 0.72rem;
          line-height: 1.16;
        }

        .prize-badge {
          position: absolute;
          z-index: 3;
          top: 0;
          left: 0;
          padding: 4px 9px;
          color: #fff8df;
          background: #371071;
          border-bottom-right-radius: 8px;
          border: 1px solid rgba(192, 123, 255, 0.78);
          border-top: 0;
          border-left: 0;
          font-family: 'Cinzel', serif;
          font-size: 0.55rem;
          font-weight: 700;
          text-transform: uppercase;
        }

        .visual-caption {
          position: relative;
          z-index: 2;
          padding: 0 5px 8px;
          text-align: center;
        }

        .visual-caption h2 {
          margin: 0;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(0.92rem, 4vw, 1.1rem);
          line-height: 1.05;
          text-transform: uppercase;
        }

        .visual-caption p {
          margin: 2px 0 0;
          color: #fff5df;
          font-size: 0.82rem;
          line-height: 1.18;
        }

        .prize-info {
          display: flex;
          flex-direction: column;
          gap: 7px;
        }

        .points-line {
          display: grid;
          grid-template-columns: 30px auto 1fr;
          align-items: center;
          column-gap: 8px;
          color: var(--gold);
          min-height: 36px;
        }

        .points-line strong {
          color: #fff8ec;
          font-family: 'Cinzel', serif;
          font-size: 1.55rem;
          line-height: 1;
        }

        .points-line span {
          color: #fff8ec;
          font-size: 0.9rem;
        }

        .points-line small {
          grid-column: 2 / -1;
          color: #a866ff;
          font-size: 0.66rem;
          line-height: 1;
        }

        .info-box {
          display: grid;
          grid-template-columns: 28px 1fr;
          gap: 7px;
          align-items: start;
          min-height: 58px;
          padding: 8px;
          color: var(--gold);
          border: 1px solid rgba(155, 94, 12, 0.88);
          border-radius: 7px;
          background: rgba(9, 8, 6, 0.78);
        }

        .info-box h3 {
          margin: 0 0 3px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 0.75rem;
        }

        .info-box p {
          margin: 0;
          color: #fff5df;
          font-size: 0.68rem;
          line-height: 1.23;
        }

        .status-box h3 {
          color: var(--gold);
        }

        .status-box p {
          color: #b573ff;
          font-weight: 700;
        }

        .warning-box {
          grid-template-columns: 28px 1fr;
          border-color: rgba(142, 73, 255, 0.78);
        }

        .warning-box svg {
          color: #b26dff;
        }

        .warning-box p {
          font-weight: 700;
        }

        .confirm-button {
          grid-column: 1 / -1;
          min-height: 42px;
          display: grid;
          grid-template-columns: 1fr auto;
          align-items: center;
          gap: 12px;
          margin: 2px 4px 0;
          padding: 0 16px;
          color: #130d04;
          background: linear-gradient(180deg, #ffe07a 0%, #d9981b 58%, #aa6405 100%);
          border: 1px solid #ffe799;
          border-radius: 12px;
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.48), 0 10px 18px rgba(0, 0, 0, 0.36);
          font-family: 'Cinzel', serif;
          font-size: clamp(0.78rem, 3.35vw, 0.96rem);
          font-weight: 700;
          text-transform: uppercase;
          cursor: pointer;
        }

        .confirm-button:disabled {
          cursor: wait;
          filter: grayscale(0.25);
          opacity: 0.76;
        }

        .confirm-button > span:first-child {
          text-align: center;
        }

        .confirm-button-end {
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }

        .secure-note {
          grid-column: 1 / -1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          margin: -2px 0 0;
          color: var(--gold);
          font-size: 0.72rem;
        }

        .redeem-success-backdrop {
          position: fixed;
          inset: 0;
          z-index: 90;
          display: grid;
          place-items: center;
          padding: 18px;
          background:
            radial-gradient(circle at 50% 34%, rgba(246, 198, 55, 0.18), transparent 15rem),
            radial-gradient(circle at 50% 54%, rgba(142, 73, 255, 0.14), transparent 13rem),
            rgba(0, 0, 0, 0.78);
          backdrop-filter: blur(7px);
          animation: successFade 260ms ease-out both;
        }

        .redeem-success-card {
          position: relative;
          overflow: hidden;
          width: min(100%, 365px);
          padding: 22px 16px 16px;
          color: #fff4df;
          border: 1.4px solid rgba(246, 198, 55, 0.76);
          border-radius: 12px;
          background:
            linear-gradient(180deg, rgba(22, 15, 4, 0.96), rgba(5, 5, 4, 0.96)),
            #050403;
          box-shadow:
            0 0 0 1px rgba(109, 55, 7, 0.5),
            0 22px 70px rgba(0, 0, 0, 0.78),
            inset 0 0 34px rgba(246, 198, 55, 0.08);
          text-align: center;
          animation: successRise 360ms cubic-bezier(0.2, 0.9, 0.2, 1.15) both;
        }

        .redeem-success-card::before {
          content: '';
          position: absolute;
          inset: -40%;
          background: conic-gradient(
            from 0deg,
            transparent,
            rgba(246, 198, 55, 0.16),
            transparent,
            rgba(142, 73, 255, 0.12),
            transparent
          );
          animation: successHalo 5s linear infinite;
        }

        .redeem-success-card > * {
          position: relative;
          z-index: 1;
        }

        .success-seal {
          position: relative;
          width: 76px;
          height: 76px;
          display: grid;
          place-items: center;
          margin: 0 auto 8px;
          color: #101008;
          border-radius: 50%;
          background: linear-gradient(180deg, #fff3ad, #f1bd34 55%, #a96307);
          box-shadow:
            0 0 0 6px rgba(246, 198, 55, 0.13),
            0 0 32px rgba(246, 198, 55, 0.45);
        }

        .success-seal i {
          position: absolute;
          inset: -7px;
          border: 1px solid rgba(246, 198, 55, 0.5);
          border-radius: 50%;
          animation: successPulse 1.8s ease-out infinite;
        }

        .success-kicker {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin: 4px 0 5px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 0.76rem;
          font-weight: 700;
          text-transform: uppercase;
        }

        .redeem-success-card h2 {
          margin: 0;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(1.42rem, 7vw, 1.9rem);
          line-height: 1.02;
          text-transform: uppercase;
        }

        .success-copy {
          margin: 8px auto 12px;
          max-width: 285px;
          color: #fff5e4;
          font-size: 0.86rem;
          line-height: 1.28;
        }

        .success-copy strong {
          color: var(--gold-soft);
        }

        .success-prize {
          display: grid;
          grid-template-columns: 76px 1fr;
          gap: 10px;
          align-items: center;
          margin: 0 0 10px;
          padding: 8px;
          border: 1px solid rgba(155, 94, 12, 0.82);
          border-radius: 8px;
          background: rgba(0, 0, 0, 0.38);
          text-align: left;
        }

        .success-prize img {
          width: 76px;
          height: 64px;
          object-fit: contain;
          border-radius: 7px;
          background: radial-gradient(circle, rgba(246, 198, 55, 0.16), rgba(0, 0, 0, 0.45));
        }

        .success-prize-empty {
          width: 76px;
          height: 64px;
          display: grid;
          place-items: center;
          color: var(--gold);
          border-radius: 7px;
          background: radial-gradient(circle, rgba(246, 198, 55, 0.16), rgba(0, 0, 0, 0.45));
        }

        .success-prize strong {
          display: block;
          color: #fff7e8;
          font-size: 0.86rem;
          line-height: 1.15;
        }

        .success-prize span {
          display: block;
          margin-top: 4px;
          color: var(--gold);
          font-size: 0.76rem;
        }

        .success-code {
          display: grid;
          grid-template-columns: 24px 1fr;
          align-items: center;
          gap: 3px 8px;
          margin: 0 0 10px;
          padding: 10px 12px;
          color: var(--gold);
          border: 1px solid rgba(142, 73, 255, 0.72);
          border-radius: 8px;
          background: rgba(43, 12, 78, 0.34);
          text-align: left;
        }

        .success-code span {
          color: #fff0da;
          font-size: 0.7rem;
          text-transform: uppercase;
        }

        .success-status {
          grid-column: 2;
          color: #90ee90;
          font-size: 0.7rem;
        }

        .success-code strong {
          grid-column: 2;
          color: #fff;
          font-family: 'Cinzel', serif;
          font-size: 1.04rem;
          letter-spacing: 0;
        }

        .success-note {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          margin: 0 2px 14px;
          color: #ffe9a6;
          font-size: 0.76rem;
          line-height: 1.25;
        }

        .success-actions {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }

        .success-actions button {
          min-height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          padding: 0 10px;
          border-radius: 10px;
          font-family: 'Cinzel', serif;
          font-size: 0.72rem;
          font-weight: 800;
          text-transform: uppercase;
          cursor: pointer;
        }

        .success-actions button:first-child {
          color: var(--gold);
          border: 1px solid rgba(246, 198, 55, 0.62);
          background: rgba(0, 0, 0, 0.3);
        }

        .success-actions button:last-child {
          color: #130d04;
          border: 1px solid #ffe799;
          background: linear-gradient(180deg, #ffe07a 0%, #d9981b 58%, #aa6405 100%);
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
        }

        .success-burst {
          position: absolute;
          width: min(86vw, 380px);
          height: min(86vw, 380px);
          pointer-events: none;
        }

        .success-burst span {
          position: absolute;
          left: 50%;
          top: 50%;
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: var(--gold);
          box-shadow: 0 0 18px rgba(246, 198, 55, 0.85);
          animation: successSpark 900ms ease-out both;
        }

        .success-burst span:nth-child(1) { --x: -142px; --y: -84px; animation-delay: 80ms; }
        .success-burst span:nth-child(2) { --x: 132px; --y: -64px; animation-delay: 150ms; }
        .success-burst span:nth-child(3) { --x: -108px; --y: 116px; animation-delay: 230ms; }
        .success-burst span:nth-child(4) { --x: 118px; --y: 120px; animation-delay: 300ms; }
        .success-burst span:nth-child(5) { --x: 0px; --y: -156px; animation-delay: 180ms; }
        .success-burst span:nth-child(6) { --x: 0px; --y: 154px; animation-delay: 260ms; }

        .redeem-block:nth-child(2) .prize-visual::before,
        .redeem-block:nth-child(3) .prize-visual::before {
          opacity: 0.25;
        }

        .redeem-block:nth-child(2) .prize-visual img,
        .redeem-block:nth-child(3) .prize-visual img {
          height: 180px;
          object-fit: cover;
          padding: 0;
        }

        @media (max-width: 370px) {
          .redeem-shell {
            width: min(100% - 8px, 430px);
          }

          .redeem-block {
            padding-inline: 5px;
          }

          .prize-panel {
            grid-template-columns: 1fr;
          }

          .prize-visual {
            min-height: 218px;
          }
        }

        @media (min-width: 900px) {
          .redeem-page {
            background:
              radial-gradient(circle at 16% 10%, rgba(146, 83, 8, 0.18), transparent 27rem),
              radial-gradient(circle at 84% 20%, rgba(92, 36, 145, 0.16), transparent 25rem),
              radial-gradient(circle at 50% 86%, rgba(246, 198, 55, 0.08), transparent 29rem),
              #020302;
          }

          .redeem-shell {
            width: min(1180px, calc(100% - 64px));
            padding: 20px 0 28px;
          }

          .redeem-header {
            min-height: 94px;
            grid-template-columns: 48px 1fr 48px;
            align-items: center;
          }

          .back-button {
            width: 40px;
            height: 40px;
          }

          .redeem-header img {
            width: clamp(240px, 20vw, 320px);
          }

          .title-area {
            margin: 0 auto 22px;
            max-width: 720px;
          }

          .title-area h1 {
            font-size: clamp(2.2rem, 3.2vw, 3.4rem);
          }

          .title-area p {
            font-size: 1.02rem;
          }

          .redeem-list {
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
            align-items: stretch;
          }

          .redeem-block,
          .redeem-block + .redeem-block {
            margin-top: 0;
            padding: 0;
            border-bottom: 0;
          }

          .prize-panel {
            height: 100%;
            grid-template-columns: 1fr;
            gap: 12px;
            padding: 12px;
            border-radius: 14px;
          }

          .prize-visual {
            min-height: 300px;
          }

          .prize-visual img,
          .redeem-block:nth-child(2) .prize-visual img,
          .redeem-block:nth-child(3) .prize-visual img {
            height: 226px;
            object-fit: contain;
            padding: 12px;
          }

          .visual-caption h2 {
            font-size: 1.08rem;
          }

          .visual-caption p {
            font-size: 0.92rem;
          }

          .prize-info {
            gap: 10px;
          }

          .points-line {
            grid-template-columns: 34px auto 1fr;
          }

          .points-line strong {
            font-size: 1.9rem;
          }

          .info-box {
            min-height: 70px;
            padding: 11px;
          }

          .info-box h3 {
            font-size: 0.84rem;
          }

          .info-box p {
            font-size: 0.78rem;
          }

          .confirm-button {
            min-height: 48px;
            margin-top: auto;
          }
        }

        @keyframes successFade {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes successRise {
          from {
            opacity: 0;
            transform: translateY(18px) scale(0.96);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        @keyframes successHalo {
          to { transform: rotate(1turn); }
        }

        @keyframes successPulse {
          from {
            opacity: 0.82;
            transform: scale(0.86);
          }
          to {
            opacity: 0;
            transform: scale(1.32);
          }
        }

        @keyframes successSpark {
          from {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.4);
          }
          35% {
            opacity: 1;
          }
          to {
            opacity: 0;
            transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y))) scale(1.1);
          }
        }

        .redeem-success-backdrop {
          padding: 10px;
          background: #020201;
          backdrop-filter: none;
        }

        .redeem-success-card {
          width: min(100%, 420px);
          max-height: calc(100svh - 20px);
          overflow-y: auto;
          padding: 12px 14px 14px;
          border: 1px solid rgba(246, 198, 55, 0.88);
          border-radius: 16px;
          background:
            linear-gradient(180deg, rgba(0, 0, 0, 0.42), rgba(0, 0, 0, 0.98) 24rem),
            #020201;
          box-shadow:
            0 0 0 1px rgba(0, 0, 0, 0.86),
            0 0 42px rgba(246, 198, 55, 0.17),
            inset 0 0 38px rgba(246, 198, 55, 0.05);
        }

        .redeem-success-card::before {
          inset: 0;
          background:
            linear-gradient(180deg, rgba(0, 0, 0, 0.24), rgba(0, 0, 0, 0.72) 47%, rgba(0, 0, 0, 0.98)),
            url('/images/background-jornada-real.jpeg') center top / cover no-repeat;
          opacity: 0.18;
          animation: none;
        }

        .success-burst {
          opacity: 0.42;
        }

        .success-hero {
          position: relative;
          min-height: 164px;
          display: grid;
          grid-template-columns: 1fr;
          align-items: start;
          justify-items: center;
          padding: 6px 8px 0;
        }

        .success-brand {
          display: grid;
          place-items: center;
          width: 86px;
          grid-column: 1;
          grid-row: 1;
          justify-self: center;
          align-self: start;
          margin: 24px 0 0;
        }

        .success-brand img {
          width: 68px;
          height: 86px;
          object-fit: contain;
          filter:
            drop-shadow(0 0 9px rgba(255, 221, 104, 0.92))
            drop-shadow(0 0 20px rgba(246, 198, 55, 0.62))
            drop-shadow(0 5px 8px rgba(0, 0, 0, 0.72));
        }

        .success-seal {
          grid-column: 1;
          grid-row: 1;
          width: 76px;
          height: 76px;
          margin: 86px auto 0;
          color: var(--gold);
          border: 4px solid rgba(255, 225, 128, 0.96);
          background:
            radial-gradient(circle, rgba(246, 198, 55, 0.16), rgba(0, 0, 0, 0.76) 66%),
            #060503;
          box-shadow:
            0 0 0 3px rgba(246, 198, 55, 0.12),
            0 0 22px rgba(246, 198, 55, 0.72),
            inset 0 0 18px rgba(246, 198, 55, 0.2);
        }

        .success-seal i {
          inset: -10px;
          border-color: rgba(246, 198, 55, 0.28);
        }

        .success-seal::before {
          content: '';
          position: absolute;
          inset: 13px;
          border: 2.5px solid rgba(246, 198, 55, 0.95);
          border-radius: 50%;
          box-shadow: inset 0 0 14px rgba(246, 198, 55, 0.16);
        }

        .success-seal > svg {
          position: relative;
          z-index: 1;
          width: 31px;
          height: 31px;
        }

        .success-kicker {
          margin: 8px 0 5px;
          color: var(--gold);
          font-size: 0.82rem;
          letter-spacing: 0;
        }

        .redeem-success-card h2 {
          max-width: 320px;
          margin: 0 auto 2px;
          color: #fffaf0;
          font-size: clamp(1.45rem, 7vw, 1.9rem);
          line-height: 1.04;
          text-transform: none;
          text-shadow: 0 0 18px rgba(246, 198, 55, 0.36);
        }

        .redeem-success-card h2 span {
          color: var(--gold);
        }

        .success-copy {
          position: relative;
          margin: 15px auto 14px;
          max-width: 292px;
          color: #fff7ed;
          font-family: Arial, sans-serif;
          font-size: 1rem;
          line-height: 1.32;
        }

        .success-copy::before {
          content: '';
          position: absolute;
          left: 50%;
          top: -12px;
          width: 170px;
          height: 1px;
          transform: translateX(-50%);
          background: linear-gradient(90deg, transparent, rgba(246, 198, 55, 0.8), transparent);
        }

        .success-copy::after {
          content: '';
          position: absolute;
          left: 50%;
          top: -16px;
          width: 10px;
          height: 10px;
          transform: translateX(-50%) rotate(45deg);
          background: var(--gold);
          box-shadow: 0 0 16px rgba(246, 198, 55, 0.8);
        }

        .success-copy strong {
          color: var(--gold);
        }

        .success-prize {
          grid-template-columns: 78px minmax(0, 1fr);
          gap: 12px;
          width: min(100%, 324px);
          margin: 0 auto 10px;
          padding: 9px 12px;
          border: 1px solid rgba(246, 198, 55, 0.68);
          border-radius: 9px;
          background: rgba(7, 5, 2, 0.92);
        }

        .success-prize > div:last-child {
          min-width: 0;
        }

        .success-prize img,
        .success-prize-empty {
          width: 70px;
          height: 70px;
          object-fit: contain;
          background: radial-gradient(circle, rgba(246, 198, 55, 0.18), rgba(0, 0, 0, 0.35));
        }

        .success-prize small {
          display: block;
          margin-bottom: 3px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 0.68rem;
          font-weight: 800;
          text-transform: uppercase;
        }

        .success-prize strong {
          color: #fffaf2;
          font-family: 'Playfair Display', serif;
          font-size: 1.08rem;
          line-height: 1.1;
        }

        .success-prize span {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #fff2dc;
          font-size: 0.76rem;
        }

        .success-prize span svg {
          color: var(--gold);
        }

        .success-code {
          display: block;
          width: min(100%, 340px);
          margin: 0 auto 11px;
          padding: 12px 14px 11px;
          border: 1px solid rgba(246, 198, 55, 0.72);
          border-radius: 11px;
          background: rgba(4, 3, 2, 0.94);
          text-align: left;
        }

        .success-code-label {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 9px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 0.78rem;
          font-weight: 800;
          text-transform: uppercase;
        }

        .success-code-box {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 36px;
          align-items: center;
          gap: 8px;
          width: 100%;
          min-height: 52px;
          padding: 0 8px 0 10px;
          overflow: hidden;
          border: 1px dashed rgba(255, 232, 156, 0.74);
          border-radius: 8px;
          background: rgba(0, 0, 0, 0.42);
        }

        .success-code-box strong {
          grid-column: 1;
          grid-row: 1;
          color: #fffaf2;
          text-shadow: 0 0 12px rgba(246, 198, 55, 0.22);
          font-family: 'Cinzel', serif;
          min-width: 0;
          max-width: 100%;
          overflow: hidden;
          font-size: clamp(1.28rem, 6.2vw, 1.72rem);
          line-height: 1;
          letter-spacing: 0;
          text-align: center;
          white-space: nowrap;
        }

        .success-code-box button {
          grid-column: 2;
          grid-row: 1;
          width: 32px;
          height: 32px;
          display: grid;
          place-items: center;
          align-self: center;
          justify-self: end;
          flex: 0 0 auto;
          color: #fff2d0;
          border: 1px solid rgba(246, 198, 55, 0.58);
          border-radius: 8px;
          background: rgba(115, 75, 10, 0.78);
          cursor: pointer;
        }

        .success-code p {
          display: grid;
          grid-template-columns: 24px 1fr;
          gap: 9px;
          align-items: start;
          margin: 12px 6px 11px;
          color: #fff5e6;
          font-family: Arial, sans-serif;
          font-size: 0.78rem;
          line-height: 1.26;
        }

        .success-code p svg {
          color: var(--gold);
        }

        .success-code aside {
          display: grid;
          grid-template-columns: 24px 1fr;
          gap: 8px;
          align-items: start;
          padding: 9px 10px;
          color: #fff0d0;
          border: 1px solid rgba(246, 198, 55, 0.52);
          border-radius: 8px;
          background: rgba(0, 0, 0, 0.52);
          font-family: Arial, sans-serif;
          font-size: 0.66rem;
          line-height: 1.28;
        }

        .success-code aside svg {
          color: var(--gold);
        }

        .success-actions {
          width: min(100%, 340px);
          margin: 0 auto 12px;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1.08fr);
          gap: 9px;
        }

        .success-actions button {
          min-height: 48px;
          border-radius: 7px;
          font-size: 0.62rem;
          line-height: 1.1;
          padding: 0 8px;
          white-space: normal;
        }

        .success-footer {
          display: grid;
          grid-template-columns: 34px 1fr;
          gap: 8px;
          align-items: center;
          width: min(100%, 330px);
          margin: 0 auto;
          color: #fff6e7;
          text-align: left;
        }

        .success-footer svg {
          color: var(--gold);
        }

        .success-footer p {
          margin: 0;
          font-family: Arial, sans-serif;
          font-size: 0.68rem;
          line-height: 1.22;
        }

        .success-footer strong {
          display: block;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 0.78rem;
        }
      `}</style>
    </main>
  )
}
