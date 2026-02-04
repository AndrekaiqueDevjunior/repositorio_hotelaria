"""
Script para gerar cliente Prisma usando Python
"""
import subprocess
import sys
import os

def generate_prisma():
    """Gerar cliente Prisma"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, "prisma", "schema.prisma")
    
    # Tentar usar o executável diretamente
    prisma_client_py = os.path.join(
        os.path.expanduser("~"),
        "AppData",
        "Roaming",
        "Python",
        "Python314",
        "Scripts",
        "prisma-client-py.exe"
    )
    
    if os.path.exists(prisma_client_py):
        print(f"Usando: {prisma_client_py}")
        result = subprocess.run(
            [prisma_client_py, "generate", "--schema", schema_path],
            cwd=script_dir
        )
        return result.returncode
    
    # Tentar usar npx com prisma
    print("Tentando usar npx prisma...")
    result = subprocess.run(
        ["npx", "prisma@5.17.0", "generate", "--schema", schema_path],
        cwd=script_dir
    )
    
    if result.returncode != 0:
        print("\nERRO: Não foi possível gerar o cliente Prisma.")
        print("Tente executar manualmente:")
        print(f"  npx prisma@5.17.0 generate --schema={schema_path}")
        print("\nOu adicione o diretório ao PATH:")
        print("  C:\\Users\\usuario\\AppData\\Roaming\\Python\\Python314\\Scripts")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(generate_prisma())

