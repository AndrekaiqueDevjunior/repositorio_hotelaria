'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle, RefreshCw, XCircle } from 'lucide-react'
import { api } from '../lib/api'
import {
  clearTefPendenciasCheck,
  getTefPendenciasCheckedAt,
  markTefPendenciasChecked
} from '../services/tefPendencias'
import { useToast } from '../contexts/ToastContext'

const TEF_REQUEST_TIMEOUT_MS = 180000

const formatarHorario = (value) => {
  if (!value) return ''
  try {
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(value))
  } catch (error) {
    return ''
  }
}

const PERFIS_PERMITIDOS = ['ADMIN', 'GERENTE']

export default function TefPendenciasGuard({ user }) {
  const podeGerenciarTef = Boolean(user) && PERFIS_PERMITIDOS.includes(user.perfil)
  const { addToast } = useToast()
  const autoRunRef = useRef(false)
  const [checkedAt, setCheckedAt] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [statusError, setStatusError] = useState('')
  const [defaultAction, setDefaultAction] = useState('')
  const [checking, setChecking] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  const verificarStatus = useCallback(async () => {
    if (!podeGerenciarTef) return

    setChecking(true)
    try {
      const res = await api.get('/pagamentos/tef/pendencias/status', {
        params: { clear: false }
      })
      const message = res.data?.message
      setDefaultAction(res.data?.default_action || '')
      if (message) {
        setStatusMessage(message)
      }
      setStatusError('')
    } catch (error) {
      if (error.response?.status !== 401) {
        setStatusError(error.response?.data?.detail || 'Nao foi possivel consultar o status TEF.')
      }
    } finally {
      setChecking(false)
    }
  }, [podeGerenciarTef])

  const processarPendencias = useCallback(async (source = 'dashboard_guard') => {
    if (!podeGerenciarTef || processing) return false

    setProcessing(true)
    setStatusError('')
    setCollapsed(false)

    try {
      const res = await api.post('/pagamentos/tef/pendencias', {}, {
        timeout: TEF_REQUEST_TIMEOUT_MS
      })
      const message = res.data?.message || 'Tratamento de pendencias TEF executado.'
      setStatusMessage(message)

      if (res.data?.success === false) {
        addToast({
          titulo: 'Pendencias TEF',
          mensagem: message,
          tipo: 'warning',
          categoria: 'tef'
        })
        return false
      }

      const novoCheckedAt = markTefPendenciasChecked({
        source,
        result: res.data
      })

      setCheckedAt(novoCheckedAt)
      addToast({
        titulo: 'TEF verificado',
        mensagem: message,
        tipo: 'success',
        categoria: 'tef'
      })
      return true
    } catch (error) {
      const message = error.response?.data?.detail || 'Falha ao tratar pendencias TEF.'
      setStatusError(message)
      addToast({
        titulo: 'Pendencias TEF',
        mensagem: message,
        tipo: 'warning',
        categoria: 'tef'
      })
      return false
    } finally {
      setProcessing(false)
    }
  }, [addToast, processing, podeGerenciarTef])

  useEffect(() => {
    if (!podeGerenciarTef) return
    setCheckedAt(getTefPendenciasCheckedAt())
    verificarStatus()
  }, [verificarStatus, podeGerenciarTef])

  useEffect(() => {
    if (!podeGerenciarTef || autoRunRef.current) return

    autoRunRef.current = true
    clearTefPendenciasCheck()
    setCheckedAt('')
    processarPendencias('dashboard_startup')
  }, [processarPendencias, podeGerenciarTef])

  if (!podeGerenciarTef || collapsed) {
    return null
  }

  const actionLabel = defaultAction === 'undo' ? 'desfazer' : 'confirmar'
  const checkedLabel = formatarHorario(checkedAt)
  const isChecked = Boolean(checkedAt)

  return (
    <div className={`mb-4 rounded border px-4 py-3 ${
      statusError
        ? 'border-red-200 bg-red-50 text-red-900'
        : isChecked
          ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
          : 'border-amber-200 bg-amber-50 text-amber-900'
    }`}>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex gap-3">
          <div className="mt-0.5">
            {statusError ? (
              <XCircle className="h-5 w-5" aria-hidden="true" />
            ) : isChecked ? (
              <CheckCircle className="h-5 w-5" aria-hidden="true" />
            ) : (
              <AlertTriangle className="h-5 w-5" aria-hidden="true" />
            )}
          </div>
          <div>
            <p className="font-semibold">
              {isChecked ? 'Pendencias TEF verificadas nesta inicializacao' : 'Verificando pendencias TEF na abertura'}
            </p>
            <p className="mt-1 text-sm">
              {isChecked
                ? `Ultima verificacao: ${checkedLabel || 'agora'}.`
                : `A aplicacao esta chamando a modalidade 130 da CliSiTef; a acao padrao do backend e ${actionLabel}.`}
            </p>
            {statusMessage && (
              <p className="mt-2 text-sm font-medium">{statusMessage}</p>
            )}
            {statusError && (
              <p className="mt-2 text-sm font-medium">{statusError}</p>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <button
            type="button"
            onClick={() => processarPendencias('dashboard_manual')}
            disabled={processing}
            className="inline-flex items-center justify-center gap-2 rounded bg-sky-700 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-800 disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${processing ? 'animate-spin' : ''}`} aria-hidden="true" />
            {processing ? 'Processando...' : isChecked ? 'Executar novamente' : 'Processar agora'}
          </button>
          {isChecked && (
            <button
              type="button"
              onClick={() => setCollapsed(true)}
              className="inline-flex items-center justify-center rounded border border-current/30 px-4 py-2 text-sm font-semibold hover:bg-white/50"
            >
              Ocultar
            </button>
          )}
          {checking && (
            <span className="text-xs opacity-80">Consultando status...</span>
          )}
        </div>
      </div>
    </div>
  )
}
