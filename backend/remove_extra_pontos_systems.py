#!/usr/bin/env python3
"""
Remove os 5 sistemas de pontos extras, mantendo apenas o principal
"""

import sys
import os
sys.path.append('/app')

import shutil
from pathlib import Path

def remove_extra_pontos_systems():
    """Remove os sistemas de pontos extras mantendo apenas o principal"""
    
    print('🗑️  Removendo Sistemas de Pontos Extras')
    print('=' * 60)
    
    app_dir = Path('/app/app')
    
    # Arquivos para remover (sistemas extras)
    files_to_remove = [
        # Services extras
        'services/pontos_acumulo_service.py',
        'services/pontos_populacao_service.py', 
        'services/pontos_rp_service.py',
        'services/pontos_unificado_service.py',
        'services/potos_jr_service.py',
        
        # Repositories extras
        'repositories/pontos_rp_repo.py',
        
        # Routes extras
        'api/v1/pontos_rp_routes.py',
        'api/v1/pontos_unificado_routes.py',
        'api/v1/pontos_jr_routes.py',
        'api/v1/pontos_populacao_routes.py',
        'api/v1/pontos_debug_routes.py',
    ]
    
    # Arquivos para manter (sistema principal)
    files_to_keep = [
        'services/pontos_service.py',
        'repositories/pontos_repo.py', 
        'api/v1/pontos_routes.py',
        'models/pontos.py',
        'schemas/pontos_schema.py'
    ]
    
    removed_files = []
    kept_files = []
    
    print('\n📁 Removendo arquivos dos sistemas extras:')
    
    for file_path in files_to_remove:
        full_path = app_dir / file_path
        
        if full_path.exists():
            try:
                # Fazer backup antes de remover
                backup_path = full_path.with_suffix('.py.backup')
                shutil.copy2(full_path, backup_path)
                
                # Remover arquivo original
                full_path.unlink()
                
                removed_files.append(file_path)
                print(f'   ✅ Removido: {file_path} (backup salvo)')
                
            except Exception as e:
                print(f'   ❌ Erro ao remover {file_path}: {e}')
        else:
            print(f'   ⚪ Não encontrado: {file_path}')
    
    print(f'\n📁 Arquivos mantidos (sistema principal):')
    for file_path in files_to_keep:
        full_path = app_dir / file_path
        if full_path.exists():
            kept_files.append(file_path)
            print(f'   ✅ Mantido: {file_path}')
        else:
            print(f'   ⚠️  Não encontrado: {file_path}')
    
    # Verificar se há algum arquivo restante com "pontos" que não deveria
    print(f'\n🔍 Verificando arquivos restantes:')
    
    remaining_pontos_files = []
    for pattern in ['*pontos*.py', '*Pontos*.py']:
        for file_path in app_dir.rglob(pattern):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(app_dir))
                
                # Verificar se está na lista de mantidos
                if not any(keep in relative_path for keep in files_to_keep):
                    remaining_pontos_files.append(relative_path)
    
    if remaining_pontos_files:
        print(f'   ⚠️  Arquivos restantes não listados:')
        for file_path in remaining_pontos_files:
            print(f'      - {file_path}')
    else:
        print(f'   ✅ Nenhum arquivo extra encontrado')
    
    # Resumo
    print(f'\n📊 Resumo da Limpeza:')
    print(f'   🗑️  Arquivos removidos: {len(removed_files)}')
    print(f'   ✅ Arquivos mantidos: {len(kept_files)}')
    print(f'   💾 Backups criados: {len(removed_files)}')
    
    return {
        'removed': removed_files,
        'kept': kept_files,
        'remaining': remaining_pontos_files
    }

if __name__ == "__main__":
    remove_extra_pontos_systems()
