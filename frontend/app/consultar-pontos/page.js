'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowRight, Crown, Gift, Star, Ticket } from 'lucide-react'
import '../jornada-real.css'
import Reveal from '@/components/jornada/Reveal'
import LuzPonteiro from '@/components/jornada/LuzPonteiro'
import BotaoSom from '@/components/jornada/BotaoSom'
import JornadaNav from '@/components/jornada/JornadaNav'
import { CantoMoldura, Fleurao } from '@/components/jornada/Ornamentos'
import { api } from '@/lib/api'
import { NIVEIS_JORNADA_REAL } from '@/lib/jornada-config'

// Usado só como escala de exibição antes da API responder — o mínimo do
// último nível em lib/jornada-config.js, não um número solto na tela.
const NIVEL_MAXIMO_MIN = NIVEIS_JORNADA_REAL[NIVEIS_JORNADA_REAL.length - 1].min

// Fallback de exibi\u00e7\u00e3o para quando a API ainda n\u00e3o respondeu ou est\u00e1 fora
// do ar em ambientes de preview \u2014 evita a vitrine aparecer vazia. Quando a
// API responde, ela sempre vence: ver normalizeReward abaixo.
const rewardDefaults = [
  {
    name: 'Tecnologia Real',
    points: 90,
    image: '/images/premios/tecnologia-real.png',
    badge: 'Mais disputado',
    footer: '+Pr\u00eamio mais disputado',
    slug: 'tecnologia-real',
  },
  {
    name: 'Rituais do Real',
    points: 35,
    image: '/images/premios/rituais-do-real.png',
    footer: 'Transforme sua rotina em experi\u00eancia',
    slug: 'rituais-do-real',
  },
  {
    name: 'O Retorno do Sonho',
    points: 25,
    image: '/images/premios/o-retorno-do-sonho.png',
    footer: '1 di\u00e1ria com hidro + champanhe cortesia',
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
    next_level_points: firstNumber(data?.next_level_points, barraNivel?.meta, NIVEL_MAXIMO_MIN),
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
  next_level_points: NIVEL_MAXIMO_MIN,
  missing_to_next_level: NIVEL_MAXIMO_MIN,
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
    badge: premio.badge || premio.destaque || defaults.badge || null,
    footer: premio.descricao || defaults.footer || 'Prêmio exclusivo da Jornada Real',
    slug,
  }
}

/*
 * Nome, faixa e objeto vêm todos de lib/jornada-config.js: a chave, o cetro
 * e a coroa são os mesmos recortes que a home usa em "A escada da corte",
 * a pedido do hotel, para as duas telas contarem a mesma história. Antes
 * daqui saíam fotos de suíte com um ícone Lucide por cima.
 */
const niveisMapa = NIVEIS_JORNADA_REAL.map((nivel) => ({
  chave: nivel.chave,
  nome: nivel.nome,
  faixa: nivel.faixa,
  objeto: nivel.objeto,
}))

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
  const currentLevelName = loyaltyData?.current_level_name || loyaltyData?.current_level?.nome
  const currentMultiplier = firstNumber(loyaltyData?.current_level?.multiplicador, 1) || 1
  const hasBonusAtivo = !isFallbackLoyalty && currentMultiplier > 1
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
  const nivelAtualChave = slugify(currentLevelName || 'essencia')

  useEffect(() => {
    let isMounted = true

    const loadRewards = async () => {
      try {
        const response = await api.get('/premios', { silentError: true })
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

  const rewards = apiRewards.length ? apiRewards : rewardDefaults
  const proximoPremio = rewards.length
    ? [...rewards].sort((a, b) => a.points - b.points).find((item) => item.points > currentPoints) || rewards[0]
    : null

  return (
    <main className="jr jr-pontos-pagina">
      <LuzPonteiro densidade={2} />

      <header className="jr-barra">
        <div className="jr-shell jr-barra__interno">
          <Link href="/" className="jr-barra__marca" aria-label="Jornada Real — Hotel Real Cabo Frio">
            <img src="/images/logo-jornada-real.png" alt="Jornada Real" />
          </Link>
          <div className="jr-barra__acoes">
            <BotaoSom />
          </div>
        </div>
      </header>

      <section className="jr-cena jr-pontos" aria-label="Minha Jornada">
        <div className="jr-shell">
          {isLoadingLoyalty && (
            <p className="jr-lede jr-pontos__estado">Carregando seus dados da Jornada Real...</p>
          )}

          {loyaltyError && !isLoadingLoyalty && cpf && (
            <div className="jr-pontos__erro">
              <p className="jr-texto">{loyaltyError}</p>
              <button type="button" className="jr-btn jr-btn--contorno" onClick={() => router.push('/consultar')}>
                Voltar e tentar novamente
              </button>
            </div>
          )}

          {loyaltyData && (
            <>
              {/* ---------------------------------------------- boas-vindas */}
              <Reveal className="jr-pontos__boasvindas">
                <div>
                  <span className="jr-sobrescrito">Você está quase lá</span>
                  <h1 className="jr-pontos__nome jr-ouro-metal">
                    {customerName}
                    <Crown size={22} strokeWidth={1.6} aria-hidden="true" />
                  </h1>
                  <p className="jr-lede">
                    Você está evoluindo na Jornada Real e conquistando experiências únicas.
                  </p>
                </div>

                <div className="jr-nota jr-pontos__saldo">
                  <CantoMoldura className="jr-nota__canto jr-nota__canto--se" tamanho={30} />
                  <CantoMoldura className="jr-nota__canto jr-nota__canto--sd" tamanho={30} rotacao={90} />
                  <CantoMoldura className="jr-nota__canto jr-nota__canto--id" tamanho={30} rotacao={180} />
                  <CantoMoldura className="jr-nota__canto jr-nota__canto--ie" tamanho={30} rotacao={270} />
                  <Crown size={30} strokeWidth={1.5} aria-hidden="true" />
                  <span className="jr-nota__valor jr-ouro-metal">{currentPoints}</span>
                  <hr className="jr-nota__fio" />
                  <span className="jr-nota__rotulo">Pontos atuais</span>
                </div>
              </Reveal>

              {/* -------------------------------------- progresso de nível e prêmios */}
              <div className="jr-pontos__grade">
              <Reveal delay={80} className="jr-painel">
                <h2 className="jr-painel__titulo">
                  <Star size={17} fill="currentColor" aria-hidden="true" />
                  Seu progresso de nível
                  <Star size={17} fill="currentColor" aria-hidden="true" />
                </h2>

                {hasBonusAtivo && (
                  <p className="jr-painel__bonus">
                    Nível {currentLevelName}: seus pontos de resgate valem <strong>{currentMultiplier}x</strong> em cada reserva
                  </p>
                )}

                <ol className="jr-pontos__niveis">
                  {niveisMapa.map((nivel) => (
                    <li key={nivel.chave} className="jr-pontos__nivel" data-atual={nivel.chave === nivelAtualChave ? 'sim' : 'nao'}>
                      {/* palco do objeto, no mesmo desenho da home: halo atrás, sombra de contato embaixo */}
                      <div className="jr-pontos__nivel-palco">
                        <span className="jr-pontos__nivel-foco" aria-hidden="true" />
                        <span className="jr-pontos__nivel-chao" aria-hidden="true" />
                        <img
                          src={nivel.objeto}
                          alt=""
                          aria-hidden="true"
                          data-objeto={nivel.chave}
                          className="jr-pontos__nivel-objeto"
                          loading="lazy"
                        />
                      </div>
                      <span className="jr-pontos__nivel-nome">{nivel.nome}</span>
                      <span className="jr-pontos__nivel-faixa">{nivel.faixa}</span>
                    </li>
                  ))}
                </ol>

                <div className="jr-barra-progresso">
                  <span className="jr-barra-progresso__preenchido" style={{ width: `${levelProgress}%` }} />
                  <span className="jr-barra-progresso__marcador" style={{ left: `${levelProgress}%` }}>
                    <Star size={13} fill="currentColor" aria-hidden="true" />
                  </span>
                </div>

                <p className="jr-painel__resumo">
                  <strong>{lifetimePoints}</strong> / {nextLevelPoints} pontos
                  <span>{levelProgressText}</span>
                </p>

                <Link href={levelPageUrl} className="jr-btn jr-btn--contorno">
                  <span>Ver tela de níveis</span>
                  <ArrowRight size={18} strokeWidth={1.9} />
                </Link>
              </Reveal>

              {/* ------------------------------------------- progresso de prêmios */}
              <Reveal delay={140} className="jr-painel">
                <h2 className="jr-painel__titulo">
                  <Crown size={18} aria-hidden="true" />
                  Seu progresso de prêmios
                  <Crown size={18} aria-hidden="true" />
                </h2>

                <div className="jr-painel__premio-linha">
                  <div className="jr-barra-progresso">
                    <span className="jr-barra-progresso__preenchido" style={{ width: `${rewardProgress}%` }} />
                    <span className="jr-barra-progresso__marcador" style={{ left: `${rewardProgress}%` }}>
                      <Crown size={12} fill="currentColor" aria-hidden="true" />
                    </span>
                  </div>

                  <div className="jr-painel__premio-resumo">
                    <strong>{rewardSummary}</strong>
                    <small>{rewardSummaryLabel}</small>
                  </div>
                </div>

                <p className="jr-painel__texto">{rewardProgressText}</p>

                {proximoPremio && (
                  <Link
                    href={withCpfParam(`/resgate_dos_premios?premio=${proximoPremio.slug}`, cpf)}
                    className="jr-painel__proximo"
                  >
                    {proximoPremio.image ? (
                      <img src={proximoPremio.image} alt="" loading="lazy" />
                    ) : (
                      <span className="jr-painel__proximo-semfoto" aria-hidden="true">
                        <Gift size={20} strokeWidth={1.7} />
                      </span>
                    )}
                    <span className="jr-painel__proximo-texto">
                      <small>Seu próximo prêmio</small>
                      <strong>{proximoPremio.name}</strong>
                    </span>
                    <span className="jr-painel__proximo-pontos">
                      <Crown size={13} strokeWidth={1.8} aria-hidden="true" />
                      {proximoPremio.points}
                    </span>
                  </Link>
                )}

                <Link href={withCpfParam('/meu-cupom', cpf)} className="jr-btn">
                  <Gift size={18} strokeWidth={1.8} />
                  <span>Convidar amigos — Meu Cupom</span>
                  <ArrowRight size={18} strokeWidth={1.9} />
                </Link>

                {/* os códigos já resgatados moram no fim da tela de prêmios:
                    sem este atalho, o hóspede não descobre onde consultá-los */}
                <Link
                  href={withCpfParam('/resgate_dos_premios#meus-resgates', cpf)}
                  className="jr-painel__link-secundario"
                >
                  <Ticket size={15} strokeWidth={1.9} aria-hidden="true" />
                  Ver meus prêmios já resgatados
                </Link>
              </Reveal>
              </div>

              {/* -------------------------------------------------- prêmios em destaque */}
              <Reveal delay={200} className="jr-cena__cabeca jr-pontos__premios-cabeca">
                <h2 className="jr-cena__titulo jr-ouro-metal">Prêmios exclusivos</h2>
                <Fleurao largura={260} />
                <p className="jr-lede">Escolha seu próximo objetivo e transforme sua estadia em conquistas.</p>
              </Reveal>

              {!isLoadingRewards && rewards.length === 0 && (
                <p className="jr-lede jr-resgate__vazio-catalogo">
                  O catálogo está sendo preparado. Volte em breve para escolher o seu.
                </p>
              )}

              <ol className="jr-premios-mini">
                {rewards.map((reward, indice) => (
                  <Reveal as="li" key={reward.slug || reward.name} delay={indice * 80}>
                    <Link
                      href={withCpfParam(`/resgate_dos_premios?premio=${reward.slug}`, cpf)}
                      className="jr-premio-mini"
                    >
                      {reward.badge && <span className="jr-premio-mini__selo">{reward.badge}</span>}
                      {reward.image ? (
                        <img src={reward.image} alt={reward.name} loading="lazy" />
                      ) : (
                        <div className="jr-premio-mini__vazio">
                          <Gift size={26} strokeWidth={1.6} aria-hidden="true" />
                          <span>{isLoadingRewards ? 'Carregando imagem' : 'Imagem não cadastrada'}</span>
                        </div>
                      )}
                      <div className="jr-premio-mini__corpo">
                        <h3>{reward.name}</h3>
                        <p className="jr-premio-mini__pontos">
                          <Crown size={15} strokeWidth={1.7} aria-hidden="true" />
                          <strong>{reward.points}</strong> pontos
                          {reward.badge && <span className="jr-premio-mini__tag">• {reward.badge}</span>}
                        </p>
                        <small>{reward.footer}</small>
                      </div>
                    </Link>
                  </Reveal>
                ))}
              </ol>

              <div className="jr-pontos__acao">
                <Link href={withCpfParam('/resgate_dos_premios', cpf)} className="jr-btn">
                  <span>Escolher meu prêmio</span>
                  <ArrowRight size={19} strokeWidth={1.9} />
                </Link>
              </div>
            </>
          )}
        </div>
      </section>

      <JornadaNav atual="/consultar-pontos" cpf={cpf} />
    </main>
  )
}





