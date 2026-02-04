#!/usr/bin/env python3

import os

# Lista de arquivos que precisam da importação Session
files_to_fix = [
    "g:\\app_hotel_cabo_frio\\backend\\app\\services\\checkin_service.py",
    "g:\\app_hotel_cabo_frio\\backend\\app\\services\\checkout_service.py", 
    "g:\\app_hotel_cabo_frio\\backend\\app\\services\\overbooking_service.py",
    "g:\\app_hotel_cabo_frio\\backend\\app\\services\\pagamento_robusto_service.py",
    "g:\\app_hotel_cabo_frio\\backend\\app\\services\\state_machine_service.py"
]

for file_path in files_to_fix:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se já tem a importação
        if "from sqlalchemy.orm import Session" not in content:
            # Encontrar a primeira linha de importação e adicionar após ela
            lines = content.split('\n')
            new_lines = []
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                # Adicionar após as importações básicas (datetime, typing, etc.)
                if line.startswith('from datetime') or line.startswith('from typing') or line.startswith('from decimal'):
                    # Verificar se a próxima linha não é outra importação do mesmo tipo
                    if i + 1 < len(lines) and (lines[i+1].startswith('from datetime') or lines[i+1].startswith('from typing') or lines[i+1].startswith('from decimal')):
                        continue
                    new_lines.append('from sqlalchemy.orm import Session')
                    break
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            print(f"✅ Fixed: {file_path}")
        else:
            print(f"⚠️  Already fixed: {file_path}")
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
