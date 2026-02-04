// Teste simplificado do Sistema RP via Frontend
// Execute no console do navegador: http://localhost:8080/test-rp-frontend.html

const API_BASE = 'http://localhost:8080';

async function testAPIsRP() {
    console.log('🧪 Iniciando testes do Sistema RP via Frontend');
    console.log('='.repeat(50));
    
    const tests = [
        {
            name: '1. Health Check',
            url: `${API_BASE}/health`,
            method: 'GET'
        },
        {
            name: '2. Regras RP',
            url: `${API_BASE}/api/v1/pontos-rp/regras`,
            method: 'GET'
        },
        {
            name: '3. Prêmios RP',
            url: `${API_BASE}/api/v1/pontos-rp/premios`,
            method: 'GET'
        },
        {
            name: '4. Saldo RP',
            url: `${API_BASE}/api/v1/pontos-rp/saldo/1`,
            method: 'GET'
        },
        {
            name: '5. Histórico RP',
            url: `${API_BASE}/api/v1/pontos-rp/historico/1`,
            method: 'GET'
        },
        {
            name: '6. Simulação Cálculo',
            url: `${API_BASE}/api/v1/pontos-rp/simular-calculo?tipo_suite=REAL&num_diarias=3&diarias_pendentes=0`,
            method: 'POST'
        }
    ];
    
    const results = [];
    
    for (const test of tests) {
        try {
            console.log(`\n🔍 ${test.name}`);
            console.log(`   URL: ${test.url}`);
            
            const response = await fetch(test.url, {
                method: test.method,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                }
            });
            
            const status = response.status;
            const data = await response.json();
            
            console.log(`   ✅ Status: ${status}`);
            console.log(`   📊 Dados: ${JSON.stringify(data, null, 2).substring(0, 200)}...`);
            
            results.push({
                test: test.name,
                status: status,
                success: status === 200,
                data: data
            });
            
        } catch (error) {
            console.log(`   ❌ Erro: ${error.message}`);
            results.push({
                test: test.name,
                status: 0,
                success: false,
                error: error.message
            });
        }
    }
    
    // Resumo final
    console.log('\n' + '='.repeat(50));
    console.log('📊 RESUMO DOS TESTES');
    console.log('='.repeat(50));
    
    const passed = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;
    const total = results.length;
    
    console.log(`✅ Passaram: ${passed}/${total}`);
    console.log(`❌ Falharam: ${failed}/${total}`);
    
    if (passed === total) {
        console.log('\n🎉 TODOS OS TESTES PASSARAM!');
        console.log('✅ Sistema RP está funcionando corretamente via Frontend!');
    } else {
        console.log('\n⚠️ ALGUNS TESTES FALHARAM');
        console.log('❌ Verificar configuração do sistema');
    }
    
    // Teste específico de cálculo se tudo passou
    if (passed === total) {
        console.log('\n🧪 Teste adicional: Validação de cálculo');
        
        try {
            const response = await fetch(`${API_BASE}/api/v1/pontos-rp/simular-calculo?tipo_suite=LUXO&num_diarias=3&diarias_pendentes=0`);
            const data = await response.json();
            
            if (data.success && data.calculo) {
                const calc = data.calculo;
                console.log(`   ✅ Suíte Luxo, 3 diárias:`);
                console.log(`      Pontos gerados: ${calc.pontos_gerados} RP`);
                console.log(`      Diárias restantes: ${calc.diarias_restantes}`);
                console.log(`      Detalhamento: ${calc.detalhamento}`);
                
                // Validação específica
                if (calc.pontos_gerados === 3 && calc.diarias_restantes === 1) {
                    console.log('   ✅ Cálculo correto!');
                } else {
                    console.log('   ❌ Cálculo incorreto!');
                }
            }
        } catch (error) {
            console.log(`   ❌ Erro no teste de cálculo: ${error.message}`);
        }
    }
    
    return results;
}

// Executar testes
testAPIsRP();
