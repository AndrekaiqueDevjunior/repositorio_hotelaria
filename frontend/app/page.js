'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import './jornada-real.css'
import Reveal from '@/components/jornada/Reveal'
import Trilha from '@/components/jornada/Trilha'
import LuzPonteiro from '@/components/jornada/LuzPonteiro'
import BotaoSom from '@/components/jornada/BotaoSom'
import { tocar } from '@/components/jornada/som'
import JornadaNav from '@/components/jornada/JornadaNav'
import { CantoMoldura, Fleurao } from '@/components/jornada/Ornamentos'
import { api } from '@/lib/api'
import { NIVEIS_JORNADA_REAL } from '@/lib/jornada-config'

/*
 * Dados da empresa para o rodapé legal.
 * ATENÇÃO: o CNPJ abaixo é um marcador — confirmar o número oficial com o
 * hotel antes de publicar no domínio de produção.
 */
const EMPRESA = {
  razaoSocial: 'Hotel Real Cabo Frio LTDA',
  nomeFantasia: 'Hotel Real Cabo Frio',
  cnpj: '29.269.359/0001-40',
  logradouro: 'Rua Enfermeiro Ricardo Sanches, 22',
  cidade: 'Cabo Frio · Rio de Janeiro',
  telefone: '(22) 2648-5900',
  whatsapp: '552226485900',
  email: 'contato@hotelrealcabofrio.com.br',
}

const ROMANOS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
const numeralPosicional = (indice) => ROMANOS[indice] || String(indice + 1)

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

// Fallback de exibição para quando a API ainda não respondeu ou está fora
// do ar em ambientes de preview — evita a cena de prêmios aparecer vazia.
// Quando a API responde, ela sempre vence: ver normalizePremio abaixo.
const premioDefaults = [
  {
    slug: 'o-retorno-do-sonho',
    nome: 'O Retorno do Sonho',
    linha: 'Diária na Suíte Real com hidromassagem e champanhe',
    custo: '25',
    imagem: '/images/jornada/premios/retorno-do-sonho.png',
  },
  {
    slug: 'rituais-do-real',
    nome: 'Rituais do Real',
    linha: 'Cafeteira Mondial Dolce Aroma, 32 xícaras',
    custo: '35',
    imagem: '/images/jornada/premios/rituais-do-real.png',
  },
  {
    slug: 'tecnologia-real',
    nome: 'Tecnologia Real',
    linha: 'iPhone 16 Pro Max 256 GB',
    custo: '90',
    imagem: '/images/jornada/premios/tecnologia-real.png',
  },
]

// Os numerais romanos são só a posição na lista, não pertencem ao prêmio.
const normalizePremio = (premio) => {
  const slug = premio.slug || slugify(premio.nome)
  const defaults = premioDefaults.find((item) => item.slug === slug) || {}

  return {
    ...defaults,
    id: premio.id,
    slug,
    nome: premio.nome || defaults.nome || 'Prêmio Real',
    linha: premio.descricao || defaults.linha || 'Prêmio exclusivo da Jornada Real.',
    custo: String(premio.preco_em_pontos ?? premio.preco_em_rp ?? defaults.custo ?? 0),
    imagem: resolveImageUrl(premio.imagem_url || premio.imagemUrl) || defaults.imagem || '',
  }
}

const passos = [
  { numeral: 'I', titulo: 'Reserve', texto: 'Hospede-se no Hotel Real e aproveite. Cada diária conta.' },
  { numeral: 'II', titulo: 'Acumule', texto: 'Cada estadia rende pontos que entram depois do check-out.' },
  { numeral: 'III', titulo: 'Suba de nível', texto: 'Quanto mais alto o posto, mais vale cada reserva.' },
  { numeral: 'IV', titulo: 'Resgate', texto: 'Troque pontos por prêmios e experiências.' },
]

// Níveis, faixas de pontos e insígnias vêm de lib/jornada-config.js — fonte
// única, ver o comentário lá para o motivo.
const niveis = NIVEIS_JORNADA_REAL


const convitePassos = [
  {
    numeral: 'I',
    titulo: 'Pegue seu cupom',
    texto: 'Ele já existe no seu painel, com o seu nome. Não precisa solicitar nada.',
  },
  {
    numeral: 'II',
    titulo: 'Envie para quem quiser',
    texto: 'Copie o código ou mande o link pelo WhatsApp, com o cupom já embutido.',
  },
  {
    numeral: 'III',
    titulo: 'Os dois ganham',
    texto: 'Seu convidado reserva com desconto e você pontua quando a estadia se concretiza.',
  },
]

const vantagens = [
  {
    valor: '10%',
    rotulo: 'Para quem chega',
    texto: 'Desconto direto na reserva de quem usa o seu cupom, aplicado no fechamento.',
  },
  {
    valor: '5',
    rotulo: 'Pontos para você',
    texto: 'Creditados quando a reserva indicada se concretiza, sem teto de indicações.',
  },
  {
    valor: '5',
    rotulo: 'CPFs por cupom',
    texto: 'O mesmo cupom atende até cinco pessoas diferentes da sua corte.',
  },
]

const provas = [
  {
    texto: 'A suíte Real é um luxo. Espaço de sobra, cama enorme e uma vista que compensa qualquer viagem.',
    autor: 'Avaliação de hóspede',
  },
  {
    texto: 'Localização impecável: mercado na frente, farmácia ao lado e a praia a minutos de caminhada.',
    autor: 'Avaliação de hóspede',
  },
  {
    texto: 'Café da manhã muito acima da média e uma equipe que trata todo mundo pelo nome.',
    autor: 'Avaliação de hóspede',
  },
]

const perguntas = [
  {
    p: 'Quando os pontos entram na minha conta?',
    r: 'Depois do check-out confirmado na recepção. O regulamento prevê até 48 horas; na prática o crédito costuma cair na hora.',
  },
  {
    p: 'Se eu resgatar um prêmio, eu caio de nível?',
    r: 'Não. Os pontos de resgate saem do saldo, mas os pontos de nível nunca regridem. Quem chegou, chegou.',
  },
  {
    p: 'E se a reserva for cancelada ou estornada?',
    r: 'Os pontos daquela reserva são estornados junto. O programa premia a hospedagem concluída.',
  },
  {
    p: 'Como funciona o cupom de indicação?',
    r: 'Quem reserva com o seu cupom ganha 10% de desconto. Você ganha 5 pontos quando a reserva se concretiza. Cada cupom vale para até 5 CPFs diferentes.',
  },
  {
    p: 'Onde eu retiro o prêmio resgatado?',
    r: 'Na recepção do Hotel Real, apresentando o código gerado no resgate. Ele é pessoal e intransferível.',
  },
]

const garantias = [
  { titulo: 'Segurança', texto: 'Seus dados ficam protegidos do começo ao fim da jornada.' },
  { titulo: 'Atendimento', texto: 'Nossa equipe responde sempre que você precisar.' },
  { titulo: 'Reservas', texto: 'As reservas são feitas pelo canal oficial do hotel.' },
  {
    titulo: 'Regras',
    texto: 'O regulamento do programa está escrito por inteiro.',
    href: '/termos-jornada-real',
    rotulo: 'Ler os termos',
  },
]

export default function JornadaReal() {
  const [aberta, setAberta] = useState(0)

  const [apiPremios, setApiPremios] = useState([])
  const [isLoadingPremios, setIsLoadingPremios] = useState(true)
  const premios = apiPremios.length ? apiPremios : premioDefaults

  useEffect(() => {
    let isMounted = true

    const carregarPremios = async () => {
      try {
        // silencioso: há catálogo de reserva se a API falhar, então o
        // hóspede não precisa ver aviso de erro por isso
        const response = await api.get('/premios', { silentError: true })
        const lista = Array.isArray(response.data) ? response.data : []

        if (isMounted) {
          setApiPremios(lista.map(normalizePremio))
        }
      } catch (error) {
        if (isMounted) {
          setApiPremios([])
        }
      } finally {
        if (isMounted) {
          setIsLoadingPremios(false)
        }
      }
    }

    carregarPremios()

    return () => {
      isMounted = false
    }
  }, [])

  // Prêmios já revelados. A cortina abre uma vez e não fecha mais.
  const [revelados, setRevelados] = useState([])
  const revelar = (slug) =>
    setRevelados((atuais) => {
      if (atuais.includes(slug)) return atuais
      tocar('revelar') // o carrilhão só soa na primeira abertura
      return [...atuais, slug]
    })

  return (
    <main className="jr jr-home">
      {/* faíscas douradas seguindo o ponteiro por toda a página */}
      <LuzPonteiro densidade={2} />

      {/* ================================================== barra do topo */}
      <header className="jr-barra">
        <div className="jr-shell jr-barra__interno">
          <Link href="/" className="jr-barra__marca" aria-label="Jornada Real — Hotel Real Cabo Frio">
            <img src="/images/logo-jornada-real.png" alt="Jornada Real" />
          </Link>

          <nav className="jr-barra__menu" aria-label="Seções da página">
            <a href="#como-avancar">Como funciona</a>
            <a href="#niveis">Níveis</a>
            <a href="#premios">Prêmios</a>
            <a href="#convite">Convite</a>
            <a href="#duvidas">Dúvidas</a>
          </nav>

          <div className="jr-barra__acoes">
            <BotaoSom />
            <Link href="/consultar-pontos" className="jr-btn jr-btn--pequeno jr-barra__cta">
              Ver meus pontos
            </Link>
          </div>
        </div>
      </header>

      {/* ============================================================ hero */}
      <section className="jr-hero">
        {/*
          A imagem entra inteira, encostada à direita. O degradê da esquerda
          para a direita apaga a borda do arquivo, para não parecer recorte.
        */}
        <div className="jr-hero__fundo" aria-hidden="true" />
        <div className="jr-hero__degrade" aria-hidden="true" />
        <div className="jr-feixe jr-hero__feixe" aria-hidden="true" />
        <div className="jr-poeira" aria-hidden="true" />

        <div className="jr-shell jr-hero__grid">
          <div className="jr-hero__texto">
            {/*
              As quebras de linha valem só no desktop, onde o texto divide a
              cena com o trono. No mobile a frase é centralizada e quebra em
              duas linhas por conta própria (ver .jr-hero__titulo br no CSS).
            */}
            <h1 className="jr-hero__titulo">
              Sua jornada te
              <br />
              espera, <span className="jr-hero__realce">majestade.</span>
            </h1>

            <p className="jr-lede jr-hero__lede">
              O programa de fidelidade do Hotel Real Cabo Frio chegou. Cada estadia rende
              pontos, cada ponto te sobe de nível, e cada nível vale mais na próxima volta.
              O sonho é real, e agora ele te recompensa.
            </p>

            <div className="jr-hero__acoes">
              <Link href="/entrar-jornada-real" className="jr-btn">
                Começar agora
              </Link>
              <Link href="/consultar-pontos" className="jr-btn jr-btn--contorno">
                Ver meus pontos
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ================================================ ato I · a trilha */}
      <section className="jr-cena jr-avancar" id="como-avancar" aria-labelledby="jr-avancar-titulo">
        {/* luz de cena: um facho de cima e o brilho que assenta na trilha */}
        <div className="jr-feixe jr-avancar__feixe" aria-hidden="true" />
        <div className="jr-avancar__brilho" aria-hidden="true" />
        <div className="jr-poeira jr-avancar__poeira" aria-hidden="true" />

        <div className="jr-shell">
          <Reveal className="jr-cena__cabeca">
            <h2 id="jr-avancar-titulo" className="jr-cena__titulo jr-ouro-metal">
              Como avançar
            </h2>
            <Fleurao largura={320} />
            <p className="jr-lede jr-avancar__lede">
              Quatro movimentos, na ordem em que acontecem. Sem sorteio e sem letra miúda:
              a jornada anda quando você se hospeda.
            </p>
          </Reveal>

          {/* O fio dourado desenha-se conforme a rolagem e acende cada passo. */}
          <Trilha passos={passos} />
        </div>
      </section>

      {/* ============================================ ato II · a escada */}
      <section className="jr-cena jr-niveis" id="niveis" aria-labelledby="jr-niveis-titulo">
        <div className="jr-shell">
          <Reveal className="jr-cena__cabeca">
            <h2 id="jr-niveis-titulo" className="jr-cena__titulo jr-ouro-metal">
              A escada da corte
            </h2>
            <Fleurao largura={320} />
          </Reveal>
        </div>

        <div className="jr-shell">
          <ol className="jr-cartas">
            {niveis.map((nivel, indice) => (
              <Reveal
                as="li"
                key={nivel.nome}
                className="jr-carta"
                data-posicao={indice + 1}
                delay={indice * 90}
                onMouseEnter={() => tocar('brilho')}
              >
                {/* palco do objeto: o foco de luz acende quando o card recebe o ponteiro */}
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
                  <h3 className="jr-carta__nome jr-ouro-metal">{nivel.nome}</h3>
                  <span className="jr-sobrescrito">{nivel.posto}</span>
                  <p className="jr-texto jr-carta__texto">{nivel.texto}</p>

                  {/*
                    Régua de alcance: mostra onde o nível cai dentro do
                    percurso de 0 a 90+ pontos, para o hóspede ver a distância
                    e não só ler o número.
                  */}
                  <div
                    className="jr-escala"
                    style={{ '--de': `${nivel.de}%`, '--ate': `${nivel.ate}%` }}
                  >
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
            ))}
          </ol>
        </div>
      </section>

      {/* ========================================== ato III · os prêmios */}
      <section className="jr-cena jr-premios" id="premios" aria-labelledby="jr-premios-titulo">
        {/* o baú com os feixes de luz é o ambiente da cena, não um enfeite */}
        <div className="jr-premios__ambiente" aria-hidden="true" />
        <div className="jr-premios__veu" aria-hidden="true" />

        <div className="jr-shell">
          <Reveal className="jr-cena__cabeca">
            <h2 id="jr-premios-titulo" className="jr-cena__titulo jr-ouro-metal">
              Um prêmio digno da corte
            </h2>
            <Fleurao largura={320} />
          </Reveal>

          {!isLoadingPremios && premios.length === 0 && (
            <p className="jr-lede jr-resgate__vazio-catalogo">
              O catálogo está sendo preparado. Volte em breve para escolher o seu.
            </p>
          )}

          <ol className="jr-premios__lista">
            {premios.map((premio, indice) => {
              const numeral = numeralPosicional(indice)
              const revelado = revelados.includes(premio.slug)
              return (
              <li
                className="jr-premio"
                key={premio.slug}
                data-revelado={revelado ? 'sim' : 'nao'}
              >
                {/*
                  A cortina abre uma vez e fica aberta. O gesto vale para
                  ponteiro, toque e teclado — daí o botão em vez de uma div.
                */}
                <button
                  type="button"
                  className="jr-premio__palco"
                  onMouseEnter={() => revelar(premio.slug)}
                  onFocus={() => revelar(premio.slug)}
                  onClick={() => revelar(premio.slug)}
                  aria-expanded={revelado}
                  aria-label={revelado ? premio.nome : `Revelar o prêmio ${numeral}`}
                >
                  {premio.imagem && (
                    <img src={premio.imagem} alt="" loading="lazy" className="jr-premio__foto" />
                  )}

                  <span className="jr-premio__folha jr-premio__folha--esq" aria-hidden="true" />
                  <span className="jr-premio__folha jr-premio__folha--dir" aria-hidden="true" />

                  <span className="jr-premio__convite" aria-hidden="true">
                    <span className="jr-premio__convite-numeral">{numeral}</span>
                    <span className="jr-premio__convite-texto">Revelar</span>
                  </span>

                  {/* placa gravada na base do quadro: o preço fica visível
                      mesmo com a cortina fechada */}
                  <span className="jr-premio__placa">
                    <b className="jr-ouro-metal">{premio.custo}</b>
                    <span>pontos</span>
                  </span>

                  <CantoMoldura className="jr-premio__canto jr-premio__canto--se" tamanho={38} />
                  <CantoMoldura className="jr-premio__canto jr-premio__canto--id" tamanho={38} rotacao={180} />
                </button>

                <div className="jr-premio__corpo">
                  <h3 className="jr-premio__nome jr-ouro-metal">{premio.nome}</h3>
                  {/* o que é o prêmio só se revela junto com a cortina */}
                  <p className="jr-premio__linha">{premio.linha}</p>
                </div>
              </li>
              )
            })}
          </ol>

          <div className="jr-premios__acao">
            <Link href="/resgate_dos_premios" className="jr-btn">
              Ver o catálogo
            </Link>
          </div>
        </div>
      </section>

      {/* ================================================== o convite */}
      <section className="jr-cena jr-convite" id="convite" aria-labelledby="jr-convite-titulo">
        <div className="jr-convite__damasco" aria-hidden="true" />
        <div className="jr-convite__veludo" aria-hidden="true" />

        <div className="jr-shell jr-convite__grid">
          <Reveal className="jr-convite__texto">
            <h2 id="jr-convite-titulo" className="jr-convite__titulo jr-ouro-metal">
              Expanda o<br />seu reinado
            </h2>
            <Fleurao largura={280} className="jr-convite__fio" />
            <p className="jr-lede">
              Todo hóspede da Jornada recebe um cupom pessoal. Você envia para quem quiser,
              seu convidado reserva com desconto, e os pontos caem na sua conta quando a
              estadia dele se concretiza. A corte cresce e os dois lados ganham.
            </p>

            <ol className="jr-convite__passos">
              {convitePassos.map((passo) => (
                <li key={passo.numeral}>
                  <span className="jr-convite__passo-numeral">{passo.numeral}</span>
                  <div>
                    <h3 className="jr-convite__passo-titulo">{passo.titulo}</h3>
                    <p className="jr-miudo">{passo.texto}</p>
                  </div>
                </li>
              ))}
            </ol>

            <Link href="/meu-cupom" className="jr-btn jr-convite__botao">
              Pegar meu cupom
            </Link>
          </Reveal>

          <Reveal className="jr-convite__carta" delay={140}>
            {/* sem a classe jr-objeto: aqui não entra reflexo nem halo dourado */}
            <img
              src="/images/jornada/objetos/envelope.png"
              alt="Convite da Jornada Real, envelope preto com lacre dourado HR"
              className="jr-convite__envelope"
              loading="lazy"
            />
            <img
              src="/images/jornada/objetos/chave.png"
              alt=""
              aria-hidden="true"
              className="jr-convite__chave"
              loading="lazy"
            />
            <span className="jr-convite__poca" aria-hidden="true" />
          </Reveal>
        </div>

        {/* as três vantagens, cada uma numa placa ornamentada */}
        <div className="jr-shell">
          <ul className="jr-vantagens">
            {vantagens.map((item, indice) => (
              <Reveal as="li" key={item.rotulo} delay={indice * 90} className="jr-vantagem">
                <CantoMoldura className="jr-vantagem__canto jr-vantagem__canto--se" tamanho={34} />
                <CantoMoldura className="jr-vantagem__canto jr-vantagem__canto--id" tamanho={34} rotacao={180} />
                <span className="jr-vantagem__valor jr-ouro-metal">{item.valor}</span>
                <span className="jr-vantagem__rotulo">{item.rotulo}</span>
                <hr className="jr-vantagem__fio" />
                <p className="jr-miudo">{item.texto}</p>
              </Reveal>
            ))}
          </ul>
        </div>
      </section>

      {/* =========================================== prova social e lugar */}
      <section className="jr-cena jr-prova" aria-labelledby="jr-prova-titulo">
        <div className="jr-shell">
          <Reveal className="jr-cena__cabeca">
            <h2 id="jr-prova-titulo" className="jr-cena__titulo jr-ouro-metal">
              Quem já se hospedou
            </h2>
            <Fleurao largura={320} />
          </Reveal>

          {/*
            A nota fica na coluna, ao lado das avaliações, e não flutuando
            acima delas. Assim o número sustenta os depoimentos em vez de
            competir com eles.
          */}
          <div className="jr-prova__grid">
            <Reveal className="jr-nota">
              <CantoMoldura className="jr-nota__canto jr-nota__canto--se" tamanho={44} />
              <CantoMoldura className="jr-nota__canto jr-nota__canto--sd" tamanho={44} rotacao={90} />
              <CantoMoldura className="jr-nota__canto jr-nota__canto--id" tamanho={44} rotacao={180} />
              <CantoMoldura className="jr-nota__canto jr-nota__canto--ie" tamanho={44} rotacao={270} />

              <span className="jr-nota__coroa" aria-hidden="true">
                <img src="/images/jornada/marcas/brasao-hr.png" alt="" />
              </span>
              <span className="jr-nota__valor jr-ouro-metal">8,7</span>
              <hr className="jr-nota__fio" />
              <span className="jr-nota__rotulo">Nota no Booking</span>
              <p className="jr-miudo jr-nota__pe">
                Avaliações reais de quem já dormiu aqui.
              </p>
            </Reveal>

            <ul className="jr-prova__lista">
              {provas.map((prova, indice) => (
                <Reveal as="li" key={prova.texto} delay={indice * 90} className="jr-prova__item">
                  <span className="jr-prova__aspas" aria-hidden="true">“</span>
                  <p className="jr-prova__texto">{prova.texto}</p>
                  <span className="jr-sobrescrito">{prova.autor}</span>
                </Reveal>
              ))}
            </ul>
          </div>

          <Reveal className="jr-lugar">
            <figure className="jr-lugar__figura">
              <img
                src="/images/jornada/braga.jpg"
                alt="Hóspede na varanda do Hotel Real, com vista para o mar no Braga"
                loading="lazy"
              />
              <span className="jr-lugar__grade" aria-hidden="true" />
            </figure>

            <div className="jr-lugar__texto">
              <span className="jr-sobrescrito">O Braga · Cabo Frio</span>
              <h3 className="jr-lugar__titulo">Perto de tudo, de propósito</h3>
              <p className="jr-texto">
                Mercado em frente ao hotel, farmácia e restaurantes ao lado, praia a minutos
                de caminhada. A localização é parte do produto, não um detalhe do endereço.
              </p>
              <ul className="jr-lugar__itens">
                <li>Mercado em frente</li>
                <li>Praia a minutos a pé</li>
                <li>Restaurantes ao lado</li>
                <li>Farmácia ao lado</li>
                <li>Centro a poucos minutos</li>
                <li>Estacionamento no local</li>
                <li>Wi-Fi em todo o hotel</li>
                <li>Recepção 24 horas</li>
              </ul>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ==================================================== as dúvidas */}
      <section className="jr-cena jr-faq" id="duvidas" aria-labelledby="jr-faq-titulo">
        <div className="jr-shell jr-shell--estreito">
          <Reveal className="jr-cena__cabeca">
            <h2 id="jr-faq-titulo" className="jr-cena__titulo jr-ouro-metal">
              Dúvidas da corte
            </h2>
            <Fleurao largura={320} />
          </Reveal>

          <ul className="jr-faq__lista">
            {perguntas.map((item, indice) => (
              <li className="jr-faq__item" key={item.p}>
                <button
                  type="button"
                  className="jr-faq__gatilho"
                  aria-expanded={aberta === indice}
                  onClick={() => {
                    tocar('toque')
                    setAberta(aberta === indice ? -1 : indice)
                  }}
                >
                  <span>{item.p}</span>
                  <span className="jr-faq__sinal" aria-hidden="true">
                    {aberta === indice ? '−' : '+'}
                  </span>
                </button>
                {aberta === indice && <p className="jr-texto jr-faq__resposta">{item.r}</p>}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* =================================================== o fechamento */}
      {/*
        O fechamento repete a construção do hero: a foto inteira encostada à
        direita e o degradê da esquerda para a direita dando chão ao texto.
        Lá é o trono; aqui é a casa.
      */}
      <section className="jr-fecho">
        {/*
          A foto é um <img> e não um background: assim a máscara do degradê
          é medida sobre a própria imagem, e não sobre a seção. Em background
          as porcentagens seguem a largura da tela, então o degradê acertava
          numa largura e falhava em todas as outras.
        */}
        <img
          src="/images/jornada/hotel-noite.jpg"
          alt=""
          aria-hidden="true"
          className="jr-fecho__foto"
          loading="lazy"
        />
        <div className="jr-fecho__degrade" aria-hidden="true" />
        <div className="jr-poeira jr-fecho__poeira" aria-hidden="true" />

        <div className="jr-shell jr-fecho__grid">
          <div className="jr-fecho__texto">
            <div className="jr-fecho__coroa">
              <img
                src="/images/jornada/objetos/coroa.png"
                alt=""
                aria-hidden="true"
                className="jr-objeto jr-fecho__coroa-img"
                loading="lazy"
              />
              <span className="jr-fecho__coroa-chao" aria-hidden="true" />
            </div>

            <p className="jr-fecho__linha jr-ouro-metal">
              Mais que um programa,
              <br />
              um estilo de reinar.
            </p>

            <p className="jr-lede jr-fecho__lede">
              Entre agora e comece a somar pontos já na próxima estadia.
            </p>

            <div className="jr-fecho__acoes">
              <Link href="/entrar-jornada-real" className="jr-btn">
                Entrar na Jornada Real
              </Link>
              <Link href="/consultar-pontos" className="jr-btn jr-btn--contorno">
                Ver meus pontos
              </Link>
            </div>

          </div>
        </div>
      </section>

      {/* ============================================ garantias, no pé */}
      <section className="jr-garantias" aria-label="Garantias do programa">
        <div className="jr-shell">
          <div className="jr-garantias__painel">
            <CantoMoldura className="jr-garantias__canto jr-garantias__canto--se" tamanho={48} />
            <CantoMoldura className="jr-garantias__canto jr-garantias__canto--sd" tamanho={48} rotacao={90} />
            <CantoMoldura className="jr-garantias__canto jr-garantias__canto--id" tamanho={48} rotacao={180} />
            <CantoMoldura className="jr-garantias__canto jr-garantias__canto--ie" tamanho={48} rotacao={270} />

            <img
              src="/images/jornada/marcas/brasao-hr.png"
              alt=""
              aria-hidden="true"
              className="jr-garantias__brasao"
            />

            <ul className="jr-garantias__lista">
              {garantias.map((item) => (
                <li className="jr-garantia" key={item.titulo}>
                  <Fleurao largura={92} className="jr-garantia__fio" />
                  <h3 className="jr-garantia__titulo">{item.titulo}</h3>
                  <p className="jr-garantia__texto">
                    {item.texto}
                    {item.href && (
                      <>
                        {' '}
                        <Link href={item.href} className="jr-link">
                          {item.rotulo}
                        </Link>
                      </>
                    )}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ==================================================== rodapé legal */}
      <footer className="jr-rodape">
        <div className="jr-shell">
          {/* três colunas ocupando a largura, como rodapé de site: marca e
              endereço, navegação, contato */}
          <div className="jr-rodape__grade">
            <div className="jr-rodape__coluna">
              <img
                src="/images/jornada/marcas/hotel-real.png"
                alt="Hotel Real Cabo Frio"
                className="jr-rodape__marca"
                loading="lazy"
              />

              <address className="jr-rodape__endereco">
                <span className="jr-rodape__rua">{EMPRESA.logradouro}</span>
                <span className="jr-rodape__cidade">{EMPRESA.cidade}</span>
              </address>
            </div>

            <nav className="jr-rodape__coluna" aria-label="Links do rodapé">
              <h2 className="jr-rodape__titulo">Navegar</h2>
              <ul className="jr-rodape__links">
                <li><Link href="/">Início</Link></li>
                <li><Link href="/reservar">Reservar</Link></li>
                <li><Link href="/consultar-pontos">Meus pontos</Link></li>
                <li><Link href="/resgate_dos_premios">Prêmios</Link></li>
                <li><Link href="/termos-jornada-real">Regulamento</Link></li>
              </ul>
            </nav>

            <div className="jr-rodape__coluna">
              <h2 className="jr-rodape__titulo">Fale com a gente</h2>

              <span className="jr-rodape__canais">
                <a href={`tel:+${EMPRESA.whatsapp}`}>{EMPRESA.telefone}</a>
                <a
                  href={`https://wa.me/${EMPRESA.whatsapp}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Falar no WhatsApp"
                  className="jr-rodape__zap"
                >
                  <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true">
                    <path d="M12.04 2A9.9 9.9 0 0 0 2.1 11.9c0 1.75.46 3.45 1.32 4.95L2 22l5.28-1.38a9.9 9.9 0 0 0 4.76 1.21h.01a9.9 9.9 0 0 0 9.9-9.9A9.9 9.9 0 0 0 12.04 2zm5.8 14.06c-.24.68-1.4 1.3-1.94 1.34-.5.05-.98.23-3.3-.69-2.78-1.1-4.54-3.94-4.68-4.12-.13-.18-1.11-1.48-1.11-2.82 0-1.34.7-2 .95-2.27a1 1 0 0 1 .72-.34h.52c.17 0 .39-.6.6.46.24.58.8 2 .87 2.14.7.14.12.31.02.5-.1.18-.14.3-.28.46l-.42.49c-.14.14-.28.3-.12.58.16.28.72 1.18 1.54 1.91 1.06.94 1.95 1.24 2.23 1.38.28.14.44.12.6-.7.17-.2.7-.81.88-1.09.19-.28.37-.23.63-.14.25.1 1.63.77 1.9.91.29.14.47.21.54.33.07.12.07.68-.17 1.34z"/>
                  </svg>
                </a>
              </span>

              <a href={`mailto:${EMPRESA.email}`} className="jr-rodape__email">
                {EMPRESA.email}
              </a>
            </div>
          </div>

          <div className="jr-rodape__base">
            <p className="jr-rodape__legal">
              {EMPRESA.razaoSocial} · CNPJ {EMPRESA.cnpj}
            </p>
            <p className="jr-rodape__legal">
              © {new Date().getFullYear()} {EMPRESA.nomeFantasia}. Todos os direitos reservados.
            </p>
          </div>
        </div>
      </footer>

      <JornadaNav atual="/" />
    </main>
  )
}
