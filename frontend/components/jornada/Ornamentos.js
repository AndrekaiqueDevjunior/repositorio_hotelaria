/*
 * Ornamentos da Jornada Real.
 *
 * Desenhados em SVG para escalarem sem perder fio, receberem o degradê de ouro
 * do logotipo e não dependerem de banco de imagem. Nenhum carrega informação:
 * todos entram com aria-hidden e quem fala é o texto ao lado.
 */

function Ouro({ id, escuro = false }) {
  return (
    <linearGradient id={id} x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0%" stopColor={escuro ? '#c8a256' : '#fbeec4'} />
      <stop offset="26%" stopColor={escuro ? '#9c7530' : '#e7c675'} />
      <stop offset="54%" stopColor={escuro ? '#6d5320' : '#cd9b40'} />
      <stop offset="78%" stopColor={escuro ? '#4a3714' : '#8f6c26'} />
      <stop offset="100%" stopColor={escuro ? '#8a6a2c' : '#e2c37e'} />
    </linearGradient>
  )
}

/* ------------------------------------------------------------------ coroa */

export function Coroa({ className = '', tamanho = 56 }) {
  return (
    <svg className={className} width={tamanho} height={(tamanho * 80) / 120}
      viewBox="0 0 120 80" fill="none" aria-hidden="true" focusable="false">
      <defs><Ouro id="jr-o-coroa" /><Ouro id="jr-o-coroa-e" escuro /></defs>
      <path d="M14 58 L26 22 L42 46 L60 12 L78 46 L94 22 L106 58 Z" fill="url(#jr-o-coroa)" />
      <circle cx="26" cy="17" r="5.5" fill="url(#jr-o-coroa)" />
      <circle cx="60" cy="7" r="6" fill="url(#jr-o-coroa)" />
      <circle cx="94" cy="17" r="5.5" fill="url(#jr-o-coroa)" />
      <path d="M12 58 H108 L104 72 H16 Z" fill="url(#jr-o-coroa-e)" />
      <circle cx="40" cy="65" r="3" fill="#2b0508" />
      <circle cx="60" cy="65" r="3.4" fill="#5a0d14" />
      <circle cx="80" cy="65" r="3" fill="#2b0508" />
    </svg>
  )
}

/* --------------------------------------------------------------- fleurão */

export function Fleurao({ className = '', largura = 420 }) {
  return (
    <svg className={className} width={largura} height="18" viewBox="0 0 420 18"
      fill="none" aria-hidden="true" focusable="false" preserveAspectRatio="xMidYMid meet">
      <defs><Ouro id="jr-o-fleurao" /></defs>
      <path d="M0 9 H150" stroke="url(#jr-o-fleurao)" strokeWidth="1" opacity="0.5" />
      <path d="M270 9 H420" stroke="url(#jr-o-fleurao)" strokeWidth="1" opacity="0.5" />
      <path d="M156 9 q10 -7 20 0 q-10 7 -20 0 Z" fill="url(#jr-o-fleurao)" />
      <path d="M264 9 q-10 -7 -20 0 q10 7 20 0 Z" fill="url(#jr-o-fleurao)" />
      <circle cx="186" cy="9" r="2.2" fill="url(#jr-o-fleurao)" />
      <circle cx="234" cy="9" r="2.2" fill="url(#jr-o-fleurao)" />
      <path d="M210 0 L220 9 L210 18 L200 9 Z" fill="url(#jr-o-fleurao)" />
      <path d="M210 4.4 L215.6 9 L210 13.6 L204.4 9 Z" fill="#000" opacity="0.6" />
    </svg>
  )
}

/* ------------------------------------------------------------- chave antiga */

export function Chave({ className = '', altura = 420 }) {
  return (
    <svg className={className} width={(altura * 120) / 420} height={altura}
      viewBox="0 0 120 420" fill="none" aria-hidden="true" focusable="false">
      <defs><Ouro id="jr-o-chave" /><Ouro id="jr-o-chave-e" escuro /></defs>

      {/* finial: pequena flor-de-lis coroando a argola */}
      <path d="M60 4 L66 18 L60 26 L54 18 Z" fill="url(#jr-o-chave)" />
      <path d="M48 20 q12 -6 12 6 q0 -12 12 -6 q-6 10 -12 10 q-6 0 -12 -10 Z" fill="url(#jr-o-chave-e)" />

      {/* argola ornamentada */}
      <circle cx="60" cy="70" r="38" fill="none" stroke="url(#jr-o-chave)" strokeWidth="9" />
      <circle cx="60" cy="70" r="38" fill="none" stroke="url(#jr-o-chave-e)" strokeWidth="1.4" opacity="0.9" />
      <circle cx="60" cy="70" r="27" fill="none" stroke="url(#jr-o-chave-e)" strokeWidth="1.6" />
      {/* volutas laterais */}
      <path d="M22 70 q-14 -12 -4 -22 q10 -8 14 6" fill="none" stroke="url(#jr-o-chave)" strokeWidth="4.5" strokeLinecap="round" />
      <path d="M98 70 q14 -12 4 -22 q-10 -8 -14 6" fill="none" stroke="url(#jr-o-chave)" strokeWidth="4.5" strokeLinecap="round" />
      <path d="M22 70 q-14 12 -4 22 q10 8 14 -6" fill="none" stroke="url(#jr-o-chave)" strokeWidth="4.5" strokeLinecap="round" />
      <path d="M98 70 q14 12 4 22 q-10 8 -14 -6" fill="none" stroke="url(#jr-o-chave)" strokeWidth="4.5" strokeLinecap="round" />
      {/* pérolas na argola */}
      <circle cx="60" cy="36" r="3.4" fill="url(#jr-o-chave)" />
      <circle cx="36" cy="94" r="3" fill="url(#jr-o-chave)" />
      <circle cx="84" cy="94" r="3" fill="url(#jr-o-chave)" />

      {/* colar */}
      <rect x="46" y="112" width="28" height="9" rx="1" fill="url(#jr-o-chave)" />
      <rect x="50" y="124" width="20" height="6" rx="1" fill="url(#jr-o-chave-e)" />
      <rect x="47" y="134" width="26" height="5" rx="1" fill="url(#jr-o-chave)" />

      {/* haste */}
      <rect x="54" y="139" width="12" height="228" fill="url(#jr-o-chave)" />
      <rect x="58.5" y="139" width="3" height="228" fill="url(#jr-o-chave-e)" opacity="0.55" />
      {/* nó ornamental no meio da haste */}
      <rect x="45" y="236" width="30" height="8" rx="1" fill="url(#jr-o-chave-e)" />
      <circle cx="40" cy="240" r="4" fill="url(#jr-o-chave)" />
      <circle cx="80" cy="240" r="4" fill="url(#jr-o-chave)" />

      {/* palhetão */}
      <rect x="66" y="300" width="30" height="13" fill="url(#jr-o-chave)" />
      <rect x="66" y="326" width="40" height="13" fill="url(#jr-o-chave)" />
      <rect x="86" y="313" width="20" height="13" fill="url(#jr-o-chave-e)" />
      <rect x="66" y="352" width="24" height="12" fill="url(#jr-o-chave)" />
      {/* ponta */}
      <path d="M54 367 L66 367 L60 382 Z" fill="url(#jr-o-chave-e)" />
    </svg>
  )
}

/* ------------------------------------------------------------------ bússola */

export function Bussola({ className = '', tamanho = 260 }) {
  const ticks = []
  for (let i = 0; i < 72; i++) {
    const ang = (i * 5 * Math.PI) / 180
    const grande = i % 9 === 0
    const r1 = grande ? 96 : 101
    const r2 = 108
    // arredondado: sem isso o servidor e o cliente divergem no último decimal
    // e o React acusa erro de hidratação
    ticks.push(
      <line
        key={i}
        x1={(120 + r1 * Math.sin(ang)).toFixed(3)}
        y1={(120 - r1 * Math.cos(ang)).toFixed(3)}
        x2={(120 + r2 * Math.sin(ang)).toFixed(3)}
        y2={(120 - r2 * Math.cos(ang)).toFixed(3)}
        stroke="url(#jr-o-bussola-e)"
        strokeWidth={grande ? 2 : 0.8}
        opacity={grande ? 0.95 : 0.55}
      />
    )
  }

  return (
    <svg className={className} width={tamanho} height={tamanho} viewBox="0 0 240 240"
      fill="none" aria-hidden="true" focusable="false">
      <defs><Ouro id="jr-o-bussola" /><Ouro id="jr-o-bussola-e" escuro /></defs>

      {/* aros */}
      <circle cx="120" cy="120" r="116" fill="none" stroke="url(#jr-o-bussola-e)" strokeWidth="1.2" opacity="0.7" />
      <circle cx="120" cy="120" r="110" fill="none" stroke="url(#jr-o-bussola)" strokeWidth="2.4" />
      <circle cx="120" cy="120" r="94" fill="none" stroke="url(#jr-o-bussola-e)" strokeWidth="1" opacity="0.8" />
      <circle cx="120" cy="120" r="62" fill="none" stroke="url(#jr-o-bussola-e)" strokeWidth="0.9" opacity="0.55" />
      {ticks}

      {/* pontos diagonais, mais discretos */}
      <path d="M120 120 L126 96 L176 64 L144 114 Z" fill="url(#jr-o-bussola-e)" />
      <path d="M120 120 L144 126 L176 176 L126 144 Z" fill="url(#jr-o-bussola-e)" />
      <path d="M120 120 L114 144 L64 176 L96 126 Z" fill="url(#jr-o-bussola-e)" />
      <path d="M120 120 L96 114 L64 64 L114 96 Z" fill="url(#jr-o-bussola-e)" />

      {/* rosa principal, cada ponta com face clara e face escura */}
      <path d="M120 14 L102 102 L120 120 Z" fill="url(#jr-o-bussola)" />
      <path d="M120 14 L138 102 L120 120 Z" fill="url(#jr-o-bussola-e)" />
      <path d="M120 226 L102 138 L120 120 Z" fill="url(#jr-o-bussola-e)" />
      <path d="M120 226 L138 138 L120 120 Z" fill="url(#jr-o-bussola)" />
      <path d="M14 120 L102 102 L120 120 Z" fill="url(#jr-o-bussola-e)" />
      <path d="M14 120 L102 138 L120 120 Z" fill="url(#jr-o-bussola)" />
      <path d="M226 120 L138 102 L120 120 Z" fill="url(#jr-o-bussola)" />
      <path d="M226 120 L138 138 L120 120 Z" fill="url(#jr-o-bussola-e)" />

      {/* pino central */}
      <circle cx="120" cy="120" r="11" fill="url(#jr-o-bussola-e)" />
      <circle cx="120" cy="120" r="5" fill="url(#jr-o-bussola)" />
    </svg>
  )
}

/* ------------------------------------------------- carta preta com lacre */

export function CartaReal({ className = '', largura = 460 }) {
  return (
    <svg className={className} width={largura} height={(largura * 320) / 460}
      viewBox="0 0 460 320" fill="none" aria-hidden="true" focusable="false">
      <defs>
        <Ouro id="jr-o-carta" />
        <Ouro id="jr-o-carta-e" escuro />
        <linearGradient id="jr-papel" x1="0" y1="0" x2="0.6" y2="1">
          <stop offset="0%" stopColor="#141013" />
          <stop offset="46%" stopColor="#0a0709" />
          <stop offset="100%" stopColor="#000000" />
        </linearGradient>
        <radialGradient id="jr-lacre-carta" cx="38%" cy="30%" r="74%">
          <stop offset="0%" stopColor="#a3212d" />
          <stop offset="56%" stopColor="#5a0d14" />
          <stop offset="100%" stopColor="#26050a" />
        </radialGradient>
      </defs>

      {/* corpo do envelope */}
      <rect x="8" y="8" width="444" height="304" fill="url(#jr-papel)" stroke="url(#jr-o-carta)" strokeWidth="2" />
      <rect x="20" y="20" width="420" height="280" fill="none" stroke="url(#jr-o-carta-e)" strokeWidth="0.9" opacity="0.75" />

      {/*
        Só a aba de cima. Se as dobras de baixo entrarem também, os quatro
        vincos se encontram no centro e a carta vira um X riscado.
      */}
      <path d="M8 8 L230 176 L452 8 Z" fill="#100c0f" />
      <path d="M8 8 L230 176 L452 8" fill="none" stroke="url(#jr-o-carta)" strokeWidth="1.6" opacity="0.85" />
      <path d="M28 8 L230 160 L432 8" fill="none" stroke="url(#jr-o-carta-e)" strokeWidth="0.8" opacity="0.5" />

      {/* cantos ornamentados */}
      {[
        { x: 30, y: 30, r: 0 },
        { x: 430, y: 30, r: 90 },
        { x: 430, y: 290, r: 180 },
        { x: 30, y: 290, r: 270 },
      ].map((c, i) => (
        <g key={i} transform={`translate(${c.x} ${c.y}) rotate(${c.r})`}>
          <path d="M0 22 L0 6 q0 -6 6 -6 L22 0" fill="none" stroke="url(#jr-o-carta)" strokeWidth="1.4" />
          <path d="M6 16 q0 -10 10 -10" fill="none" stroke="url(#jr-o-carta-e)" strokeWidth="1" />
          <circle cx="4" cy="4" r="2" fill="url(#jr-o-carta)" />
        </g>
      ))}

      {/* fita atravessando */}
      <rect x="196" y="8" width="16" height="304" fill="#5a0d14" opacity="0.72" />
      <rect x="248" y="8" width="16" height="304" fill="#5a0d14" opacity="0.72" />
      <rect x="196" y="8" width="3" height="304" fill="url(#jr-o-carta-e)" opacity="0.5" />
      <rect x="261" y="8" width="3" height="304" fill="url(#jr-o-carta-e)" opacity="0.5" />

      {/* lacre */}
      <g transform="translate(230 176)">
        <path
          d="M0 -46 L14 -40 L28 -42 L34 -30 L47 -24 L46 -10 L54 0 L47 12 L50 26 L38 33 L34 46 L21 48 L11 57 L0 52
             L-11 57 L-21 48 L-34 46 L-38 33 L-50 26 L-47 12 L-54 0 L-46 -10 L-47 -24 L-34 -30 L-28 -42 L-14 -40 Z"
          fill="url(#jr-lacre-carta)"
        />
        <circle r="38" fill="none" stroke="url(#jr-o-carta)" strokeWidth="1.3" opacity="0.8" />
        <text y="13" textAnchor="middle" fill="url(#jr-o-carta)" fontFamily="'Cinzel', serif"
          fontSize="34" fontWeight="700">HR</text>
      </g>
    </svg>
  )
}

/* --------------------------------------------- canto de moldura (filigrana) */

export function CantoMoldura({ className = '', tamanho = 56, rotacao = 0 }) {
  return (
    <svg className={className} width={tamanho} height={tamanho} viewBox="0 0 60 60"
      fill="none" aria-hidden="true" focusable="false" style={{ transform: `rotate(${rotacao}deg)` }}>
      <defs><Ouro id={`jr-o-canto-${rotacao}`} /></defs>
      <g stroke={`url(#jr-o-canto-${rotacao})`} fill="none">
        <path d="M2 58 L2 14 q0 -12 12 -12 L58 2" strokeWidth="1.4" />
        <path d="M10 44 L10 20 q0 -10 10 -10 L44 10" strokeWidth="0.9" opacity="0.7" />
        <path d="M10 30 q0 -20 20 -20" strokeWidth="0.8" opacity="0.55" />
      </g>
      <circle cx="6" cy="6" r="2.4" fill={`url(#jr-o-canto-${rotacao})`} />
    </svg>
  )
}

/* --------------------------------------------------- selo solto (fechamento) */

/*
 * O lacre traz o brasão oficial da marca (escudo azul, coroa dourada, HR),
 * não um "HR" redesenhado: é a assinatura do hotel, tem que ser a de
 * verdade. O disco claro atrás existe para o azul-marinho do escudo não
 * sumir contra a cera vermelha.
 */
export function Selo({ className = '', tamanho = 116 }) {
  return (
    <svg className={className} width={tamanho} height={tamanho} viewBox="0 0 120 120"
      fill="none" aria-hidden="true" focusable="false">
      <defs>
        <radialGradient id="jr-lacre" cx="38%" cy="32%" r="72%">
          <stop offset="0%" stopColor="#a3212d" />
          <stop offset="58%" stopColor="#5a0d14" />
          <stop offset="100%" stopColor="#26050a" />
        </radialGradient>
        <radialGradient id="jr-lacre-disco" cx="42%" cy="34%" r="70%">
          <stop offset="0%" stopColor="#fdf6e6" />
          <stop offset="72%" stopColor="#efe1c4" />
          <stop offset="100%" stopColor="#cbb894" />
        </radialGradient>
        <Ouro id="jr-o-selo" />
      </defs>

      {/* cera */}
      <path
        d="M60 4 L74 10 L88 8 L95 20 L109 26 L108 41 L117 52 L110 65 L114 79 L102 87 L98 101 L84 103 L74 113 L60 108
           L46 113 L36 103 L22 101 L18 87 L6 79 L10 65 L3 52 L12 41 L11 26 L25 20 L32 8 L46 10 Z"
        fill="url(#jr-lacre)"
      />

      {/* medalhão claro + fio dourado, onde o brasão é impresso */}
      <circle cx="60" cy="58" r="36" fill="url(#jr-lacre-disco)" />
      <circle cx="60" cy="58" r="36" fill="none" stroke="url(#jr-o-selo)" strokeWidth="1.6" opacity="0.9" />
      <circle cx="60" cy="58" r="31" fill="none" stroke="#5a0d14" strokeWidth="0.8" opacity="0.28" />

      <image
        href="/images/jornada/marcas/brasao-hr.png"
        x="36" y="34" width="48" height="48"
        preserveAspectRatio="xMidYMid meet"
      />
    </svg>
  )
}
