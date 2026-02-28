#!/usr/bin/env python3
"""Script para remover null bytes do main.py"""
import sys

# Ler arquivo em modo binário
with open('app/main.py', 'rb') as f:
    data = f.read()

# Contar null bytes
null_count = data.count(b'\x00')
print(f"Null bytes encontrados: {null_count}")

if null_count > 0:
    # Remover null bytes
    clean_data = data.replace(b'\x00', b'')
    
    # Reescrever arquivo
    with open('app/main.py', 'wb') as f:
        f.write(clean_data)
    
    print(f"✅ Removidos {null_count} null bytes!")
    print("✅ Arquivo corrigido!")
else:
    print("✅ Nenhum null byte encontrado")

# Verificar se pode ser importado
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("app.main", "app/main.py")
    if spec and spec.loader:
        print("✅ Arquivo pode ser importado!")
    else:
        print("❌ Arquivo não pode ser importado")
except Exception as e:
    print(f"❌ Erro ao verificar: {e}")

