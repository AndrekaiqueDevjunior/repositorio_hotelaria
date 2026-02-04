#!/usr/bin/env python3
"""
Valida se existe apenas um sistema de pontos no projeto
"""

import sys
import os
sys.path.append('/app')

import re
from pathlib import Path

def validate_pontos_system():
    """Verifica se existe apenas um sistema de pontos"""
    
    print('🎯 Validando Sistema de Pontos')
    print('=' * 50)
    
    app_dir = Path('/app/app')
    
    # Procurar todos os arquivos relacionados a pontos
    pontos_files = []
    pontos_patterns = [
        '*ponto*.py',
        '*Pontos*.py',
        '*pontos*.py'
    ]
    
    for pattern in pontos_patterns:
        pontos_files.extend(app_dir.rglob(pattern))
    
    # Procurar classes e funções relacionadas a pontos
    pontos_classes = []
    pontos_functions = []
    pontos_services = []
    pontos_repositories = []
    pontos_schemas = []
    
    for file_path in app_dir.rglob('*.py'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Classes de pontos
            class_matches = re.findall(r'class\s+(\w*[Pp]ontos?\w*)\s*\(', content)
            for match in class_matches:
                pontos_classes.append({
                    'file': str(file_path.relative_to(app_dir)),
                    'class': match
                })
            
            # Funções de pontos
            func_matches = re.findall(r'def\s+(\w*[pP]ontos?\w*)\s*\(', content)
            for match in func_matches:
                pontos_functions.append({
                    'file': str(file_path.relative_to(app_dir)),
                    'function': match
                })
            
            # Services de pontos
            if 'pontos' in file_path.name.lower() and 'service' in file_path.name.lower():
                pontos_services.append(str(file_path.relative_to(app_dir)))
            
            # Repositories de pontos
            if 'pontos' in file_path.name.lower() and 'repo' in file_path.name.lower():
                pontos_repositories.append(str(file_path.relative_to(app_dir)))
            
            # Schemas de pontos
            if 'pontos' in file_path.name.lower() and 'schema' in file_path.name.lower():
                pontos_schemas.append(str(file_path.relative_to(app_dir)))
                
        except Exception as e:
            print(f'❌ Erro ao ler {file_path}: {e}')
    
    # Verificar tabelas de pontos no banco
    print('\n📊 Arquivos Relacionados a Pontos:')
    print(f'   📁 Arquivos com "pontos" no nome: {len(pontos_files)}')
    for f in sorted(pontos_files):
        print(f'      - {f.relative_to(app_dir)}')
    
    print(f'\n🏗️  Classes de Pontos Encontradas ({len(pontos_classes)}):')
    for cls in sorted(pontos_classes, key=lambda x: x['class']):
        print(f'   📋 {cls["class"]} em {cls["file"]}')
    
    print(f'\n⚙️  Funções de Pontos Encontradas ({len(pontos_functions)}):')
    for func in sorted(pontos_functions, key=lambda x: x['function']):
        print(f'   🔧 {func["function"]} em {func["file"]}')
    
    print(f'\n🛠️  Services de Pontos ({len(pontos_services)}):')
    for service in sorted(pontos_services):
        print(f'   📦 {service}')
    
    print(f'\n💾 Repositories de Pontos ({len(pontos_repositories)}):')
    for repo in sorted(pontos_repositories):
        print(f'   🗄️  {repo}')
    
    print(f'\n📄 Schemas de Pontos ({len(pontos_schemas)}):')
    for schema in sorted(pontos_schemas):
        print(f'   📋 {schema}')
    
    # Verificar duplicações
    print(f'\n🔍 Análise de Duplicações:')
    
    # Verificar classes duplicadas
    class_names = [cls['class'] for cls in pontos_classes]
    duplicated_classes = set([name for name in class_names if class_names.count(name) > 1])
    
    if duplicated_classes:
        print(f'   ⚠️  Classes duplicadas: {duplicated_classes}')
        for dup_class in duplicated_classes:
            dup_files = [cls['file'] for cls in pontos_classes if cls['class'] == dup_class]
            print(f'      - {dup_class}: {dup_files}')
    else:
        print('   ✅ Nenhuma classe de pontos duplicada')
    
    # Verificar services duplicados
    if len(pontos_services) > 1:
        print(f'   ⚠️  Múltiplos services de pontos encontrados!')
        for service in pontos_services:
            print(f'      - {service}')
    else:
        print('   ✅ Apenas um service de pontos')
    
    # Verificar repositories duplicados
    if len(pontos_repositories) > 1:
        print(f'   ⚠️  Múltiplos repositories de pontos encontrados!')
        for repo in pontos_repositories:
            print(f'      - {repo}')
    else:
        print('   ✅ Apenas um repository de pontos')
    
    # Verificar schemas duplicados
    if len(pontos_schemas) > 1:
        print(f'   ⚠️  Múltiplos schemas de pontos encontrados!')
        for schema in pontos_schemas:
            print(f'      - {schema}')
    else:
        print('   ✅ Apenas um schema de pontos')
    
    # Verificar se há sistemas concorrentes
    print(f'\n🎯 Conclusão:')
    total_pontos_files = len(pontos_files) + len(pontos_classes) + len(pontos_functions)
    
    if total_pontos_files > 10:
        print(f'   ⚠️  POSSÍVEL PROBLEMA: Muitos arquivos relacionados a pontos ({total_pontos_files})')
        print(f'   💡 Recomendação: Consolidar em um único sistema')
    elif len(pontos_services) > 1 or len(pontos_repositories) > 1:
        print(f'   ⚠️  POSSÍVEL PROBLEMA: Múltiplos services/repositories de pontos')
        print(f'   💡 Recomendação: Unificar em um único service e repository')
    else:
        print(f'   ✅ Sistema de pontos parece consolidado')
    
    return {
        'total_files': total_pontos_files,
        'services': len(pontos_services),
        'repositories': len(pontos_repositories),
        'schemas': len(pontos_schemas),
        'duplicated_classes': len(duplicated_classes)
    }

if __name__ == "__main__":
    validate_pontos_system()
