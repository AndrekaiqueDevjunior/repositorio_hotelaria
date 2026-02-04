#!/usr/bin/env python3
"""
Seed de temporadas 2026 - Hotel Real Cabo Frio
Cria tarifas diferenciadas por temporada e feriados
"""
import asyncio
from datetime import date, datetime
from app.core.database import get_db_connected

def criar_sql_temporadas_2026():
    """
    Gera SQL para inserção das temporadas 2026
    """
    
    # Limpa tarifas existentes de 2026
    LIMPEZA_SQL = """
    DELETE FROM tarifas_suites 
    WHERE data_inicio >= '2026-01-01' AND data_fim <= '2026-12-31';
    """
    
    # SQL completo com todas as temporadas
    TARIFAS_2026_SQL = """
    -- BAIXA TEMPORADA: ABRIL A AGOSTO --
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'BAIXA', '2026-04-01', '2026-08-31', 290.00, true, NOW(), NOW()),
        ('MASTER', 'BAIXA', '2026-04-01', '2026-08-31', 450.00, true, NOW(), NOW()),
        ('DUPLA', 'BAIXA', '2026-04-01', '2026-08-31', 580.00, true, NOW(), NOW()),
        ('REAL', 'BAIXA', '2026-04-01', '2026-08-31', 500.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- TEMPORADA MÉDIA: SETEMBRO A OUTUBRO --
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'MEDIA', '2026-09-01', '2026-10-31', 300.00, true, NOW(), NOW()),
        ('MASTER', 'MEDIA', '2026-09-01', '2026-10-31', 450.00, true, NOW(), NOW()),
        ('DUPLA', 'MEDIA', '2026-09-01', '2026-10-31', 600.00, true, NOW(), NOW()),
        ('REAL', 'MEDIA', '2026-09-01', '2026-10-31', 550.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- TEMPORADA ALTA: NOVEMBRO A DEZEMBRO --
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'ALTA', '2026-11-01', '2026-12-31', 350.00, true, NOW(), NOW()),
        ('MASTER', 'ALTA', '2026-11-01', '2026-12-31', 450.00, true, NOW(), NOW()),
        ('DUPLA', 'ALTA', '2026-11-01', '2026-12-31', 700.00, true, NOW(), NOW()),
        ('REAL', 'ALTA', '2026-11-01', '2026-12-31', 590.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- FERIADOS 2026 --
    
    -- Fevereiro - Carnaval (13/02 a 18/02)
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'FERIADO', '2026-02-13', '2026-02-18', 590.00, true, NOW(), NOW()),
        ('MASTER', 'FERIADO', '2026-02-13', '2026-02-18', 650.00, true, NOW(), NOW()),
        ('DUPLA', 'FERIADO', '2026-02-13', '2026-02-18', 1180.00, true, NOW(), NOW()),
        ('REAL', 'FERIADO', '2026-02-13', '2026-02-18', 690.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- Abril - Páscoa (02/04 a 05/04)
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'FERIADO', '2026-04-02', '2026-04-05', 400.00, true, NOW(), NOW()),
        ('MASTER', 'FERIADO', '2026-04-02', '2026-04-05', 500.00, true, NOW(), NOW()),
        ('DUPLA', 'FERIADO', '2026-04-02', '2026-04-05', 800.00, true, NOW(), NOW()),
        ('REAL', 'FERIADO', '2026-04-02', '2026-04-05', 590.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- Abril - Tiradentes (18/04 a 21/04)
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'FERIADO', '2026-04-18', '2026-04-21', 400.00, true, NOW(), NOW()),
        ('MASTER', 'FERIADO', '2026-04-18', '2026-04-21', 500.00, true, NOW(), NOW()),
        ('DUPLA', 'FERIADO', '2026-04-18', '2026-04-21', 800.00, true, NOW(), NOW()),
        ('REAL', 'FERIADO', '2026-04-18', '2026-04-21', 590.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- Abril/Maio - Dia do Trabalho (30/04 a 03/05)
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'FERIADO', '2026-04-30', '2026-05-03', 400.00, true, NOW(), NOW()),
        ('MASTER', 'FERIADO', '2026-04-30', '2026-05-03', 590.00, true, NOW(), NOW()),
        ('DUPLA', 'FERIADO', '2026-04-30', '2026-05-03', 800.00, true, NOW(), NOW()),
        ('REAL', 'FERIADO', '2026-04-30', '2026-05-03', 590.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- Setembro - Independência do Brasil (04/09 a 07/09)
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'FERIADO', '2026-09-04', '2026-09-07', 400.00, true, NOW(), NOW()),
        ('MASTER', 'FERIADO', '2026-09-04', '2026-09-07', 590.00, true, NOW(), NOW()),
        ('DUPLA', 'FERIADO', '2026-09-04', '2026-09-07', 800.00, true, NOW(), NOW()),
        ('REAL', 'FERIADO', '2026-09-04', '2026-09-07', 590.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- Outubro - Nossa Senhora Aparecida (09/10 a 12/10)
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'FERIADO', '2026-10-09', '2026-10-12', 400.00, true, NOW(), NOW()),
        ('MASTER', 'FERIADO', '2026-10-09', '2026-10-12', 500.00, true, NOW(), NOW()),
        ('DUPLA', 'FERIADO', '2026-10-09', '2026-10-12', 800.00, true, NOW(), NOW()),
        ('REAL', 'FERIADO', '2026-10-09', '2026-10-12', 590.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- Outubro/Novembro - Finados (30/10 a 07/11)
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'FERIADO', '2026-10-30', '2026-11-07', 400.00, true, NOW(), NOW()),
        ('MASTER', 'FERIADO', '2026-10-30', '2026-11-07', 500.00, true, NOW(), NOW()),
        ('DUPLA', 'FERIADO', '2026-10-30', '2026-11-07', 800.00, true, NOW(), NOW()),
        ('REAL', 'FERIADO', '2026-10-30', '2026-11-07', 590.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- Novembro - Proclamação da República (19/11 a 22/11)
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'FERIADO', '2026-11-19', '2026-11-22', 400.00, true, NOW(), NOW()),
        ('MASTER', 'FERIADO', '2026-11-19', '2026-11-22', 500.00, true, NOW(), NOW()),
        ('DUPLA', 'FERIADO', '2026-11-19', '2026-11-22', 800.00, true, NOW(), NOW()),
        ('REAL', 'FERIADO', '2026-11-19', '2026-11-22', 590.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;

    -- Dezembro/Ano Novo - Réveillon (29/12 a 02/01)
    INSERT INTO tarifas_suites (suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo, created_at, updated_at)
    VALUES 
        ('LUXO', 'FERIADO', '2026-12-29', '2027-01-02', 690.00, true, NOW(), NOW()),
        ('MASTER', 'FERIADO', '2026-12-29', '2027-01-02', 750.00, true, NOW(), NOW()),
        ('DUPLA', 'FERIADO', '2026-12-29', '2027-01-02', 1380.00, true, NOW(), NOW()),
        ('REAL', 'FERIADO', '2026-12-29', '2027-01-02', 800.00, true, NOW(), NOW())
    ON CONFLICT DO NOTHING;
    """
    
    return LIMPEZA_SQL + TARIFAS_2026_SQL

async def seed_temporadas_2026():
    """
    Executa o seed de temporadas 2026
    """
    print("=== SEED TEMPORADAS 2026 - HOTEL REAL CABO FRIO ===\n")
    
    db = await get_db_connected()
    
    try:
        # Gerar SQL
        sql_completo = criar_sql_temporadas_2026()
        
        print("📋 Executando limpeza das tarifas existentes de 2026...")
        await db.execute_raw("DELETE FROM tarifas_suites WHERE data_inicio >= '2026-01-01' AND data_fim <= '2026-12-31';")
        
        # Separar os comandos SQL para execução individual
        comandos_sql = sql_completo.split(';')
        
        print("📋 Inserindo novas temporadas 2026...")
        for i, comando in enumerate(comandos_sql):
            comando = comando.strip()
            if comando and not comando.startswith('--'):
                try:
                    await db.execute_raw(comando + ';')
                    if i % 5 == 0:  # Progresso a cada 5 comandos
                        print(f"  Processando... ({i+1}/{len(comandos_sql)})")
                except Exception as e:
                    print(f"  ⚠️ Erro no comando {i+1}: {e}")
                    continue
        
        print("✅ Temporadas 2026 criadas com sucesso!")
        
        # Verificar quantidade por temporada
        print("\n📊 Resumo das temporadas criadas:")
        contagem_sql = """
        SELECT temporada, COUNT(*) as total, 
               MIN(preco_diaria) as menor_preco, 
               MAX(preco_diaria) as maior_preco
        FROM tarifas_suites 
        WHERE data_inicio >= '2026-01-01' 
        AND (data_fim <= '2026-12-31' OR data_fim <= '2027-01-02')
        GROUP BY temporada 
        ORDER BY temporada;
        """
        
        resultado = await db.execute_raw(contagem_sql)
        
        # Verificar se o resultado é uma lista
        if isinstance(resultado, list):
            for linha in resultado:
                temporada = linha.get('temporada', 'N/A')
                total = linha.get('total', 0)
                menor = linha.get('menor_preco', 0)
                maior = linha.get('maior_preco', 0)
                print(f"  • {temporada}: {total} tarifas (R$ {menor:.2f} - R$ {maior:.2f})")
        else:
            print("  ⚠️ Não foi possível obter o resumo das temporadas")
        
        # Verificar total geral
        total_sql = """
        SELECT COUNT(*) as total 
        FROM tarifas_suites 
        WHERE data_inicio >= '2026-01-01' 
        AND (data_fim <= '2026-12-31' OR data_fim <= '2027-01-02');
        """
        
        total_result = await db.execute_raw(total_sql)
        total_geral = total_result[0]['total'] if isinstance(total_result, list) and total_result else 0
        print(f"\n🎯 Total de tarifas criadas: {total_geral}")
        
        # Exemplo de consulta para datas específicas
        print("\n🔍 Exemplo de tarifas por data:")
        exemplo_sql = """
        SELECT suite_tipo, temporada, preco_diaria,
               CASE 
                 WHEN CURRENT_DATE >= data_inicio AND CURRENT_DATE <= data_fim 
                 THEN 'VIGENTE'
                 ELSE 'NÃO VIGENTE'
               END as status
        FROM tarifas_suites 
        WHERE data_inicio >= '2026-01-01' 
        AND (data_fim <= '2026-12-31' OR data_fim <= '2027-01-02')
        ORDER BY temporada, suite_tipo
        LIMIT 10;
        """
        
        exemplos = await db.execute_raw(exemplo_sql)
        if isinstance(exemplos, list):
            for ex in exemplos:
                status_emoji = "✅" if ex.get('status') == 'VIGENTE' else "⏰"
                print(f"  {status_emoji} {ex.get('suite_tipo', 'N/A')} - {ex.get('temporada', 'N/A')}: R$ {ex.get('preco_diaria', 0):.2f}")
        else:
            print("  ⚠️ Não foi possível obter exemplos de tarifas")
        
    except Exception as e:
        print(f"❌ Erro ao executar seed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_temporadas_2026())
