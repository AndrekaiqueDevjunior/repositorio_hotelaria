# Salve como: test_prisma.py
# Execute com: python test_prisma.py

import asyncio
from prisma import Prisma
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    """Testa a conexão com Prisma Accelerate"""
    
    # Pegar a URL do ambiente
    db_url = os.getenv("DATABASE_URL")
    
    # Se a URL começar com prisma+, está usando Accelerate
    if db_url and db_url.startswith("prisma+"):
        print("✅ Usando Prisma Accelerate")
        print(f"📍 URL: {db_url[:50]}...")
    else:
        print("⚠️ Não está usando Prisma Accelerate")
    
    # Conectar ao Prisma
    db = Prisma(
        datasource={
            'url': db_url
        }
    )
    
    try:
        await db.connect()
        print("\n✅ Conectado com sucesso ao banco de dados!")
        
        # Testar uma query simples
        count = await db.usuario.count()
        print(f"📊 Total de usuários: {count}")
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar: {e}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_connection())