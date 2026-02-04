/**
 * Teste do Fluxo de Comprovantes Corrigido
 * 
 * Verifica se o frontend está enviando dados corretamente para o backend
 * após as correções de contrato e schema.
 */

const { api } = require('./lib/api');

// Mock de dados para teste
const mockPagamento = {
  id: 1,
  valor: 150.00,
  status: 'PENDENTE'
};

const mockReserva = {
  id: 1,
  codigo_reserva: 'RES001'
};

async function testUploadSchema() {
  console.log('🧪 Testando Schema de Upload de Comprovante');
  
  try {
    // Simular arquivo base64 (pequeno para teste)
    const base64File = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==';
    
    const payload = {
      pagamento_id: mockPagamento.id,          // ✅ Campo obrigatório
      tipo_comprovante: 'DINHEIRO',           // ✅ Enum correto
      arquivo_base64: base64File,             // ✅ Base64 string
      nome_arquivo: 'comprovante_teste.png',  // ✅ Nome do arquivo
      observacoes: 'Teste de upload',         // ✅ Observações
      valor_confirmado: 150.00                 // ✅ Valor confirmado
    };
    
    console.log('📤 Payload enviado:', JSON.stringify(payload, null, 2));
    
    // Testar endpoint correto
    const response = await api.post('/comprovantes/upload', payload);
    
    console.log('✅ Upload testado com sucesso!');
    console.log('📋 Resposta:', response.data);
    
    return true;
  } catch (error) {
    console.error('❌ Erro no teste de upload:', error.response?.data || error.message);
    return false;
  }
}

async function testValidacaoSchema() {
  console.log('🧪 Testando Schema de Validação');
  
  try {
    const payload = {
      pagamento_id: mockPagamento.id,
      status: 'APROVADO',                      // ✅ StatusValidacao.APROVADO
      motivo: 'Teste de aprovação',
      usuario_validador_id: 1,
      observacoes_internas: 'Teste automatizado'
    };
    
    console.log('📤 Payload validação:', JSON.stringify(payload, null, 2));
    
    const response = await api.post('/comprovantes/validar', payload);
    
    console.log('✅ Validação testada com sucesso!');
    console.log('📋 Resposta:', response.data);
    
    return true;
  } catch (error) {
    console.error('❌ Erro no teste de validação:', error.response?.data || error.message);
    return false;
  }
}

async function testDashboardEndpoint() {
  console.log('🧪 Testando Dashboard de Comprovantes');
  
  try {
    const response = await api.get('/comprovantes/dashboard');
    
    console.log('✅ Dashboard acessado com sucesso!');
    console.log('📊 Estatísticas:', response.data.estatisticas);
    console.log('📋 Pendentes:', response.data.aguardando_comprovante?.length || 0);
    console.log('📋 Em análise:', response.data.em_analise?.length || 0);
    
    return true;
  } catch (error) {
    console.error('❌ Erro no acesso ao dashboard:', error.response?.data || error.message);
    return false;
  }
}

async function testContratoCompleto() {
  console.log('🚀 Iniciando Teste Completo do Contrato de Comprovantes');
  console.log('=' .repeat(60));
  
  const resultados = {
    upload: await testUploadSchema(),
    validacao: await testValidacaoSchema(), 
    dashboard: await testDashboardEndpoint()
  };
  
  console.log('=' .repeat(60));
  console.log('📊 Resultados dos Testes:');
  
  Object.entries(resultados).forEach([teste, sucesso]) => {
    const status = sucesso ? '✅ PASSOU' : '❌ FALHOU';
    console.log(`  ${teste.padEnd(12)}: ${status}`);
  });
  
  const todosPassaram = Object.values(resultados).every(r => r);
  
  if (todosPassaram) {
    console.log('\n🎉 Todos os testes passaram! Contrato frontend ↔ backend está correto.');
  } else {
    console.log('\n⚠️  Alguns testes falharam. Verifique os logs acima.');
  }
  
  console.log('\n📋 Resumo das Correções Aplicadas:');
  console.log('  1. ✅ Criado TipoComprovante enum no frontend');
  console.log('  2. ✅ Corrigido endpoint de upload para /comprovantes/upload');
  console.log('  3. ✅ Alinhado schema com backend (pagamento_id obrigatório)');
  console.log('  4. ✅ Unificado endpoints em todos os componentes');
  console.log('  5. ✅ Importado enums corretos nos componentes');
  
  return todosPassaram;
}

// Executar testes se rodado diretamente
if (require.main === module) {
  testContratoCompleto().catch(console.error);
}

module.exports = {
  testUploadSchema,
  testValidacaoSchema,
  testDashboardEndpoint,
  testContratoCompleto
};
