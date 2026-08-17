/*
 * Modo demonstração da Jornada Real.
 *
 * Serve para percorrer o fluxo de reserva inteiro (datas → quarto → dados →
 * pagamento → confirmação) em ambientes sem backend, como o preview do
 * Vercel, para revisar tela por tela o que o hóspede vê.
 *
 * SEGURANÇA — só liga quando TODAS estas condições valem:
 *   1. está rodando no navegador;
 *   2. a URL tem `?demo=1`;
 *   3. o host NÃO é o domínio de produção.
 *
 * A checagem de host é a trava que importa: mesmo que alguém acesse
 * hotelrealcabofrio.com/reservar?demo=1, o modo continua desligado e o site
 * fala com o backend de verdade. Nenhum dado falso pode alcançar o hóspede.
 */

const HOSTS_DE_PRODUCAO = ['hotelrealcabofrio.com', 'www.hotelrealcabofrio.com']

const CHAVE_SESSAO = 'jr_demo'

/*
 * Uma vez ligado por `?demo=1`, o modo fica valendo pelo resto da aba: as
 * telas da Jornada navegam entre si (pontos → prêmios → cupom) e o
 * parâmetro se perderia no caminho, quebrando o teste no meio.
 * sessionStorage e não localStorage: sai sozinho ao fechar a aba.
 */
export function demoAtivo() {
  if (typeof window === 'undefined') return false
  if (HOSTS_DE_PRODUCAO.includes(window.location.hostname)) return false

  const naUrl = new URLSearchParams(window.location.search).get('demo')

  try {
    if (naUrl === '1') {
      window.sessionStorage.setItem(CHAVE_SESSAO, '1')
      return true
    }
    if (naUrl === '0') {
      window.sessionStorage.removeItem(CHAVE_SESSAO)
      return false
    }
    return window.sessionStorage.getItem(CHAVE_SESSAO) === '1'
  } catch (erro) {
    // sessionStorage bloqueado (modo privado): vale só o parâmetro da URL
    return naUrl === '1'
  }
}

const hoje = () => new Date()
const emDias = (dias) => {
  const d = hoje()
  d.setDate(d.getDate() + dias)
  return d.toISOString().slice(0, 10)
}

const CLIENTE_DEMO = {
  id: 9001,
  nome_completo: 'Marina Duarte',
  documento: '11144477735',
  email: 'marina.duarte@exemplo.com',
  telefone: '22988887777',
}

const SUITES_DEMO = [
  {
    tipo: 'LUXO',
    preco_diaria: 320,
    quantidade_disponivel: 3,
    quartos: [{ numero: '201' }, { numero: '202' }, { numero: '203' }],
  },
  {
    tipo: 'MASTER',
    preco_diaria: 450,
    quantidade_disponivel: 2,
    quartos: [{ numero: '301' }, { numero: '302' }],
  },
  {
    tipo: 'DUPLA',
    preco_diaria: 540,
    quantidade_disponivel: 2,
    quartos: [{ numero: '305' }, { numero: '306' }],
  },
  {
    tipo: 'REAL',
    preco_diaria: 690,
    quantidade_disponivel: 1,
    quartos: [{ numero: '401' }],
  },
]

/*
 * Estado vivo da demonstração: o saldo cai quando um prêmio é resgatado e
 * os resgates entram na lista. Sem isso, dava para "resgatar" o mesmo
 * prêmio infinitas vezes e o saldo nunca mudava — a tela mentiria sobre o
 * que o sistema real faz. Reinicia ao recarregar a página, de propósito.
 */
const PREMIOS_DEMO = [
  {
    id: 1,
    nome: 'Tecnologia Real',
    descricao: 'iPhone 16e — transforme sua rotina em experiência.',
    preco_em_pontos: 90,
    imagem_url: '/images/premios/tecnologia-real.png',
  },
  {
    id: 2,
    nome: 'Rituais do Real',
    descricao: 'Cafeteira premium para o café de todo dia.',
    preco_em_pontos: 35,
    imagem_url: '/images/premios/rituais-do-real.png',
  },
  {
    id: 3,
    nome: 'O Retorno do Sonho',
    descricao: '1 diária com hidro e champanhe cortesia.',
    preco_em_pontos: 25,
    imagem_url: '/images/premios/o-retorno-do-sonho.png',
  },
]

const estado = {
  saldo: 62,
  resgates: [
    {
      id: 501,
      premio_nome: 'O Retorno do Sonho',
      pontos_usados: 25,
      codigo_resgate: 'REAL-9F2K7Q',
      codigo_status: 'ativo',
      expira_em: emDias(21) + 'T00:00:00Z',
    },
  ],
  proximoId: 502,
}

const codigoAleatorio = () =>
  'REAL-' + Math.random().toString(36).slice(2, 8).toUpperCase()

// erro no formato que o axios entrega ao componente
const recusar = (config, status, detail) => {
  const erro = new Error(detail)
  erro.isAxiosError = true
  erro.config = config
  erro.response = { status, data: { detail }, headers: {}, config }
  return Promise.reject(erro)
}

const diariasEntre = (checkin, checkout) => {
  const ini = new Date(checkin)
  const fim = new Date(checkout)
  const dias = Math.round((fim - ini) / 86400000)
  return Number.isFinite(dias) && dias > 0 ? dias : 1
}

/*
 * Cada rota devolve o mesmo formato do backend real (conferido em
 * public_routes.py). Se o contrato do backend mudar, isto aqui também
 * precisa mudar — por isso o modo é de revisão visual, não de teste de
 * integração.
 */
const ROTAS = [
  {
    quando: (url) => url.includes('/jornada/regras'),
    responde: () => ({
      pontuacao_por_suite: [
        { tipo: 'LUXO', pontos: 1 },
        { tipo: 'MASTER', pontos: 2 },
        { tipo: 'DUPLA', pontos: 3 },
        { tipo: 'REAL', pontos: 3 },
      ],
    }),
  },

  {
    quando: (url) => url.includes('/quartos/disponiveis'),
    responde: (config) => {
      const p = config.params || {}
      const num_diarias = diariasEntre(p.data_checkin, p.data_checkout)

      return {
        success: true,
        data_checkin: p.data_checkin,
        data_checkout: p.data_checkout,
        num_diarias,
        total_quartos_disponiveis: SUITES_DEMO.reduce((s, q) => s + q.quantidade_disponivel, 0),
        tipos_disponiveis: SUITES_DEMO.map((s) => ({
          ...s,
          preco_total: s.preco_diaria * num_diarias,
        })),
      }
    },
  },

  {
    // hóspede fictícia no nível Experiência, a meio caminho do topo
    quando: (url, metodo) =>
      metodo === 'get' && (/\/customers\/\d+\/loyalty/.test(url) || url.includes('/pontos/consultar/')),
    responde: () => ({
      customer_name: CLIENTE_DEMO.nome_completo,
      customer_id: CLIENTE_DEMO.id,
      document: CLIENTE_DEMO.documento,
      // saldo vem do estado vivo: cai a cada resgate feito na demonstração
      redeemable_points: estado.saldo,
      lifetime_points: 62,
      total_redeemed_points: 62 - estado.saldo + 25,
      current_level_name: 'Experiência',
      current_level: { nome: 'Experiência', multiplicador: 2 },
      next_level: { nome: 'Real', min_points: 90 },
      next_level_points: 90,
      missing_to_next_level: 28,
      level_progress: 69,
      reward_goal_points: 90,
      missing_to_next_reward: Math.max(90 - estado.saldo, 0),
      reward_progress: Math.min((estado.saldo / 90) * 100, 100),
      rewards_unlocked: PREMIOS_DEMO.filter((p) => p.preco_em_pontos <= estado.saldo).length,
      rewards_total: PREMIOS_DEMO.length,
    }),
  },

  {
    quando: (url, metodo) => metodo === 'get' && url.includes('/premios'),
    responde: () => PREMIOS_DEMO,
  },

  /*
   * Resgate. Reproduz as duas recusas que o backend real faz — saldo
   * insuficiente (402) e prêmio inexistente (404) — para dar para conferir
   * também o que o hóspede vê quando dá errado, não só o caminho feliz.
   */
  {
    quando: (url, metodo) =>
      metodo === 'post' && (url.includes('/rewards/redeem') || url.includes('/premios/resgatar-publico')),
    responde: (config) => {
      const corpo = config.data ? JSON.parse(config.data) : {}
      const id = Number(corpo.reward_id ?? corpo.premio_id)
      const premio = PREMIOS_DEMO.find((p) => p.id === id)

      if (!premio) return recusar(config, 404, 'Prêmio não encontrado.')
      if (premio.preco_em_pontos > estado.saldo) {
        return recusar(config, 402, 'Saldo insuficiente de pontos.')
      }

      estado.saldo -= premio.preco_em_pontos
      const codigo = codigoAleatorio()
      const expira = emDias(30) + 'T00:00:00Z'

      estado.resgates.unshift({
        id: estado.proximoId++,
        premio_nome: premio.nome,
        pontos_usados: premio.preco_em_pontos,
        codigo_resgate: codigo,
        codigo_status: 'ativo',
        expira_em: expira,
      })

      return {
        success: true,
        codigo_resgate: codigo,
        codigo_status: 'ativo',
        expira_em: expira,
        pontos_usados: premio.preco_em_pontos,
        novo_saldo: estado.saldo,
      }
    },
  },

  {
    quando: (url, metodo) => metodo === 'post' && /\/resgates\/\d+\/renovar/.test(url),
    responde: (config) => {
      const id = Number((config.url || '').match(/\/resgates\/(\d+)\/renovar/)?.[1])
      const resgate = estado.resgates.find((r) => r.id === id)
      if (resgate) {
        resgate.codigo_resgate = codigoAleatorio()
        resgate.codigo_status = 'ativo'
        resgate.expira_em = emDias(30) + 'T00:00:00Z'
      }
      return { success: true }
    },
  },

  {
    quando: (url) => url.includes('/jornada/meu-cupom'),
    responde: () => ({
      coupon: {
        code: 'AMIGO_REAL7X9K',
        link: 'https://hotelrealcabofrio.com/reservar?cupom=AMIGO_REAL7X9K',
        active: true,
        status: 'active',
        current_uses: 2,
        max_uses: 5,
        expires_at: emDias(45) + 'T00:00:00Z',
        discount_percentage: 10,
        points_per_referral: 5,
        whatsapp_share_url: 'https://wa.me/?text=Jornada%20Real',
      },
      usages: [
        { friend_name: 'Bruno Alves', used_at: emDias(-28) + 'T00:00:00Z' },
        { friend_name: 'Carla Menezes', used_at: emDias(-9) + 'T00:00:00Z' },
      ],
      referral_points_earned: 10,
    }),
  },

  {
    quando: (url) => url.includes('/jornada/meus-resgates'),
    responde: () => ({ resgates: estado.resgates }),
  },

  {
    quando: (url, metodo) => metodo === 'get' && /\/customers\/\d+$/.test(url),
    responde: () => CLIENTE_DEMO,
  },

  {
    quando: (url, metodo) => metodo === 'post' && url.includes('/customers/create'),
    responde: (config) => ({ ...CLIENTE_DEMO, ...(config.data ? JSON.parse(config.data) : {}) }),
  },

  {
    quando: (url) => url.includes('/auth/otp/generate'),
    responde: () => ({ otp_id: 'demo-otp', expires_in_seconds: 300 }),
  },

  {
    // no modo demo qualquer código de 6 dígitos passa
    quando: (url) => url.includes('/auth/otp/validate'),
    responde: () => ({
      access_token: 'demo-token',
      customer: CLIENTE_DEMO,
    }),
  },

  {
    quando: (url) => url.includes('/cupons/validar'),
    responde: (config) => {
      const corpo = config.data ? JSON.parse(config.data) : {}
      return {
        valido: true,
        codigo: corpo.codigo,
        tipo_desconto: 'PERCENTUAL',
        valor_desconto: 10,
        mensagem: 'Cupom aplicado no modo demonstração',
      }
    },
  },

  {
    quando: (url) => url.includes('/public/reservas'),
    responde: (config) => {
      const p = config.data ? JSON.parse(config.data) : {}
      const num_diarias = diariasEntre(p.data_checkin, p.data_checkout)
      const suite = SUITES_DEMO.find((s) => s.tipo === p.tipo_suite) || SUITES_DEMO[0]
      const valor_total = suite.preco_diaria * num_diarias
      const temCupom = Boolean(p.cupom_codigo)
      const valor_desconto = temCupom ? valor_total * 0.1 : 0

      return {
        success: true,
        reserva: {
          codigo: 'DEMO-4821',
          cliente: p.nome_completo || CLIENTE_DEMO.nome_completo,
          tipo_suite: suite.tipo,
          quarto: p.quarto_numero,
          checkin: p.data_checkin,
          checkout: p.data_checkout,
          num_diarias,
          valor_total,
          valor_desconto,
          valor_total_com_desconto: valor_total - valor_desconto,
        },
        instrucoes: {
          documentos: 'Trazer documento de identificação com foto',
          checkin_horario: '12:00',
          checkout_horario: '11:00',
          contato: '(22) 2648-5900',
        },
      }
    },
  },
]

/*
 * Substitui o adapter do axios só nas chamadas que o modo demo conhece. As
 * demais seguem para a rede normalmente (e falham, se não houver backend) —
 * de propósito: assim fica evidente o que ainda não está coberto.
 */
export function instalarDemo(api) {
  api.interceptors.request.use((config) => {
    if (!demoAtivo()) return config

    const url = config.url || ''
    const metodo = (config.method || 'get').toLowerCase()
    const rota = ROTAS.find((r) => r.quando(url, metodo))
    if (!rota) return config

    config.adapter = () =>
      // pequeno atraso para o estado de "carregando" aparecer de verdade
      new Promise((resolve) => setTimeout(resolve, 280)).then(() =>
        /*
         * `responde` pode devolver dados ou uma promessa recusada (ver
         * `recusar`): o Promise.resolve normaliza os dois casos, e a recusa
         * propaga como erro de rede de verdade para o componente.
         */
        Promise.resolve(rota.responde(config)).then((data) => ({
          data,
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
        }))
      )

    return config
  })
}

export const DADOS_DEMO = { cliente: CLIENTE_DEMO, suites: SUITES_DEMO, emDias }
