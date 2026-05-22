#!/usr/bin/env python3
import os
import requests
import json
from datetime import datetime

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== ADICIONANDO QUARTOS AO SISTEMA ===')
print()

# Dados dos quartos da imagem
quartos_para_adicionar = [
    # Quartos LUXO
    {'numero': '106', 'tipo_suite': 'LUXO', 'capacidade': 2, 'diaria': 150.00},
    {'numero': '107', 'tipo_suite': 'LUXO', 'capacidade': 2, 'diaria': 150.00},
    {'numero': '108', 'tipo_suite': 'LUXO', 'capacidade': 2, 'diaria': 150.00},
    {'numero': '109', 'tipo_suite': 'LUXO', 'capacidade': 2, 'diaria': 150.00},
    {'numero': '110', 'tipo_suite': 'LUXO', 'capacidade': 2, 'diaria': 150.00},
    
    # Quartos MASTER
    {'numero': '203', 'tipo_suite': 'MASTER', 'capacidade': 2, 'diaria': 200.00},
    {'numero': '204', 'tipo_suite': 'MASTER', 'capacidade': 2, 'diaria': 200.00},
    {'numero': '205', 'tipo_suite': 'MASTER', 'capacidade': 2, 'diaria': 200.00},
    {'numero': '206', 'tipo_suite': 'MASTER', 'capacidade': 2, 'diaria': 200.00},
    {'numero': '207', 'tipo_suite': 'MASTER', 'capacidade': 2, 'diaria': 200.00},
    
    # Quartos REAL
    {'numero': '302', 'tipo_suite': 'REAL', 'capacidade': 4, 'diaria': 350.00},
    {'numero': '303', 'tipo_suite': 'REAL', 'capacidade': 4, 'diaria': 350.00},
    {'numero': '304', 'tipo_suite': 'REAL', 'capacidade': 4, 'diaria': 350.00},
    {'numero': '306', 'tipo_suite': 'REAL', 'capacidade': 4, 'diaria': 350.00},
    {'numero': '307', 'tipo_suite': 'REAL', 'capacidade': 4, 'diaria': 350.00},
    {'numero': '308', 'tipo_suite': 'REAL', 'capacidade': 4, 'diaria': 350.00},
    {'numero': '309', 'tipo_suite': 'REAL', 'capacidade': 4, 'diaria': 350.00},
    {'numero': '310', 'tipo_suite': 'REAL', 'capacidade': 4, 'diaria': 350.00},
]

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
    headers = {'Content-Type': 'application/json'}
    
    # 2. Verificar quartos existentes
    print()
    print('2. VERIFICANDO QUARTOS EXISTENTES...')
    r = requests.get(f'{base_url}/quartos', cookies=cookies)
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        response_data = r.json()
        quartos_existentes = response_data['quartos']
        numeros_existentes = {q['numero'] for q in quartos_existentes}
        
        print(f'✅ Quartos existentes: {len(quartos_existentes)}')
        print(f'   Números existentes: {sorted(numeros_existentes)}')
        
        # 3. Adicionar quartos que não existem
        print()
        print('3. ADICIONANDO QUARTOS NOVOS...')
        
        quartos_adicionados = 0
        quartos_ja_existem = 0
        
        for quarto in quartos_para_adicionar:
            if quarto['numero'] in numeros_existentes:
                print(f'⚠️  Quarto {quarto["numero"]} já existe - pulando')
                quartos_ja_existem += 1
                continue
            
            # Adicionar quarto
            quarto_data = {
                'numero': quarto['numero'],
                'tipo_suite': quarto['tipo_suite'],
                'capacidade': quarto['capacidade'],
                'diaria': quarto['diaria'],
                'status': 'LIVRE'
            }
            
            r = requests.post(f'{base_url}/quartos', json=quarto_data, headers=headers, cookies=cookies)
            print(f'   Quarto {quarto["numero"]}: ', end='')
            
            if r.status_code == 201:
                print(f'✅ ADICIONADO ({quarto["tipo_suite"]})')
                quartos_adicionados += 1
            else:
                print(f'❌ ERRO ({r.status_code}): {r.text}')
        
        print()
        print(f'📊 RESUMO DA OPERAÇÃO:')
        print(f'   • Quartos adicionados: {quartos_adicionados}')
        print(f'   • Quartos já existentes: {quartos_ja_existem}')
        print(f'   • Total processados: {len(quartos_para_adicionar)}')
        
        # 4. Verificar resultado final
        print()
        print('4. VERIFICANDO RESULTADO FINAL...')
        r = requests.get(f'{base_url}/quartos', cookies=cookies)
        
        if r.status_code == 200:
            response_data = r.json()
            quartos_finais = response_data['quartos']
            
            # Agrupar por tipo
            por_tipo = {}
            for q in quartos_finais:
                tipo = q['tipo_suite']
                if tipo not in por_tipo:
                    por_tipo[tipo] = []
                por_tipo[tipo].append(q)
            
            print(f'✅ Total de quartos no sistema: {len(quartos_finais)}')
            print()
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
                        print(f'     - {status}: {count}')
            
            print()
            print('🏨 LISTA COMPLETA DE QUARTOS:')
            for q in sorted(quartos_finais, key=lambda x: (x['tipo_suite'], x['numero'])):
                status_emoji = {
                    'LIVRE': '🟢',
                    'OCUPADO': '🔴',
                    'MANUTENCAO': '🟡',
                    'BLOQUEADO': '⚫'
                }.get(q['status'], '❓')
                
                print(f'   {status_emoji} {q["numero"]} - {q["tipo_suite"]} - Cap.: {q["capacidade"]} - R$ {q["diaria"]}')
        
        print()
        print('🎉 OPERAÇÃO CONCLUÍDA!')
        
    else:
        print(f'❌ Erro ao listar quartos existentes: {r.text}')
else:
    print(f'❌ Erro no login: {r.text}')

print()
print('=== PROCESSO FINALIZADO ===')
