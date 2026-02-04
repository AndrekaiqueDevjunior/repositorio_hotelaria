#!/usr/bin/env python3
"""Script para remover null bytes de todos os arquivos Python"""
import os
import glob

def clean_file(filepath):
    """Remove null bytes de um arquivo"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        null_count = data.count(b'\x00')
        
        if null_count > 0:
            clean_data = data.replace(b'\x00', b'')
            with open(filepath, 'wb') as f:
                f.write(clean_data)
            print(f"✅ {filepath}: Removidos {null_count} null bytes")
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ Erro em {filepath}: {e}")
        return False

# Limpar todos os arquivos Python
python_files = []
python_files.extend(glob.glob('app/**/*.py', recursive=True))
python_files.extend(glob.glob('*.py', recursive=False))

cleaned = 0
for filepath in python_files:
    if clean_file(filepath):
        cleaned += 1

print(f"\n✅ Processo concluído! {cleaned} arquivo(s) limpo(s)")

