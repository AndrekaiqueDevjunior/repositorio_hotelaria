#!/usr/bin/env python3
"""
Verifica e corrige problemas de datetime no código
"""

import sys
import os
sys.path.append('/app')

import re
from pathlib import Path

def check_datetime_issues():
    """Verifica problemas de datetime no código"""
    
    print('🔍 Verificando Problemas de Datetime')
    print('=' * 50)
    
    # Diretório do app
    app_dir = Path('/app/app')
    
    # Padrões problemáticos
    problematic_patterns = [
        r'datetime\.now\(\)',  # datetime.now() sem timezone
        r'from datetime import datetime\s*$',  # Import sem timezone
        r'compare.*datetime',  # Comentários sobre comparação
    ]
    
    # Arquivos para verificar
    files_to_check = []
    for pattern in ['**/*.py']:
        files_to_check.extend(app_dir.glob(pattern))
    
    issues_found = []
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            for i, line in enumerate(lines, 1):
                for pattern in problematic_patterns:
                    if re.search(pattern, line):
                        issues_found.append({
                            'file': str(file_path.relative_to(app_dir)),
                            'line': i,
                            'content': line.strip(),
                            'pattern': pattern
                        })
        except Exception as e:
            print(f'❌ Erro ao ler {file_path}: {e}')
    
    # Relatório
    if issues_found:
        print(f'⚠️  Encontrados {len(issues_found)} problemas:')
        print()
        
        for issue in issues_found:
            print(f'📁 {issue["file"]}:{issue["line"]}')
            print(f'   ❌ {issue["content"]}')
            print(f'   🔍 Padrão: {issue["pattern"]}')
            print()
        
        print('💡 Recomendações:')
        print('   1. Usar "from app.utils.datetime_utils import now_utc"')
        print('   2. Substituir datetime.now() por now_utc()')
        print('   3. Usar to_utc() para converter datetimes')
        
    else:
        print('✅ Nenhum problema de datetime encontrado!')
    
    return issues_found

if __name__ == "__main__":
    check_datetime_issues()
