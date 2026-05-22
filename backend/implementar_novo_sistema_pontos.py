#!/usr/bin/env python3
"""
Atualiza o sistema de pontos para seguir a nova lógica de RP (Reais Pontos)

Sistema Principal:
- Luxo: 3 RP
- Master: 4 RP
- Real: 5 RP

Regras: a cada duas diárias

Cálculo baseado no valor total da estadia:
- Suíte Luxo: R$ 600-700 (2 diárias) = 3 RP
- Suíte Dupla: R$ 1200-1400 (2 diárias) = 4 RP
- Suíte Master: R$ 800-900 (2 diárias) = 4 RP
- Suíte Real: R$ 1000-1200 (2 diárias) = 5 RP
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor

def implementar_novo_sistema_pontos():
    """Implementa o novo sistema de pontos RP"""

    print('🎯 Implementando Novo Sistema de Pontos RP')
    print('=' * 60)

    try:
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password=os.environ.get("DB_PASSWORD"),
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()

        print('✅ Conectado ao banco de dados')

        # 1. Atualizar tipos de suíte
        print('\n📝 Atualizando Tipos de Suíte...')

        # Limpar tipos existentes
        cursor.execute("DELETE FROM tipos_suite")

        # Inserir novos tipos conforme especificação
        novos_tipos = [
            ('Suíte Luxo', 'Suíte de luxo para casal, 300-350 por diária', 2, 3),
            ('Suíte Dupla', 'Suíte dupla para casal, 600-700 por diária', 2, 4),
            ('Suíte Master', 'Suíte master para casal, 400-450 por diária', 2, 4),
            ('Suíte Real', 'Suíte real para casal, 500-600 por diária', 2, 5)
        ]

        for nome, descricao, capacidade, rp_por_duas_diarias in novos_tipos:
            cursor.execute("""
                INSERT INTO tipos_suite (nome, descricao, capacidade, pontos_por_par)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (nome, descricao, capacidade, rp_por_duas_diarias))

            suite_id = cursor.fetchone()["id"]
            print(f'   ✅ {nome}: {rp_por_duas_diarias} RP por 2 diárias')

        # 2. Atualizar quartos
        print('\n🏨 Atualizando Quartos...')

        # Limpar quartos existentes
        cursor.execute("DELETE FROM quartos")

        # Inserir quartos para cada tipo
        cursor.execute("SELECT id, nome FROM tipos_suite ORDER BY id")
        tipos = cursor.fetchall()

        for tipo in tipos:
            # Criar 2 quartos de cada tipo
            for i in range(1, 3):
                numero = f"{tipo['id']}{i:02d}"
                cursor.execute("""
                    INSERT INTO quartos (numero, tipo_suite_id, status)
                    VALUES (%s, %s, 'ATIVO')
                """, (numero, tipo['id']))
                print(f'   ✅ Quarto {numero} - {tipo["nome"]}')

        # 3. Atualizar prêmios
        print('\n🏆 Atualizando Prêmios...')

        # Limpar prêmios existentes
        cursor.execute("DELETE FROM premios")

        # Inserir novos prêmios conforme especificação
        novos_premios = [
            ('1 Diária Suíte Luxo', 20, 'Uma diária gratuita na suíte luxo'),
            ('Cafeteira', 35, 'Cafeteira premium para quarto'),
            ('Luminária Carregador', 25, 'Luminária com porta de carregamento USB'),
            ('iPhone 16', 100, 'iPhone 16 128GB latest')
        ]

        for nome, pontos, descricao in novos_premios:
            cursor.execute("""
                INSERT INTO premios (nome, preco_em_pontos, descricao, ativo)
                VALUES (%s, %s, %s, TRUE)
                RETURNING id
            """, (nome, pontos, descricao))

            premio_id = cursor.fetchone()["id"]
            print(f'   ✅ {nome}: {pontos} RP')

        # 4. Criar função para calcular pontos
        print('\n⚙️  Criando Função de Cálculo de Pontos...')

        cursor.execute("""
            DROP FUNCTION IF EXISTS calcular_pontos_rp;

            CREATE OR REPLACE FUNCTION calcular_pontos_rp(
                p_valor_total NUMERIC,
                p_num_diarias INTEGER
            ) RETURNS INTEGER AS $$
            DECLARE
                v_pontos_por_diaria INTEGER;
                v_pontos_totais INTEGER;
            BEGIN
                -- Regra: a cada duas diárias
                IF p_num_diarias < 2 THEN
                    RETURN 0;
                END IF;

                -- Calcular pontos baseado no valor total
                -- Suíte Luxo: 600-700 = 3 RP
                -- Suíte Dupla: 1200-1400 = 4 RP
                -- Suíte Master: 800-900 = 4 RP
                -- Suíte Real: 1000-1200 = 5 RP

                IF p_valor_total >= 1000 THEN
                    v_pontos_por_diaria := 5; -- Real
                ELSIF p_valor_total >= 1200 THEN
                    v_pontos_por_diaria := 5; -- Real
                ELSIF p_valor_total >= 800 THEN
                    v_pontos_por_diaria := 4; -- Master
                ELSIF p_valor_total >= 600 THEN
                    v_pontos_por_diaria := 3; -- Luxo
                ELSE
                    v_pontos_por_diaria := 0;
                END IF;

                -- Calcular pontos totais (a cada 2 diárias)
                v_pontos_totais := (p_num_diarias / 2) * v_pontos_por_diaria;

                RETURN v_pontos_totais;
            END;
            $$ LANGUAGE plpgsql;
        """)

        print('   ✅ Função calcular_pontos_rp criada')

        # 5. Atualizar modelo de pontos (se necessário)
        print('\n📋 Atualizando Estrutura de Pontos...')

        # Verificar se a coluna rp_points existe em usuarios_pontos
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'usuarios_pontos'
            AND column_name = 'rp_points'
        """)

        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE usuarios_pontos
                ADD COLUMN rp_points INTEGER DEFAULT 0
            """)
            print('   ✅ Coluna rp_points adicionada')
        else:
            print('   ✅ Coluna rp_points já existe')

        # 6. Testar a função
        print('\n🧪 Testando Função de Cálculo...')

        testes = [
            (650, 2, 3),   # Suíte Luxo: 2 diárias = 3 RP
            (1300, 2, 4),  # Suíte Dupla: 2 diárias = 4 RP
            (850, 2, 4),   # Suíte Master: 2 diárias = 4 RP
            (1100, 2, 5),  # Suíte Real: 2 diárias = 5 RP
            (650, 4, 6),   # Suíte Luxo: 4 diárias = 6 RP
            (1300, 4, 8),  # Suíte Dupla: 4 diárias = 8 RP
        ]

        for valor, diarias, esperado in testes:
            cursor.execute("SELECT calcular_pontos_rp(%s, %s)", (valor, diarias))
            resultado = cursor.fetchone()["calcular_pontos_rp"]

            status = "✅" if resultado == esperado else "❌"
            print(f'   {status} R$ {valor} ({diarias} diárias) = {resultado} RP (esperado: {esperado})')

        conn.commit()

        # 7. Relatório final
        print('\n📊 Relatório Final - Novo Sistema RP')
        print('=' * 60)

        cursor.execute("SELECT * FROM tipos_suite ORDER BY id")
        tipos = cursor.fetchall()

        print('\n🏨 Tipos de Suíte Configurados:')
        for tipo in tipos:
            print(f'   {tipo["nome"]}: {tipo["pontos_por_par"]} RP por 2 diárias')

        cursor.execute("SELECT * FROM premios ORDER BY preco_em_pontos")
        premios = cursor.fetchall()

        print('\n🏆 Prêmios Disponíveis:')
        for premio in premios:
            print(f'   {premio["nome"]}: {premio["preco_em_pontos"]} RP')

        cursor.execute("SELECT COUNT(*) as total FROM quartos")
        total_quartos = cursor.fetchone()["total"]

        print(f'\n🏢 Quartos Configurados: {total_quartos}')

        print('\n✅ Novo sistema de pontos RP implementado com sucesso!')
        print('🎯 Regras aplicadas: a cada duas diárias conforme valor')

    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()

    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    implementar_novo_sistema_pontos()
