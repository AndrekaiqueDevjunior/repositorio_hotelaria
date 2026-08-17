'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
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
import '../jornada-real.css'
import Reveal from '@/components/jornada/Reveal'
import LuzPonteiro from '@/components/jornada/LuzPonteiro'
import BotaoSom from '@/components/jornada/BotaoSom'
import JornadaNav from '@/components/jornada/JornadaNav'
import { Fleurao } from '@/components/jornada/Ornamentos'
import { api } from '@/lib/api'

const getApiErrorMessage = (error, fallback) => {
  const status = error.response?.status
  const data = error.response?.data

  // Erro 5xx: o corpo costuma ser texto cru do servidor ("Internal Server
  // Error"), não uma mensagem pensada para o hóspede — nesses casos sempre
  // usa o texto de fallback em vez de expor o erro interno.
  if (status && status >= 500) return fallback

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
  const [retryTick, setRetryTick] = useState(0)

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
          setLoadError(getApiErrorMessage(error, 'Seu cupom está indisponível no momento. Tente novamente em instantes.'))
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
  }, [cpf, router, retryTick])

  const coupon = data?.coupon || null
  const usages = Array.isArray(data?.usages) ? data.usages : []
  const isActive = Boolean(coupon?.active)
  const statusEstado = coupon?.status || (isActive ? 'active' : 'inactive')
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
    <main className="jr jr-cupom-pagina">
      <LuzPonteiro densidade={2} />

      <header className="jr-barra">
        <div className="jr-shell jr-barra__interno">
          <button
            type="button"
            className="jr-barra__voltar"
            aria-label="Voltar"
            onClick={() => router.push(withCpfParam('/consultar-pontos', cpf))}
          >
            <ArrowLeft size={18} strokeWidth={1.9} />
          </button>

          <Link href="/" className="jr-barra__marca" aria-label="Jornada Real — Hotel Real Cabo Frio">
            <img src="/images/logo-jornada-real.png" alt="Jornada Real" />
          </Link>

          <div className="jr-barra__acoes">
            <BotaoSom />
          </div>
        </div>
      </header>

      <section className="jr-cena jr-cupom" aria-label="Meu Cupom">
        <img
          src="/images/jornada/marcas/brasao-hr.png"
          alt=""
          aria-hidden="true"
          className="jr-cupom__marca-agua"
        />

        <div className="jr-shell">
          <Reveal className="jr-cena__cabeca jr-cupom__cabeca">
            <h1 className="jr-cena__titulo jr-ouro-metal">
              <Crown size={20} strokeWidth={1.7} aria-hidden="true" style={{ verticalAlign: '-0.15em', marginRight: 10 }} />
              Meu Cupom
              <Crown size={20} strokeWidth={1.7} aria-hidden="true" style={{ verticalAlign: '-0.15em', marginLeft: 10 }} />
            </h1>
            <Fleurao largura={260} />
            <p className="jr-lede">Convite Real: compartilhe com amigos e ganhem benefícios juntos.</p>
          </Reveal>

          {isLoading && <p className="jr-lede jr-pontos__estado">Carregando seu cupom Convite Real...</p>}

          {loadError && !isLoading && (
            <div className="jr-cupom__aviso-topo">
              <p className="jr-texto">{loadError}</p>
              <button type="button" className="jr-btn jr-btn--contorno" onClick={() => setRetryTick((tick) => tick + 1)}>
                Tentar novamente
              </button>
            </div>
          )}

          {coupon && !isLoading && (
            <div className="jr-cupom__grade">
              <Reveal delay={80} className="jr-painel">
                <div className="jr-cupom__topo">
                  <img
                    src="/images/jornada/objetos/envelope.png"
                    alt="Convite da Jornada Real, envelope preto com lacre dourado HR"
                    className="jr-cupom__envelope jr-objeto"
                    loading="lazy"
                  />

                  <div>
                    <p className="jr-cupom__rotulo">
                      <Ticket size={18} strokeWidth={1.9} aria-hidden="true" />
                      Seu código exclusivo
                    </p>

                    <div className="jr-cupom__caixa">
                      <strong>{coupon.code}</strong>
                      <button
                        type="button"
                        aria-label="Copiar código"
                        onClick={() => copyToClipboard(coupon.code, 'code')}
                      >
                        {copied === 'code' ? <Check size={17} strokeWidth={2} /> : <Copy size={16} strokeWidth={1.8} />}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="jr-cupom__status">
                  <span className="jr-chip" data-estado={statusEstado}>{statusLabel}</span>
                  <span className="jr-chip">{usageSummary}</span>
                  {expiresAt && isActive && <span className="jr-chip">válido até {expiresAt}</span>}
                </div>

                {isActive ? (
                  <div className="jr-cupom__acoes">
                    <button type="button" className="jr-btn" onClick={shareOnWhatsApp}>
                      <MessageCircle size={18} strokeWidth={1.9} aria-hidden="true" />
                      <span>Compartilhar no WhatsApp</span>
                    </button>

                    <button
                      type="button"
                      className="jr-btn jr-btn--contorno"
                      onClick={() => copyToClipboard(coupon.link, 'link')}
                      disabled={!coupon.link}
                    >
                      {copied === 'link' ? <Check size={16} strokeWidth={2} /> : <Link2 size={16} strokeWidth={1.9} />}
                      <span>{copied === 'link' ? 'Link copiado!' : 'Copiar link do convite'}</span>
                    </button>
                  </div>
                ) : (
                  <div className="jr-cupom__renovar">
                    <p>
                      Este cupom não pode mais ser usado.
                      <br />
                      Gere um novo para continuar convidando amigos.
                    </p>
                    <button
                      type="button"
                      className="jr-btn"
                      onClick={generateNewCoupon}
                      disabled={isGenerating}
                    >
                      <RefreshCw size={16} strokeWidth={2} aria-hidden="true" />
                      <span>{isGenerating ? 'Gerando...' : 'Gerar novo cupom'}</span>
                    </button>
                  </div>
                )}

                <div className="jr-cupom__aviso">
                  <Info size={18} strokeWidth={2} aria-hidden="true" />
                  <p>
                    Seu amigo ganha <strong>{Number(coupon.discount_percentage || 0)}% de desconto</strong> na
                    reserva e você ganha <strong>{coupon.points_per_referral} pontos</strong> quando ele conclui a
                    estadia.
                  </p>
                </div>
              </Reveal>

              <Reveal delay={140} className="jr-painel">
                <h2 className="jr-painel__titulo">
                  <Users size={18} strokeWidth={1.9} aria-hidden="true" />
                  Amigos que usaram
                </h2>

                <div className="jr-cupom__ganho">
                  <Sparkles size={17} strokeWidth={1.8} aria-hidden="true" />
                  <span>
                    Pontos ganhos com convites: <strong>{data?.referral_points_earned ?? 0}</strong>
                  </span>
                </div>

                {usages.length ? (
                  <ul className="jr-cupom__lista">
                    {usages.map((usage, index) => (
                      <li key={`${usage.friend_name}-${usage.used_at}-${index}`} className="jr-cupom__item">
                        <Gift size={16} strokeWidth={1.8} aria-hidden="true" />
                        <span className="jr-cupom__item-nome">{usage.friend_name}</span>
                        <span className="jr-cupom__item-data">{formatDate(usage.used_at) || '—'}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="jr-cupom__vazio">
                    Ninguém usou seu cupom ainda. Compartilhe com seus amigos e comece a ganhar pontos! 🔥
                  </p>
                )}
              </Reveal>
            </div>
          )}
        </div>
      </section>

      <JornadaNav atual="/meu-cupom" cpf={cpf} />
    </main>
  )
}
