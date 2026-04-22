// Funções para corrigir as ações do frontend de quartos
// Adicionar estas funções ao arquivo page.js de reservas

// 1. Estados necessários (adicionar ao useState)
const quartosStates = `
  // Estados para gestão de quartos
  const [showQuartoModal, setShowQuartoModal] = useState(false)
  const [quartoForm, setQuartoForm] = useState({
    numero: '',
    tipo_suite: 'LUXO',
    status: 'LIVRE'
  })
  const [editingQuarto, setEditingQuarto] = useState(null)
`;

// 2. Funções CRUD para quartos
const quartosFunctions = `
  // Funções para gestão de quartos
  const handleCreateQuarto = async () => {
    try {
      setLoading(true)
      
      // Validar formulário
      if (!quartoForm.numero.trim()) {
        toast.error('Número do quarto é obrigatório')
        return
      }
      
      // Verificar se quarto já existe
      const quartoExistente = quartos.find(q => q.numero === quartoForm.numero)
      if (quartoExistente && !editingQuarto) {
        toast.error('Quarto com este número já existe')
        return
      }
      
      const quartoData = {
        numero: quartoForm.numero,
        tipo_suite: quartoForm.tipo_suite,
        status: quartoForm.status
      }
      
      if (editingQuarto) {
        // Editar quarto existente
        await api.put(\`/quartos/\${editingQuarto.numero}\`, quartoData)
        toast.success('Quarto atualizado com sucesso!')
      } else {
        // Criar novo quarto
        await api.post('/quartos', quartoData)
        toast.success('Quarto criado com sucesso!')
      }
      
      // Resetar formulário e recarregar
      setQuartoForm({ numero: '', tipo_suite: 'LUXO', status: 'LIVRE' })
      setEditingQuarto(null)
      setShowQuartoModal(false)
      loadQuartos()
      
    } catch (error) {
      console.error('Erro ao salvar quarto:', error)
      toast.error(formatErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }
  
  const handleEditQuarto = (quarto) => {
    setEditingQuarto(quarto)
    setQuartoForm({
      numero: quarto.numero,
      tipo_suite: quarto.tipo_suite,
      status: quarto.status
    })
    setShowQuartoModal(true)
  }
  
  const handleDeleteQuarto = async (quarto) => {
    if (!window.confirm(\`Tem certeza que deseja excluir o quarto \${quarto.numero}?\`)) {
      return
    }
    
    try {
      setLoading(true)
      await api.delete(\`/quartos/\${quarto.numero}\`)
      toast.success('Quarto excluído com sucesso!')
      loadQuartos()
    } catch (error) {
      console.error('Erro ao excluir quarto:', error)
      toast.error(formatErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }
  
  const handleHistoricoQuarto = (quarto) => {
    // Implementar modal de histórico do quarto
    toast.info(\`Histórico do quarto \${quarto.numero} - Em desenvolvimento\`)
  }
  
  const updateQuartoForm = (field, value) => {
    setQuartoForm(prev => ({
      ...prev,
      [field]: value
    }))
  }
`;

// 3. Modal para criação/edição de quartos
const quartoModal = `
  {/* Modal de Criação/Edição de Quarto */}
  {showQuartoModal && (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">
          {editingQuarto ? '✏️ Editar Quarto' : '➕ Novo Quarto'}
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Número do Quarto
            </label>
            <input
              type="text"
              value={quartoForm.numero}
              onChange={(e) => updateQuartoForm('numero', e.target.value)}
              className="w-full p-2 border rounded-lg"
              placeholder="Ex: 101, 201, 301"
              disabled={!!editingQuarto}
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de Suíte
            </label>
            <select
              value={quartoForm.tipo_suite}
              onChange={(e) => updateQuartoForm('tipo_suite', e.target.value)}
              className="w-full p-2 border rounded-lg"
            >
              <option value="LUXO">Luxo</option>
              <option value="MASTER">Master</option>
              <option value="REAL">Real</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={quartoForm.status}
              onChange={(e) => updateQuartoForm('status', e.target.value)}
              className="w-full p-2 border rounded-lg"
            >
              <option value="LIVRE">Livre</option>
              <option value="OCUPADO">Ocupado</option>
              <option value="MANUTENCAO">Manutenção</option>
              <option value="BLOQUEADO">Bloqueado</option>
            </select>
          </div>
        </div>
        
        <div className="flex gap-2 mt-6">
          <button
            onClick={handleCreateQuarto}
            disabled={loading}
            className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Salvando...' : (editingQuarto ? 'Atualizar' : 'Criar')}
          </button>
          <button
            onClick={() => {
              setShowQuartoModal(false)
              setEditingQuarto(null)
              setQuartoForm({ numero: '', tipo_suite: 'LUXO', status: 'LIVRE' })
            }}
            className="px-4 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )}
`;

// 4. Botões corrigidos
const correctedButtons = `
  <td className="px-4 py-3">
    <div className="flex gap-2">
      <button 
        onClick={() => handleHistoricoQuarto(q)}
        className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
        title="Ver histórico do quarto"
      >
        📋 Histórico
      </button>
      <button 
        onClick={() => handleEditQuarto(q)}
        className="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200"
        title="Editar quarto"
      >
        ✏️ Editar
      </button>
      <button 
        onClick={() => handleDeleteQuarto(q)}
        className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
        title="Excluir quarto"
      >
        🗑️ Excluir
      </button>
    </div>
  </td>
`;

console.log('🔧 Funções para corrigir o frontend de quartos criadas!');
console.log('📋 Implementar:');
console.log('1. Adicionar estados necessários');
console.log('2. Adicionar funções CRUD');
console.log('3. Adicionar modal');
console.log('4. Corrigir botões');

export { quartosStates, quartosFunctions, quartoModal, correctedButtons };
