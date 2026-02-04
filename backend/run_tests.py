#!/usr/bin/env python3
"""
Script para executar testes do sistema Hotel Real Cabo Frio
"""
import subprocess
import sys
import os

def check_prisma():
    """Verificar se Prisma está configurado"""
    try:
        from prisma import Prisma
        return True
    except ImportError:
        print("AVISO: Prisma client não encontrado. Execute 'npx prisma generate' primeiro.")
        return False

def run_tests():
    """Executar testes pytest"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("=" * 60)
    print("Executando testes do sistema Hotel Real Cabo Frio")
    print("=" * 60)
    print()
    
    # Verificar Prisma
    if not check_prisma():
        print("Tentando gerar cliente Prisma...")
        try:
            subprocess.run(["npx", "prisma", "generate"], check=False)
        except:
            pass
    
    # Executar pytest usando python -m pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--asyncio-mode=auto"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    if result.returncode == 0:
        print()
        print("=" * 60)
        print("SUCESSO: Todos os testes passaram!")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("ERRO: Alguns testes falharam. Verifique os erros acima.")
        print("=" * 60)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())

