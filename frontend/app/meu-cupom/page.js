'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  ArrowLeft,
  Check,
  Copy,
  Crown,
  Gift,
  Info,
  Link2,
  MessageCircle,
  RefreshCw,
  Sparkles,
  Ticket,
  Users,
} from 'lucide-react'
import GoldParticles from '@/components/GoldParticles'
import { api } from '@/lib/api'

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

const formatDate = (value) => {
  if (!value) return null

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null

  return date.toLocaleDateString('pt-BR')
}

const STATUS_LABELS = {
  active: 'Cupom ativo',
  expired: 'Cupom expirado',
  cancelled: 'Cupom cancelado',
  max_usage_reached: 'Cupom esgotado',
  used: 'Cupom esgotado',
}

export default function MeuCupom() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const cpf = (searchParams.get('cpf') || searchParams.get('documento') || '').replace(/\D/g, '')

  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [copied, setCopied] = useState(null) // 'code' | 'link'

  useEffect(() => {
    if (!cpf) {
      router.push('/consultar')
      return
    }

    let isMounted = true

    const loadCoupon = async () => {
      setIsLoading(true)
      setLoadError(null)

      try {
        const response = await api.get('/jornada/meu-cupom', { params: { cpf }, silentError: true })

        if (isMounted) {
          setData(response.data)
        }
      } catch (error) {
        if (isMounted) {
          setLoadError(getApiErrorMessage(error, 'Não foi possível carregar seu cupom.'))
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadCoupon()

    return () => {
      isMounted = false
    }
  }, [cpf, router])

  const coupon = data?.coupon || null
  const usages = Array.isArray(data?.usages) ? data.usages : []
  const isActive = Boolean(coupon?.active)
  const statusLabel = STATUS_LABELS[coupon?.status] || 'Cupom indisponível'
  const expiresAt = formatDate(coupon?.expires_at)
  const usageSummary = coupon?.max_uses
    ? `${coupon.current_uses ?? 0}/${coupon.max_uses} usos`
    : `${coupon?.current_uses ?? 0} usos`

  const copyToClipboard = async (value, key) => {
    try {
      await navigator.clipboard?.writeText(value)
      setCopied(key)
      setTimeout(() => setCopied(null), 2200)
    } catch (error) {
      // clipboard indisponivel (http antigo/permissao) -- sem feedback, sem quebrar
    }
  }

  const shareOnWhatsApp = () => {
    if (!coupon) return

    const url =
      coupon.whatsapp_share_url ||
      `https://wa.me/?text=${encodeURIComponent(coupon.whatsapp_message || coupon.link || coupon.code)}`

    window.open(url, '_blank', 'noopener,noreferrer')
  }

  const generateNewCoupon = async () => {
    if (isGenerating) return

    setIsGenerating(true)
    setLoadError(null)

    try {
      const response = await api.post('/jornada/meu-cupom/gerar', { cpf }, { silentError: true })
      setData(response.data)
    } catch (error) {
      setLoadError(getApiErrorMessage(error, 'Não foi possível gerar um novo cupom.'))
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <main className="coupon-page">
      <GoldParticles />

      <section className="coupon-shell">
        <header className="coupon-header">
          <button
            type="button"
            className="back-button"
            aria-label="Voltar"
            onClick={() => router.push(withCpfParam('/consultar-pontos', cpf))}
          >
            <ArrowLeft size={22} strokeWidth={1.9} />
          </button>

          <img src="/images/logo-jornada-real.png" alt="Hotel Real Cabo Frio" />

          <span aria-hidden="true" />
        </header>

        <div className="title-area">
          <h1>
            <Crown size={20} />
            Meu Cupom
            <Crown size={20} />
          </h1>
          <p>Convite Real: compartilhe com amigos e ganhem benefícios juntos.</p>
        </div>

        {isLoading && (
          <section className="coupon-card notice-card">
            <p>Carregando seu cupom Convite Real...</p>
          </section>
        )}

        {loadError && !isLoading && (
          <section className="coupon-card error-card" role="alert">
            <p>{loadError}</p>
          </section>
        )}

        {coupon && !isLoading && (
          <>
            <section className="coupon-card">
              <div className="coupon-code-label">
                <Ticket size={19} strokeWidth={1.9} />
                <span>Seu código exclusivo</span>
              </div>

              <div className="coupon-code-box">
                <strong>{coupon.code}</strong>
                <button
                  type="button"
                  aria-label="Copiar código"
                  onClick={() => copyToClipboard(coupon.code, 'code')}
                >
                  {copied === 'code' ? <Check size={18} strokeWidth={2} /> : <Copy size={18} strokeWidth={1.8} />}
                </button>
              </div>

              <div className="coupon-status-row">
                <span className={`status-chip ${isActive ? 'status-active' : 'status-inactive'}`}>
                  {statusLabel}
                </span>
                <span className="usage-chip">{usageSummary}</span>
                {expiresAt && isActive && <span className="expires-chip">válido até {expiresAt}</span>}
              </div>

              {isActive ? (
                <>
                  <button type="button" className="whatsapp-button" onClick={shareOnWhatsApp}>
                    <MessageCircle size={19} strokeWidth={1.9} />
                    Compartilhar no WhatsApp
                  </button>

                  <button
                    type="button"
                    className="copy-link-button"
                    onClick={() => copyToClipboard(coupon.link, 'link')}
                    disabled={!coupon.link}
                  >
                    {copied === 'link' ? <Check size={17} strokeWidth={2} /> : <Link2 size={17} strokeWidth={1.9} />}
                    {copied === 'link' ? 'Link copiado!' : 'Copiar link do convite'}
                  </button>
                </>
              ) : (
                <div className="renew-area">
                  <p>
                    Este cupom não pode mais ser usado.
                    <br />
                    Gere um novo para continuar convidando amigos.
                  </p>
                  <button
                    type="button"
                    className="renew-button"
                    onClick={generateNewCoupon}
                    disabled={isGenerating}
                  >
                    <RefreshCw size={17} strokeWidth={2} />
                    {isGenerating ? 'Gerando...' : 'Gerar novo cupom'}
                  </button>
                </div>
              )}

              <aside className="benefit-note">
                <Info size={18} strokeWidth={2} />
                <span>
                  Seu amigo ganha <strong>{Number(coupon.discount_percentage || 0)}% de desconto</strong> na
                  reserva e você ganha <strong>{coupon.points_per_referral} pontos</strong> quando ele conclui a
                  estadia.
                </span>
              </aside>
            </section>

            <section className="coupon-card history-card">
              <h2>
                <Users size={18} strokeWidth={1.9} />
                Amigos que usaram
              </h2>

              <div className="points-earned">
                <Sparkles size={18} strokeWidth={1.8} />
                <span>
                  Pontos ganhos com convites: <strong>{data?.referral_points_earned ?? 0}</strong>
                </span>
              </div>

              {usages.length ? (
                <ul className="usage-list">
                  {usages.map((usage, index) => (
                    <li key={`${usage.friend_name}-${usage.used_at}-${index}`}>
                      <Gift size={16} strokeWidth={1.8} />
                      <span className="usage-name">{usage.friend_name}</span>
                      <span className="usage-date">{formatDate(usage.used_at) || '—'}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty-history">
                  Ninguém usou seu cupom ainda. Compartilhe com seus amigos e comece a ganhar pontos! 🔥
                </p>
              )}
            </section>
          </>
        )}
      </section>

      <style jsx global>{`
        .coupon-page {
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

        body:has(.coupon-page) button[aria-label^=Abrir][aria-label*=configura],
        body:has(.coupon-page) nextjs-portal {
          display: none;
        }

        .coupon-shell {
          position: relative;
          z-index: 30;
          width: min(100% - 14px, 430px);
          margin: 0 auto;
          padding: 6px 0 24px;
        }

        .coupon-header {
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

        .coupon-header img {
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
          margin: 8px 0 12px;
          color: #fff6e8;
          font-size: clamp(0.72rem, 3vw, 0.86rem);
          line-height: 1.25;
        }

        .coupon-card {
          margin-top: 12px;
          padding: 16px 14px;
          border: 1.3px solid var(--line);
          border-radius: 12px;
          background:
            radial-gradient(circle at 24% 12%, rgba(246, 198, 55, 0.1), transparent 36%),
            rgba(5, 5, 4, 0.86);
          box-shadow:
            inset 0 0 22px rgba(246, 198, 55, 0.05),
            0 0 18px rgba(246, 198, 55, 0.08);
        }

        .notice-card p,
        .error-card p {
          margin: 0;
          font-family: Arial, sans-serif;
          font-size: 0.85rem;
          text-align: center;
        }

        .error-card {
          border-color: rgba(255, 106, 106, 0.6);
        }

        .coupon-code-label {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 10px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 0.78rem;
          font-weight: 800;
          text-transform: uppercase;
        }

        .coupon-code-box {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 36px;
          align-items: center;
          gap: 8px;
          min-height: 54px;
          padding: 0 8px 0 10px;
          border: 1px dashed rgba(255, 232, 156, 0.74);
          border-radius: 8px;
          background: rgba(0, 0, 0, 0.42);
        }

        .coupon-code-box strong {
          min-width: 0;
          overflow: hidden;
          color: #fffaf2;
          font-family: 'Cinzel', serif;
          font-size: clamp(1.1rem, 5.4vw, 1.5rem);
          line-height: 1;
          text-align: center;
          text-shadow: 0 0 12px rgba(246, 198, 55, 0.22);
          white-space: nowrap;
        }

        .coupon-code-box button {
          width: 32px;
          height: 32px;
          display: grid;
          place-items: center;
          color: #fff2d0;
          border: 1px solid rgba(246, 198, 55, 0.58);
          border-radius: 8px;
          background: rgba(115, 75, 10, 0.78);
          cursor: pointer;
        }

        .coupon-status-row {
          display: flex;
          flex-wrap: wrap;
          gap: 7px;
          margin: 12px 0;
        }

        .status-chip,
        .usage-chip,
        .expires-chip {
          padding: 4px 10px;
          border-radius: 999px;
          font-family: Arial, sans-serif;
          font-size: 0.68rem;
          font-weight: 700;
        }

        .status-active {
          color: #9dffb0;
          border: 1px solid rgba(110, 231, 138, 0.55);
          background: rgba(26, 84, 40, 0.4);
        }

        .status-inactive {
          color: #ffb3a6;
          border: 1px solid rgba(255, 120, 96, 0.55);
          background: rgba(96, 27, 16, 0.42);
        }

        .usage-chip {
          color: #ffe9ae;
          border: 1px solid rgba(246, 198, 55, 0.5);
          background: rgba(94, 62, 8, 0.36);
        }

        .expires-chip {
          color: #fff0d0;
          border: 1px solid rgba(246, 198, 55, 0.34);
          background: rgba(0, 0, 0, 0.4);
        }

        .whatsapp-button {
          width: 100%;
          min-height: 46px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 9px;
          color: #04170a;
          border: 1px solid #a8ffc4;
          border-radius: 10px;
          background: linear-gradient(180deg, #6fe58c 0%, #25b34a 62%, #14813a 100%);
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42), 0 10px 18px rgba(0, 0, 0, 0.34);
          font-family: 'Cinzel', serif;
          font-size: 0.82rem;
          font-weight: 800;
          text-transform: uppercase;
          cursor: pointer;
        }

        .copy-link-button {
          width: 100%;
          min-height: 42px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-top: 8px;
          color: var(--gold);
          border: 1px solid rgba(246, 198, 55, 0.62);
          border-radius: 10px;
          background: rgba(0, 0, 0, 0.3);
          font-family: 'Cinzel', serif;
          font-size: 0.74rem;
          font-weight: 800;
          text-transform: uppercase;
          cursor: pointer;
        }

        .copy-link-button:disabled {
          opacity: 0.6;
          cursor: default;
        }

        .renew-area {
          text-align: center;
        }

        .renew-area p {
          margin: 0 0 10px;
          color: #ffd9c8;
          font-family: Arial, sans-serif;
          font-size: 0.8rem;
          line-height: 1.35;
        }

        .renew-button {
          width: 100%;
          min-height: 46px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 9px;
          color: #130d04;
          border: 1px solid #ffe799;
          border-radius: 10px;
          background: linear-gradient(180deg, #ffe07a 0%, #d9981b 58%, #aa6405 100%);
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
          font-family: 'Cinzel', serif;
          font-size: 0.82rem;
          font-weight: 800;
          text-transform: uppercase;
          cursor: pointer;
        }

        .renew-button:disabled {
          cursor: wait;
          opacity: 0.75;
        }

        .benefit-note {
          display: grid;
          grid-template-columns: 24px 1fr;
          gap: 8px;
          align-items: start;
          margin-top: 12px;
          padding: 9px 10px;
          color: #fff0d0;
          border: 1px solid rgba(246, 198, 55, 0.4);
          border-radius: 8px;
          background: rgba(0, 0, 0, 0.4);
          font-family: Arial, sans-serif;
          font-size: 0.72rem;
          line-height: 1.32;
        }

        .benefit-note svg {
          color: var(--gold);
        }

        .benefit-note strong {
          color: var(--gold-soft);
        }

        .history-card h2 {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0 0 10px;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: 0.92rem;
          text-transform: uppercase;
        }

        .points-earned {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
          padding: 9px 10px;
          color: #ffe9ae;
          border: 1px solid rgba(246, 198, 55, 0.44);
          border-radius: 8px;
          background: rgba(94, 62, 8, 0.28);
          font-family: Arial, sans-serif;
          font-size: 0.78rem;
        }

        .points-earned strong {
          color: var(--gold-soft);
          font-size: 0.92rem;
        }

        .usage-list {
          display: grid;
          gap: 8px;
          margin: 0;
          padding: 0;
          list-style: none;
        }

        .usage-list li {
          display: grid;
          grid-template-columns: 20px 1fr auto;
          align-items: center;
          gap: 8px;
          padding: 8px 10px;
          color: #fff5df;
          border: 1px solid rgba(157, 91, 8, 0.5);
          border-radius: 8px;
          background: rgba(9, 8, 6, 0.72);
          font-family: Arial, sans-serif;
          font-size: 0.8rem;
        }

        .usage-list svg {
          color: var(--gold);
        }

        .usage-name {
          font-weight: 700;
        }

        .usage-date {
          color: #ffe9ae;
          font-size: 0.72rem;
        }

        .empty-history {
          margin: 0;
          color: #fff0d0;
          font-family: Arial, sans-serif;
          font-size: 0.78rem;
          line-height: 1.35;
          text-align: center;
        }

        @media (min-width: 900px) {
          .coupon-shell {
            width: min(560px, calc(100% - 64px));
            padding: 20px 0 32px;
          }

          .coupon-header {
            min-height: 94px;
            grid-template-columns: 48px 1fr 48px;
            align-items: center;
          }

          .back-button {
            width: 40px;
            height: 40px;
          }

          .coupon-header img {
            width: clamp(240px, 20vw, 320px);
          }

          .coupon-card {
            padding: 22px 20px;
          }
        }
      `}</style>
    </main>
  )
}
