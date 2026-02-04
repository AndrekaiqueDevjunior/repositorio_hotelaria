#!/usr/bin/env python3
"""
Corrige os problemas de datetime encontrados (16 ocorrências reais)
"""

import sys
import os
sys.path.append('/app')

import re
from pathlib import Path

def fix_real_datetime_issues():
    """Corrige os problemas reais de datetime encontrados"""
    
    print('🔧 Corrigindo Problemas Reais de Datetime')
    print('=' * 50)
    
    # Arquivos com datetime.now() encontrados
    files_with_issues = [
        'api/v1/runtime_debug.py',
        'repositories/convite_repo.py', 
        'api/v1/voucher_routes.py',
        'middleware/rate_limit.py',
        'api/v1/notificacao_routes.py',
        'api/v1/public_routes.py',
        'api/v1/routes_test.py',
        'utils/export_utils.py',
        'utils/security_utils.py'
    ]
    
    app_dir = Path('/app/app')
    total_fixes = 0
    fixed_files = []
    
    for file_path in files_with_issues:
        full_path = app_dir / file_path
        
        if not full_path.exists():
            print(f'⚠️  Arquivo não encontrado: {file_path}')
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content
            
            # Verificar se já tem o import do datetime_utils
            has_utils_import = 'from app.utils.datetime_utils import' in content
            
            # 1. Adicionar import se não existir
            if not has_utils_import:
                # Encontrar o primeiro import de datetime e adicionar após
                datetime_import_pattern = r'(from datetime import datetime)'
                if re.search(datetime_import_pattern, content):
                    content = re.sub(
                        datetime_import_pattern,
                        r'\1\nfrom app.utils.datetime_utils import now_utc, to_utc',
                        content
                    )
            
            # 2. Corrigir datetime.now() para now_utc()
            now_pattern = r'datetime\.now\(\)'
            matches = re.findall(now_pattern, content)
            
            if matches:
                content = re.sub(now_pattern, 'now_utc()', content)
                
                # Salvar arquivo
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                total_fixes += len(matches)
                fixed_files.append(file_path)
                
                print(f'✅ {file_path}: {len(matches)} correções')
            else:
                print(f'⚪ {file_path}: nenhuma correção necessária')
                
        except Exception as e:
            print(f'❌ Erro ao corrigir {file_path}: {e}')
    
    print(f'\n📊 Resumo das Correções:')
    print(f'   Arquivos corrigidos: {len(fixed_files)}')
    print(f'   Total de correções: {total_fixes}')
    
    return fixed_files, total_fixes

if __name__ == "__main__":
    fix_real_datetime_issues()
