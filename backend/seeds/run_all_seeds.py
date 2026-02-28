#!/usr/bin/env python3
"""
Executa todos os seeds em ordem recomendada
"""
import subprocess
import sys

SEEDS_ORDER = [
    ("seed_5_users.py", "Funcionários/Admins"),
    ("seed_clientes.py", "Clientes"),
    ("seed_quartos.py", "Quartos"),
    ("seed_tarifas_simple.py", "Tarifas"),
    ("seed_pontos_regras.py", "Regras de Pontos"),
    ("seed_premios.py", "Prêmios"),
    ("seed_demo_data.py", "Dados Completos")
]

def run_seed(seed_file, description):
    """Executa um seed específico"""
    print(f"\n{'='*60}")
    print(f"🌱 Executando: {seed_file}")
    print(f"📝 Descrição: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            ["python", "-c", f"import sys; sys.path.append('/app'); import seeds.{seed_file.replace('.py', '')}"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✅ {seed_file} executado com sucesso!")
            if result.stdout:
                print("📄 Saída:")
                print(result.stdout)
        else:
            print(f"❌ Erro ao executar {seed_file}")
            if result.stderr:
                print("🚨 Erro:")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout ao executar {seed_file}")
        return False
    except Exception as e:
        print(f"💥 Erro inesperado ao executar {seed_file}: {e}")
        return False
    
    return True

def main():
    print("🚀 Iniciando execução de todos os seeds...")
    print("📍 Diretório: /app/seeds")
    
    success_count = 0
    total_count = len(SEEDS_ORDER)
    
    for seed_file, description in SEEDS_ORDER:
        if run_seed(seed_file, description):
            success_count += 1
        else:
            print(f"\n⚠️  Pulando próximos seeds devido ao erro em {seed_file}")
            break
    
    print(f"\n{'='*60}")
    print(f"📊 Resumo da Execução")
    print(f"{'='*60}")
    print(f"✅ Sucessos: {success_count}/{total_count}")
    print(f"❌ Falhas: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 Todos os seeds executados com sucesso!")
        print("🏨 Banco de dados do Hotel Cabo Frio está pronto!")
    else:
        print("⚠️  Alguns seeds falharam. Verifique os erros acima.")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
