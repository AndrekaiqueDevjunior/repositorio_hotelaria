#!/usr/bin/env python3
"""
Verifica endpoints fantasmas e não utilizados no projeto
"""

import sys
import os
sys.path.append('/app')

import re
from pathlib import Path

def find_ghost_endpoints():
    """Encontra endpoints fantasmas e não utilizados"""
    
    print('👻 Verificando Endpoints Fantasmas')
    print('=' * 50)
    
    app_dir = Path('/app/app')
    
    # Encontrar todos os arquivos de routes
    routes_files = list(app_dir.rglob('*routes*.py'))
    
    all_endpoints = []
    route_decorators = []
    
    for file_path in routes_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Encontrar decorators @app.get, @router.post, etc.
            decorator_pattern = r'@(app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
            matches = re.findall(decorator_pattern, content)
            
            for match in matches:
                method = match[1].upper()
                path = match[2]
                
                # Verificar se endpoint está comentado
                lines = content.split('\n')
                endpoint_line = -1
                for i, line in enumerate(lines):
                    if path in line and match[1] in line.lower():
                        endpoint_line = i
                        break
                
                is_commented = False
                if endpoint_line >= 0:
                    line_content = lines[endpoint_line].strip()
                    if line_content.startswith('#'):
                        is_commented = True
                
                all_endpoints.append({
                    'file': str(file_path.relative_to(app_dir)),
                    'method': method,
                    'path': path,
                    'commented': is_commented
                })
                
                route_decorators.append({
                    'file': str(file_path.relative_to(app_dir)),
                    'decorator': f"@{match[0]}.{match[1]}('{path}')",
                    'commented': is_commented
                })
                
        except Exception as e:
            print(f'❌ Erro ao ler {file_path}: {e}')
    
    # Analisar endpoints
    print(f'\n📊 Total de Endpoints Encontrados: {len(all_endpoints)}')
    
    # Separar por status
    active_endpoints = [ep for ep in all_endpoints if not ep['commented']]
    commented_endpoints = [ep for ep in all_endpoints if ep['commented']]
    
    print(f'   ✅ Endpoints ativos: {len(active_endpoints)}')
    print(f'   💀 Endpoints comentados: {len(commented_endpoints)}')
    
    # Agrupar por arquivo
    endpoints_by_file = {}
    for ep in all_endpoints:
        if ep['file'] not in endpoints_by_file:
            endpoints_by_file[ep['file']] = {'active': [], 'commented': []}
        
        if ep['commented']:
            endpoints_by_file[ep['file']]['commented'].append(ep)
        else:
            endpoints_by_file[ep['file']]['active'].append(ep)
    
    # Relatório por arquivo
    print(f'\n📁 Endpoints por Arquivo:')
    for file_path, data in sorted(endpoints_by_file.items()):
        active_count = len(data['active'])
        commented_count = len(data['commented'])
        total_count = active_count + commented_count
        
        status = '🟢' if commented_count == 0 else '🟡' if commented_count < active_count else '🔴'
        
        print(f'   {status} {file_path}')
        print(f'      📊 {active_count} ativos, {commented_count} comentados, {total_count} total')
        
        # Mostrar endpoints comentados
        if commented_count > 0:
            print(f'      💀 Endpoints comentados:')
            for ep in data['commented']:
                print(f'         ❌ {ep["method"]} {ep["path"]}')
    
    # Verificar endpoints suspeitos (fantasmas)
    print(f'\n👻 Análise de Endpoints Fantasmas:')
    
    ghost_indicators = [
        'test', 'debug', 'temp', 'old', 'legacy', 'deprecated',
        'v1', 'v2', 'experimental', 'backup'
    ]
    
    potential_ghosts = []
    
    for ep in active_endpoints:
        path_lower = ep['path'].lower()
        file_lower = ep['file'].lower()
        
        # Verificar indicadores de endpoint fantasma
        for indicator in ghost_indicators:
            if indicator in path_lower or indicator in file_lower:
                potential_ghosts.append({
                    'endpoint': f"{ep['method']} {ep['path']}",
                    'file': ep['file'],
                    'reason': f"Contém '{indicator}' no path ou arquivo"
                })
    
    # Verificar endpoints com nomes estranhos
    weird_patterns = [
        r'/.*_test.*',
        r'/.*_debug.*',
        r'/.*_temp.*',
        r'/.*_old.*',
        r'/.*_backup.*',
        r'/.*_experimental.*'
    ]
    
    for ep in active_endpoints:
        for pattern in weird_patterns:
            if re.match(pattern, ep['path'], re.IGNORECASE):
                if not any(gh['endpoint'] == f"{ep['method']} {ep['path']}" for gh in potential_ghosts):
                    potential_ghosts.append({
                        'endpoint': f"{ep['method']} {ep['path']}",
                        'file': ep['file'],
                        'reason': f"Match com padrão suspeito: {pattern}"
                    })
    
    # Verificar endpoints duplicados
    endpoint_signatures = {}
    duplicates = []
    
    for ep in active_endpoints:
        signature = f"{ep['method']} {ep['path']}"
        if signature in endpoint_signatures:
            duplicates.append({
                'signature': signature,
                'files': [endpoint_signatures[signature], ep['file']]
            })
        else:
            endpoint_signatures[signature] = ep['file']
    
    # Relatório de fantasmas
    if potential_ghosts:
        print(f'   ⚠️  {len(potential_ghosts)} endpoints potencialmente fantasmas:')
        for ghost in potential_ghosts:
            print(f'      👻 {ghost["endpoint"]} em {ghost["file"]}')
            print(f'         💡 Motivo: {ghost["reason"]}')
    else:
        print('   ✅ Nenhum endpoint fantasma óbvio encontrado')
    
    # Relatório de duplicatas
    if duplicates:
        print(f'\n🔄 Endpoints Duplicados:')
        for dup in duplicates:
            print(f'   ⚠️  {dup["signature"]} encontrado em:')
            for file_path in dup['files']:
                print(f'      - {file_path}')
    else:
        print(f'\n✅ Nenhuma duplicata de endpoint encontrada')
    
    # Verificar endpoints não utilizados (sem imports)
    print(f'\n🔍 Verificando Endpoints Não Utilizados:')
    
    # Procurar por imports de cada route
    unused_endpoints = []
    
    for file_path, data in endpoints_by_file.items():
        # Verificar se o arquivo de routes é importado em algum lugar
        file_name = Path(file_path).stem
        
        # Procurar imports do arquivo
        imported_somewhere = False
        for check_file in app_dir.rglob('*.py'):
            if check_file.name == file_path or 'routes' in str(check_file):
                continue
                
            try:
                with open(check_file, 'r', encoding='utf-8') as f:
                    check_content = f.read()
                
                # Verificar se o arquivo é importado
                if re.search(rf'from.*{file_name}|import.*{file_name}', check_content):
                    imported_somewhere = True
                    break
            except:
                continue
        
        if not imported_somewhere and len(data['active']) > 0:
            unused_endpoints.append({
                'file': file_path,
                'active_count': len(data['active']),
                'endpoints': [f"{ep['method']} {ep['path']}" for ep in data['active']]
            })
    
    if unused_endpoints:
        print(f'   ⚠️  {len(unused_endpoints)} arquivos de routes não importados:')
        for unused in unused_endpoints:
            print(f'      📁 {unused["file"]} ({unused["active_count"]} endpoints)')
            for ep in unused["endpoints"][:3]:  # Mostrar apenas 3
                print(f'         - {ep}')
            if len(unused["endpoints"]) > 3:
                print(f'         ... e mais {len(unused["endpoints"]) - 3}')
    else:
        print('   ✅ Todos os arquivos de routes parecem ser utilizados')
    
    # Resumo final
    print(f'\n📋 Resumo Final:')
    print(f'   📊 Total de endpoints: {len(all_endpoints)}')
    print(f'   ✅ Ativos: {len(active_endpoints)}')
    print(f'   💀 Comentados: {len(commented_endpoints)}')
    print(f'   👻 Potencialmente fantasmas: {len(potential_ghosts)}')
    print(f'   🔄 Duplicados: {len(duplicates)}')
    print(f'   ❌ Não utilizados: {len(unused_endpoints)}')
    
    # Recomendações
    print(f'\n💡 Recomendações:')
    if len(commented_endpoints) > 0:
        print(f'   🔧 Remover {len(commented_endpoints)} endpoints comentados')
    
    if len(potential_ghosts) > 0:
        print(f'   👻 Investigar {len(potential_ghosts)} endpoints potencialmente fantasmas')
    
    if len(duplicates) > 0:
        print(f'   🔄 Resolver {len(duplicates)} endpoints duplicados')
    
    if len(unused_endpoints) > 0:
        print(f'   🗑️  Remover {len(unused_endpoints)} arquivos de routes não utilizados')
    
    if len(commented_endpoints) == 0 and len(potential_ghosts) == 0 and len(duplicates) == 0:
        print(f'   ✅ Estrutura de endpoints appears limpa e organizada')
    
    return {
        'total': len(all_endpoints),
        'active': len(active_endpoints),
        'commented': len(commented_endpoints),
        'ghosts': len(potential_ghosts),
        'duplicates': len(duplicates),
        'unused': len(unused_endpoints)
    }

if __name__ == "__main__":
    find_ghost_endpoints()
