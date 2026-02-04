#!/usr/bin/env python3
"""
Seed simplificado de temporadas 2026 - Hotel Real Cabo Frio
"""
import asyncio
from app.core.database import get_db_connected

async def seed_temporadas_2026_simplificado():
    """
    Versão simplificada para testar inserção
    """
    print("=== SEED TEMPORADAS 2026 - VERSÃO SIMPLIFICADA ===\n")
    
    db = await get_db_connected()
    
    try:
        # Limpar tarifas existentes de 2026
        print("📋 Limpando tarifas existentes de 2026...")
        await db.execute_raw("DELETE FROM tarifas_suites WHERE data_inicio >= date '2026-01-01';")
        
        # Inserir uma temporada de teste
        print("📋 Inserindo temporada de teste...")
        await db.execute_raw("""
            INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
            VALUES ('LUXO', 'BAIXA', date '2026-04-01', date '2026-08-31', 290.00, true, NOW(), NOW())
        """)
        
        print("✅ Temporada de teste inserida!")
        
        # Verificar
        resultado = await db.execute_raw("SELECT COUNT(*) as total FROM tarifas_suites WHERE data_inicio >= date '2026-01-01';")
        print(f"📊 Total de tarifas 2026: {resultado}")
        
        # Listar
        tarifas = await db.execute_raw("SELECT suite_tipo, temporada, data_inicio, data_fim, preco_diaria FROM tarifas_suites WHERE data_inicio >= date '2026-01-01';")
        print("📋 Tarifas criadas:")
        if isinstance(tarifas, list):
            for tarifa in tarifas:
                print(f"  • {tarifa.get('suite_tipo')} - {tarifa.get('temporada')}: R$ {tarifa.get('preco_diaria'):.2f}")
        else:
            print(f"  Resultado: {tarifas}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_temporadas_2026_simplificado())
