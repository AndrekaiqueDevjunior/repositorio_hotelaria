'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '../../../contexts/AuthContext'
import { useToast } from '../../../contexts/ToastContext'
import { api } from '../../../lib/api'

const TEMPORADAS = ['ALTA', 'MEDIA', 'BAIXA']
const TIPOS_SUITE = ['LUXO', 'DUPLA', 'MASTER', 'REAL']

export default function TarifasPage() {
  const { user } = useAuth()
  const { addToast } = useToast()

  const [tarifas, setTarifas] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingTarifa, setEditingTarifa] = useState(null)
  const [feedback, setFeedback] = useState(null) // { tipo: 'sucesso' | 'erro', titulo, mensagem }
  const [formData, setFormData] = useState({
    suite_tipo: 'LUXO',
    temporada: 'ALTA',
    data_inicio: '',
    data_fim: '',
    preco_diaria: '',
    ativo: true
  })

  const mostrarFeedback = (tipo, titulo, mensagem) => {
    setFeedback({ tipo, titulo, mensagem })
    addToast({ tipo: tipo === 'sucesso' ? 'success' : 'error', titulo, mensagem })
  }

  useEffect(() => {
    fetchTarifas()
  }, [])

  const fetchTarifas = async () => {
    try {
      setLoading(true)
      const response = await api.get('/tarifas')
      setTarifas(response.data || [])
    } catch (error) {
      mostrarFeedback('erro', 'Erro ao buscar tarifas', error.response?.data?.detail || 'Nao foi possivel carregar a lista de tarifas.')
      console.error('Erro:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      if (editingTarifa) {
        await api.put(`/tarifas/${editingTarifa.id}`, formData)
        mostrarFeedback('sucesso', 'Tarifa atualizada', 'A tarifa foi atualizada com sucesso.')
      } else {
        await api.post('/tarifas', formData)
        mostrarFeedback('sucesso', 'Tarifa criada', 'A nova tarifa foi criada com sucesso.')
      }

      setShowModal(false)
      setEditingTarifa(null)
      resetForm()
      fetchTarifas()
    } catch (error) {
      mostrarFeedback(
        'erro',
        editingTarifa ? 'Erro ao atualizar tarifa' : 'Erro ao criar tarifa',
        error.response?.data?.detail || 'Nao foi possivel salvar a tarifa.'
      )
      console.error('Erro:', error)
    }
  }

  const handleEdit = (tarifa) => {
    setEditingTarifa(tarifa)
    setFormData({
      suite_tipo: tarifa.suite_tipo,
      temporada: tarifa.temporada,
      data_inicio: new Date(tarifa.data_inicio).toISOString().split('T')[0],
      data_fim: new Date(tarifa.data_fim).toISOString().split('T')[0],
      preco_diaria: tarifa.preco_diaria,
      ativo: tarifa.ativo
    })
    setShowModal(true)
  }

  const handleDelete = async (id) => {
    if (!confirm('Tem certeza que deseja excluir esta tarifa?')) return
    
    try {
      await api.delete(`/tarifas/${id}`)
      mostrarFeedback('sucesso', 'Tarifa excluida', 'A tarifa foi excluida com sucesso.')
      fetchTarifas()
    } catch (error) {
      mostrarFeedback('erro', 'Erro ao excluir tarifa', error.response?.data?.detail || 'Nao foi possivel excluir a tarifa.')
      console.error('Erro:', error)
    }
  }

  const toggleStatus = async (id, ativo) => {
    try {
      await api.patch(`/tarifas/${id}`, { ativo: !ativo })
      mostrarFeedback('sucesso', !ativo ? 'Tarifa ativada' : 'Tarifa desativada', `A tarifa foi ${!ativo ? 'ativada' : 'desativada'} com sucesso.`)
      fetchTarifas()
    } catch (error) {
      mostrarFeedback('erro', 'Erro ao alterar status', error.response?.data?.detail || 'Nao foi possivel alterar o status da tarifa.')
      console.error('Erro:', error)
    }
  }

  const resetForm = () => {
    setFormData({
      suite_tipo: 'LUXO',
      temporada: 'ALTA',
      data_inicio: '',
      data_fim: '',
      preco_diaria: '',
      ativo: true
    })
  }

  const openModal = () => {
    resetForm()
    setEditingTarifa(null)
    setShowModal(true)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Carregando...</div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Tarifas</h1>
        <button
          onClick={openModal}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Nova Tarifa
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo Suíte</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Temporada</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Período</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Diária</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ações</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tarifas.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                  Nenhuma tarifa encontrada
                </td>
              </tr>
            ) : (
              tarifas.map((tarifa) => (
                <tr key={tarifa.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {tarifa.suite_tipo}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      tarifa.temporada === 'ALTA' ? 'bg-red-100 text-red-800' :
                      tarifa.temporada === 'MEDIA' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {tarifa.temporada}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(tarifa.data_inicio).toLocaleDateString('pt-BR')} até{' '}
                    {new Date(tarifa.data_fim).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                    R$ {Number(tarifa.preco_diaria).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      tarifa.ativo ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {tarifa.ativo ? 'Ativa' : 'Inativa'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(tarifa)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => toggleStatus(tarifa.id, tarifa.ativo)}
                        className={`${tarifa.ativo ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'}`}
                      >
                        {tarifa.ativo ? 'Desativar' : 'Ativar'}
                      </button>
                      <button
                        onClick={() => handleDelete(tarifa.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Excluir
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingTarifa ? 'Editar Tarifa' : 'Nova Tarifa'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo Suíte
                </label>
                <select
                  value={formData.suite_tipo}
                  onChange={(e) => setFormData({ ...formData, suite_tipo: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  required
                >
                  {TIPOS_SUITE.map(tipo => (
                    <option key={tipo} value={tipo}>{tipo}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temporada
                </label>
                <select
                  value={formData.temporada}
                  onChange={(e) => setFormData({ ...formData, temporada: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  required
                >
                  {TEMPORADAS.map(temp => (
                    <option key={temp} value={temp}>{temp}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data de Início
                </label>
                <input
                  type="date"
                  value={formData.data_inicio}
                  onChange={(e) => setFormData({ ...formData, data_inicio: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data de Fim
                </label>
                <input
                  type="date"
                  value={formData.data_fim}
                  onChange={(e) => setFormData({ ...formData, data_fim: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preço Diária (R$)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.preco_diaria}
                  onChange={(e) => setFormData({ ...formData, preco_diaria: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="ativo"
                  checked={formData.ativo}
                  onChange={(e) => setFormData({ ...formData, ativo: e.target.checked })}
                  className="mr-2"
                />
                <label htmlFor="ativo" className="text-sm font-medium text-gray-700">
                  Tarifa ativa
                </label>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {editingTarifa ? 'Atualizar' : 'Criar'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de feedback (sucesso/erro) das acoes de CRUD */}
      {feedback && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-lg p-6 w-full max-w-sm shadow-xl">
            <div className="flex items-center gap-3 mb-3">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full text-xl font-bold ${
                feedback.tipo === 'sucesso' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                {feedback.tipo === 'sucesso' ? '✓' : '!'}
              </div>
              <h3 className="text-lg font-bold text-gray-900">{feedback.titulo}</h3>
            </div>
            <p className="text-sm text-gray-600 mb-5">{feedback.mensagem}</p>
            <button
              type="button"
              onClick={() => setFeedback(null)}
              className={`w-full px-4 py-2 rounded-lg font-semibold text-white ${
                feedback.tipo === 'sucesso' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              OK
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
