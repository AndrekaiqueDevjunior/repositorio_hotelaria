#!/usr/bin/env python3
"""
Teste simples de inserção
"""
import asyncio
from app.core.database import get_db_connected

async def test_insert():
    db = await get_db_connected()
    
    try:
        # Teste simples
        await db.execute_raw("""
            INSERT INTO tarifas_suites (nome, suite_tipo, temporada, data_inicio, data_fim, valor_diaria, preco_diaria, status, ativo, min_noites, max_noites, taxa_cancelamento, created_at, updated_at)
            VALUES ('Teste', 'LUXO', 'BAIXA', '2026-04-01', '2026-04-02', 290.00, 290.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW())
        """)
        
        print("✅ Inserção de teste bem-sucedida!")
        
        # Verificar
        result = await db.execute_raw("SELECT COUNT(*) as total FROM tarifas_suites WHERE data_inicio >= date '2026-01-01'")
        print(f"Total: {result}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_insert())
