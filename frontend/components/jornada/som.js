/*
 * Efeitos sonoros da Jornada Real.
 *
 * Sintetizados na hora com Web Audio, não carregados de arquivo: são poucos
 * osciladores, não pesam no carregamento e não dependem de biblioteca nem
 * de licença de banco de áudio.
 *
 * O timbre é de sino/celesta — seno com um parcial inarmônico em 2,76x, que
 * é o que dá a cor de carrilhão dos desenhos antigos — somado a um sopro de
 * veludo feito com ruído filtrado.
 *
 * O navegador só libera áudio depois de um gesto do usuário, então o
 * contexto nasce suspenso e é retomado no primeiro clique.
 */

const CHAVE = 'jr-som'

let ctx = null
let mestre = null
let ligadoEmMemoria = null

function ehCliente() {
  return typeof window !== 'undefined'
}

export function somLigado() {
  if (!ehCliente()) return false
  if (ligadoEmMemoria !== null) return ligadoEmMemoria
  try {
    ligadoEmMemoria = window.localStorage.getItem(CHAVE) !== 'off'
  } catch {
    ligadoEmMemoria = true
  }
  return ligadoEmMemoria
}

export function alternarSom() {
  const novo = !somLigado()
  ligadoEmMemoria = novo
  try {
    window.localStorage.setItem(CHAVE, novo ? 'on' : 'off')
  } catch {
    /* navegação privada: fica só em memória */
  }
  if (novo) garantirContexto()
  return novo
}

function garantirContexto() {
  if (!ehCliente()) return null
  if (!ctx) {
    const Contexto = window.AudioContext || window.webkitAudioContext
    if (!Contexto) return null
    ctx = new Contexto()
    mestre = ctx.createGain()
    mestre.gain.value = 0.42
    mestre.connect(ctx.destination)
  }
  if (ctx.state === 'suspended') ctx.resume()
  return ctx
}

/*
 * O primeiro "hover" da página costuma cair num prêmio (onMouseEnter), e
 * hover não é gesto válido para o navegador liberar áudio: o resume() falha
 * calado e o prêmio já fica marcado como revelado, sem tocar o carrilhão.
 * Por isso destravamos o contexto assim que o gesto válido (clique, toque
 * ou tecla) acontecer pela primeira vez em qualquer lugar da página — não
 * só no botão de som.
 */
if (ehCliente()) {
  const destravar = () => {
    if (somLigado()) garantirContexto()
    window.removeEventListener('pointerdown', destravar)
    window.removeEventListener('keydown', destravar)
    window.removeEventListener('touchstart', destravar)
  }
  window.addEventListener('pointerdown', destravar, { once: true })
  window.addEventListener('keydown', destravar, { once: true })
  window.addEventListener('touchstart', destravar, { once: true })
}

/* Sino: seno puro mais um parcial inarmônico, ambos com queda exponencial. */
function sino(t0, freq, duracao, volume) {
  const fundamental = ctx.createOscillator()
  const ganho = ctx.createGain()
  fundamental.type = 'sine'
  fundamental.frequency.setValueAtTime(freq, t0)
  ganho.gain.setValueAtTime(0, t0)
  ganho.gain.linearRampToValueAtTime(volume, t0 + 0.008)
  ganho.gain.exponentialRampToValueAtTime(0.0001, t0 + duracao)
  fundamental.connect(ganho)
  ganho.connect(mestre)
  fundamental.start(t0)
  fundamental.stop(t0 + duracao + 0.02)

  const parcial = ctx.createOscillator()
  const ganhoParcial = ctx.createGain()
  parcial.type = 'sine'
  parcial.frequency.setValueAtTime(freq * 2.76, t0)
  ganhoParcial.gain.setValueAtTime(0, t0)
  ganhoParcial.gain.linearRampToValueAtTime(volume * 0.26, t0 + 0.006)
  ganhoParcial.gain.exponentialRampToValueAtTime(0.0001, t0 + duracao * 0.55)
  parcial.connect(ganhoParcial)
  ganhoParcial.connect(mestre)
  parcial.start(t0)
  parcial.stop(t0 + duracao)
}

/* Sopro de veludo: ruído passando por um filtro que varre de grave a agudo. */
function veludo(t0, duracao = 0.72, volume = 0.16) {
  const amostras = Math.floor(ctx.sampleRate * duracao)
  const buffer = ctx.createBuffer(1, amostras, ctx.sampleRate)
  const dados = buffer.getChannelData(0)
  for (let i = 0; i < amostras; i++) dados[i] = Math.random() * 2 - 1

  const fonte = ctx.createBufferSource()
  fonte.buffer = buffer

  const filtro = ctx.createBiquadFilter()
  filtro.type = 'bandpass'
  filtro.Q.value = 0.9
  filtro.frequency.setValueAtTime(300, t0)
  filtro.frequency.exponentialRampToValueAtTime(2600, t0 + duracao * 0.55)
  filtro.frequency.exponentialRampToValueAtTime(520, t0 + duracao)

  const ganho = ctx.createGain()
  ganho.gain.setValueAtTime(0, t0)
  ganho.gain.linearRampToValueAtTime(volume, t0 + 0.11)
  ganho.gain.exponentialRampToValueAtTime(0.0001, t0 + duracao)

  fonte.connect(filtro)
  filtro.connect(ganho)
  ganho.connect(mestre)
  fonte.start(t0)
  fonte.stop(t0 + duracao)
}

const RECEITAS = {
  /* cortina abrindo: sopro de veludo e o carrilhão subindo por cima */
  revelar(t0) {
    veludo(t0, 0.78, 0.15)
    const notas = [1046.5, 1318.5, 1568.0, 2093.0, 2637.0]
    notas.forEach((freq, i) => {
      const atraso = i * 0.082
      sino(t0 + 0.1 + atraso, freq, 1.5 - i * 0.16, 0.2 - i * 0.026)
    })
  },

  /* toque curto e agudo, para passagem de ponteiro */
  brilho(t0) {
    sino(t0, 2093.0, 0.42, 0.075)
    sino(t0 + 0.045, 2637.0, 0.32, 0.05)
  },

  /* clique macio de abrir e fechar */
  toque(t0) {
    sino(t0, 1568.0, 0.26, 0.07)
  },
}

export function tocar(nome) {
  if (!somLigado()) return
  const contexto = garantirContexto()
  if (!contexto) return
  const receita = RECEITAS[nome]
  if (!receita) return
  try {
    receita(contexto.currentTime + 0.01)
  } catch {
    /* se o navegador recusar o áudio, a página segue sem som */
  }
}
