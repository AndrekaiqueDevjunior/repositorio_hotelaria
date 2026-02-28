#!/usr/bin/env python3
"""Script para testar conexão com banco de dados"""
import asyncio
import sys
from app.core.database import get_db

async def test_connection():
    """Testar conexão com banco de dados"""
    try:
        db = get_db()
        print("🔌 Tentando conectar ao banco de dados...")
        await db.connect()
        print("✅ Banco de dados conectado com sucesso!")
        
        # Testar uma query simples
        result = await db.query_raw("SELECT 1 as test")
        print("✅ Query de teste executada com sucesso!")
        
        await db.disconnect()
        print("✅ Conexão fechada corretamente")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        print(f"   Tipo: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)

