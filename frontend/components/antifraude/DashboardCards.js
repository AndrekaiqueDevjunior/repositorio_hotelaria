'use client'
import { Line, LineChart, LineArea, AreaChart, Area, BarChart, PieChart, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, AlertTriangle, Users, CreditCard, Shield, Activity } from 'lucide-react'

export default function DashboardCards({ stats, transacoesSuspeitas }) {
  const formatarMoeda = (valor) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

  // Dados para gráficos
  const riscoData = [
    { name: 'Baixo', value: stats.risco_baixo, fill: '#10b981' },
    { name: 'Médio', value: stats.risco_medio, fill: '#f59e0b' },
    { name: 'Alto', value: stats.risco_alto, fill: '#ef4444' }
  ]

  const tendenciaData = [
    { dia: 'Seg', baixo: 45, medio: 12, alto: 3 },
    { dia: 'Ter', baixo: 42, medio: 15, alto: 5 },
    { dia: 'Qua', baixo: 48, medio: 10, alto: 2 },
    { dia: 'Qui', baixo: 51, medio: 8, alto: 4 },
    { dia: 'Sex', baixo: 44, medio: 14, alto: 6 },
    { dia: 'Sáb', baixo: 38, medio: 18, alto: 8 }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Card Score Médio */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-800">Score Médio</h3>
          <div className={`p-2 rounded-full ${stats.score_medio > 50 ? 'bg-red-100' : stats.score_medio > 30 ? 'bg-yellow-100' : 'bg-green-100'}`}>
            <Activity className={`w-4 h-4 ${stats.score_medio > 50 ? 'text-red-600' : stats.score_medio > 30 ? 'text-yellow-600' : 'text-green-600'}`} />
          </div>
        </div>
        <div className="text-3xl font-bold text-gray-900">{stats.score_medio}</div>
        <p className="text-sm text-gray-600">Score médio do sistema</p>
        <div className="mt-2 text-xs text-gray-500">
          {stats.score_medio > 50 ? '🚨 Atenção necessária' : '✅ Sistema saudável'}
        </div>
      </div>

      {/* Card Total Analisado */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-800">Clientes Analisados</h3>
          <Users className="w-5 h-5 text-blue-600" />
        </div>
        <div className="text-3xl font-bold text-gray-900">{stats.total_clientes_analisados}</div>
        <p className="text-sm text-gray-600">Total de clientes verificados</p>
        <div className="mt-2 text-xs text-gray-500">
          Período: últimos 30 dias
        </div>
      </div>

      {/* Card Alertas */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-800">Alertas Ativas</h3>
          <AlertTriangle className="w-5 h-5 text-orange-600" />
        </div>
        <div className="text-3xl font-bold text-orange-600">{transacoesSuspeitas.length}</div>
        <p className="text-sm text-gray-600">Transações suspeitas</p>
        <div className="mt-2 text-xs text-gray-500">
          Score >= 30
        </div>
      </div>

      {/* Card Taxa de Fraude */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-800">Taxa de Fraude</h3>
          <Shield className="w-5 h-5 text-purple-600" />
        </div>
        <div className="text-3xl font-bold text-purple-600">{stats.percentual_alto}%</div>
        <p className="text-sm text-gray-600">Clientes de alto risco</p>
        <div className="mt-2 text-xs text-gray-500">
          {stats.percentual_alto > 10 ? '⚠️ Monitorar' : '✅ Controlado'}
        </div>
      </div>

      {/* Gráfico de Distribuição de Risco */}
      <div className="col-span-1 md:col-span-2 bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Distribuição de Risco</h3>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={riscoData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
              label={({ name, percent, value }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            >
              {riscoData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Gráfico de Tendência */}
      <div className="col-span-1 md:col-span-2 bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Tendência de Risco (7 dias)</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={tendenciaData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="dia" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="baixo" stroke="#10b981" strokeWidth={2} />
            <Line type="monotone" dataKey="medio" stroke="#f59e0b" strokeWidth={2} />
            <Line type="monotone" dataKey="alto" stroke="#ef4444" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
