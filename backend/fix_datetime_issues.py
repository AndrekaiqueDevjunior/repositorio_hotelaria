#!/usr/bin/env python3
"""
Corrige automaticamente os 56 problemas de datetime encontrados
"""

import sys
import os
sys.path.append('/app')

import re
from pathlib import Path

def fix_datetime_issues():
    """Corrige problemas de datetime no código"""
    
    print('🔧 Corrigindo Problemas de Datetime')
    print('=' * 50)
    
    # Diretório do app
    app_dir = Path('/app/app')
    
    # Arquivos para corrigir (prioridade crítica)
    critical_files = [
        'services/pagamento_service.py',
        'services/cielo_service.py',
        'repositories/pagamento_repo.py',
        'schemas/pagamento_schema.py',
        'services/reserva_service.py',
        'repositories/reserva_repo.py',
        'schemas/reserva_schema.py'
    ]
    
    fixed_files = []
    total_fixes = 0
    
    for file_pattern in critical_files:
        file_path = app_dir / file_pattern
        
        if not file_path.exists():
            print(f'⚠️  Arquivo não encontrado: {file_pattern}')
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content
            
            # 1. Corrigir imports
            content = re.sub(
                r'^from datetime import datetime$',
                'from datetime import datetime\nfrom app.utils.datetime_utils import now_utc, to_utc',
                content,
                flags=re.MULTILINE
            )
            
            # 2. Corrigir datetime.now() para now_utc()
            content = re.sub(
                r'datetime\.now\(\)',
                'now_utc()',
                content
            )
            
            # 3. Corrigir datetime.now() + timedelta
            content = re.sub(
                r'now_utc\(\) \+ timedelta\(',
                'now_utc() + timedelta(',
                content
            )
            
            # 4. Corrigir datetime.now() - timedelta  
            content = re.sub(
                r'now_utc\(\) - timedelta\(',
                'now_utc() - timedelta(',
                content
            )
            
            # Salvar se houve mudanças
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Contar as correções
                fixes = len(re.findall(r'datetime\.now\(\)', original_content))
                total_fixes += fixes
                fixed_files.append(file_pattern)
                
                print(f'✅ {file_pattern}: {fixes} correções')
            else:
                print(f'⚪ {file_pattern}: nenhuma correção necessária')
                
        except Exception as e:
            print(f'❌ Erro ao corrigir {file_pattern}: {e}')
    
    print(f'\n📊 Resumo das Correções:')
    print(f'   Arquivos corrigidos: {len(fixed_files)}')
    print(f'   Total de correções: {total_fixes}')
    
    return fixed_files, total_fixes

if __name__ == "__main__":
    fix_datetime_issues()
