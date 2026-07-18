'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { toast } from 'react-toastify'
import { api } from '../lib/api'

const websocketUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/v1/tarifas/ws/alertas`
}

export default function TarifaTemporadaAlert() {
  const [alerta, setAlerta] = useState(null)
  const [loading, setLoading] = useState(false)
  const toastSignature = useRef('')

  const aplicarAlerta = useCallback((data, mostrarToast = true) => {
    if (!data || data.evento === 'PING') return
    setAlerta(data.ativo ? data : null)
    if (mostrarToast && data.ativo) {
      const signature = (data.tarifas_vencidas || []).map((item) => `${item.suite_tipo}:${item.data_fim}`).join('|')
      if (toastSignature.current !== signature) {
        toastSignature.current = signature
        toast.warning(`⚠️ ${data.mensagem}`, { autoClose: 10000 })
      }
    }
  }, [])

  const verificar = useCallback(async (mostrarToast = true) => {
    setLoading(true)
    try {
      const response = await api.post('/tarifas/alerta-temporada/verificar')
      aplicarAlerta(response.data, mostrarToast)
    } catch (error) {
      console.error('Erro ao verificar temporadas tarifarias:', error)
    } finally {
      setLoading(false)
    }
  }, [aplicarAlerta])

  useEffect(() => {
    verificar(true)
    const intervalId = setInterval(() => verificar(false), 5 * 60 * 1000)
    let socket
    let reconnectId
    let encerrado = false

    const conectar = () => {
      socket = new WebSocket(websocketUrl())
      socket.onmessage = (event) => {
        try { aplicarAlerta(JSON.parse(event.data), true) } catch (_) {}
      }
      socket.onclose = () => {
        if (!encerrado) reconnectId = setTimeout(conectar, 5000)
      }
    }
    conectar()

    return () => {
      encerrado = true
      clearInterval(intervalId)
      clearTimeout(reconnectId)
      if (socket) socket.close()
    }
  }, [aplicarAlerta, verificar])

  if (!alerta) return null

  return (
    <section className="mb-6 rounded-lg border-l-4 border-amber-500 bg-amber-50 p-4 shadow-sm" role="alert">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-amber-600" aria-hidden="true" />
          <div>
            <h2 className="font-semibold text-amber-900">Temporada tarifária vencida</h2>
            <p className="text-sm text-amber-800">{alerta.mensagem}</p>
            <p className="mt-1 text-xs text-amber-700">
              {alerta.tarifas_vencidas.map((item) => `${item.suite_tipo} (venceu em ${item.data_fim})`).join(' • ')}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => verificar(true)} disabled={loading} className="inline-flex items-center gap-2 rounded border border-amber-400 px-3 py-2 text-sm font-medium text-amber-900 hover:bg-amber-100 disabled:opacity-60">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Atualizar
          </button>
          <Link href="/tarifas" className="rounded bg-amber-600 px-3 py-2 text-sm font-semibold text-white hover:bg-amber-700">
            Atualizar tarifas
          </Link>
        </div>
      </div>
    </section>
  )
}
