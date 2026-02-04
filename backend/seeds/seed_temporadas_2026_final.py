#!/usr/bin/env python3
"""
Seed de temporadas 2026 - Hotel Real Cabo Frio
Versão corrigida com estrutura exata da tabela
"""
import asyncio
from app.core.database import get_db_connected

async def seed_temporadas_2026_corrigido():
    """
    Seed corrigido com base no schema Prisma
    """
    print("=== SEED TEMPORADAS 2026 - HOTEL REAL CABO FRIO ===\n")
    
    db = await get_db_connected()
    
    try:
        # Limpar tarifas existentes de 2026
        print("📋 Limpando tarifas existentes de 2026...")
        await db.execute_raw("DELETE FROM tarifas_suites WHERE data_inicio >= date '2026-01-01';")
        
        # BAIXA TEMPORADA: ABRIL A AGOSTO
        print("📋 Inserindo BAIXA TEMPORADA (Abril a Agosto)...")
        await db.tarifasuite.create({
            'suite_tipo': 'LUXO',
            'temporada': 'BAIXA',
            'data_inicio': '2026-04-01',
            'data_fim': '2026-08-31',
            'preco_diaria': 290.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'MASTER',
            'temporada': 'BAIXA',
            'data_inicio': '2026-04-01',
            'data_fim': '2026-08-31',
            'preco_diaria': 450.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'DUPLA',
            'temporada': 'BAIXA',
            'data_inicio': '2026-04-01',
            'data_fim': '2026-08-31',
            'preco_diaria': 580.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'REAL',
            'temporada': 'BAIXA',
            'data_inicio': '2026-04-01',
            'data_fim': '2026-08-31',
            'preco_diaria': 500.00,
            'ativo': True
        })
        
        # TEMPORADA MÉDIA: SETEMBRO A OUTUBRO
        print("📋 Inserindo TEMPORADA MÉDIA (Setembro a Outubro)...")
        await db.tarifasuite.create({
            'suite_tipo': 'LUXO',
            'temporada': 'MEDIA',
            'data_inicio': '2026-09-01',
            'data_fim': '2026-10-31',
            'preco_diaria': 300.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'MASTER',
            'temporada': 'MEDIA',
            'data_inicio': '2026-09-01',
            'data_fim': '2026-10-31',
            'preco_diaria': 450.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'DUPLA',
            'temporada': 'MEDIA',
            'data_inicio': '2026-09-01',
            'data_fim': '2026-10-31',
            'preco_diaria': 600.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'REAL',
            'temporada': 'MEDIA',
            'data_inicio': '2026-09-01',
            'data_fim': '2026-10-31',
            'preco_diaria': 550.00,
            'ativo': True
        })
        
        # TEMPORADA ALTA: NOVEMBRO A DEZEMBRO
        print("📋 Inserindo TEMPORADA ALTA (Novembro a Dezembro)...")
        await db.tarifasuite.create({
            'suite_tipo': 'LUXO',
            'temporada': 'ALTA',
            'data_inicio': '2026-11-01',
            'data_fim': '2026-12-31',
            'preco_diaria': 350.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'MASTER',
            'temporada': 'ALTA',
            'data_inicio': '2026-11-01',
            'data_fim': '2026-12-31',
            'preco_diaria': 450.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'DUPLA',
            'temporada': 'ALTA',
            'data_inicio': '2026-11-01',
            'data_fim': '2026-12-31',
            'preco_diaria': 700.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'REAL',
            'temporada': 'ALTA',
            'data_inicio': '2026-11-01',
            'data_fim': '2026-12-31',
            'preco_diaria': 590.00,
            'ativo': True
        })
        
        # FERIADOS - Carnaval (Fevereiro)
        print("📋 Inserindo FERIADOS - Carnaval (13/02 a 18/02)...")
        await db.tarifasuite.create({
            'suite_tipo': 'LUXO',
            'temporada': 'FERIADO',
            'data_inicio': '2026-02-13',
            'data_fim': '2026-02-18',
            'preco_diaria': 590.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'MASTER',
            'temporada': 'FERIADO',
            'data_inicio': '2026-02-13',
            'data_fim': '2026-02-18',
            'preco_diaria': 650.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'DUPLA',
            'temporada': 'FERIADO',
            'data_inicio': '2026-02-13',
            'data_fim': '2026-02-18',
            'preco_diaria': 1180.00,
            'ativo': True
        })
        
        await db.tarifasuite.create({
            'suite_tipo': 'REAL',
            'temporada': 'FERIADO',
            'data_inicio': '2026-02-13',
            'data_fim': '2026-02-18',
            'preco_diaria': 690.00,
            'ativo': True
        })
        
        print("✅ Temporadas 2026 criadas com sucesso!")
        
        # Verificar total
        tarifas = await db.tarifasuite.find_many(
            where={'data_inicio': {'gte': '2026-01-01'}}
        )
        
        print(f"\n📊 Total de tarifas criadas: {len(tarifas)}")
        
        # Agrupar por temporada
        temporadas = {}
        for tarifa in tarifas:
            temp = tarifa.temporada or 'SEM_TEMPORADA'
            if temp not in temporadas:
                temporadas[temp] = []
            temporadas[temp].append(tarifa)
        
        print("\n📊 Resumo por temporada:")
        for temporada, lista in temporadas.items():
            precos = [float(t.preco_diaria) for t in lista]
            print(f"  • {temporada}: {len(lista)} tarifas (R$ {min(precos):.2f} - R$ {max(precos):.2f})")
        
    except Exception as e:
        print(f"❌ Erro ao executar seed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_temporadas_2026_corrigido())
