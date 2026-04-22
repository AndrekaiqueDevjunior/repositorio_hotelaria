// Teste simples para verificar se a API está funcionando
import { api } from './lib/api.js';

async function testAPI() {
  console.log('🔍 Testando API...');
  
  try {
    // Testar endpoint simples sem autenticação
    console.log('📡 Testando endpoint público...');
    const response = await api.get('/pontos/regras');
    console.log('✅ API funcionando:', response.data);
    
    // Testar endpoint de clientes (requer autenticação)
    console.log('📡 Testando endpoint clientes...');
    try {
      const clientesResponse = await api.get('/clientes');
      console.log('✅ Clientes:', clientesResponse.data);
    } catch (error) {
      console.log('❌ Clientes (autenticação necessária):', error.response?.status);
    }
    
    // Testar endpoint de pontos (requer autenticação)
    console.log('📡 Testando endpoint pontos...');
    try {
      const pontosResponse = await api.get('/pontos/saldo/1');
      console.log('✅ Pontos:', pontosResponse.data);
    } catch (error) {
      console.log('❌ Pontos (autenticação necessária):', error.response?.status);
      console.log('❌ Erro detalhado:', error.response?.data);
    }
    
  } catch (error) {
    console.error('❌ Erro geral na API:', error);
  }
}

// Executar teste
testAPI();
