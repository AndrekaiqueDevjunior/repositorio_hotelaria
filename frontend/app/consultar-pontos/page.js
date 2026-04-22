'use client'

import { useRef } from 'react'

const rewards = [
  { name: 'Tecnologia Real', points: 90, icon: '📱', image: '/images/premios/tecnologia-real.png' },
  { name: 'Rituais do Real', points: 35, icon: '☕', image: '/images/premios/rituais-do-real.png' },
  { name: 'O Retorno do Sonho', points: 25, icon: '🛁', image: '/images/premios/o-retorno-do-sonho.png' },
]

export default function JornadaReal() {
  const rewardsRef = useRef(null)
  const currentPoints = 36
  const nextReward = 50
  const progressPercent = Math.min((currentPoints / nextReward) * 100, 100)
  const missing = Math.max(nextReward - currentPoints, 0)

  const handleBenefits = () => {
    rewardsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const handleReward = (reward) => {
    const diff = reward.points - currentPoints
    if (diff <= 0) {
      alert(`Você já pode resgatar: ${reward.name}.`)
      return
    }
    alert(`Faltam ${diff} pontos para resgatar "${reward.name}".`)
  }

  const handleAllRewards = () => {
    const list = rewards.map((reward) => `${reward.name} — ${reward.points} pts`).join('\n')
    alert(`Prêmios disponíveis:\n\n${list}`)
  }

  return (
    <div className="jornada-page">
      <main className="phone">
        <header className="topbar">
          <button className="circle-btn" aria-label="Abrir menu" type="button">☰</button>
          <div className="logo-wrap">
            <img src="/images/logo-jornada-real.png" alt="Hotel Real Cabo Frio - Jornada Real" />
          </div>
          <button className="circle-btn" aria-label="Notificações" type="button">
            🔔<span className="notif-dot" />
          </button>
        </header>

        <section className="card welcome">
          <div className="welcome-main">
            <div className="avatar-glow" aria-hidden="true" />
            <div>
              <h1>Bem-vindo, João! 👑</h1>
              <p>Cada estadia te leva mais longe.</p>
              <p>Mais pontos, mais benefícios,</p>
              <p>mais experiências inesquecíveis.</p>
            </div>
          </div>

          <aside className="points-box">
            <div className="points-label">⭐ Seus pontos</div>
            <div className="points-value">{currentPoints}</div>
            <div className="points-label points-spacer">Troque por benefícios incríveis!</div>
            <button className="mini-btn" onClick={handleBenefits} type="button">🎁 Ver benefícios</button>
          </aside>
        </section>

        <section className="card">
          <h2 className="progress-title">Seu progresso: RUMO AO NÍVEL EXCLUSIVO 🚀</h2>
          <div className="levels">
            <div className="level">
              <div className="level-icon">🍃</div>
              <h3>ESSÊNCIA</h3>
              <span className="range">0 – 499 pts</span>
              <div className="desc">Descubra o começo</div>
              <div className="status-dot active" />
            </div>
            <div className="level">
              <div className="level-icon">💎</div>
              <h3>EXPERIÊNCIA</h3>
              <span className="range">500 – 1499 pts</span>
              <div className="desc">Viva mais experiências</div>
              <div className="status-dot current" />
            </div>
            <div className="level">
              <div className="level-icon">👑</div>
              <h3>EXCLUSIVO</h3>
              <span className="range">1500+ pts</span>
              <div className="desc">O topo te espera</div>
              <div className="status-dot" />
            </div>
          </div>
        </section>

        <section className="card">
          <h2 className="progress-title">
            {missing > 0 ? `Faltam ${missing} pontos para o próximo prêmio!` : 'Você já alcançou o próximo prêmio!'}
          </h2>
          <div className="progress-row">
            <div className="bar-column">
              <div className="bar-wrap" aria-label="Progresso até o próximo prêmio">
                <div className="bar-fill" style={{ width: `${progressPercent}%` }} />
                <div className="bar-text">{currentPoints} / {nextReward}</div>
              </div>
            </div>
            <div className="tub-img" aria-label="O Retorno do Sonho">
              <img src="/images/premios/o-retorno-do-sonho.png" alt="" />
            </div>
          </div>
          <div className="slogan">Reserve, Acumule, Conquiste.</div>
        </section>

        <section className="card" ref={rewardsRef}>
          <h2 className="section-title">🎁 Prêmios em destaque</h2>
          <div className="rewards">
            {rewards.map((reward) => (
              <article
                className="reward-item"
                key={reward.name}
                onClick={() => handleReward(reward)}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    handleReward(reward)
                  }
                }}
              >
                <div className="reward-thumb" aria-hidden="true">
                  {reward.image ? (
                    <img src={reward.image} alt="" />
                  ) : (
                    reward.icon
                  )}
                </div>
                <div>
                  <h3 className="reward-name">{reward.name}</h3>
                  <p className="reward-sub">{reward.points} pts</p>
                </div>
                <div className="points-chip">{reward.points}<br />pts</div>
              </article>
            ))}
          </div>
          <button className="mini-btn all-btn" onClick={handleAllRewards} type="button">🎁 Ver todos os prêmios</button>
        </section>

        <section className="card stats">
          <div className="stat">
            <div className="stat-emoji">🔥</div>
            <div>
              <small>Sequência atual</small>
              <strong>🚀 3 estadias seguidas</strong>
              <span>Continue assim para chegar no próximo nível!</span>
            </div>
          </div>
          <div className="stat">
            <div className="stat-emoji">✨</div>
            <div>
              <small>Bônus de Nível Experiência</small>
              <strong>+10% pontos</strong>
              <span>Mais vantagens para cada nova reserva.</span>
            </div>
          </div>
        </section>

        <section className="card bottom-cta">
          <div className="cta-box">
            <h2 className="cta-title">Continue sua jornada e alcance o topo!</h2>
            <button
              className="primary-btn"
              onClick={() => alert('Ação de reserva iniciada. Integre este botão com sua rota de checkout ou página de reservas.')}
              type="button"
            >
              FAZER NOVA RESERVA
            </button>
          </div>
          <button
            className="bottom-icon"
            onClick={() => alert('Central de notificações.')}
            aria-label="Abrir notificações"
            type="button"
          >
            🔔
          </button>
        </section>

        <div className="home-indicator" />
      </main>

      <style jsx>{`
        .jornada-page {
          --bg: #050302;
          --panel: #0a0705;
          --panel-2: #120b07;
          --gold: #f5c465;
          --gold-2: #d7962e;
          --gold-3: #8d5a10;
          --line: rgba(232, 167, 61, 0.55);
          --soft: rgba(255, 212, 132, 0.88);
          --text: #f4d28a;
          --muted: #d3ae6d;
          --shadow: 0 0 16px rgba(243, 173, 54, 0.2), inset 0 0 14px rgba(255, 195, 92, 0.06);
          min-height: 100vh;
          padding: 14px;
          display: flex;
          justify-content: center;
          color: var(--text);
          font-family: Georgia, "Times New Roman", serif;
          background:
            radial-gradient(circle at 50% -5%, rgba(247,178,65,0.14), transparent 35%),
            radial-gradient(circle at 50% 10%, rgba(247,178,65,0.05), transparent 25%),
            linear-gradient(180deg, #140c06 0%, #070403 14%, #030202 100%);
        }

        .phone {
          width: 100%;
          max-width: 430px;
          background: linear-gradient(180deg, rgba(17,11,7,0.98), rgba(6,4,3,0.99));
          border: 1.5px solid var(--line);
          border-radius: 28px;
          padding: 14px 14px 26px;
          box-shadow: var(--shadow);
          position: relative;
          overflow: hidden;
        }

        .phone::before {
          content: "";
          position: absolute;
          inset: 0;
          background: radial-gradient(circle at 50% 0%, rgba(255, 186, 59, 0.08), transparent 30%);
          pointer-events: none;
        }

        .topbar,
        .bottom-cta {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
        }

        .circle-btn {
          width: 54px;
          height: 54px;
          border-radius: 50%;
          border: 1.5px solid rgba(240, 174, 65, 0.35);
          display: grid;
          place-items: center;
          color: var(--gold);
          background: radial-gradient(circle at 50% 35%, rgba(255,187,84,0.11), rgba(0,0,0,0.65));
          box-shadow: inset 0 0 12px rgba(255, 187, 84, 0.08);
          font-size: 26px;
          position: relative;
          flex: 0 0 auto;
          cursor: pointer;
          font-family: inherit;
        }

        .notif-dot {
          position: absolute;
          top: 8px;
          right: 8px;
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #ff5d52;
          box-shadow: 0 0 10px rgba(255, 98, 71, 0.8);
        }

        .logo-wrap {
          text-align: center;
          flex: 1;
          min-width: 0;
        }

        .logo-wrap img {
          width: 250px;
          max-width: 100%;
          display: block;
          margin: 0 auto 6px;
          filter: drop-shadow(0 0 10px rgba(255, 192, 73, 0.18));
        }

        .brand-script {
          font-size: 1.1rem;
          color: #f6cc7a;
          font-style: italic;
          text-shadow: 0 0 10px rgba(255, 190, 78, 0.35);
        }

        .card {
          background: linear-gradient(180deg, rgba(10, 7, 5, 0.97), rgba(6, 4, 3, 0.98));
          border: 1.2px solid var(--line);
          border-radius: 22px;
          padding: 16px;
          box-shadow: var(--shadow);
          margin-top: 14px;
          position: relative;
        }

        .welcome {
          display: grid;
          grid-template-columns: 1fr;
          gap: 14px;
        }

        .welcome-main {
          display: flex;
          gap: 14px;
          align-items: center;
        }

        .avatar-glow {
          width: 92px;
          height: 92px;
          border-radius: 50%;
          border: 2px solid #e9aa3f;
          background:
            radial-gradient(circle at 50% 28%, #f1c06c 0 12px, transparent 13px),
            radial-gradient(circle at 50% 61%, #dda044 0 20px, transparent 21px),
            radial-gradient(circle at 50% 50%, rgba(255,193,84,0.08), rgba(0,0,0,0.95));
          box-shadow: 0 0 18px rgba(255, 176, 58, 0.34), inset 0 0 18px rgba(255, 176, 58, 0.08);
          position: relative;
          flex: 0 0 auto;
        }

        .avatar-glow::before {
          content: "👑";
          position: absolute;
          top: -20px;
          left: 50%;
          transform: translateX(-50%);
          font-size: 20px;
          filter: drop-shadow(0 0 8px rgba(255, 198, 86, 0.8));
        }

        .welcome h1,
        .section-title,
        .progress-title,
        .cta-title {
          margin: 0;
          font-weight: 700;
        }

        .welcome h1 {
          font-size: 1.05rem;
          line-height: 1.15;
          margin-bottom: 8px;
        }

        .welcome p {
          margin: 0;
          line-height: 1.35;
          color: #edd3a0;
          font-size: 0.86rem;
        }

        .points-box {
          border: 1.2px solid rgba(236, 170, 64, 0.48);
          border-radius: 18px;
          padding: 14px;
          background: linear-gradient(180deg, rgba(69,39,9,0.55), rgba(18,10,5,0.8));
          text-align: center;
          box-shadow: inset 0 0 14px rgba(255, 185, 71, 0.06);
        }

        .points-label {
          color: #f2dfbf;
          font-size: 0.9rem;
        }

        .points-spacer {
          margin-bottom: 12px;
        }

        .points-value {
          font-size: 3rem;
          line-height: 1;
          margin: 6px 0 8px;
          color: #f5c465;
          text-shadow: 0 0 10px rgba(255, 183, 68, 0.18);
        }

        .mini-btn,
        .primary-btn {
          border: 1.2px solid rgba(235, 171, 69, 0.45);
          border-radius: 14px;
          cursor: pointer;
          transition: 0.2s ease;
          font-family: inherit;
        }

        .mini-btn {
          padding: 10px 14px;
          color: var(--gold);
          font-weight: 700;
          background: rgba(9, 7, 5, 0.82);
          width: 100%;
          font-size: 1rem;
        }

        .mini-btn:hover,
        .primary-btn:hover,
        .reward-item:hover {
          transform: translateY(-1px);
          box-shadow: 0 0 12px rgba(255, 190, 81, 0.16);
        }

        .progress-title,
        .section-title,
        .cta-title {
          text-align: center;
          font-size: 0.98rem;
          margin-bottom: 14px;
          color: #eebd67;
        }

        .levels {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
          text-align: center;
          align-items: start;
          position: relative;
          padding-top: 22px;
        }

        .levels::before {
          content: "";
          position: absolute;
          left: 8%;
          right: 8%;
          top: 46px;
          height: 4px;
          border-radius: 999px;
          background: linear-gradient(90deg, #f0b74f 0%, #f9dd97 42%, rgba(126,81,16,0.4) 43%, rgba(126,81,16,0.35) 100%);
          box-shadow: 0 0 14px rgba(255, 188, 77, 0.28);
          z-index: 0;
        }

        .level {
          position: relative;
          z-index: 1;
          padding: 0 4px;
        }

        .level-icon {
          width: 58px;
          height: 58px;
          border-radius: 50%;
          margin: 0 auto 10px;
          border: 1.5px solid rgba(239, 175, 67, 0.55);
          display: grid;
          place-items: center;
          font-size: 1.5rem;
          background: radial-gradient(circle at 50% 35%, rgba(255,194,87,0.4), rgba(89,47,8,0.85));
          box-shadow: inset 0 0 12px rgba(255, 196, 87, 0.16);
        }

        .level:nth-child(2) .level-icon {
          background: radial-gradient(circle at 50% 35%, rgba(255,172,63,0.6), rgba(159,73,6,0.88));
        }

        .level:nth-child(3) .level-icon {
          background: radial-gradient(circle at 50% 35%, rgba(255,221,93,0.65), rgba(162,112,6,0.9));
        }

        .level h3 {
          margin: 0;
          font-size: 0.78rem;
          color: #f0c979;
        }

        .level .range {
          display: block;
          margin-top: 6px;
          font-size: 0.62rem;
          font-weight: 700;
          color: #f3d59b;
        }

        .level .desc {
          margin-top: 6px;
          font-size: 0.58rem;
          line-height: 1.3;
          color: #d7ae6e;
          min-height: 28px;
        }

        .status-dot {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          margin: 10px auto 0;
          border: 1.2px solid rgba(255, 190, 75, 0.45);
          background: transparent;
          box-shadow: inset 0 0 8px rgba(255, 190, 75, 0.08);
        }

        .status-dot.active {
          background: #34c759;
          box-shadow: 0 0 10px rgba(52,199,89,0.7);
          border-color: #34c759;
        }

        .status-dot.current {
          background: #f3a43d;
          box-shadow: 0 0 10px rgba(243,164,61,0.7);
          border-color: #f3a43d;
        }

        .bar-wrap {
          background: linear-gradient(90deg, rgba(251,223,154,0.92), rgba(114,67,14,0.7));
          border-radius: 999px;
          padding: 3px;
          position: relative;
          overflow: hidden;
          height: 34px;
          margin-top: 10px;
          border: 1px solid rgba(255, 201, 105, 0.18);
        }

        .bar-fill {
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          border-radius: 999px;
          background: linear-gradient(90deg, #fbe4a2, #ebb14f 70%, #ffd87e 100%);
          box-shadow: 0 0 18px rgba(255, 194, 76, 0.28);
        }

        .bar-text {
          position: absolute;
          inset: 0;
          display: grid;
          place-items: center;
          font-weight: 700;
          color: #432300;
          font-size: 0.95rem;
          z-index: 2;
        }

        .progress-row {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .bar-column {
          flex: 1;
        }

        .tub-img {
          width: 74px;
          height: 74px;
          display: grid;
          place-items: center;
          filter: drop-shadow(0 0 14px rgba(255, 176, 67, 0.2));
          border-radius: 18px;
          background: radial-gradient(circle at 50% 40%, rgba(255,188,79,0.12), rgba(0,0,0,0.35));
          overflow: hidden;
        }

        .tub-img img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .slogan {
          margin-top: 10px;
          text-align: center;
          font-size: 0.95rem;
          color: #f0c672;
          font-weight: 700;
        }

        .rewards {
          display: grid;
          gap: 12px;
        }

        .reward-item {
          display: grid;
          grid-template-columns: 96px 1fr 78px;
          gap: 12px;
          align-items: center;
          border: 1px solid rgba(232, 167, 61, 0.45);
          border-radius: 18px;
          padding: 10px;
          background: linear-gradient(180deg, rgba(18,11,8,0.95), rgba(11,7,4,0.95));
          transition: 0.2s ease;
          cursor: pointer;
        }

        .reward-thumb {
          width: 100%;
          height: 84px;
          border-radius: 14px;
          background: radial-gradient(circle at 50% 40%, rgba(255,188,79,0.08), rgba(0,0,0,0.45));
          display: grid;
          place-items: center;
          font-size: 2.35rem;
          overflow: hidden;
        }

        .reward-thumb img {
          width: 100%;
          height: 100%;
          object-fit: contain;
          filter: drop-shadow(0 0 10px rgba(255, 190, 81, 0.16));
        }

        .reward-name {
          font-size: 0.95rem;
          margin: 0 0 6px;
          color: #f3d394;
        }

        .reward-sub {
          color: #d8ae67;
          font-size: 0.82rem;
          margin: 0;
        }

        .points-chip {
          border: 1.2px solid rgba(235, 171, 69, 0.42);
          border-radius: 16px;
          text-align: center;
          padding: 10px 8px;
          color: #f5d18c;
          font-size: 0.8rem;
          line-height: 1.05;
          background: linear-gradient(180deg, rgba(84,47,10,0.4), rgba(18,11,7,0.85));
          min-width: 70px;
        }

        .all-btn {
          margin-top: 14px;
          width: 100%;
          background: rgba(11, 8, 6, 0.92);
          color: var(--gold);
          padding: 12px 16px;
          font-weight: 700;
          font-size: 1rem;
        }

        .stats {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0;
          overflow: hidden;
        }

        .stat {
          padding: 8px 10px;
          display: flex;
          gap: 10px;
          align-items: center;
          min-height: 92px;
        }

        .stat + .stat {
          border-left: 1px solid rgba(234, 170, 64, 0.22);
        }

        .stat-emoji {
          font-size: 2rem;
          filter: drop-shadow(0 0 8px rgba(255, 173, 58, 0.34));
        }

        .stat small {
          color: #eadcc0;
          display: block;
          font-size: 0.76rem;
          margin-bottom: 4px;
        }

        .stat strong {
          display: block;
          font-size: 0.92rem;
          color: #efc878;
          margin-bottom: 4px;
        }

        .stat span {
          color: #dcb36d;
          font-size: 0.73rem;
          line-height: 1.25;
        }

        .bottom-cta {
          margin-top: 14px;
          gap: 10px;
          align-items: end;
        }

        .cta-box {
          flex: 1;
        }

        .cta-title {
          margin-bottom: 10px;
        }

        .primary-btn {
          width: 100%;
          padding: 16px;
          font-size: 1.15rem;
          font-weight: 700;
          color: #342000;
          background: linear-gradient(180deg, #f8d57f 0%, #e4a94a 100%);
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.3), 0 0 14px rgba(255, 188, 74, 0.16);
        }

        .bottom-icon {
          width: 58px;
          height: 58px;
          border-radius: 16px;
          border: 1.2px solid rgba(235, 171, 69, 0.45);
          background: rgba(11, 8, 6, 0.92);
          color: var(--gold);
          font-size: 1.55rem;
          display: grid;
          place-items: center;
          cursor: pointer;
          font-family: inherit;
        }

        .home-indicator {
          width: 140px;
          height: 6px;
          background: rgba(255,255,255,0.9);
          border-radius: 999px;
          margin: 14px auto 0;
        }

        @media (min-width: 390px) {
          .welcome {
            grid-template-columns: 1.5fr 1fr;
          }

          .welcome-main {
            align-items: center;
          }

          .welcome h1 {
            font-size: 1.18rem;
          }

          .level h3 {
            font-size: 0.95rem;
          }

          .level .range {
            font-size: 0.78rem;
          }

          .level .desc {
            font-size: 0.68rem;
          }

          .reward-name {
            font-size: 1.06rem;
          }

          .reward-sub {
            font-size: 0.95rem;
          }
        }
      `}</style>
    </div>
  )
}
