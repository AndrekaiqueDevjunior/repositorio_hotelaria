'use client'
import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'
import Link from 'next/link'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [ultimasReservas, setUltimasReservas] = useState([])
  const [pagamentos, setPagamentos] = useState({ total: 0, pendente: 0 })
  const [horaAtual, setHoraAtual] = useState('')

  useEffect(() => {
    loadStats()
    loadUltimasReservas()
    loadPagamentos()
    
    // Atualizar hora
    const updateTime = () => {
      setHoraAtual(new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }))
    }
    updateTime()
    const interval = setInterval(updateTime, 60000)
    return () => clearInterval(interval)
  }, [])

  const loadStats = async (retryCount = 0) => {
    try {
      setLoading(true)
      
      // Tentar rota autenticada primeiro
      let res
      try {
        res = await api.get('/dashboard/stats')
      } catch (authError) {
        console.log('⚠️ Rota autenticada falhou, tentando rota pública...')
        // Fallback para rota pública (sem autenticação)
        res = await api.get('/dashboard/stats/public')
      }
      
      if (res.data.success) {
        // Suportar formato antigo (data) e novo (kpis_principais)
        if (res.data.data) {
          // O backend pode retornar o formato antigo (data) e também o novo (kpis_principais).
          // O card de comprovantes depende de total_comprovantes (novo), então mesclamos.
          setStats({
            ...res.data.data,
            reservas_pendentes:
              res.data.data.reservas_pendentes ?? res.data.kpis_principais?.reservas_pendentes ?? 0,
            reservas_ativas:
              res.data.data.reservas_ativas ?? res.data.kpis_principais?.reservas_ativas ?? 0,
            reservas_finalizadas:
              res.data.data.reservas_finalizadas ?? res.data.kpis_principais?.reservas_finalizadas ?? 0,
            total_comprovantes:
              res.data.data.total_comprovantes ?? res.data.kpis_principais?.total_comprovantes ?? 0,
          })
        } else if (res.data.kpis_principais) {
          // Converter formato novo para formato esperado pelo frontend
          setStats({
            total_clientes: res.data.kpis_principais.total_clientes || 0,
            total_reservas: res.data.kpis_principais.total_reservas || 0,
            total_quartos: res.data.kpis_principais.total_quartos || 0,
            taxa_ocupacao: res.data.kpis_principais.taxa_ocupacao || 0,
            receita_total: res.data.kpis_principais.receita_total || 0,
            checkins_hoje: res.data.operacoes_dia?.checkins_hoje || 0,
            checkouts_hoje: res.data.operacoes_dia?.checkouts_hoje || 0,
            reservas_pendentes: res.data.kpis_principais.reservas_pendentes || 0,
            quartos_ocupados: res.data.operacoes_dia?.quartos_ocupados || 0,
            quartos_disponiveis: (res.data.kpis_principais.total_quartos || 0) - (res.data.operacoes_dia?.quartos_ocupados || 0),
            reservas_confirmadas: res.data.operacoes_dia?.reservas_ativas || 0,
            reservas_ativas: res.data.kpis_principais.reservas_ativas || 0,
            reservas_finalizadas: res.data.kpis_principais.reservas_finalizadas || 0,
            total_comprovantes: res.data.kpis_principais.total_comprovantes || 0,
          })
        } else {
          throw new Error('Formato de resposta inválido')
        }
        setError(null)
      } else {
        throw new Error(res.data.message || 'Erro ao carregar estatísticas')
      }
    } catch (err) {
      console.error('Erro ao carregar dashboard:', err)
      
      // Retry automático até 3 tentativas
      if (retryCount < 3) {
        console.log(`🔄 Tentativa ${retryCount + 1}/3 em 2 segundos...`)
        setTimeout(() => loadStats(retryCount + 1), 2000)
      } else {
        setError('Não foi possível conectar ao servidor. Verifique se o backend está rodando.')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadUltimasReservas = async () => {
    try {
      const res = await api.get('/reservas')
      if (res.data.reservas) {
        setUltimasReservas(res.data.reservas.slice(0, 5))
      }
    } catch (err) {
      console.error('Erro ao carregar reservas:', err)
    }
  }

  const loadPagamentos = async () => {
    try {
      const res = await api.get('/pagamentos')
      if (res.data.success && res.data.pagamentos) {
        const total = res.data.pagamentos
          .filter(p => p.status === 'APROVADO')
          .reduce((acc, p) => acc + p.valor, 0)
        const pendente = res.data.pagamentos
          .filter(p => p.status === 'PENDENTE' || p.status === 'AGUARDANDO')
          .reduce((acc, p) => acc + p.valor, 0)
        setPagamentos({ total, pendente })
      }
    } catch (err) {
      console.error('Erro ao carregar pagamentos:', err)
    }
  }

  const refreshAll = () => {
    loadStats()
    loadUltimasReservas()
    loadPagamentos()
  }

  // Status badge
  const getStatusBadge = (status) => {
    const configs = {
      'PENDENTE': { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '⏳' },
      'HOSPEDADO': { bg: 'bg-green-100', text: 'text-green-800', icon: '✅' },
      'CHECKED_OUT': { bg: 'bg-blue-100', text: 'text-blue-800', icon: '🏁' },
      'CANCELADO': { bg: 'bg-red-100', text: 'text-red-800', icon: '❌' }
    }
    const config = configs[status] || { bg: 'bg-gray-100', text: 'text-gray-800', icon: '❓' }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.icon} {status}
      </span>
    )
  }

  // Saudação baseada na hora
  const getSaudacao = () => {
    const hora = new Date().getHours()
    if (hora < 12) return 'Bom dia'
    if (hora < 18) return 'Boa tarde'
    return 'Boa noite'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="relative">
            <div className="w-20 h-20 border-4 border-blue-200 rounded-full animate-pulse"></div>
            <div className="absolute top-0 left-0 w-20 h-20 border-4 border-t-blue-600 rounded-full animate-spin"></div>
          </div>
          <p className="text-gray-600 mt-4 animate-pulse">Carregando dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-8 max-w-md text-center">
          <div className="text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-red-800 mb-2">Erro ao carregar</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <button 
            onClick={refreshAll}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all font-medium"
          >
            🔄 Tentar novamente
          </button>
        </div>
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="space-y-6 pb-8">
      {/* Header com saudação */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-blue-200 text-sm">{getSaudacao()}! 👋</p>
            <h1 className="text-2xl md:text-3xl font-bold">Dashboard Hotel Real</h1>
            <p className="text-blue-100 text-sm mt-1">
              {new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
              {' • '}{horaAtual}
            </p>
          </div>
          <div className="mt-4 md:mt-0 flex gap-2">
            <button
              onClick={refreshAll}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-all flex items-center gap-2"
            >
              🔄 Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* Alertas do dia */}
      {(stats.checkins_hoje > 0 || stats.checkouts_hoje > 0 || stats.reservas_pendentes > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {stats.checkins_hoje > 0 && (
            <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-xl p-4 text-white flex items-center gap-4">
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center text-2xl">
                🛬
              </div>
              <div>
                <p className="text-green-100 text-sm">Check-ins Hoje</p>
                <p className="text-2xl font-bold">{stats.checkins_hoje}</p>
              </div>
              <Link href="/reservas" className="ml-auto text-white/80 hover:text-white">
                Ver →
              </Link>
            </div>
          )}
          
          {stats.checkouts_hoje > 0 && (
            <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl p-4 text-white flex items-center gap-4">
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center text-2xl">
                🛫
              </div>
              <div>
                <p className="text-orange-100 text-sm">Check-outs Hoje</p>
                <p className="text-2xl font-bold">{stats.checkouts_hoje}</p>
              </div>
              <Link href="/reservas" className="ml-auto text-white/80 hover:text-white">
                Ver →
              </Link>
            </div>
          )}
          
          {stats.reservas_pendentes > 0 && (
            <div className="bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-xl p-4 text-white flex items-center gap-4">
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center text-2xl">
                ⏳
              </div>
              <div>
                <p className="text-yellow-100 text-sm">Reservas Pendentes</p>
                <p className="text-2xl font-bold">{stats.reservas_pendentes}</p>
              </div>
              <Link href="/reservas" className="ml-auto text-white/80 hover:text-white">
                Ver →
              </Link>
            </div>
          )}
        </div>
      )}

      {/* Cards Principais */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-all border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wider">Clientes</p>
              <p className="text-3xl font-bold text-gray-800 mt-1">{stats.total_clientes || 0}</p>
            </div>
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-xl">👥</span>
            </div>
          </div>
          <Link href="/clientes" className="text-blue-600 text-sm mt-3 inline-block hover:underline">
            Ver todos →
          </Link>
        </div>
        
        <div className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-all border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wider">Reservas</p>
              <p className="text-3xl font-bold text-gray-800 mt-1">{stats.total_reservas || 0}</p>
            </div>
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-xl">📋</span>
            </div>
          </div>
          <Link href="/reservas" className="text-blue-600 text-sm mt-3 inline-block hover:underline">
            Ver relatório →
          </Link>
        </div>
      </div>

      {/* Novas Estatísticas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Reservas Pendentes */}
        <div className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-all border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wider flex items-center gap-1">
                <span>⏳</span> Reservas Pendentes
              </p>
              <p className="text-3xl font-bold text-gray-800 mt-1">{stats.reservas_pendentes || 0}</p>
            </div>
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
              <span className="text-xl">⏳</span>
            </div>
          </div>
          <Link href="/reservas?status=PENDENTE" className="text-yellow-600 text-sm mt-3 inline-block hover:underline">
            Ver detalhes →
          </Link>
        </div>
        
        {/* Reservas Ativas */}
        <div className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-all border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wider flex items-center gap-1">
                <span>✅</span> Reservas Ativas
              </p>
              <p className="text-3xl font-bold text-gray-800 mt-1">{stats.reservas_ativas || 0}</p>
            </div>
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-xl">✅</span>
            </div>
          </div>
          <Link href="/reservas?status=ATIVO" className="text-green-600 text-sm mt-3 inline-block hover:underline">
            Ver detalhes →
          </Link>
        </div>
        
        {/* Reservas Finalizadas/Excluídas */}
        <div className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-all border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wider flex items-center gap-1">
                <span>🏁</span> Finalizadas
              </p>
              <p className="text-3xl font-bold text-gray-800 mt-1">{stats.reservas_finalizadas || 0}</p>
            </div>
            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <span className="text-xl">🏁</span>
            </div>
          </div>
          <Link href="/reservas?status=FINALIZADO" className="text-gray-600 text-sm mt-3 inline-block hover:underline">
            Ver histórico →
          </Link>
        </div>
        
        {/* Total de Quartos */}
        <div className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-all border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wider flex items-center gap-1">
                <span>🏠</span> Total de Quartos
              </p>
              <p className="text-3xl font-bold text-gray-800 mt-1">{stats.total_quartos || 0}</p>
            </div>
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <span className="text-xl">🛏️</span>
            </div>
          </div>
          <Link href="/quartos" className="text-purple-600 text-sm mt-3 inline-block hover:underline">
            Gerenciar →
          </Link>
        </div>
        
        {/* Comprovantes */}
        <div className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-all border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wider flex items-center gap-1">
                <span>📄</span> Comprovantes
              </p>
              <p className="text-3xl font-bold text-gray-800 mt-1">{stats.total_comprovantes || 0}</p>
            </div>
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-xl">📄</span>
            </div>
          </div>
          <Link href="/comprovantes" className="text-green-600 text-sm mt-3 inline-block hover:underline">
            Ver todos →
          </Link>
        </div>
      </div>

      {/* Seção financeira e ocupação */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Financeiro */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-green-600 to-green-700 p-4 text-white">
            <h2 className="font-bold flex items-center gap-2">
              💰 Resumo Financeiro
            </h2>
          </div>
          <div className="p-5 space-y-4">
            <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
              <div>
                <p className="text-sm text-gray-600">Receita Total</p>
                <p className="text-2xl font-bold text-green-600">
                  R$ {(stats.receita_total || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <span className="text-3xl">💵</span>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-gray-500">Pagamentos Recebidos</p>
                <p className="text-lg font-bold text-blue-600">
                  R$ {pagamentos.total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="p-3 bg-yellow-50 rounded-lg">
                <p className="text-xs text-gray-500">Pendentes</p>
                <p className="text-lg font-bold text-yellow-600">
                  R$ {pagamentos.pendente.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Ocupação de quartos */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-4 text-white">
            <h2 className="font-bold flex items-center gap-2">
              🏨 Status dos Quartos
            </h2>
          </div>
          <div className="p-5">
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="text-center p-3 bg-green-50 rounded-lg border-2 border-green-200">
                <p className="text-2xl font-bold text-green-600">{stats.quartos_disponiveis || 0}</p>
                <p className="text-xs text-gray-600">Livres</p>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg border-2 border-red-200">
                <p className="text-2xl font-bold text-red-600">{stats.quartos_ocupados || 0}</p>
                <p className="text-xs text-gray-600">Ocupados</p>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg border-2 border-blue-200">
                <p className="text-2xl font-bold text-blue-600">{stats.reservas_confirmadas || 0}</p>
                <p className="text-xs text-gray-600">Reservados</p>
              </div>
            </div>
            
            {/* Barra visual de ocupação */}
            <div className="mt-4">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Disponibilidade</span>
                <span>{stats.quartos_disponiveis}/{stats.total_quartos} quartos livres</span>
              </div>
              <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden flex">
                <div 
                  className="bg-red-500 h-full transition-all"
                  style={{ width: `${(stats.quartos_ocupados / stats.total_quartos) * 100}%` }}
                  title="Ocupados"
                ></div>
                <div 
                  className="bg-blue-500 h-full transition-all"
                  style={{ width: `${(stats.reservas_confirmadas / stats.total_quartos) * 100}%` }}
                  title="Reservados"
                ></div>
                <div 
                  className="bg-green-500 h-full transition-all"
                  style={{ width: `${(stats.quartos_disponiveis / stats.total_quartos) * 100}%` }}
                  title="Livres"
                ></div>
              </div>
              <div className="flex gap-4 mt-2 text-xs">
                <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-500 rounded"></span> Ocupados</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 rounded"></span> Reservados</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-500 rounded"></span> Livres</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Últimas reservas */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b bg-gray-50 flex justify-between items-center">
          <h2 className="font-bold text-gray-800 flex items-center gap-2">
            📋 Últimas Reservas
          </h2>
          <Link href="/reservas" className="text-blue-600 text-sm hover:underline">
            Ver todas →
          </Link>
        </div>
        <div className="overflow-x-auto">
          {ultimasReservas.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Código</th>
                  <th className="px-4 py-3 text-left">Cliente</th>
                  <th className="px-4 py-3 text-left">Quarto</th>
                  <th className="px-4 py-3 text-left">Check-in</th>
                  <th className="px-4 py-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {ultimasReservas.map((reserva) => (
                  <tr key={reserva.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="font-mono text-sm text-blue-600">
                        {reserva.codigo_reserva || `#${reserva.id}`}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-800">
                      {reserva.cliente_nome}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {reserva.quarto_numero} - {reserva.tipo_suite}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {reserva.checkin_previsto ? new Date(reserva.checkin_previsto).toLocaleDateString('pt-BR') : '-'}
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(reserva.status)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center text-gray-500">
              <span className="text-4xl">📭</span>
              <p className="mt-2">Nenhuma reserva encontrada</p>
            </div>
          )}
        </div>
      </div>

      {/* Ações Rápidas */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h2 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
          ⚡ Ações Rápidas
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Link
            href="/reservas"
            className="flex flex-col items-center gap-2 p-4 bg-blue-50 rounded-xl hover:bg-blue-100 transition-all"
          >
            <span className="text-2xl">➕</span>
            <span className="text-sm font-medium text-blue-800">Nova Reserva</span>
          </Link>
          
          <Link
            href="/clientes"
            className="flex flex-col items-center gap-2 p-4 bg-green-50 rounded-xl hover:bg-green-100 transition-all"
          >
            <span className="text-2xl">👤</span>
            <span className="text-sm font-medium text-green-800">Novo Cliente</span>
          </Link>
          
          <Link
            href="/pontos"
            className="flex flex-col items-center gap-2 p-4 bg-yellow-50 rounded-xl hover:bg-yellow-100 transition-all"
          >
            <span className="text-2xl">🎯</span>
            <span className="text-sm font-medium text-yellow-800">Pontos</span>
          </Link>
          
          <Link
            href="/antifraude"
            className="flex flex-col items-center gap-2 p-4 bg-purple-50 rounded-xl hover:bg-purple-100 transition-all"
          >
            <span className="text-2xl">🛡️</span>
            <span className="text-sm font-medium text-purple-800">Antifraude</span>
          </Link>
        </div>
      </div>

      {/* Footer info */}
      <div className="text-center text-gray-400 text-xs pt-4">
        <p>Hotel Real Cabo Frio • Sistema de Gestão v2.0</p>
        <p>Última atualização: {new Date().toLocaleTimeString('pt-BR')}</p>
      </div>
    </div>
  )
}
