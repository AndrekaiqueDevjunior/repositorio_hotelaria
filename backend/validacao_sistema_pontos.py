import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db

async def validar_sistema_pontos():
    db = get_db()
    await db.connect()
    
    print('🔍 VALIDAÇÃO COMPLETA DO SISTEMA DE PONTOS')
    print('=' * 70)
    
    try:
        # 1. Verificar sistemas de pontos existentes
        print('\n📋 1. VERIFICANDO SISTEMAS DE PONTOS...')
        
        sistemas_encontrados = []
        
        # Verificar se PontosUnificadoService existe
        try:
            from app.services.pontos_unificado_service import PontosUnificadoService
            sistemas_encontrados.append("PontosUnificadoService (BACKUP)")
            print('   ✅ PontosUnificadoService encontrado (arquivo .backup)')
        except ImportError as e:
            print(f'   ❌ PontosUnificadoService não encontrado: {e}')
        
        # Verificar se PontosService existe
        try:
            from app.services.pontos_service import PontosService
            sistemas_encontrados.append("PontosService (ATIVO)")
            print('   ✅ PontosService encontrado (ativo)')
        except ImportError as e:
            print(f'   ❌ PontosService não encontrado: {e}')
        
        # Verificar outros sistemas
        outros_sistemas = [
            'pontos_acumulo_service',
            'pontos_populacao_service', 
            'pontos_rp_service',
            'potos_jr_service'
        ]
        
        for sistema in outros_sistemas:
            try:
                __import__(f'app.services.{sistema}')
                sistemas_encontrados.append(sistema)
                print(f'   ⚠️  {sistema} encontrado (deveria ser removido)')
            except ImportError:
                print(f'   ✅ {sistema} não encontrado (correto)')
        
        print(f'\n   📊 Total de sistemas encontrados: {len(sistemas_encontrados)}')
        
        # 2. Verificar regra de cálculo em cada sistema
        print('\n🧮 2. VERIFICANDO REGRA DE CÁLCULO...')
        
        valor_teste = 350.00  # R$ 350,00 = 35 pontos esperados
        pontos_esperados = int(valor_teste / 10)
        
        print(f'   💰 Valor teste: R$ {valor_teste}')
        print(f'   🎯 Pontos esperados: {pontos_esperados} (1 ponto por R$ 10)')
        
        # Testar PontosService
        try:
            pontos_service = PontosService(None, None, None)
            pontos_calculados = pontos_service.calcular_pontos_reserva(valor_teste)
            print(f'   📊 PontosService: {pontos_calculados} pontos {"✅" if pontos_calculados == pontos_esperados else "❌"}')
        except Exception as e:
            print(f'   ❌ Erro no PontosService: {e}')
        
        # Testar PontosUnificadoService (se disponível)
        try:
            pontos_unificados = PontosUnificadoService.calcular_pontos_reserva(valor_teste)
            print(f'   📊 PontosUnificadoService: {pontos_unificados} pontos {"✅" if pontos_unificados == pontos_esperados else "❌"}')
        except Exception as e:
            print(f'   ❌ Erro no PontosUnificadoService: {e}')
        
        # 3. Verificar como o checkout está creditando pontos
        print('\n🚪 3. VERIFICANDO CRÉDITO AUTOMÁTICO NO CHECKOUT...')
        
        # Verificar o código do reserva_repo.py
        with open('app/repositories/reserva_repo.py', 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
        if 'PontosUnificadoService' in conteudo:
            print('   ✅ Checkout está usando PontosUnificadoService')
        elif 'PontosService' in conteudo:
            print('   ⚠️  Checkout está usando PontosService')
        else:
            print('   ❌ Checkout não está creditando pontos automaticamente')
        
        # 4. Verificar API endpoints
        print('\n🌐 4. VERIFICANDO ENDPOINTS DA API...')
        
        # Verificar se existe arquivo de rotas de pontos
        try:
            with open('app/api/v1/pontos_routes.py', 'r', encoding='utf-8') as f:
                rotas_pontos = f.read()
                print('   ✅ Arquivo pontos_routes.py encontrado')
                
                # Contar endpoints
                endpoints = rotas_pontos.count('@router.')
                print(f'   📊 Endpoints encontrados: {endpoints}')
        except FileNotFoundError:
            print('   ❌ pontos_routes.py não encontrado')
        
        # 5. Verificar frontend
        print('\n🖥️  5. VERIFICANDO FRONTEND...')
        
        try:
            with open('../frontend/app/(dashboard)/pontos/page.js', 'r', encoding='utf-8') as f:
                frontend_pontos = f.read()
                
                # Verificar cálculos no frontend
                if 'reduce((sum, t) => sum + t.pontos, 0)' in frontend_pontos:
                    print('   ✅ Frontend está somando pontos corretamente')
                else:
                    print('   ⚠️  Frontend pode não estar somando pontos')
                
                # Verificar chamadas à API
                if '/pontos/saldo/' in frontend_pontos:
                    print('   ✅ Frontend está chamando API de saldo')
                else:
                    print('   ❌ Frontend não está chamando API de saldo')
                    
                if '/pontos/historico/' in frontend_pontos:
                    print('   ✅ Frontend está chamando API de histórico')
                else:
                    print('   ❌ Frontend não está chamando API de histórico')
                    
        except FileNotFoundError:
            print('   ❌ Arquivo frontend/pontos/page.js não encontrado')
        
        # 6. Verificar consistência entre sistemas
        print('\n🔄 6. VERIFICANDO CONSISTÊNCIA...')
        
        inconsistencias = []
        
        if len(sistemas_encontrados) > 1:
            inconsistencias.append("Múltiplos sistemas de pontos encontrados")
        
        # Verificar se há duplicação de lógica
        try:
            with open('app/services/pontos_service.py', 'r', encoding='utf-8') as f:
                pontos_service_content = f.read()
                
            with open('app/services/pontos_unificado_service.py.backup', 'r', encoding='utf-8') as f:
                pontos_unificado_content = f.read()
                
            # Comparar regras de cálculo
            if 'int(valor_total / 10)' in pontos_service_content and 'int(valor_total / 10)' in pontos_unificado_content:
                print('   ✅ Ambos sistemas usam a mesma regra (1 ponto/R$10)')
            else:
                inconsistencias.append("Regras de cálculo diferentes entre sistemas")
                
        except Exception as e:
            print(f'   ⚠️  Não foi possível comparar regras: {e}')
        
        # 7. Verificar dados reais no banco
        print('\n💾 7. VERIFICANDO DADOS REAIS...')
        
        try:
            # Contar transações de pontos
            transacoes = await db.transacaopontos.find_many(take=5)
            print(f'   📊 Transações de pontos no banco: {len(transacoes)}')
            
            if transacoes:
                print('   📋 Últimas transações:')
                for t in transacoes:
                    print(f'      - ID: {t.id} | Cliente: {t.clienteId} | Pontos: {t.pontos} | Tipo: {t.tipo}')
            
            # Contar usuários com pontos
            usuarios_pontos = await db.usuariopontos.find_many(take=5)
            print(f'   👥 Usuários com pontos: {len(usuarios_pontos)}')
            
            if usuarios_pontos:
                print('   📋 Saldos:')
                for u in usuarios_pontos:
                    print(f'      - Cliente: {u.clienteId} | Saldo: {u.saldo}')
                    
        except Exception as e:
            print(f'   ❌ Erro ao consultar banco: {e}')
        
        # 8. Recomendações
        print('\n💡 8. RECOMENDAÇÕES...')
        
        if len(sistemas_encontrados) > 1:
            print('   🔧 REMOVER sistemas duplicados:')
            for sistema in sistemas_encontrados:
                if sistema != "PontosService (ATIVO)":
                    print(f'      - Remover {sistema}')
        
        if inconsistencias:
            print('   🔧 CORRIGIR inconsistências:')
            for inc in inconsistencias:
                print(f'      - {inc}')
        else:
            print('   ✅ Sistema consistente!')
        
        print('\n' + '=' * 70)
        print('🎉 VALIDAÇÃO CONCLUÍDA!')
        print('=' * 70)
        
        return {
            "sistemas_encontrados": sistemas_encontrados,
            "inconsistencias": inconsistencias,
            "regra_calculo": "1 ponto por R$ 10",
            "status": "CONSISTENTE" if not inconsistencias else "COM INCONSISTÊNCIAS"
        }
        
    except Exception as e:
        print(f'\n❌ ERRO NA VALIDAÇÃO: {str(e)}')
        return {
            "erro": str(e),
            "status": "ERRO"
        }

if __name__ == "__main__":
    resultado = asyncio.run(validar_sistema_pontos())
    print(f'\n📊 Resultado Final: {resultado}')
