'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  BedDouble,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  LogIn,
  LogOut,
  RefreshCw,
  X,
} from 'lucide-react'
import { api } from '../lib/api'

const DIAS_SEMANA = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

const STATUS_CANCELADOS = new Set(['CANCELADA', 'CANCELADO', 'NO_SHOW'])

const STATUS_CHIP = {
  PENDENTE: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200',
  PENDENTE_PAGAMENTO: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200',
  AGUARDANDO_COMPROVANTE: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200',
  EM_ANALISE: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200',
  CONFIRMADA: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-200',
  PAGA_APROVADA: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-200',
  CHECKIN_LIBERADO: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-200',
  CHECKIN_REALIZADO: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-200',
  HOSPEDADO: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-200',
  CHECKOUT_REALIZADO: 'bg-neutral-200 text-neutral-600 dark:bg-neutral-700 dark:text-neutral-300',
}

function toDateKey(value) {
  if (!value) return null
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return null
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function formatDiaLongo(date) {
  return date.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })
}

export default function CalendarioReservasModal({ isOpen, onClose }) {
  const hoje = new Date()
  const [mesBase, setMesBase] = useState(new Date(hoje.getFullYear(), hoje.getMonth(), 1))
  const [diaSelecionado, setDiaSelecionado] = useState(new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate()))
  const [reservas, setReservas] = useState([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')

  useEffect(() => {
    if (!isOpen) return
    let isMounted = true
    setLoading(true)
    setErro('')
    api
      .get('/reservas', { silentError: true })
      .then((res) => {
        if (isMounted) setReservas(res.data?.reservas || [])
      })
      .catch(() => {
        if (isMounted) setErro('Não foi possível carregar as reservas do calendário')
      })
      .finally(() => {
        if (isMounted) setLoading(false)
      })
    return () => {
      isMounted = false
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return undefined
    const handleKey = (event) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [isOpen, onClose])

  // Indice por dia: entradas (check-in previsto), saidas (check-out previsto)
  // e ocupadas (check-in <= dia < check-out), ignorando canceladas/no-show.
  const indicePorDia = useMemo(() => {
    const indice = new Map()
    const garantir = (key) => {
      if (!indice.has(key)) indice.set(key, { entradas: [], saidas: [], ocupadas: [] })
      return indice.get(key)
    }
    for (const reserva of reservas) {
      const status = String(reserva.status || '').toUpperCase()
      if (STATUS_CANCELADOS.has(status)) continue
      const checkin = reserva.checkin_previsto ? new Date(reserva.checkin_previsto) : null
      const checkout = reserva.checkout_previsto ? new Date(reserva.checkout_previsto) : null
      const keyIn = toDateKey(checkin)
      const keyOut = toDateKey(checkout)
      if (keyIn) garantir(keyIn).entradas.push(reserva)
      if (keyOut) garantir(keyOut).saidas.push(reserva)
      if (checkin && checkout) {
        const cursor = new Date(checkin.getFullYear(), checkin.getMonth(), checkin.getDate())
        const fim = new Date(checkout.getFullYear(), checkout.getMonth(), checkout.getDate())
        // Limite defensivo de 120 noites para nao travar com dados invalidos
        for (let i = 0; cursor < fim && i < 120; i += 1) {
          garantir(toDateKey(cursor)).ocupadas.push(reserva)
          cursor.setDate(cursor.getDate() + 1)
        }
      }
    }
    return indice
  }, [reservas])

  const diasDoGrid = useMemo(() => {
    const primeiroDia = new Date(mesBase.getFullYear(), mesBase.getMonth(), 1)
    const inicioGrid = new Date(primeiroDia)
    inicioGrid.setDate(inicioGrid.getDate() - primeiroDia.getDay())
    const dias = []
    const cursor = new Date(inicioGrid)
    for (let i = 0; i < 42; i += 1) {
      dias.push(new Date(cursor))
      cursor.setDate(cursor.getDate() + 1)
    }
    return dias
  }, [mesBase])

  if (!isOpen) return null

  const hojeKey = toDateKey(hoje)
  const selecionadoKey = toDateKey(diaSelecionado)
  const detalheDia = indicePorDia.get(selecionadoKey) || { entradas: [], saidas: [], ocupadas: [] }
  const hospedadosNoDia = detalheDia.ocupadas.filter(
    (r) => !detalheDia.entradas.includes(r) && !detalheDia.saidas.includes(r)
  )

  const mudarMes = (delta) => {
    setMesBase((atual) => new Date(atual.getFullYear(), atual.getMonth() + delta, 1))
  }

  const irParaHoje = () => {
    const agora = new Date()
    setMesBase(new Date(agora.getFullYear(), agora.getMonth(), 1))
    setDiaSelecionado(new Date(agora.getFullYear(), agora.getMonth(), agora.getDate()))
  }

  const tituloMes = mesBase.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })

  const renderLista = (titulo, icone, itens, corIcone) => {
    if (itens.length === 0) return null
    const Icone = icone
    return (
      <div>
        <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400">
          <Icone className={`h-3.5 w-3.5 ${corIcone}`} aria-hidden="true" />
          {titulo} ({itens.length})
        </p>
        <ul className="mt-1.5 space-y-1.5">
          {itens.map((reserva) => (
            <li
              key={`${titulo}-${reserva.id}`}
              className="rounded-lg border border-neutral-200 bg-white p-2 text-sm shadow-sm dark:border-neutral-700 dark:bg-neutral-800"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-medium text-neutral-900 dark:text-white">
                  {reserva.cliente_nome || 'Cliente'}
                </span>
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                    STATUS_CHIP[String(reserva.status || '').toUpperCase()] ||
                    'bg-neutral-100 text-neutral-600 dark:bg-neutral-700 dark:text-neutral-300'
                  }`}
                >
                  {String(reserva.status || '').replace(/_/g, ' ')}
                </span>
              </div>
              <p className="mt-0.5 text-xs text-neutral-500 dark:text-neutral-400">
                Quarto {reserva.quarto_numero || '-'} • {reserva.codigo_reserva || ''}
              </p>
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50 p-3 backdrop-blur-sm sm:p-6"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Calendário de reservas"
    >
      <div
        className="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-neutral-900"
        onClick={(event) => event.stopPropagation()}
      >
        {/* Cabecalho */}
        <div className="flex items-center justify-between gap-3 border-b border-neutral-200 bg-gradient-to-r from-primary-600 to-primary-700 px-4 py-3 dark:border-neutral-700 sm:px-6">
          <div className="flex items-center gap-2 text-white">
            <CalendarDays className="h-5 w-5" aria-hidden="true" />
            <h2 className="text-base font-bold capitalize sm:text-lg">{tituloMes}</h2>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => mudarMes(-1)}
              className="rounded-lg p-2 text-white/90 transition-colors hover:bg-white/15"
              aria-label="Mês anterior"
            >
              <ChevronLeft className="h-5 w-5" aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={irParaHoje}
              className="rounded-lg border border-white/30 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-white/15"
            >
              Hoje
            </button>
            <button
              type="button"
              onClick={() => mudarMes(1)}
              className="rounded-lg p-2 text-white/90 transition-colors hover:bg-white/15"
              aria-label="Próximo mês"
            >
              <ChevronRight className="h-5 w-5" aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="ml-1 rounded-lg p-2 text-white/90 transition-colors hover:bg-white/15"
              aria-label="Fechar calendário"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </div>

        <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
          {/* Grade do mes */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-4">
            {loading ? (
              <div className="flex h-64 items-center justify-center gap-2 text-neutral-500 dark:text-neutral-400">
                <RefreshCw className="h-5 w-5 animate-spin" aria-hidden="true" />
                Carregando reservas...
              </div>
            ) : erro ? (
              <div className="flex h-64 items-center justify-center text-sm text-red-600 dark:text-red-400">{erro}</div>
            ) : (
              <>
                <div className="grid grid-cols-7 gap-1 text-center text-[11px] font-semibold uppercase tracking-wide text-neutral-400 dark:text-neutral-500">
                  {DIAS_SEMANA.map((dia) => (
                    <div key={dia} className="py-1">
                      {dia}
                    </div>
                  ))}
                </div>
                <div className="mt-1 grid grid-cols-7 gap-1">
                  {diasDoGrid.map((dia) => {
                    const key = toDateKey(dia)
                    const info = indicePorDia.get(key)
                    const doMes = dia.getMonth() === mesBase.getMonth()
                    const ehHoje = key === hojeKey
                    const selecionado = key === selecionadoKey
                    return (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setDiaSelecionado(new Date(dia))}
                        className={`group relative flex min-h-[62px] flex-col items-start rounded-xl border p-1.5 text-left transition-all sm:min-h-[72px] ${
                          selecionado
                            ? 'border-primary-500 bg-primary-50 shadow-md dark:border-primary-400 dark:bg-primary-900/30'
                            : 'border-transparent hover:border-primary-200 hover:bg-neutral-50 dark:hover:border-primary-800 dark:hover:bg-neutral-800'
                        } ${doMes ? '' : 'opacity-40'}`}
                      >
                        <span
                          className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${
                            ehHoje
                              ? 'bg-primary-600 text-white'
                              : 'text-neutral-700 dark:text-neutral-200'
                          }`}
                        >
                          {dia.getDate()}
                        </span>
                        {info && (
                          <span className="mt-auto flex flex-wrap items-center gap-1 pt-1">
                            {info.entradas.length > 0 && (
                              <span className="rounded-full bg-green-100 px-1.5 text-[10px] font-bold text-green-700 dark:bg-green-900/50 dark:text-green-300">
                                ↓{info.entradas.length}
                              </span>
                            )}
                            {info.saidas.length > 0 && (
                              <span className="rounded-full bg-amber-100 px-1.5 text-[10px] font-bold text-amber-700 dark:bg-amber-900/50 dark:text-amber-300">
                                ↑{info.saidas.length}
                              </span>
                            )}
                            {info.ocupadas.length > 0 && (
                              <span className="rounded-full bg-sky-100 px-1.5 text-[10px] font-bold text-sky-700 dark:bg-sky-900/50 dark:text-sky-300">
                                ●{info.ocupadas.length}
                              </span>
                            )}
                          </span>
                        )}
                      </button>
                    )
                  })}
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px] text-neutral-500 dark:text-neutral-400">
                  <span className="flex items-center gap-1">
                    <span className="rounded-full bg-green-100 px-1.5 font-bold text-green-700 dark:bg-green-900/50 dark:text-green-300">↓</span>
                    Check-ins
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="rounded-full bg-amber-100 px-1.5 font-bold text-amber-700 dark:bg-amber-900/50 dark:text-amber-300">↑</span>
                    Check-outs
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="rounded-full bg-sky-100 px-1.5 font-bold text-sky-700 dark:bg-sky-900/50 dark:text-sky-300">●</span>
                    Quartos ocupados
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Detalhe do dia selecionado */}
          <div className="max-h-64 shrink-0 overflow-y-auto border-t border-neutral-200 bg-neutral-50 p-3 dark:border-neutral-700 dark:bg-neutral-800/60 sm:p-4 lg:max-h-none lg:w-80 lg:border-l lg:border-t-0">
            <p className="text-sm font-bold capitalize text-neutral-900 dark:text-white">
              {formatDiaLongo(diaSelecionado)}
            </p>
            {detalheDia.entradas.length === 0 && detalheDia.saidas.length === 0 && hospedadosNoDia.length === 0 ? (
              <p className="mt-3 text-sm text-neutral-500 dark:text-neutral-400">
                Nenhuma movimentação neste dia.
              </p>
            ) : (
              <div className="mt-3 space-y-4">
                {renderLista('Check-ins', LogIn, detalheDia.entradas, 'text-green-600 dark:text-green-400')}
                {renderLista('Check-outs', LogOut, detalheDia.saidas, 'text-amber-600 dark:text-amber-400')}
                {renderLista('Hospedados', BedDouble, hospedadosNoDia, 'text-sky-600 dark:text-sky-400')}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
