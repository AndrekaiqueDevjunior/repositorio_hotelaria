#!/usr/bin/env python3
"""
🧪 TESTE DA API REAL POINTS
============================

Teste completo da API Real Points via HTTP requests
"""

import requests
import json

def testar_api_real_points():
    """Testar todos os endpoints da API Real Points"""
    
    print('🧪 TESTE DA API REAL POINTS')
    print('=' * 50)
    
    base_url = 'http://localhost:8000/api/v1/real-points'
    
    # Teste 1: Obter tabela oficial
    print('\n📋 TESTE 1: Tabela Oficial')
    try:
        response = requests.get(f'{base_url}/tabela')
        if response.status_code == 200:
            tabela = response.json()
            print(f'✅ Tabela oficial: {len(tabela)} suítes')
            for suite, dados in tabela.items():
                print(f'   {suite}: {dados["rp_por_bloco"]} RP por bloco')
        else:
            print(f'❌ Erro tabela: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Erro tabela: {e}')
        return False
    
    # Teste 2: Calcular pontos
    print('\n🧮 TESTE 2: Calcular Pontos')
    try:
        response = requests.post(
            f'{base_url}/calcular',
            params={'suite': 'MASTER', 'diarias': 2, 'valor_total': 960}
        )
        if response.status_code == 200:
            resultado = response.json()
            print(f'✅ Cálculo MASTER: {resultado["rp_calculados"]} RP ({resultado["detalhe"]})')
        else:
            print(f'❌ Erro cálculo: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Erro cálculo: {e}')
        return False
    
    # Teste 3: Listar prêmios
    print('\n🎁 TESTE 3: Listar Prêmios')
    try:
        response = requests.get(f'{base_url}/premios')
        if response.status_code == 200:
            premios = response.json()
            print(f'✅ Prêmios disponíveis: {len(premios)}')
            for premio_id, premio in premios.items():
                print(f'   {premio_id}: {premio["custo_rp"]} RP - {premio["nome"]}')
        else:
            print(f'❌ Erro prêmios: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Erro prêmios: {e}')
        return False
    
    # Teste 4: Simular cálculo completo
    print('\n🔍 TESTE 4: Simulação Completa')
    try:
        response = requests.post(
            f'{base_url}/simular',
            params={'suite': 'REAL', 'diarias': 4, 'valor_total': 1100}
        )
        if response.status_code == 200:
            simulacao = response.json()
            print(f'✅ Simulação REAL: {simulacao["rp_calculados"]} RP')
            print(f'   Pode conceder: {simulacao["pode_conceder"]}')
            print(f'   Validações: {len(simulacao["validacoes"])}')
            print(f'   Erros: {len(simulacao["erros"])}')
        else:
            print(f'❌ Erro simulação: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Erro simulação: {e}')
        return False
    
    # Teste 5: Validar requisitos
    print('\n✅ TESTE 5: Validar Requisitos')
    try:
        reserva_teste = {
            'id': 1,
            'codigo': 'TEST-001',
            'cliente_id': 123,
            'tipo_suite': 'MASTER',
            'num_diarias': 2,
            'valor_total': 960,
            'status': 'CHECKED_OUT',
            'pagamento_confirmado': True,
            'created_at': '2026-01-10T10:00:00Z',
            'checkout_realizado': '2026-01-12T12:00:00Z'
        }
        
        response = requests.post(
            f'{base_url}/validar-requisitos',
            json=reserva_teste
        )
        if response.status_code == 200:
            resultado = response.json()
            print(f'✅ Validação: {resultado["pode_conceder"]} - {resultado["motivo"]}')
        else:
            print(f'❌ Erro validação: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Erro validação: {e}')
        return False
    
    # Teste 6: Validar antifraude
    print('\n🛡️ TESTE 6: Validar Antifraude')
    try:
        response = requests.post(
            f'{base_url}/validar-antifraude',
            json=reserva_teste
        )
        if response.status_code == 200:
            resultado = response.json()
            print(f'✅ Antifraude: {resultado["valido"]} - {resultado["motivo"]}')
        else:
            print(f'❌ Erro antifraude: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Erro antifraude: {e}')
        return False
    
    # Teste 7: Verificar resgate
    print('\n🎁 TESTE 7: Verificar Resgate')
    try:
        response = requests.post(
            f'{base_url}/pode-resgatar',
            params={'cliente_rp': 25, 'premio_id': 'luminaria'}
        )
        if response.status_code == 200:
            resultado = response.json()
            print(f'✅ Resgate: {resultado["pode_resgatar"]} - {resultado["motivo"]}')
        else:
            print(f'❌ Erro resgate: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Erro resgate: {e}')
        return False
    
    return True

if __name__ == "__main__":
    sucesso = testar_api_real_points()
    
    print(f'\n🎯 RESULTADO FINAL:')
    if sucesso:
        print('✅ API REAL POINTS 100% FUNCIONAL!')
        print('🌐 URL NGROK: https://jacoby-unshifted-kylie.ngrok-free.dev')
        print('📋 Endpoints disponíveis:')
        print('   GET /api/v1/real-points/tabela')
        print('   GET /api/v1/real-points/premios')
        print('   POST /api/v1/real-points/calcular')
        print('   POST /api/v1/real-points/simular')
        print('   POST /api/v1/real-points/validar-requisitos')
        print('   POST /api/v1/real-points/validar-antifraude')
        print('   POST /api/v1/real-points/pode-resgatar')
        print('\n🎉 SISTEMA PRONTO PARA TESTES VIA NGROK!')
    else:
        print('❌ API COM PROBLEMAS - VERIFICAR LOGS')
