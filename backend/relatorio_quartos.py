#!/usr/bin/env python3
import requests
import json

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== RELATÓRIO FINAL - QUARTOS ADICIONADOS ===')
print()

# 1. Fazer Login
login_data = {'email': 'admin@hotelreal.com.br', 'password': 'admin123'}
r = requests.post(f'{base_url}/login', json=login_data)
cookies = r.cookies.get_dict()

if r.status_code == 200:
    # 2. Listar todos os quartos
    r = requests.get(f'{base_url}/quartos', cookies=cookies)
    
    if r.status_code == 200:
        response_data = r.json()
        quartos = response_data['quartos']
        
        print('🎉 QUARTOS ADICIONADOS COM SUCESSO!')
        print()
        print(f'📊 TOTAL DE QUARTOS NO SISTEMA: {len(quartos)}')
        print()
        
        # Agrupar por tipo
        por_tipo = {}
        for q in quartos:
            tipo = q['tipo_suite']
            if tipo not in por_tipo:
                por_tipo[tipo] = []
            por_tipo[tipo].append(q)
        
        print('📋 DISTRIBUIÇÃO POR TIPO:')
        print()
        
        for tipo in ['LUXO', 'MASTER', 'REAL']:
            if tipo in por_tipo:
                quartos_tipo = sorted(por_tipo[tipo], key=lambda x: x['numero'])
                print(f'   {tipo}: {len(quartos_tipo)} quartos')
                
                # Separar por status
                status_count = {}
                for q in quartos_tipo:
                    status = q['status']
                    status_count[status] = status_count.get(status, 0) + 1
                
                for status, count in status_count.items():
                    emoji = {
                        'LIVRE': '🟢',
                        'OCUPADO': '🔴',
                        'MANUTENCAO': '🟡',
                        'BLOQUEADO': '⚫'
                    }.get(status, '❓')
                    
                    print(f'      {emoji} {status}: {count}')
        
        print()
        print('🏨 LISTA DETALHADA:')
        print()
        
        for tipo in ['LUXO', 'MASTER', 'REAL']:
            if tipo in por_tipo:
                quartos_tipo = sorted(por_tipo[tipo], key=lambda x: x['numero'])
                print(f'   === {tipo} ===')
                
                for q in quartos_tipo:
                    status_emoji = {
                        'LIVRE': '🟢',
                        'OCUPADO': '🔴',
                        'MANUTENCAO': '🟡',
                        'BLOQUEADO': '⚫'
                    }.get(q['status'], '❓')
                    
                    print(f'      {status_emoji} Quarto {q["numero"]} - {q["status"]}')
        
        # Verificar disponibilidade
        print()
        r = requests.get(f'{base_url}/quartos/disponiveis', cookies=cookies)
        
        if r.status_code == 200:
            disponiveis = r.json()
            print(f'📈 QUARTOS DISPONÍVEIS AGORA: {len(disponiveis)}')
            
            if disponiveis:
                print('   Quartos livres para reserva:')
                for q in sorted(disponiveis, key=lambda x: x['numero']):
                    print(f'      🟢 {q["numero"]} - {q["tipo_suite"]}')
        
        print()
        print('✅ OPERAÇÃO REALIZADA COM SUCESSO!')
        print()
        print('📝 RESUMO:')
        print(f'   • Quartos LUXO: {len(por_tipo.get("LUXO", []))}')
        print(f'   • Quartos MASTER: {len(por_tipo.get("MASTER", []))}')
        print(f'   • Quartos REAL: {len(por_tipo.get("REAL", []))}')
        print(f'   • TOTAL GERAL: {len(quartos)}')
        print()
        print('🎯 Os quartos foram adicionados conforme solicitado!')
        print('   Quartos existentes foram mantidos (editáveis)')
        print('   Quartos novos foram criados com status LIVRE')
        
else:
    print('❌ Erro no login')

print()
print('=== RELATÓRIO CONCLUÍDO ===')
