'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowLeft, ArrowRight, Check, Crown } from 'lucide-react'
import '../jornada-real.css'
import Reveal from '@/components/jornada/Reveal'
import LuzPonteiro from '@/components/jornada/LuzPonteiro'
import BotaoSom from '@/components/jornada/BotaoSom'
import JornadaNav from '@/components/jornada/JornadaNav'
import { Fleurao } from '@/components/jornada/Ornamentos'
import { api } from '@/lib/api'
import { NIVEIS_JORNADA_REAL, nivelPorPontos, nivelPorChaveOuNome, proximoNivel } from '@/lib/jornada-config'

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

const getApiErrorMessage = (error, fallback) => {
  const status = error.response?.status
  if (status && status >= 500) return fallback

  const data = error.response?.data
  if (typeof data === 'string') return data
  if (typeof data?.detail === 'string') return data.detail
  if (typeof data?.message === 'string') return data.message

  return fallback
}

const normalizeLoyaltyData = (data) => {
  const programa = data?.programa_pontos || {}

  return {
    customerName: data?.customer_name || data?.customerName || data?.cliente?.nome || data?.cliente_nome,
    points: firstNumber(
      data?.lifetime_points,
      data?.lifetimePoints,
      data?.total_pontos_nivel,
      programa?.total_pontos_nivel,
      data?.redeemable_points,
      data?.saldo_atual,
      data?.saldo_pontos,
      data?.saldo
    ),
    // se a API já disser o nível atual, ele vence a leitura local por faixa
    currentLevelName: data?.current_level_name || data?.current_level?.nome || programa?.nivel?.nome,
  }
}

export default function NivelJornadaReal() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const cpf = (searchParams.get('cpf') || searchParams.get('documento') || '').replace(/\D/g, '')

  const [loyaltyData, setLoyaltyData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [retryTick, setRetryTick] = useState(0)

  useEffect(() => {
    if (!cpf) {
      router.push('/consultar')
      return
    }

    let isMounted = true

    const loadLoyalty = async () => {
      setIsLoading(true)
      setLoadError(null)

      try {
        const response = await api.get(`/customers/${cpf}/loyalty`, { silentError: true })
        if (isMounted) setLoyaltyData(normalizeLoyaltyData(response.data))
      } catch (primaryError) {
        try {
          const response = await api.get(`/pontos/consultar/${cpf}`, { silentError: true })
          if (isMounted) setLoyaltyData(normalizeLoyaltyData(response.data))
        } catch (error) {
          if (isMounted) {
            setLoyaltyData(null)
            setLoadError(getApiErrorMessage(error, 'Não foi possível carregar seus pontos agora.'))
          }
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    loadLoyalty()

    return () => {
      isMounted = false
    }
  }, [cpf, router, retryTick])

  const nome = loyaltyData?.customerName || 'Hóspede Real'
  const pontos = loyaltyData?.points ?? 0
  const nivelAtual =
    (loyaltyData?.currentLevelName && nivelPorChaveOuNome(loyaltyData.currentLevelName)) || nivelPorPontos(pontos)
  const nivelSeguinte = proximoNivel(nivelAtual)
  const faltam = nivelSeguinte ? Math.max(nivelSeguinte.min - pontos, 0) : 0
  const progresso = nivelSeguinte
    ? Math.min(100, Math.max(0, ((pontos - nivelAtual.min) / (nivelSeguinte.min - nivelAtual.min)) * 100))
    : 100

  return (
    <main className="jr jr-niveis-pagina">
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

      <section className="jr-cena jr-niveis" aria-label="Seus níveis na Jornada Real">
        <div className="jr-shell">
          <Reveal className="jr-cena__cabeca">
            <h1 className="jr-cena__titulo jr-ouro-metal">A escada da corte</h1>
            <Fleurao largura={260} />
            <p className="jr-lede">
              {isLoading
                ? 'Carregando seus pontos...'
                : `${nome} está no nível ${nivelAtual.nome}, com ${pontos} pontos.`}
            </p>
          </Reveal>

          {loadError && !isLoading && (
            <div className="jr-pontos__erro">
              <p className="jr-texto">{loadError}</p>
              <button type="button" className="jr-btn jr-btn--contorno" onClick={() => setRetryTick((tick) => tick + 1)}>
                Tentar novamente
              </button>
            </div>
          )}

          <ol className="jr-cartas">
            {NIVEIS_JORNADA_REAL.map((nivel, indice) => {
              const atual = nivel.chave === nivelAtual.chave
              return (
                <Reveal
                  as="li"
                  key={nivel.chave}
                  className="jr-carta"
                  data-posicao={indice + 1}
                  data-atual={atual ? 'sim' : 'nao'}
                  delay={indice * 90}
                >
                  <div className="jr-carta__palco">
                    <span className="jr-carta__foco" aria-hidden="true" />
                    <span className="jr-carta__chao" aria-hidden="true" />
                    <img
                      src={nivel.objeto}
                      alt={nivel.objetoAlt}
                      loading="lazy"
                      className={`jr-objeto jr-carta__objeto ${nivel.objetoClasse}`}
                    />
                  </div>

                  <div className="jr-carta__corpo">
                    <span className="jr-carta__numeral" aria-hidden="true">{nivel.numeral}</span>
                    <h2 className="jr-carta__nome jr-ouro-metal">{nivel.nome}</h2>
                    <span className="jr-sobrescrito">{nivel.posto}</span>
                    <p className="jr-texto jr-carta__texto">{nivel.texto}</p>

                    {atual && !isLoading && <span className="jr-carta__selo-atual">Seu nível atual</span>}

                    <div className="jr-escala" style={{ '--de': `${nivel.de}%`, '--ate': `${nivel.ate}%` }}>
                      <span className="jr-escala__faixa-rotulo">{nivel.faixa}</span>
                      <span className="jr-escala__trilho" aria-hidden="true">
                        <span className="jr-escala__preenchido" />
                        <span className="jr-escala__pino jr-escala__pino--de" />
                        <span className="jr-escala__pino jr-escala__pino--ate" />
                      </span>
                      <span className="jr-escala__marcas" aria-hidden="true">
                        <i>0</i>
                        <i>50</i>
                        <i>90+</i>
                      </span>
                    </div>
                  </div>
                </Reveal>
              )
            })}
          </ol>

          {!isLoading && (
            <Reveal delay={120} className="jr-painel">
              <h2 className="jr-painel__titulo">
                <Crown size={17} aria-hidden="true" />
                Seus benefícios no nível {nivelAtual.nome}
              </h2>

              <ul className="jr-beneficios">
                {nivelAtual.beneficios.map((beneficio) => (
                  <li key={beneficio}>
                    <Check size={16} strokeWidth={2.2} aria-hidden="true" />
                    {beneficio}
                  </li>
                ))}
              </ul>

              {nivelSeguinte && (
                <>
                  <div className="jr-barra-progresso" style={{ marginTop: 20 }}>
                    <span className="jr-barra-progresso__preenchido" style={{ width: `${progresso}%` }} />
                    <span className="jr-barra-progresso__marcador" style={{ left: `${progresso}%` }}>
                      <Crown size={12} fill="currentColor" aria-hidden="true" />
                    </span>
                  </div>
                  <p className="jr-painel__resumo">
                    <strong>{pontos}</strong> / {nivelSeguinte.min} pontos
                    <span>Faltam {faltam} pontos para o nível {nivelSeguinte.nome}</span>
                  </p>
                </>
              )}
            </Reveal>
          )}

          <div className="jr-niveis-pagina__acao">
            <Link href={withCpfParam('/consultar-pontos', cpf)} className="jr-btn">
              <span>Continuar minha jornada</span>
              <ArrowRight size={19} strokeWidth={1.9} />
            </Link>
          </div>
        </div>
      </section>

      <JornadaNav atual="/consultar-pontos" cpf={cpf} />
    </main>
  )
}
