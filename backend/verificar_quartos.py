#!/usr/bin/env python3
import os
import requests
import json

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== VERIFICANDO QUARTOS ADICIONADOS ===')
print()

# 1. Fazer Login
print('1. FAZENDO LOGIN...')
admin_password = os.environ.get('ADMIN_PASSWORD')
if not admin_password:
    raise RuntimeError('Defina ADMIN_PASSWORD no ambiente antes de executar este script.')
login_data = {'email': 'admin@hotelreal.com.br', 'password': admin_password}
r = requests.post(f'{base_url}/login', json=login_data)
print(f'Status: {r.status_code}')

if r.status_code == 200:
    print('✅ Login bem-sucedido')
    cookies = r.cookies.get_dict()
    
    # 2. Listar todos os quartos
    print()
    print('2. LISTANDO TODOS OS QUARTOS...')
    r = requests.get(f'{base_url}/quartos', cookies=cookies)
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        response_data = r.json()
        quartos = response_data['quartos']
        
        print(f'✅ Total de quartos no sistema: {len(quartos)}')
        print()
        
        # Agrupar por tipo
        por_tipo = {}
        for q in quartos:
            tipo = q['tipo_suite']
            if tipo not in por_tipo:
                por_tipo[tipo] = []
            por_tipo[tipo].append(q)
        
        print('📋 QUARTOS POR TIPO:')
        
        for tipo in ['LUXO', 'MASTER', 'REAL']:
            if tipo in por_tipo:
                quartos_tipo = por_tipo[tipo]
                print(f'   • {tipo}: {len(quartos_tipo)} quartos')
                
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
                    
                    print(f'     - {emoji} {status}: {count}')
        
        print()
        print('🏨 LISTA COMPLETA DE QUARTOS:')
        print()
        
        for tipo in ['LUXO', 'MASTER', 'REAL']:
            if tipo in por_tipo:
                quartos_tipo = sorted(por_tipo[tipo], key=lambda x: x['numero'])
                print(f'   {tipo}:')
                
                for q in quartos_tipo:
                    status_emoji = {
                        'LIVRE': '🟢',
                        'OCUPADO': '🔴',
                        'MANUTENCAO': '🟡',
                        'BLOQUEADO': '⚫'
                    }.get(q['status'], '❓')
                    
                    print(f'      {status_emoji} Quarto {q["numero"]} - Diária: R$ {q["diaria"]}')
        
        print()
        print('🎉 QUARTOS ADICIONADOS COM SUCESSO!')
        print()
        print('📊 RESUMO FINAL:')
        print(f'   • LUXO: {len(por_tipo.get("LUXO", []))} quartos')
        print(f'   • MASTER: {len(por_tipo.get("MASTER", []))} quartos')
        print(f'   • REAL: {len(por_tipo.get("REAL", []))} quartos')
        print(f'   • TOTAL: {len(quartos)} quartos')
        
        # Verificar quartos disponíveis
        print()
        print('3. VERIFICANDO DISPONIBILIDADE...')
        r = requests.get(f'{base_url}/quartos/disponiveis', cookies=cookies)
        
        if r.status_code == 200:
            disponiveis = r.json()
            print(f'✅ Quartos disponíveis agora: {len(disponiveis)}')
            
            if disponiveis:
                print('   Quartos livres para reserva:')
                for q in sorted(disponiveis, key=lambda x: x['numero']):
                    print(f'      🟢 {q["numero"]} - {q["tipo_suite"]} - R$ {q["diaria"]}')
        
    else:
        print(f'❌ Erro ao listar quartos: {r.text}')
else:
    print(f'❌ Erro no login: {r.text}')

print()
print('=== VERIFICAÇÃO CONCLUÍDA ===')
