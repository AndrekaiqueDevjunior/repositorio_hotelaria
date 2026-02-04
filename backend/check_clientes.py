"""
Script para verificar clientes no banco de dados
"""
import asyncio
from app.core.database import db

async def check_clientes():
    print("🔍 Verificando clientes no banco de dados...")
    await db.connect()
    
    try:
        # Contar total de clientes
        total = await db.cliente.count()
        print(f"✅ Total de clientes: {total}")
        
        if total > 0:
            # Buscar primeiros 5 clientes
            clientes = await db.cliente.find_many(take=5)
            print("\n📋 Primeiros clientes:")
            for c in clientes:
                print(f"  - ID {c.id}: {c.nomeCompleto} ({c.email or 'sem email'})")
        else:
            print("⚠️ Nenhum cliente encontrado no banco de dados")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_clientes())
