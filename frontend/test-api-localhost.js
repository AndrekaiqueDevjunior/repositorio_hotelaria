// Teste simples para verificar se a API está funcionando via localhost
import axios from 'axios';

async function testAPI() {
  console.log('🔍 Testando API via localhost...');
  
  // Forçar baseURL para localhost
  const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    timeout: 10000,
  });
  
  try {
    // Testar endpoint simples sem autenticação
    console.log('📡 Testando endpoint público...');
    const response = await api.get('/pontos/regras');
    console.log('✅ API funcionando:', response.data);
    
    // Testar endpoint de pontos (sem autenticação para ver erro)
    console.log('📡 Testando endpoint pontos...');
    try {
      const pontosResponse = await api.get('/pontos/saldo/1');
      console.log('✅ Pontos:', pontosResponse.data);
    } catch (error) {
      console.log('❌ Pontos (autenticação necessária):', error.response?.status);
      console.log('❌ Erro detalhado:', error.response?.data);
    }
    
  } catch (error) {
    console.error('❌ Erro geral na API:', error.message);
  }
}

// Executar teste
testAPI();
