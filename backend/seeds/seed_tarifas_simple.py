#!/usr/bin/env python3
"""
Seed simples para criar tarifas usando SQL direto
"""
import asyncio
from app.core.database import get_db_connected

TARIFAS_SQL = """
INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
VALUES 
    ('DUPLA', 'ALTA', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '365 days', 180.00, true, NOW(), NOW()),
    ('LUXO', 'ALTA', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '365 days', 250.00, true, NOW(), NOW()),
    ('LUXO 2º', 'ALTA', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '365 days', 280.00, true, NOW(), NOW()),
    ('LUXO 3º', 'ALTA', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '365 days', 300.00, true, NOW(), NOW()),
    ('LUXO 4º EC', 'ALTA', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '365 days', 320.00, true, NOW(), NOW()),
    ('MASTER', 'ALTA', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '365 days', 450.00, true, NOW(), NOW()),
    ('REAL', 'ALTA', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '365 days', 600.00, true, NOW(), NOW())
ON CONFLICT DO NOTHING;
"""

async def seed_tarifas_sql():
    print("=== SEED TARIFAS (SQL Direto) ===\n")
    
    db = await get_db_connected()
    
    try:
        # Executar SQL diretamente
        result = await db.execute_raw(TARIFAS_SQL)
        print("✅ Tarifas criadas com sucesso usando SQL direto")
        
        # Verificar quantidade
        count_result = await db.execute_raw("SELECT COUNT(*) as total FROM tarifas_suites WHERE ativo = true")
        print(f"📊 Total de tarifas ativas: {count_result[0]['total'] if count_result else 0}")
        
    except Exception as e:
        print(f"❌ Erro ao executar SQL: {e}")

if __name__ == "__main__":
    asyncio.run(seed_tarifas_sql())
