/*
 * Configuração central da Jornada Real — níveis e faixas de pontos.
 *
 * A regra de multiplicador por nível ainda não está fechada com o hotel e
 * vai mudar. Este arquivo existe para que, quando o valor final for
 * confirmado, a troca aconteça em um lugar só — nenhuma tela escreve limiar
 * de pontos direto no JSX.
 *
 * Quando o dado existir na API (ex.: `current_level_name`, `next_level`),
 * a API vence esta configuração local: os valores aqui são o que a tela usa
 * como referência de exibição (nome, faixa, benefícios, imagem do objeto),
 * não uma fonte de verdade que sobrepõe o que o backend calculou.
 */

export const NIVEIS_JORNADA_REAL = [
  {
    chave: 'essencia',
    numeral: 'I',
    nome: 'Essência',
    posto: 'Nível 1',
    min: 0,
    max: 49,
    de: 0,
    ate: 50,
    faixa: '0 a 50 pontos',
    texto: 'O início da sua jornada na corte. Você pontua pelo valor padrão de cada suíte.',
    objeto: '/images/jornada/objetos/chave.png',
    objetoAlt: 'Chave antiga dourada',
    objetoClasse: 'jr-carta__objeto--chave',
    beneficios: [
      'Entrada na Jornada Real',
      'Acompanhamento dos seus pontos',
      'Acesso aos prêmios iniciais',
    ],
  },
  {
    chave: 'experiencia',
    numeral: 'II',
    nome: 'Experiência',
    posto: 'Nível 2',
    min: 50,
    max: 89,
    de: 50,
    ate: 90,
    faixa: '50 a 90 pontos',
    texto: 'Suas reservas passam a render em dobro. A volta ao hotel vale o dobro da primeira.',
    objeto: '/images/jornada/objetos/cetro.png',
    objetoAlt: 'Cetro dourado',
    objetoClasse: 'jr-carta__objeto--cetro',
    beneficios: [
      'Prioridade no atendimento',
      'Ofertas e experiências exclusivas',
      '+20% de pontos por reserva',
    ],
  },
  {
    chave: 'real',
    numeral: 'III',
    nome: 'Real',
    posto: 'Nível máximo',
    min: 90,
    max: Infinity,
    de: 90,
    ate: 100,
    faixa: '90+ pontos',
    texto: 'O topo da Jornada. O trono é seu, e cada reserva rende o máximo do programa.',
    objeto: '/images/jornada/objetos/coroa.png',
    objetoAlt: 'Coroa real em ouro',
    objetoClasse: 'jr-carta__objeto--coroa',
    beneficios: [
      'Nível máximo da Jornada Real',
      'Prêmios mais exclusivos',
      '+40% de pontos por reserva',
    ],
  },
]

// Fallback local: só usado quando a API não manda o nível atual do
// cliente. Se a API responder `current_level_name`/`current_level`, use o
// dado da API em vez desta função.
export const nivelPorPontos = (pontos) =>
  NIVEIS_JORNADA_REAL.find((nivel) => pontos >= nivel.min && pontos <= nivel.max) || NIVEIS_JORNADA_REAL[0]

export const proximoNivel = (nivelAtual) => {
  const indice = NIVEIS_JORNADA_REAL.findIndex((nivel) => nivel.chave === nivelAtual.chave)
  return NIVEIS_JORNADA_REAL[indice + 1] || null
}

export const nivelPorChaveOuNome = (valor) => {
  const alvo = String(valor || '').toLowerCase()
  return NIVEIS_JORNADA_REAL.find((nivel) => nivel.chave === alvo || nivel.nome.toLowerCase() === alvo)
}
