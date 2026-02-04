# 🎯 MODAL DE HISTÓRICO DO CLIENTE - ADMIN PONTOS

**Data**: 05/01/2026 10:18 UTC-03:00
**Status**: ✅ **PROPOSTA COMPLETA DE IMPLEMENTAÇÃO**

---

## 🎨 **O QUE PODEMOS COLOCAR NO MODAL**

### **1. INFORMAÇÕES DO CLIENTE**
- Foto/Avatar do cliente
- Nome completo
- ID do cliente
- Email
- Telefone
- Data de cadastro
- Status (ativo/inativo)

### **2. RESUMO DE PONTOS**
- Saldo atual de pontos
- Total acumulado (histórico)
- Total de créditos
- Total de débitos
- Nível do programa (Bronze, Prata, Ouro)
- Próximo nível

### **3. HISTÓRICO DETALHADO**
- Lista completa de transações
- Filtros por período
- Filtros por tipo
- Busca por motivo
- Paginação

### **4. ESTATÍSTICAS VISUAIS**
- Gráfico de evolução de pontos
- Gráfico de tipos de transação
- Gráfico mensal
- Métricas importantes

### **5. AÇÕES ADMINISTRATIVAS**
- Ajuste manual de pontos
- Gerar convite
- Ver reservas do cliente
- Exportar histórico
- Bloquear/Desbloquear cliente

---

## 🎯 **PROPOSTA DE MODAL COMPLETO**

### **Estrutura do Modal**:
```jsx
// Modal com abas internas
<ModalHistoricoCliente>
  <TabClienteInfo />      // Informações do cliente
  <TabResumoPontos />     // Saldo e estatísticas
  <TabHistorico />        // Histórico detalhado
  <TabAcoes />            // Ações administrativas
</ModalHistoricoCliente>
```

---

## 📱 **IMPLEMENTAÇÃO COMPLETA**

### **1. Componente Principal do Modal**:

```jsx
// ModalHistoricoCliente.jsx
import { useState, useEffect } from 'react'
import { api } from '../../../lib/api'

export default function ModalHistoricoCliente({ 
  isOpen, 
  onClose, 
  clienteId,
  clienteNome 
}) {
  const [activeTab, setActiveTab] = useState('info')
  const [clienteData, setClienteData] = useState(null)
  const [saldo, setSaldo] = useState(0)
  const [historico, setHistorico] = useState([])
  const [estatisticas, setEstatisticas] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen && clienteId) {
      loadClienteData()
    }
  }, [isOpen, clienteId])

  const loadClienteData = async () => {
    try {
      setLoading(true)
      
      // Carregar dados do cliente
      const resCliente = await api.get(`/clientes/${clienteId}`)
      setClienteData(resCliente.data)
      
      // Carregar saldo
      const resSaldo = await api.get(`/pontos/saldo/${clienteId}`)
      setSaldo(resSaldo.data.saldo || 0)
      
      // Carregar histórico
      const resHistorico = await api.get(`/pontos/historico/${clienteId}?limit=50`)
      setHistorico(resHistorico.data.transacoes || [])
      
      // Carregar estatísticas do cliente
      const resStats = await api.get(`/pontos/estatisticas-cliente/${clienteId}`)
      setEstatisticas(resStats.data)
      
    } catch (error) {
      console.error('Erro ao carregar dados do cliente:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden">
        
        {/* Header do Modal */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">📊 Histórico de Pontos</h2>
              <p className="text-blue-100">
                Cliente: {clienteNome} (ID: {clienteId})
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        {/* Tabs do Modal */}
        <div className="bg-white border-b">
          <div className="flex">
            {[
              { id: 'info', label: '👤 Cliente', icon: 'user' },
              { id: 'resumo', label: '📈 Resumo', icon: 'chart' },
              { id: 'historico', label: '📜 Histórico', icon: 'history' },
              { id: 'acoes', label: '⚙️ Ações', icon: 'settings' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-3 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-b-2 border-blue-600 text-blue-600 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Conteúdo do Modal */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="text-center py-8">
              <div className="text-2xl mb-2">⏳</div>
              <p>Carregando dados...</p>
            </div>
          ) : (
            <>
              {activeTab === 'info' && <TabClienteInfo cliente={clienteData} />}
              {activeTab === 'resumo' && <TabResumoPontos saldo={saldo} estatisticas={estatisticas} />}
              {activeTab === 'historico' && <TabHistorico historico={historico} clienteId={clienteId} />}
              {activeTab === 'acoes' && <TabAcoes clienteId={clienteId} cliente={clienteData} />}
            </>
          )}
        </div>

        {/* Footer do Modal */}
        <div className="bg-gray-50 px-6 py-4 border-t flex justify-end gap-2">
          <button
            onClick={onClose}
            className="bg-gray-600 text-white px-6 py-2 rounded hover:bg-gray-700"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  )
}
```

### **2. Tab de Informações do Cliente**:

```jsx
// TabClienteInfo.jsx
export default function TabClienteInfo({ cliente }) {
  if (!cliente) return <div>Carregando...</div>

  return (
    <div className="space-y-6">
      {/* Card Principal do Cliente */}
      <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6">
        <div className="flex items-center space-x-4">
          <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            {cliente.nome_completo?.charAt(0) || cliente.nomeCompleto?.charAt(0) || '?'}
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">
              {cliente.nome_completo || cliente.nomeCompleto}
            </h3>
            <p className="text-gray-600">ID: {cliente.id}</p>
            <p className="text-gray-600">{cliente.email}</p>
            <p className="text-gray-600">{cliente.telefone}</p>
          </div>
        </div>
      </div>

      {/* Informações Detalhadas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg border">
          <h4 className="font-semibold mb-4">📋 Informações Pessoais</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Nome Completo:</span>
              <span className="font-medium">{cliente.nome_completo || cliente.nomeCompleto}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Documento:</span>
              <span className="font-medium">{cliente.documento}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Email:</span>
              <span className="font-medium">{cliente.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Telefone:</span>
              <span className="font-medium">{cliente.telefone}</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border">
          <h4 className="font-semibold mb-4">📅 Informações do Sistema</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">ID do Cliente:</span>
              <span className="font-medium">#{cliente.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Data de Cadastro:</span>
              <span className="font-medium">
                {new Date(cliente.created_at).toLocaleDateString('pt-BR')}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Status:</span>
              <span className={`px-2 py-1 rounded text-xs ${
                cliente.status === 'ATIVO' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {cliente.status || 'ATIVO'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Última Atividade:</span>
              <span className="font-medium">
                {cliente.ultima_atividade 
                  ? new Date(cliente.ultima_atividade).toLocaleDateString('pt-BR')
                  : 'Nunca'
                }
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Estatísticas Rápidas */}
      <div className="bg-white p-6 rounded-lg border">
        <h4 className="font-semibold mb-4">📊 Resumo Rápido</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl mb-1">🏨</div>
            <p className="text-sm text-gray-600">Reservas</p>
            <p className="text-xl font-bold text-blue-600">{cliente.total_reservas || 0}</p>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-1">💰</div>
            <p className="text-sm text-gray-600">Total Gasto</p>
            <p className="text-xl font-bold text-green-600">
              R$ {(cliente.total_gasto || 0).toLocaleString('pt-BR')}
            </p>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-1">🌟</div>
            <p className="text-sm text-gray-600">Pontos</p>
            <p className="text-xl font-bold text-purple-600">{saldo || 0} RP</p>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-1">🎁</div>
            <p className="text-sm text-gray-600">Convites</p>
            <p className="text-xl font-bold text-orange-600">{cliente.total_convites || 0}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
```

### **3. Tab de Resumo de Pontos**:

```jsx
// TabResumoPontos.jsx
export default function TabResumoPontos({ saldo, estatisticas }) {
  return (
    <div className="space-y-6">
      {/* Card Principal de Saldo */}
      <div className="bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg shadow-lg p-8 text-white text-center">
        <h3 className="text-xl font-semibold mb-2">Saldo Atual de Pontos</h3>
        <div className="text-6xl font-bold mb-4">
          {saldo.toLocaleString('pt-BR')} RP
        </div>
        <div className="flex justify-center gap-4 text-sm">
          <span>📈 Nível: {getNivelPontos(saldo)}</span>
          <span>🎯 Próximo: {getProximoNivel(saldo)} RP</span>
        </div>
      </div>

      {/* Estatísticas Detalhadas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg border">
          <div className="text-3xl mb-2 text-green-600">📈</div>
          <h4 className="text-gray-600 text-sm mb-1">Total de Créditos</h4>
          <p className="text-2xl font-bold text-green-600">
            +{estatisticas?.total_creditos || 0} RP
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {estatisticas?.qtd_creditos || 0} transações
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg border">
          <div className="text-3xl mb-2 text-red-600">📉</div>
          <h4 className="text-gray-600 text-sm mb-1">Total de Débitos</h4>
          <p className="text-2xl font-bold text-red-600">
            -{estatisticas?.total_debitos || 0} RP
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {estatisticas?.qtd_debitos || 0} transações
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg border">
          <div className="text-3xl mb-2 text-blue-600">🎯</div>
          <h4 className="text-gray-600 text-sm mb-1">Transações Totais</h4>
          <p className="text-2xl font-bold text-blue-600">
            {estatisticas?.total_transacoes || 0}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Desde {new Date(estatisticas?.primeira_transacao || Date.now()).toLocaleDateString('pt-BR')}
          </p>
        </div>
      </div>

      {/* Gráfico de Evolução (Simples) */}
      <div className="bg-white p-6 rounded-lg border">
        <h4 className="font-semibold mb-4">📊 Evolução de Pontos (Últimos 6 meses)</h4>
        <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">Gráfico de evolução (implementar com Chart.js)</p>
        </div>
      </div>

      {/* Badges e Conquistas */}
      <div className="bg-white p-6 rounded-lg border">
        <h4 className="font-semibold mb-4">🏆 Conquistas e Badges</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {getBadges(saldo).map((badge, index) => (
            <div key={index} className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-3xl mb-2">{badge.icon}</div>
              <p className="text-sm font-medium">{badge.nome}</p>
              <p className="text-xs text-gray-500">{badge.descricao}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Funções auxiliares
function getNivelPontos(saldo) {
  if (saldo >= 100) return 'Ouro'
  if (saldo >= 50) return 'Prata'
  if (saldo >= 20) return 'Bronze'
  return 'Iniciante'
}

function getProximoNivel(saldo) {
  if (saldo >= 100) return 'Máximo'
  if (saldo >= 50) return 100 - saldo
  if (saldo >= 20) return 50 - saldo
  return 20 - saldo
}

function getBadges(saldo) {
  const badges = []
  if (saldo >= 100) badges.push({ icon: '👑', nome: 'Ouro', descricao: '100+ pontos' })
  if (saldo >= 50) badges.push({ icon: '🥈', nome: 'Prata', descricao: '50+ pontos' })
  if (saldo >= 20) badges.push({ icon: '🥉', nome: 'Bronze', descricao: '20+ pontos' })
  if (saldo >= 5) badges.push({ icon: '🌟', nome: 'Iniciante', descricao: '5+ pontos' })
  return badges
}
```

### **4. Tab de Histórico Detalhado**:

```jsx
// TabHistorico.jsx
export default function TabHistorico({ historico, clienteId }) {
  const [filtros, setFiltros] = useState({
    periodo: 'todos',
    tipo: 'todos',
    origem: 'todos'
  })

  const historicoFiltrado = filtrarHistorico(historico, filtros)

  return (
    <div className="space-y-6">
      {/* Filtros */}
      <div className="bg-white p-4 rounded-lg border">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Período</label>
            <select 
              value={filtros.periodo}
              onChange={(e) => setFiltros({...filtros, periodo: e.target.value})}
              className="w-full rounded border-gray-300"
            >
              <option value="todos">Todos</option>
              <option value="7dias">Últimos 7 dias</option>
              <option value="30dias">Últimos 30 dias</option>
              <option value="90dias">Últimos 90 dias</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
            <select 
              value={filtros.tipo}
              onChange={(e) => setFiltros({...filtros, tipo: e.target.value})}
              className="w-full rounded border-gray-300"
            >
              <option value="todos">Todos</option>
              <option value="CREDITO">Créditos</option>
              <option value="DEBITO">Débitos</option>
              <option value="AJUSTE">Ajustes</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Origem</label>
            <select 
              value={filtros.origem}
              onChange={(e) => setFiltros({...filtros, origem: e.target.value})}
              className="w-full rounded border-gray-300"
            >
              <option value="todos">Todas</option>
              <option value="RESERVA">Reservas</option>
              <option value="CONVITE">Convites</option>
              <option value="AJUSTE_MANUAL">Ajustes Manuais</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tabela de Histórico */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Data</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Tipo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Origem</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Pontos</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Saldo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Motivo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Ações</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {historicoFiltrado.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-4 py-8 text-center text-gray-500">
                    Nenhuma transação encontrada
                  </td>
                </tr>
              ) : (
                historicoFiltrado.map((transacao) => (
                  <tr key={transacao.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">
                      {new Date(transacao.created_at).toLocaleDateString('pt-BR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        transacao.tipo === 'CREDITO' || transacao.tipo === 'GANHO' 
                          ? 'bg-green-100 text-green-800' 
                          : transacao.tipo === 'DEBITO' || transacao.tipo === 'RESGATE'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {transacao.tipo}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {getOrigemLabel(transacao.origem)}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`font-bold ${
                        transacao.pontos > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {transacao.pontos > 0 ? '+' : ''}{transacao.pontos} RP
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm font-semibold">
                      {transacao.saldo_posterior} RP
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate" title={transacao.motivo}>
                      {transacao.motivo || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex gap-1">
                        <button
                          onClick={() => verDetalhesTransacao(transacao)}
                          className="text-blue-600 hover:text-blue-800 text-xs"
                          title="Ver detalhes"
                        >
                          👁️
                        </button>
                        {transacao.tipo === 'AJUSTE' && (
                          <button
                            onClick={() => estornarTransacao(transacao.id)}
                            className="text-orange-600 hover:text-orange-800 text-xs"
                            title="Estornar"
                          >
                            ↩️
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Exportação */}
      <div className="flex justify-end gap-2">
        <button
          onClick={() => exportarHistoricoCSV(clienteId, historicoFiltrado)}
          className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700"
        >
          📄 Exportar CSV
        </button>
        <button
          onClick={() => imprimirHistorico(clienteId, historicoFiltrado)}
          className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
        >
          🖨️ Imprimir
        </button>
      </div>
    </div>
  )
}
```

### **5. Tab de Ações Administrativas**:

```jsx
// TabAcoes.jsx
export default function TabAcoes({ clienteId, cliente }) {
  const [showAjuste, setShowAjuste] = useState(false)
  const [showConvite, setShowConvite] = useState(false)

  return (
    <div className="space-y-6">
      {/* Ações Rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg border">
          <h4 className="font-semibold mb-4">⚙️ Ações Administrativas</h4>
          <div className="space-y-3">
            <button
              onClick={() => setShowAjuste(true)}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              🎯 Ajustar Pontos
            </button>
            <button
              onClick={() => setShowConvite(true)}
              className="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            >
              🎁 Gerar Convite
            </button>
            <button
              onClick={() => verReservasCliente(clienteId)}
              className="w-full bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
            >
              🏨 Ver Reservas
            </button>
            <button
              onClick={() => toggleStatusCliente(clienteId)}
              className={`w-full px-4 py-2 rounded hover:opacity-90 ${
                cliente?.status === 'ATIVO' 
                  ? 'bg-red-600 text-white' 
                  : 'bg-green-600 text-white'
              }`}
            >
              {cliente?.status === 'ATIVO' ? '🚫 Bloquear' : '✅ Ativar'}
            </button>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border">
          <h4 className="font-semibold mb-4">📊 Relatórios</h4>
          <div className="space-y-3">
            <button
              onClick={() => gerarRelatorioCompleto(clienteId)}
              className="w-full bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
            >
              📋 Relatório Completo
            </button>
            <button
              onClick={() => gerarRelatorioPontos(clienteId)}
              className="w-full bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700"
            >
              🌟 Relatório de Pontos
            </button>
            <button
              onClick={() => gerarRelatorioReservas(clienteId)}
              className="w-full bg-teal-600 text-white px-4 py-2 rounded hover:bg-teal-700"
            >
              🏨 Relatório de Reservas
            </button>
            <button
              onClick={() => enviarEmailCliente(clienteId)}
              className="w-full bg-pink-600 text-white px-4 py-2 rounded hover:bg-pink-700"
            >
              📧 Enviar Email
            </button>
          </div>
        </div>
      </div>

      {/* Histórico de Ações Administrativas */}
      <div className="bg-white p-6 rounded-lg border">
        <h4 className="font-semibold mb-4">📝 Histórico de Ações</h4>
        <div className="space-y-2">
          <div className="flex justify-between items-center py-2 border-b">
            <div>
              <p className="font-medium">Ajuste Manual</p>
              <p className="text-sm text-gray-500">+10 pontos - Bônus de aniversário</p>
            </div>
            <span className="text-sm text-gray-500">02/01/2026</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b">
            <div>
              <p className="font-medium">Geração de Convite</p>
              <p className="text-sm text-gray-500">Código: ABC123</p>
            </div>
            <span className="text-sm text-gray-500">01/01/2026</span>
          </div>
        </div>
      </div>

      {/* Modal de Ajuste de Pontos */}
      {showAjuste && (
        <ModalAjustePontos
          clienteId={clienteId}
          onClose={() => setShowAjuste(false)}
          onSuccess={() => {
            setShowAjuste(false)
            // Recarregar dados
          }}
        />
      )}

      {/* Modal de Convite */}
      {showConvite && (
        <ModalGerarConvite
          clienteId={clienteId}
          onClose={() => setShowConvite(false)}
          onSuccess={() => {
            setShowConvite(false)
            // Recarregar dados
          }}
        />
      )}
    </div>
  )
}
```

---

## 🎯 **COMO INTEGRAR NO SISTEMA ATUAL**

### **1. Adicionar Botão na Tabela Principal**:

```jsx
// Na tabela de histórico existente (linha 458)
<td className="px-6 py-4 whitespace-nowrap text-sm">
  <button
    onClick={() => abrirModalHistorico(cliente.id)}
    className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700"
  >
    📊 Ver Histórico
  </button>
</td>
```

### **2. Estado do Modal no Componente Principal**:

```jsx
// No componente PontosContent (linha 7)
const [modalHistorico, setModalHistorico] = useState({
  isOpen: false,
  clienteId: null,
  clienteNome: ''
})

// Funções para controlar o modal
const abrirModalHistorico = (clienteId, clienteNome) => {
  setModalHistorico({
    isOpen: true,
    clienteId,
    clienteNome
  })
}

const fecharModalHistorico = () => {
  setModalHistorico({
    isOpen: false,
    clienteId: null,
    clienteNome: ''
  })
}
```

### **3. Renderizar o Modal**:

```jsx
// No final do componente (antes de </div>)
{modalHistorico.isOpen && (
  <ModalHistoricoCliente
    isOpen={modalHistorico.isOpen}
    onClose={fecharModalHistorico}
    clienteId={modalHistorico.clienteId}
    clienteNome={modalHistorico.clienteNome}
  />
)}
```

---

## 📋 **BACKEND NECESSÁRIO**

### **Endpoints Adicionais**:
```python
# Adicionar em pontos_routes.py
@router.get("/estatisticas-cliente/{cliente_id}")
async def obter_estatisticas_cliente(cliente_id: int):
    """Estatísticas detalhadas do cliente"""
    return await service.get_estatisticas_cliente(cliente_id)

@router.get("/acoes-admin/{cliente_id}")
async def obter_acoes_admin(cliente_id: int):
    """Histórico de ações administrativas"""
    return await service.get_acoes_admin(cliente_id)
```

---

## 🎉 **BENEFÍCIOS DO MODAL**

### **Para o Administrador**:
- ✅ **Visão completa do cliente**
- ✅ **Ações administrativas centralizadas**
- ✅ **Relatórios e exportações**
- ✅ **Histórico detalhado**

### **Para o Sistema**:
- ✅ **Interface profissional e moderna**
- ✅ **Organização das informações**
- ✅ **Facilidade de uso**
- ✅ **Produtividade aumentada**

---

## 🚀 **IMPLEMENTAÇÃO**

### **Passo 1**: Criar o componente ModalHistoricoCliente
### **Passo 2**: Criar as tabs internas
### **Passo 3**: Integrar com o sistema atual
### **Passo 4**: Adicionar endpoints necessários
### **Passo 5**: Testar e refinar

---

**O modal transformará a experiência administrativa do sistema de pontos!** 🎉

---

**Documentado por**: Cascade AI
**Timestamp**: 2026-01-05 10:18:00 UTC-03:00
