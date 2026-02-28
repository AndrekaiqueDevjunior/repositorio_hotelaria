#!/usr/bin/env python3
"""
Seed simples para criar tarifas usando SQL direto
"""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seeds.bootstrap import bootstrap_seed_environment

bootstrap_seed_environment()

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
        await db.execute_raw(TARIFAS_SQL)
        print("✅ Tarifas criadas com sucesso usando SQL direto")
        
        # Verificar quantidade
        total_tarifas = await db.tarifasuite.count(where={"ativo": True})
        print(f"📊 Total de tarifas ativas: {total_tarifas}")
        
    except Exception as e:
        print(f"❌ Erro ao executar SQL: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_tarifas_sql())
