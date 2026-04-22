// Teste de conectividade com backend
const http = require('http');

function testBackendConnection() {
  console.log('🔍 Testando conectividade com backend...');
  
  const options = {
    hostname: 'backend',
    port: 8000,
    path: '/',
    method: 'GET',
    timeout: 5000
  };
  
  const req = http.request(options, (res) => {
    console.log('✅ Status:', res.statusCode);
    console.log('✅ Headers:', res.headers);
    
    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });
    
    res.on('end', () => {
      console.log('✅ Response:', data);
      console.log('🎉 Backend está acessível!');
    });
  });
  
  req.on('error', (err) => {
    console.error('❌ Erro de conexão:', err.message);
  });
  
  req.on('timeout', () => {
    console.error('❌ Timeout de conexão');
    req.destroy();
  });
  
  req.end();
}

testBackendConnection();
