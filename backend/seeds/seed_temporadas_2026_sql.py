#!/usr/bin/env python3
"""
Seed de temporadas 2026 - Hotel Real Cabo Frio
Baseado na estrutura exata da tabela tarifas_suites
"""
import asyncio
from app.core.database import get_db_connected

async def seed_temporadas_2026_sql():
    """
    Seed usando SQL direto com base na estrutura real da tabela
    """
    print("=== SEED TEMPORADAS 2026 - HOTEL REAL CABO FRIO ===\n")
    
    db = await get_db_connected()
    
    try:
        # Limpar tarifas existentes de 2026
        print("📋 Limpando tarifas existentes de 2026...")
        await db.execute_raw("DELETE FROM tarifas_suites WHERE data_inicio >= date '2026-01-01';")
        
        # SQL completo com todas as temporadas
        TEMPORADAS_2026_SQL = """
        -- BAIXA TEMPORADA: ABRIL A AGOSTO --
        INSERT INTO tarifas_suites (nome, suite_tipo, temporada, data_inicio, data_fim, valor_diaria, preco_diaria, preco_semana, preco_fim_semana, preco_promocional, status, ativo, min_noites, max_noites, taxa_cancelamento, created_at, updated_at)
        VALUES 
            ('Temporada Baixa - Luxo', 'LUXO', 'BAIXA', '2026-04-01', '2026-08-31', 290.00, 290.00, 350.00, 400.00, 260.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Temporada Baixa - Master', 'MASTER', 'BAIXA', '2026-04-01', '2026-08-31', 450.00, 450.00, 540.00, 620.00, 400.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Temporada Baixa - Dupla', 'DUPLA', 'BAIXA', '2026-04-01', '2026-08-31', 580.00, 580.00, 696.00, 800.00, 520.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Temporada Baixa - Real', 'REAL', 'BAIXA', '2026-04-01', '2026-08-31', 500.00, 500.00, 600.00, 690.00, 450.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW());

        -- TEMPORADA MÉDIA: SETEMBRO A OUTUBRO --
        INSERT INTO tarifas_suites (nome, suite_tipo, temporada, data_inicio, data_fim, valor_diaria, preco_diaria, preco_semana, preco_fim_semana, preco_promocional, status, ativo, min_noites, max_noites, taxa_cancelamento, created_at, updated_at)
        VALUES 
            ('Temporada Média - Luxo', 'LUXO', 'MEDIA', '2026-09-01', '2026-10-31', 300.00, 300.00, 360.00, 415.00, 270.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Temporada Média - Master', 'MASTER', 'MEDIA', '2026-09-01', '2026-10-31', 450.00, 450.00, 540.00, 620.00, 400.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Temporada Média - Dupla', 'DUPLA', 'MEDIA', '2026-09-01', '2026-10-31', 600.00, 600.00, 720.00, 830.00, 540.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Temporada Média - Real', 'REAL', 'MEDIA', '2026-09-01', '2026-10-31', 550.00, 550.00, 660.00, 760.00, 490.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW());

        -- TEMPORADA ALTA: NOVEMBRO A DEZEMBRO --
        INSERT INTO tarifas_suites (nome, suite_tipo, temporada, data_inicio, data_fim, valor_diaria, preco_diaria, preco_semana, preco_fim_semana, preco_promocional, status, ativo, min_noites, max_noites, taxa_cancelamento, created_at, updated_at)
        VALUES 
            ('Temporada Alta - Luxo', 'LUXO', 'ALTA', '2026-11-01', '2026-12-31', 350.00, 350.00, 420.00, 485.00, 315.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Temporada Alta - Master', 'MASTER', 'ALTA', '2026-11-01', '2026-12-31', 450.00, 450.00, 540.00, 620.00, 400.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Temporada Alta - Dupla', 'DUPLA', 'ALTA', '2026-11-01', '2026-12-31', 700.00, 700.00, 840.00, 965.00, 630.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Temporada Alta - Real', 'REAL', 'ALTA', '2026-11-01', '2026-12-31', 590.00, 590.00, 708.00, 815.00, 530.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW());

        -- FERIADOS 2026 --
        
        -- Fevereiro - Carnaval (13/02 a 18/02)
        INSERT INTO tarifas_suites (nome, suite_tipo, temporada, data_inicio, data_fim, valor_diaria, preco_diaria, preco_semana, preco_fim_semana, preco_promocional, status, ativo, min_noites, max_noites, taxa_cancelamento, created_at, updated_at)
        VALUES 
            ('Feriado Carnaval - Luxo', 'LUXO', 'FERIADO', '2026-02-13', '2026-02-18', 590.00, 590.00, 708.00, 815.00, 530.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Feriado Carnaval - Master', 'MASTER', 'FERIADO', '2026-02-13', '2026-02-18', 650.00, 650.00, 780.00, 900.00, 580.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Feriado Carnaval - Dupla', 'DUPLA', 'FERIADO', '2026-02-13', '2026-02-18', 1180.00, 1180.00, 1416.00, 1630.00, 1060.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW()),
            ('Feriado Carnaval - Real', 'REAL', 'FERIADO', '2026-02-13', '2026-02-18', 690.00, 690.00, 828.00, 950.00, 620.00, 'ATIVA', true, 1, 30, 10.00, NOW(), NOW());
        """
        
        print("📋 Inserindo temporadas 2026...")
        
        # Separar e executar comandos SQL individualmente
        comandos = TEMPORADAS_2026_SQL.split(';')
        
        for i, comando in enumerate(comandos):
            comando = comando.strip()
            if comando and not comando.startswith('--'):
                try:
                    await db.execute_raw(comando + ';')
                    if (i + 1) % 3 == 0:
                        print(f"  Processando... ({i+1}/{len(comandos)})")
                except Exception as e:
                    print(f"  ⚠️ Erro no comando: {e}")
                    continue
        
        print("✅ Temporadas 2026 criadas com sucesso!")
        
        # Verificar resultado
        resultado = await db.execute_raw("""
            SELECT temporada, COUNT(*) as total, 
                   MIN(preco_diaria) as menor_preco, 
                   MAX(preco_diaria) as maior_preco
            FROM tarifas_suites 
            WHERE data_inicio >= date '2026-01-01'
            GROUP BY temporada 
            ORDER BY temporada;
        """)
        
        print("\n📊 Resumo das temporadas criadas:")
        if isinstance(resultado, list):
            for linha in resultado:
                temporada = linha.get('temporada', 'N/A')
                total = linha.get('total', 0)
                menor = linha.get('menor_preco', 0)
                maior = linha.get('maior_preco', 0)
                print(f"  • {temporada}: {total} tarifas (R$ {menor:.2f} - R$ {maior:.2f})")
        
        # Total geral
        total_result = await db.execute_raw("""
            SELECT COUNT(*) as total 
            FROM tarifas_suites 
            WHERE data_inicio >= date '2026-01-01';
        """)
        
        total_geral = total_result[0]['total'] if isinstance(total_result, list) and total_result else 0
        print(f"\n🎯 Total de tarifas criadas: {total_geral}")
        
    except Exception as e:
        print(f"❌ Erro ao executar seed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_temporadas_2026_sql())
