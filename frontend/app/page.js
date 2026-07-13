'use client'

import Link from 'next/link'
import {
  CalendarDays,
  Gift,
  Headphones,
  HelpCircle,
  Home,
  Menu,
  ShieldCheck,
  TrendingUp,
  User,
  Coins,
  Crown,
  Gem,
  Leaf,
} from 'lucide-react'
import GoldParticles from '@/components/GoldParticles'

const steps = [
  {
    icon: CalendarDays,
    label: 'Reserve',
    text: 'Hospede-se no Hotel Real Cabo Frio e aproveite.',
  },
  {
    icon: Coins,
    label: 'Acumule',
    text: 'Ganhe pontos a cada hospedagem e avance na sua jornada.',
  },
  {
    icon: Crown,
    label: 'Suba de nível',
    text: 'Quanto mais pontos, mais benefícios exclusivos.',
  },
  {
    icon: Gift,
    label: 'Resgate',
    text: 'Troque seus pontos por prêmios e experiências inesquecíveis.',
  },
]

const levels = [
  {
    icon: Leaf,
    name: 'Essência',
    level: 'Nível 1',
    text: 'Início da sua jornada no Hotel Real.',
  },
  {
    icon: Gem,
    name: 'Experiência',
    level: 'Nível 2',
    text: 'Mais vantagens e benefícios exclusivos para você.',
  },
  {
    icon: Crown,
    name: 'Exclusivo',
    level: 'Nível máximo',
    text: 'O mais alto nível de privilégio e recompensas do Hotel Real.',
  },
]

const assurances = [
  {
    icon: ShieldCheck,
    title: 'Segurança',
    text: 'Seus dados protegidos com total segurança.',
  },
  {
    icon: Headphones,
    title: 'Atendimento',
    text: 'Fale com nossa equipe sempre que precisar.',
  },
  {
    icon: CalendarDays,
    title: 'Reservas',
    text: 'As reservas devem ser feitas pelo canal oficial.',
  },
  {
    icon: HelpCircle,
    title: 'Dúvidas',
    text: 'Consulte nossas perguntas frequentes.',
  },
]

const navItems = [
  { icon: Home, label: 'Início', href: '/' },
  { icon: TrendingUp, label: 'Minha Jornada', href: '/consultar-pontos' },
  { icon: Gift, label: 'Prêmios', href: '/resgate_dos_premios' },
  { icon: User, label: 'Perfil', href: '/entrar-jornada-real' },
]

export default function JornadaReal() {
  return (
    <main className="jornada-page">
      <section className="hero">
        <div className="hero-bg" />
        <div className="hero-vignette" />
        <GoldParticles />

        <div className="hero-content">
          <header className="topbar">
            <button className="menu-button" type="button" aria-label="Abrir menu">
              <Menu size={42} strokeWidth={1.7} />
            </button>
          </header>

          <div className="hero-brand">
            <img
              src="/images/logo-jornada-real.png"
              alt="Hotel Real Cabo Frio - Jornada Real"
              className="hero-title-logo"
            />
          </div>

          <div className="hero-copy">
            <p>
              A cada estadia,
              <br />
              você avança na sua
              <br />
              Jornada Real.
            </p>
            <strong>O sonho é real</strong>
          </div>

          <div className="hero-actions">
            <Link href="/entrar-jornada-real" className="primary-cta">
              <span className="action-label">
                <span>Começar agora</span>
                <img className="button-crest jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
              </span>
              <span className="cta-arrow" aria-hidden="true">→</span>
            </Link>

            <Link href="/consultar-pontos" className="secondary-cta">
              <span className="action-label">
                <span>Ver meus pontos</span>
                <img className="button-crest jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
              </span>
              <User size={30} strokeWidth={1.7} />
            </Link>

            <Link href="/resgate_dos_premios" className="reward-card">
              <span className="reward-icon">
                <Gift size={52} strokeWidth={1.7} />
              </span>
              <span>
                <span className="action-label reward-title">
                  <span>Prêmios exclusivos</span>
                  <img className="button-crest jr-button-crest" src="/images/brasao-hotel-real-transparente.png?v=4" alt="" aria-hidden="true" />
                </span>
                <small>Resgates únicos para momentos inesquecíveis.</small>
              </span>
            </Link>
          </div>
        </div>
      </section>

      <section className="content-section">
        <div className="section-title">
          <Crown size={28} strokeWidth={1.7} />
          <h2>Como avançar na Jornada Real</h2>
          <Crown size={28} strokeWidth={1.7} />
        </div>

        <div className="steps-grid">
          {steps.map((step, index) => {
            const Icon = step.icon
            return (
              <article className="step-item" key={step.label}>
                <div className="step-icon">
                  <Icon size={58} strokeWidth={1.7} />
                  <span>{index + 1}</span>
                </div>
                <h3>{step.label}</h3>
                <p>{step.text}</p>
              </article>
            )
          })}
        </div>

        <div className="section-title levels-title">
          <Crown size={28} strokeWidth={1.7} />
          <h2>Seus níveis</h2>
        </div>

        <div className="levels-grid">
          {levels.map((level) => {
            const Icon = level.icon
            return (
              <article className="level-card" key={level.name}>
                <div className="hexagon">
                  <Icon size={50} strokeWidth={1.7} />
                </div>
                <div>
                  <h3>{level.name}</h3>
                  <strong>{level.level}</strong>
                  <span />
                  <p>{level.text}</p>
                </div>
              </article>
            )
          })}
        </div>

        <div className="assurance-grid">
          {assurances.map((item) => {
            const Icon = item.icon
            return (
              <article className="assurance-item" key={item.title}>
                <Icon size={50} strokeWidth={1.7} />
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </div>
              </article>
            )
          })}
        </div>

        <p className="closing-line">
          <Crown size={28} strokeWidth={1.7} />
          Hotel Real Cabo Frio: mais que um programa, um estilo de viver.
        </p>
      </section>

      <nav className="bottom-nav" aria-label="Navegação principal">
        {navItems.map((item, index) => {
          const Icon = item.icon
          return (
            <Link
              href={item.href}
              className={index === 0 ? 'active' : ''}
              key={item.label}
            >
              <Icon size={38} strokeWidth={1.7} />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      <style jsx global>{`
        .jornada-page {
          --gold: #f7c536;
          --gold-deep: #b87508;
          --text: #f8f2e7;
          --page-gutter: 24px;
          --hero-title: clamp(4.3rem, 8vw, 6.25rem);
          --hero-copy: clamp(1.62rem, 3.6vw, 2.25rem);
          --section-gap: 52px;
          min-height: 100vh;
          background:
            radial-gradient(circle at 50% 18%, rgba(128, 74, 16, 0.34), transparent 28rem),
            #030404;
          color: var(--text);
          font-family: 'Playfair Display', serif;
          overflow-x: hidden;
          padding-bottom: 0;
        }

        body:has(.jornada-page) button[aria-label^=Abrir][aria-label*=configura] {
          display: none;
        }

        body:has(.jornada-page) nextjs-portal {
          display: none;
        }

        .hero {
          position: relative;
          min-height: 760px;
          isolation: isolate;
        }

        .hero-bg {
          position: absolute;
          inset: 0;
          background-image: url('/images/background-jornada-real.jpeg');
          background-size: cover;
          background-position: 70% 0%;
          filter: saturate(1.18) contrast(1.08);
          z-index: -3;
        }

        .hero-vignette {
          position: absolute;
          inset: 0;
          background:
            linear-gradient(90deg, rgba(0, 0, 0, 0.96) 0%, rgba(0, 0, 0, 0.78) 36%, rgba(0, 0, 0, 0.18) 68%, rgba(0, 0, 0, 0.6) 100%),
            linear-gradient(180deg, rgba(0, 0, 0, 0.28) 0%, rgba(0, 0, 0, 0.24) 45%, #030404 100%);
          z-index: -2;
        }

        .hero-content,
        .content-section {
          width: min(1180px, calc(100% - (var(--page-gutter) * 2)));
          margin: 0 auto;
        }

        .hero-content {
          position: relative;
          z-index: 25;
          padding: 28px 0 44px;
        }

        .topbar {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          min-height: 166px;
        }

        .brand-logo {
          width: min(470px, 72vw);
          height: auto;
          object-fit: contain;
          filter: drop-shadow(0 6px 18px rgba(0, 0, 0, 0.78));
        }

        .menu-button {
          width: 64px;
          height: 64px;
          display: grid;
          place-items: center;
          color: var(--gold);
          background: transparent;
          border: 0;
          cursor: pointer;
          filter: drop-shadow(0 0 8px rgba(247, 197, 54, 0.5));
        }

        .hero-copy {
          width: min(490px, 100%);
          margin-top: 4px;
          text-shadow: 0 3px 12px rgba(0, 0, 0, 0.9);
        }

        .hero-brand {
          width: 100%;
          display: flex;
          justify-content: center;
          margin: -60px 0 30px;
        }

        .small-crown {
          color: var(--gold);
          margin-bottom: 16px;
          filter: drop-shadow(0 0 8px rgba(247, 197, 54, 0.6));
        }

        .hero-title-logo {
          display: block;
          width: min(500px, 94vw);
          height: auto;
          margin: 0;
          object-fit: contain;
          filter: drop-shadow(0 5px 18px rgba(0, 0, 0, 0.82));
        }

        .jornada-page h1 {
          color: var(--gold);
          font-size: var(--hero-title);
          font-weight: 600;
          line-height: 0.92;
          margin: 0 0 34px;
        }

        .jornada-page h1 span {
          display: block;
        }

        .hero-copy p {
          font-size: var(--hero-copy);
          line-height: 1.45;
          margin: 0;
        }

        .hero-copy strong {
          display: block;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(1.5rem, 3vw, 2.05rem);
          font-weight: 700;
          margin-top: 28px;
          text-transform: uppercase;
        }

        .hero-actions {
          display: grid;
          grid-template-columns: 1fr 1fr;
          grid-template-rows: auto auto;
          gap: 22px;
          align-items: stretch;
          margin-top: 28px;
          max-width: 100%;
        }

        .primary-cta,
        .secondary-cta,
        .reward-card {
          min-height: 90px;
          border-radius: 18px;
          font-family: 'Cinzel', serif;
          text-transform: uppercase;
          text-align: center;
          transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
        }

        .primary-cta:hover,
        .secondary-cta:hover,
        .reward-card:hover {
          transform: translateY(-2px);
        }

        .primary-cta {
          display: flex;
          align-items: center;
          justify-content: space-evenly;
          gap: 36px;
          color: #15100a;
          background: linear-gradient(180deg, #ffe17a 0%, #d99015 100%);
          border: 1px solid #ffdf70;
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55), 0 14px 30px rgba(0, 0, 0, 0.45);
          font-size: clamp(1.08rem, 2vw, 1.45rem);
          font-weight: 700;
        }

        .primary-cta .cta-arrow {
          font-family: Arial, sans-serif;
          font-size: 3rem;
          line-height: 0;
        }

        .action-label {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          min-width: 0;
        }

        .button-crest {
          width: 34px;
          height: 42px;
          flex: 0 0 34px;
          display: block;
          object-fit: contain;
          background: transparent;
          transform: translateX(18px);
          filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.35));
        }

        .secondary-cta {
          display: flex;
          align-items: center;
          justify-content: space-evenly;
          gap: 18px;
          color: #fff8ea;
          background: rgba(0, 0, 0, 0.34);
          border: 2px solid var(--gold);
          font-size: clamp(1rem, 1.8vw, 1.35rem);
          font-weight: 600;
        }

        .reward-card {
          grid-column: 2;
          grid-row: 1 / span 2;
          display: flex;
          align-items: center;
          gap: 24px;
          color: #fff8ea;
          background: rgba(0, 0, 0, 0.44);
          border: 2px solid var(--gold);
          padding: 28px 34px;
          text-transform: none;
        }

        .reward-icon {
          width: 116px;
          height: 116px;
          display: grid;
          place-items: center;
          color: var(--gold);
          clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
          border: 2px solid var(--gold);
          background: rgba(9, 9, 7, 0.75);
        }

        .reward-card span span {
          display: block;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(1.25rem, 2.1vw, 1.75rem);
          font-weight: 700;
          line-height: 1.15;
          text-transform: uppercase;
        }

        .reward-card .reward-title {
          display: inline-flex;
        }

        .reward-card .button-crest {
          display: block;
          text-transform: none;
          transform: translateX(-18px);
        }

        .reward-card small {
          display: block;
          margin-top: 12px;
          color: #f8f2e7;
          font-size: clamp(1.05rem, 1.8vw, 1.5rem);
          line-height: 1.38;
        }

        .content-section {
          position: relative;
          z-index: 30;
          padding: 28px 0 42px;
        }

        .section-title {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 22px;
          color: var(--gold);
          margin: 0 auto 28px;
          text-align: center;
        }

        .section-title h2 {
          font-family: 'Cinzel', serif;
          font-size: clamp(1.35rem, 2.8vw, 1.9rem);
          font-weight: 700;
          text-transform: uppercase;
        }

        .steps-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 36px;
          margin-bottom: var(--section-gap);
        }

        .step-item {
          position: relative;
          text-align: center;
        }

        .step-item:not(:last-child)::after {
          content: '';
          position: absolute;
          top: 72px;
          right: -36px;
          width: 72px;
          border-top: 6px dotted var(--gold);
          opacity: 0.95;
        }

        .step-icon {
          position: relative;
          width: 144px;
          height: 144px;
          display: grid;
          place-items: center;
          margin: 0 auto 24px;
          color: var(--gold);
          border: 3px solid var(--gold);
          border-radius: 50%;
          background: rgba(6, 6, 5, 0.72);
          box-shadow: 0 0 22px rgba(247, 197, 54, 0.16);
        }

        .step-icon span {
          position: absolute;
          bottom: -26px;
          left: 50%;
          width: 58px;
          height: 58px;
          display: grid;
          place-items: center;
          transform: translateX(-50%);
          color: #17110a;
          background: linear-gradient(180deg, #ffe27b, #d7961c);
          border-radius: 50%;
          font-family: 'Cinzel', serif;
          font-size: 1.65rem;
          font-weight: 700;
        }

        .step-item h3,
        .level-card h3,
        .assurance-item h3 {
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-weight: 700;
          text-transform: uppercase;
        }

        .step-item h3 {
          margin-top: 36px;
          font-size: clamp(1.25rem, 2.2vw, 1.65rem);
        }

        .step-item p {
          margin: 16px auto 0;
          max-width: 210px;
          font-size: clamp(1.05rem, 1.8vw, 1.34rem);
          line-height: 1.55;
        }

        .levels-title {
          margin-bottom: 24px;
        }

        .levels-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 22px;
          margin-bottom: 50px;
        }

        .level-card {
          min-height: 270px;
          display: grid;
          grid-template-columns: 112px 1fr;
          gap: 24px;
          align-items: center;
          padding: 30px;
          border: 1.5px solid var(--gold);
          border-radius: 8px;
          background:
            radial-gradient(circle at 22% 10%, rgba(196, 109, 20, 0.34), transparent 13rem),
            rgba(0, 0, 0, 0.35);
        }

        .hexagon {
          width: 106px;
          height: 118px;
          display: grid;
          place-items: center;
          color: #ffe27b;
          background: linear-gradient(145deg, rgba(255, 223, 107, 0.25), rgba(0, 0, 0, 0.62));
          clip-path: polygon(50% 0%, 94% 25%, 94% 75%, 50% 100%, 6% 75%, 6% 25%);
          filter: drop-shadow(0 0 10px rgba(247, 197, 54, 0.26));
        }

        .level-card h3 {
          font-size: clamp(1.24rem, 2.2vw, 1.75rem);
          margin-bottom: 10px;
        }

        .level-card strong {
          display: block;
          color: var(--gold);
          font-family: 'Cinzel', serif;
          font-size: clamp(1.05rem, 1.6vw, 1.35rem);
          text-transform: uppercase;
        }

        .level-card span {
          display: block;
          width: 40px;
          height: 3px;
          background: var(--gold);
          margin: 24px 0;
        }

        .level-card p {
          font-size: clamp(1rem, 1.55vw, 1.25rem);
          line-height: 1.45;
        }

        .assurance-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 20px;
          margin-bottom: 38px;
        }

        .assurance-item {
          display: grid;
          grid-template-columns: 58px 1fr;
          gap: 18px;
          align-items: start;
          color: var(--gold);
          border-right: 2px solid var(--gold);
          min-height: 110px;
          padding-right: 18px;
        }

        .assurance-item:last-child {
          border-right: 0;
        }

        .assurance-item h3 {
          font-size: clamp(0.94rem, 1.45vw, 1.18rem);
          margin-bottom: 10px;
        }

        .assurance-item p {
          color: #f8f2e7;
          font-size: clamp(0.9rem, 1.35vw, 1.05rem);
          line-height: 1.55;
        }

        .closing-line {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 16px;
          color: #ddd1bd;
          font-size: clamp(1.12rem, 2.4vw, 1.65rem);
          text-align: center;
        }

        .closing-line svg {
          color: var(--gold);
          flex: 0 0 auto;
        }

        .bottom-nav {
          position: relative;
          z-index: 60;
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          min-height: 104px;
          border-top: 1px solid var(--gold);
          background: linear-gradient(180deg, rgba(7, 7, 7, 0.94), rgba(0, 0, 0, 0.98));
          backdrop-filter: blur(14px);
        }

        .bottom-nav a {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 10px;
          color: rgba(248, 242, 231, 0.5);
          font-family: 'Cinzel', serif;
          font-size: clamp(0.78rem, 1.7vw, 1.05rem);
          text-transform: uppercase;
          text-align: center;
          white-space: nowrap;
        }

        .bottom-nav a.active {
          color: var(--gold);
        }

        .bottom-nav a.active svg {
          fill: var(--gold);
          filter: drop-shadow(0 0 10px rgba(247, 197, 54, 0.7));
        }

        @media (max-width: 900px) {
          .jornada-page {
            --page-gutter: 22px;
            --hero-title: clamp(4.2rem, 14vw, 5.45rem);
            --hero-copy: clamp(1.45rem, 5.5vw, 2rem);
            --section-gap: 46px;
          }

          .hero {
            min-height: 760px;
          }

          .hero-bg {
            background-position: 72% 0%;
          }

          .hero-vignette {
            background:
              linear-gradient(90deg, rgba(0, 0, 0, 0.98) 0%, rgba(0, 0, 0, 0.78) 48%, rgba(0, 0, 0, 0.24) 100%),
              linear-gradient(180deg, rgba(0, 0, 0, 0.22) 0%, rgba(0, 0, 0, 0.42) 54%, #030404 100%);
          }

          .topbar {
            min-height: 136px;
          }

          .hero-actions,
          .steps-grid,
          .levels-grid,
          .assurance-grid {
            grid-template-columns: 1fr;
          }

          .reward-card {
            grid-column: auto;
            grid-row: auto;
          }

          .step-item:not(:last-child)::after {
            display: none;
          }

          .levels-grid,
          .assurance-grid {
            gap: 16px;
          }

          .content-section {
            padding-top: 34px;
          }

          .assurance-item {
            border-right: 0;
            border-bottom: 1px solid rgba(247, 197, 54, 0.62);
            padding-bottom: 16px;
          }

          .assurance-item:last-child {
            border-bottom: 0;
          }
        }

        @media (max-width: 560px) {
          .jornada-page {
            --page-gutter: clamp(16px, 4.4vw, 20px);
            --hero-title: clamp(3.95rem, 15.4vw, 4.8rem);
            --hero-copy: clamp(1.42rem, 6vw, 1.72rem);
            padding-bottom: 0;
          }

          .hero {
            min-height: max(790px, 100svh);
          }

          .hero-bg {
            background-position: 69% top;
            background-size: auto 100%;
          }

          .hero-content {
            padding: 20px 0 44px;
          }

          .brand-logo {
            width: clamp(258px, 72vw, 326px);
          }

          .menu-button {
            width: 48px;
            height: 48px;
          }

          .menu-button svg {
            width: 36px;
            height: 36px;
          }

          .hero-title-logo {
            width: min(410px, 92vw);
          }

          .hero-brand {
            margin-bottom: 24px;
          }

          .small-crown {
            width: 38px;
            height: 38px;
            margin-bottom: 14px;
          }

          .hero-copy strong {
            margin-top: 22px;
            font-size: clamp(1.28rem, 5.2vw, 1.55rem);
          }

          .hero-actions {
            gap: 16px;
            margin-top: 26px;
          }

          .primary-cta,
          .secondary-cta {
            min-height: 78px;
            border-radius: 14px;
            padding: 0 18px;
          }

          .primary-cta {
            gap: 12px;
            font-size: clamp(0.98rem, 4vw, 1.12rem);
          }

          .primary-cta .cta-arrow {
            font-size: 2.4rem;
          }

          .secondary-cta {
            font-size: clamp(0.92rem, 3.7vw, 1.08rem);
          }

          .secondary-cta svg {
            flex: 0 0 auto;
          }

          .reward-card {
            min-height: 130px;
            gap: 16px;
            padding: 18px;
            border-radius: 14px;
          }

          .reward-icon {
            width: 82px;
            height: 82px;
            flex: 0 0 82px;
          }

          .reward-card span span {
            font-size: clamp(1rem, 4.5vw, 1.22rem);
          }

          .reward-card small {
            font-size: clamp(0.88rem, 3.8vw, 1.02rem);
          }

          .steps-grid {
            gap: 42px;
          }

          .step-icon {
            width: 128px;
            height: 128px;
          }

          .step-icon svg {
            width: 52px;
            height: 52px;
          }

          .step-icon span {
            width: 52px;
            height: 52px;
            bottom: -24px;
            font-size: 1.45rem;
          }

          .step-item h3 {
            font-size: 1.24rem;
            margin-top: 32px;
          }

          .step-item p {
            max-width: 240px;
            font-size: 1.04rem;
          }

          .level-card {
            grid-template-columns: 86px 1fr;
            gap: 18px;
            min-height: 210px;
            padding: 22px;
          }

          .hexagon {
            width: 84px;
            height: 94px;
          }

          .level-card h3 {
            font-size: clamp(1.08rem, 4.8vw, 1.3rem);
          }

          .level-card strong {
            font-size: clamp(0.94rem, 4vw, 1.08rem);
          }

          .level-card p {
            font-size: clamp(0.96rem, 3.9vw, 1.06rem);
          }

          .assurance-item {
            grid-template-columns: 56px 1fr;
            gap: 16px;
            min-height: auto;
            padding: 14px 0 22px;
          }

          .closing-line {
            align-items: flex-start;
            padding: 22px 4px 26px;
            line-height: 1.35;
          }

          .bottom-nav {
            min-height: 86px;
          }

          .bottom-nav a {
            gap: 7px;
            font-size: clamp(0.54rem, 2.55vw, 0.68rem);
          }

          .bottom-nav svg {
            width: 30px;
            height: 30px;
          }
        }

        @media (max-width: 390px) {
          .jornada-page {
            --hero-title: clamp(3.6rem, 15.8vw, 4.05rem);
            --hero-copy: clamp(1.25rem, 5.75vw, 1.42rem);
          }

          .hero {
            min-height: max(760px, 100svh);
          }

          .topbar {
            min-height: 118px;
          }

          .brand-logo {
            width: 244px;
          }

          .hero-title-logo {
            width: min(370px, 90vw);
          }

          .primary-cta,
          .secondary-cta {
            min-height: 72px;
          }

          .reward-card {
            padding: 16px;
          }

          .reward-icon {
            width: 72px;
            height: 72px;
            flex-basis: 72px;
          }

          .reward-icon svg {
            width: 42px;
            height: 42px;
          }

          .level-card {
            grid-template-columns: 72px 1fr;
            gap: 15px;
            padding: 18px;
          }

          .hexagon {
            width: 72px;
            height: 82px;
          }

          .bottom-nav a {
            font-size: 0.52rem;
          }
        }

        @media (max-width: 360px) {
          .jornada-page {
            --page-gutter: 14px;
            --hero-title: 3.45rem;
            --hero-copy: 1.2rem;
          }

          .hero {
            min-height: max(730px, 100svh);
          }

          .topbar {
            min-height: 108px;
          }

          .brand-logo {
            width: 228px;
          }

          .hero-title-logo {
            width: min(340px, 90vw);
          }

          .primary-cta,
          .secondary-cta {
            padding: 0 14px;
          }

          .primary-cta {
            font-size: 0.88rem;
          }

          .secondary-cta {
            font-size: 0.82rem;
          }

          .reward-card {
            gap: 12px;
          }

          .reward-card span span {
            font-size: 0.94rem;
          }

          .reward-card small {
            font-size: 0.82rem;
          }

          .bottom-nav svg {
            width: 26px;
            height: 26px;
          }
        }
      `}</style>
    </main>
  )
}
