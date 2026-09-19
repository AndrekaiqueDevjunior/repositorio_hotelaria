'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  ArrowLeft,
  ArrowRight,
  Copy,
  Crown,
  Gift,
  Info,
  LockKeyhole,
  MapPin,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Ticket,
} from 'lucide-react'
import '../jornada-real.css'
import Reveal from '@/components/jornada/Reveal'
import LuzPonteiro from '@/components/jornada/LuzPonteiro'
import BotaoSom from '@/components/jornada/BotaoSom'
import JornadaNav from '@/components/jornada/JornadaNav'
import { CantoMoldura, Fleurao } from '@/components/jornada/Ornamentos'
import { api } from '@/lib/api'

// Fallback de exibição para quando a API ainda não respondeu ou está fora
// do ar em ambientes de preview (ex.: deploy sem backend conectado) — evita
// a vitrine aparecer vazia nesses casos. Quando a API responde, ela sempre
// vence: ver normalizePrize/prizes abaixo.
const prizeDefaults = [
  {
    slug: 'tecnologia-real',
    name: 'Tecnologia Real',
    subtitle: 'iPhone 16e',
    points: 90,
    image: '/images/premios/tecnologia-real.png',
    badge: 'Mais disputado',
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
    .replace(/[̀-ͯ]/g, '')
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

const ONBOARDING_STORAGE_KEY = 'jr_resgate_onboarding_visto'

// Status do codigo de resgate vindos do backend (codigos_resgate):
// ativo | utilizado | expirado | cancelado. Um codigo "ativo" com validade
// vencida e tratado como expirado aqui, pois a marcacao no banco e lazy.
const getRedemptionCodeState = (redemption) => {
  const status = String(redemption.codigo_status || redemption.status || '').toLowerCase()

  if (['utilizado', 'used'].includes(status)) return 'used'
  if (['expirado', 'expired'].includes(status)) return 'expired'
  if (['cancelado', 'cancelled'].includes(status)) return 'cancelled'

  const expiresAt = redemption.expira_em ? new Date(redemption.expira_em) : null
  if (expiresAt && !Number.isNaN(expiresAt.getTime()) && expiresAt < new Date()) return 'expired'

  return 'active'
}

const REDEMPTION_STATE_LABELS = {
  active: 'Código ativo',
  used: 'Utilizado',
  expired: 'Código expirado',
  cancelled: 'Código cancelado',
}

const withCpfParam = (href, cpf) => {
  if (!cpf) return href

  const separator = href.includes('?') ? '&' : '?'
  return `${href}${separator}cpf=${encodeURIComponent(cpf)}`
}

// Nome, pontuação e imagem vêm de GET /premios sempre que a API responde —
// prizeDefaults entra só como aparência de reserva quando a API falha ou
// está vazia (ex.: preview sem backend conectado).
const normalizePrize = (premio) => {
  const slug = premio.slug || slugify(premio.nome)
  const defaults = prizeDefaults.find((item) => item.slug === slug) || {}
  const points = premio.preco_em_pontos ?? premio.preco_em_rp ?? defaults.points ?? 0

  return {
    ...defaults,
    id: premio.id,
    slug,
    name: premio.nome || defaults.name || 'Prêmio Real',
    subtitle: premio.descricao || defaults.subtitle || 'Experiência exclusiva Hotel Real',
    points,
    image: resolveImageUrl(premio.imagem_url || premio.imagemUrl) || defaults.image || '',
    badge: premio.badge || premio.destaque || defaults.badge || null,
    aboutTitle: defaults.aboutTitle || 'Sobre o prêmio',
    about: premio.descricao || defaults.about || 'Prêmio exclusivo da Jornada Real.',
  }
}

const onboardingPassos = [
  {
    numeral: 'I',
    Icone: Sparkles,
    titulo: 'Escolha e confirme',
    texto: 'Escolha um prêmio disponível e confirme o resgate com seus pontos acumulados.',
  },
  {
    numeral: 'II',
    Icone: Ticket,
    titulo: 'Receba seu código',
    texto: 'Um código exclusivo é gerado na hora, aparece nesta tela e também chega no seu WhatsApp.',
  },
  {
    numeral: 'III',
    Icone: MapPin,
    titulo: 'Apresente na recepção',
    texto: 'Mostre o código na recepção do Hotel Real para retirar seu prêmio. Ele é pessoal, intransferível e tem validade.',
  },
]

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
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [myRedemptions, setMyRedemptions] = useState([])
  const [renewingId, setRenewingId] = useState(null)

  const loadMyRedemptions = async () => {
    if (!cpf) return

    try {
      const response = await api.get('/jornada/meus-resgates', { params: { cpf }, silentError: true })
      const resgates = Array.isArray(response.data?.resgates) ? response.data.resgates : []
      setMyRedemptions(resgates)
    } catch (error) {
      // Historico e complementar: sem ele a tela de resgate continua funcionando
      setMyRedemptions([])
    }
  }

  useEffect(() => {
    loadMyRedemptions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cpf])

  const handleRenewCode = async (redemption) => {
    if (renewingId) return

    setRenewingId(redemption.id)
    setRedeemError(null)

    try {
      await api.post(`/jornada/resgates/${redemption.id}/renovar`, { cpf }, { silentError: true })
      await loadMyRedemptions()
    } catch (error) {
      setRedeemError(getApiErrorMessage(error, 'Erro ao renovar código.'))
    } finally {
      setRenewingId(null)
    }
  }

  useEffect(() => {
    try {
      if (!window.localStorage.getItem(ONBOARDING_STORAGE_KEY)) {
        setShowOnboarding(true)
      }
    } catch (error) {
      setShowOnboarding(true)
    }
  }, [])

  const dismissOnboarding = () => {
    setShowOnboarding(false)
    try {
      window.localStorage.setItem(ONBOARDING_STORAGE_KEY, '1')
    } catch (error) {
      // localStorage indisponivel (modo privado etc) -- sem problema, so reaparece na proxima visita
    }
  }

  useEffect(() => {
    let isMounted = true

    const loadPrizes = async () => {
      try {
        const response = await api.get('/premios', { silentError: true })
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

  const prizes = apiPrizes.length ? apiPrizes : prizeDefaults

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
      loadMyRedemptions()
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
    <main className="jr jr-resgate-pagina">
      <LuzPonteiro densidade={2} />

      {redeemError && !redeemedPrize && (
        <div className="jr-toast" role="alert">
          <p>{redeemError}</p>
          <button type="button" className="jr-btn jr-btn--pequeno" onClick={() => setRedeemError(null)}>
            Fechar
          </button>
        </div>
      )}

      {showOnboarding && !redeemedPrize && (
        <div className="jr-modal" role="dialog" aria-modal="true" aria-label="Como funciona o resgate">
          <article className="jr-modal__cartao">
            <CantoMoldura className="jr-porta__canto jr-porta__canto--se" tamanho={34} />
            <CantoMoldura className="jr-porta__canto jr-porta__canto--sd" tamanho={34} rotacao={90} />
            <CantoMoldura className="jr-porta__canto jr-porta__canto--id" tamanho={34} rotacao={180} />
            <CantoMoldura className="jr-porta__canto jr-porta__canto--ie" tamanho={34} rotacao={270} />

            <p className="jr-sobrescrito jr-modal__kicker">
              <Crown size={14} strokeWidth={1.9} aria-hidden="true" />
              Como funciona o resgate
              <Crown size={14} strokeWidth={1.9} aria-hidden="true" />
            </p>

            <ol className="jr-convite__passos jr-modal__passos">
              {onboardingPassos.map((passo) => (
                <li key={passo.numeral}>
                  <span className="jr-convite__passo-numeral">
                    <passo.Icone size={19} strokeWidth={1.8} aria-hidden="true" />
                  </span>
                  <div>
                    <h3 className="jr-convite__passo-titulo">{passo.titulo}</h3>
                    <p className="jr-miudo">{passo.texto}</p>
                  </div>
                </li>
              ))}
            </ol>

            <p className="jr-modal__nota">
              <ShieldCheck size={16} strokeWidth={1.9} aria-hidden="true" />
              O código é gerado e validado com segurança pelo hotel — não compartilhe com ninguém.
            </p>

            <button type="button" className="jr-btn jr-modal__botao" onClick={dismissOnboarding}>
              Entendi
            </button>
          </article>
        </div>
      )}

      {!redeemedPrize && (
        <>
          <header className="jr-barra">
            <div className="jr-shell jr-resgate__topo">
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
                <button
                  type="button"
                  className="jr-barra__voltar"
                  aria-label="Como funciona o resgate"
                  onClick={() => setShowOnboarding(true)}
                >
                  <Info size={17} strokeWidth={1.9} />
                </button>
                <BotaoSom />
              </div>
            </div>
          </header>

          <section className="jr-cena jr-resgate" aria-label="Resgatar prêmio">
            <div className="jr-shell">
              <Reveal className="jr-cena__cabeca">
                <h1 className="jr-cena__titulo jr-ouro-metal jr-resgate__titulo">
                  <Crown size={22} strokeWidth={1.7} aria-hidden="true" />
                  Resgatar Prêmio
                  <Crown size={22} strokeWidth={1.7} aria-hidden="true" />
                </h1>
                <Fleurao largura={260} />
                <p className="jr-lede">Escolha seu prêmio e transforme seus pontos em experiências únicas.</p>

                {/* atalho para os códigos já resgatados, que ficam no fim da página */}
                {cpf && myRedemptions.length > 0 && (
                  <button
                    type="button"
                    className="jr-atalho-resgates"
                    onClick={() =>
                      document
                        .getElementById('meus-resgates')
                        ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                    }
                  >
                    <span className="jr-atalho-resgates__texto">
                      <Ticket size={20} strokeWidth={1.8} aria-hidden="true" />
                      <span>
                        <b>
                          {myRedemptions.length === 1
                            ? 'Você tem 1 prêmio resgatado'
                            : `Você tem ${myRedemptions.length} prêmios resgatados`}
                        </b>
                        <small>Veja os códigos para apresentar na recepção</small>
                      </span>
                    </span>

                    <span className="jr-atalho-resgates__ir">
                      Ver meus resgates
                      <ArrowRight size={15} strokeWidth={2} aria-hidden="true" />
                    </span>
                  </button>
                )}
              </Reveal>

              {!isLoadingPrizes && orderedPrizes.length === 0 && (
                <p className="jr-lede jr-resgate__vazio-catalogo">
                  O catálogo está sendo preparado. Volte em breve para escolher o seu.
                </p>
              )}

              <div className="jr-resgate__lista">
                {orderedPrizes.map((prize, indice) => (
                  <Reveal as="article" key={prize.slug} delay={indice * 80} className="jr-resgate__item">
                    <figure className="jr-resgate__visual">
                      {prize.badge && <span className="jr-premio-mini__selo jr-resgate__selo">{prize.badge}</span>}
                      {prize.image ? (
                        <img src={prize.image} alt={prize.name} />
                      ) : (
                        <div className="jr-premio-mini__vazio jr-resgate__vazio">
                          <Gift size={30} strokeWidth={1.6} aria-hidden="true" />
                          <span>{isLoadingPrizes ? 'Carregando imagem do prêmio' : 'Imagem não cadastrada'}</span>
                        </div>
                      )}
                      <figcaption>
                        <h2 className="jr-resgate__nome">{prize.name}</h2>
                        <p className="jr-miudo">{prize.subtitle}</p>
                      </figcaption>
                    </figure>

                    <div className="jr-resgate__info">
                      <div className="jr-resgate__pontos">
                        <Crown size={26} strokeWidth={1.6} aria-hidden="true" />
                        <strong className="jr-ouro-metal">{prize.points}</strong>
                        <span>pontos</span>
                        {prize.badge && <small>• Mais disputado</small>}
                      </div>

                      <div className="jr-resgate__aviso">
                        <Gift size={19} strokeWidth={1.8} aria-hidden="true" />
                        <div>
                          <h3>{prize.aboutTitle}</h3>
                          <p>{prize.about}</p>
                        </div>
                      </div>

                      <div className="jr-resgate__aviso jr-resgate__aviso--alerta">
                        <Sparkles size={19} strokeWidth={1.8} aria-hidden="true" />
                        <p>Ao confirmar, seus pontos serão resgatados e não poderão ser cancelados.</p>
                      </div>

                      <button
                        type="button"
                        className="jr-btn jr-resgate__botao"
                        onClick={() => handleRedeem(prize)}
                        disabled={isRedeeming}
                      >
                        <span>{isRedeeming ? 'Processando...' : 'Confirmar Resgate'}</span>
                        <ArrowRight size={20} strokeWidth={1.9} />
                      </button>

                      <p className="jr-resgate__seguro">
                        <LockKeyhole size={13} strokeWidth={2} aria-hidden="true" />
                        Resgate 100% seguro
                      </p>
                    </div>
                  </Reveal>
                ))}
              </div>

              {cpf && myRedemptions.length > 0 && (
                <>
                  <Reveal className="jr-cena__cabeca jr-resgate__meus-cabeca" id="meus-resgates">
                    <h2 className="jr-cena__titulo jr-ouro-metal jr-resgate__titulo">
                      <Ticket size={19} strokeWidth={1.9} aria-hidden="true" />
                      Meus resgates
                      <Ticket size={19} strokeWidth={1.9} aria-hidden="true" />
                    </h2>
                  </Reveal>

                  <ol className="jr-resgates-grade">
                    {myRedemptions.map((redemption, indice) => {
                      const state = getRedemptionCodeState(redemption)
                      const expiresAt = formatDate(redemption.expira_em)
                      const usedAt = formatDate(redemption.usado_em)
                      const canRenew = ['expired', 'cancelled'].includes(state)

                      return (
                        <Reveal as="li" key={redemption.id} delay={indice * 70} className="jr-resgate-card">
                          <header>
                            <strong>{redemption.premio_nome}</strong>
                            <span className="jr-chip" data-estado={state}>
                              {REDEMPTION_STATE_LABELS[state]}
                            </span>
                          </header>

                          <div className="jr-resgate-card__codigo">
                            <code>{redemption.codigo_resgate || '—'}</code>
                            {state === 'active' && redemption.codigo_resgate && (
                              <button
                                type="button"
                                aria-label="Copiar código"
                                onClick={() => navigator.clipboard?.writeText(redemption.codigo_resgate)}
                              >
                                <Copy size={14} strokeWidth={1.8} />
                              </button>
                            )}
                          </div>

                          <p className="jr-miudo">
                            {redemption.pontos_usados} pontos
                            {state === 'active' && expiresAt && <> · válido até {expiresAt}</>}
                            {state === 'used' && usedAt && <> · utilizado em {usedAt}</>}
                            {state === 'expired' && expiresAt && <> · venceu em {expiresAt}</>}
                          </p>

                          {canRenew && (
                            <button
                              type="button"
                              className="jr-btn jr-btn--contorno jr-btn--pequeno jr-resgate-card__renovar"
                              onClick={() => handleRenewCode(redemption)}
                              disabled={renewingId !== null}
                            >
                              <RefreshCw size={14} strokeWidth={2} />
                              {renewingId === redemption.id ? 'Renovando...' : 'Renovar código'}
                            </button>
                          )}
                        </Reveal>
                      )
                    })}
                  </ol>
                </>
              )}
            </div>
          </section>

          <JornadaNav atual="/resgate_dos_premios" cpf={cpf} />
        </>
      )}

      {redeemedPrize && (
        <section className="jr-sucesso" role="dialog" aria-modal="true">
          <div className="jr-sucesso__brilho" aria-hidden="true" />

          <article className="jr-sucesso__cartao">
            <CantoMoldura className="jr-porta__canto jr-porta__canto--se" tamanho={38} />
            <CantoMoldura className="jr-porta__canto jr-porta__canto--sd" tamanho={38} rotacao={90} />
            <CantoMoldura className="jr-porta__canto jr-porta__canto--id" tamanho={38} rotacao={180} />
            <CantoMoldura className="jr-porta__canto jr-porta__canto--ie" tamanho={38} rotacao={270} />

            <img className="jr-sucesso__brasao" src="/images/jornada/marcas/brasao-hr.png" alt="" aria-hidden="true" />

            <p className="jr-sobrescrito jr-sucesso__kicker">
              <Crown size={14} strokeWidth={1.9} aria-hidden="true" />
              Jornada Real
              <Crown size={14} strokeWidth={1.9} aria-hidden="true" />
            </p>

            <h2 className="jr-sucesso__titulo">
              Experiência <span className="jr-hero__realce">Confirmada</span>
            </h2>
            <p className="jr-lede jr-sucesso__copia">
              Sua experiência <strong>{redeemedPrize.name}</strong> foi confirmada com sucesso.
            </p>

            <div className="jr-sucesso__premio">
              {redeemedPrize.image ? (
                <img src={redeemedPrize.image} alt={redeemedPrize.name} />
              ) : (
                <div className="jr-premio-mini__vazio jr-resgate__vazio">
                  <Gift size={22} strokeWidth={1.7} aria-hidden="true" />
                </div>
              )}
              <div>
                <small>{redeemedPrize.name}</small>
                <strong>{redeemedPrize.subtitle}</strong>
                <span>
                  <Sparkles size={13} fill="currentColor" strokeWidth={1.6} aria-hidden="true" />
                  {redeemedPrize.points} pontos utilizados
                </span>
              </div>
            </div>

            <div className="jr-sucesso__codigo">
              <div className="jr-sucesso__codigo-rotulo">
                <Ticket size={18} strokeWidth={1.9} aria-hidden="true" />
                <span>Código exclusivo</span>
              </div>

              <div className="jr-sucesso__codigo-caixa">
                <strong>{redeemedPrize.code}</strong>
                <button
                  type="button"
                  aria-label="Copiar código"
                  onClick={() => navigator.clipboard?.writeText(redeemedPrize.code)}
                >
                  <Copy size={17} strokeWidth={1.8} />
                </button>
              </div>

              <p className="jr-miudo jr-sucesso__aviso">
                <ShieldCheck size={17} strokeWidth={1.9} aria-hidden="true" />
                Apresente este código na recepção para liberar sua experiência exclusiva.
              </p>

              <p className="jr-miudo jr-sucesso__nota">
                <Info size={15} strokeWidth={2} aria-hidden="true" />
                <span>
                  Seu código é pessoal, intransferível e{' '}
                  {redeemedPrizeExpiresAt ? (
                    <>válido até <strong>{redeemedPrizeExpiresAt}</strong>.</>
                  ) : (
                    <>com validade definida no momento do resgate.</>
                  )}{' '}
                  Resgates são realizados apenas no Hotel Real.
                </span>
              </p>

              {isRedeemedCodeActive && <span className="jr-chip jr-sucesso__status" data-estado="active">Código ativo</span>}
            </div>

            <div className="jr-sucesso__acoes">
              <button type="button" className="jr-btn jr-btn--contorno" onClick={() => setRedeemedPrize(null)}>
                <Gift size={18} strokeWidth={1.8} />
                <span>Ver outras experiências</span>
              </button>
              <Link href={withCpfParam('/consultar-pontos', cpf)} className="jr-btn">
                <Crown size={18} strokeWidth={1.9} />
                <span>Continuar Jornada Real</span>
              </Link>
            </div>

            <footer className="jr-sucesso__rodape">
              <Crown size={20} strokeWidth={1.9} aria-hidden="true" />
              <p>
                Cada estadia te aproxima de novas experiências exclusivas.
                <strong> Continue avançando!</strong>
              </p>
            </footer>
          </article>
        </section>
      )}
    </main>
  )
}
