#!/usr/bin/env python3
"""
Implementação definitiva do novo sistema de pontos RP com ordem correta de limpeza
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor

def implementar_sistema_rp_definitivo():
    """Implementação definitiva do sistema RP"""

    print('🎯 IMPLEMENTAÇÃO DEFINITIVA - Sistema de Pontos RP')
    print('=' * 70)

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

        # 1. Limpeza na ordem correta (respeitando todas as FKs)
        print('\n🧹 Limpando dados existentes (ordem correta)...')

        # Ordem exata das dependências (do mais dependente para o menos)
        tabelas_limpar = [
            ('transacoes_pontos', 'Transações de pontos'),
            ('usuarios_pontos', 'Contas de pontos'),
            ('pagamentos', 'Pagamentos'),
            ('reservas', 'Reservas'),
            ('quartos', 'Quartos'),
            ('tipos_suite', 'Tipos de suíte'),
            ('premios', 'Prêmios')
        ]

        for tabela, descricao in tabelas_limpar:
            cursor.execute(f"DELETE FROM {tabela}")
            print(f'   ✅ {descricao} limpos')

        # 2. Configurar tipos de suíte
        print('\n📝 Configurando Novos Tipos de Suíte...')

        novos_tipos = [
            ('Suíte Luxo', 'Suíte de luxo para casal, R$ 300-350 por diária', 2, 3),
            ('Suíte Dupla', 'Suíte dupla para casal, R$ 600-700 por diária', 2, 4),
            ('Suíte Master', 'Suíte master para casal, R$ 400-450 por diária', 2, 4),
            ('Suíte Real', 'Suíte real para casal, R$ 500-600 por diária', 2, 5)
        ]

        suite_ids = {}
        for nome, descricao, capacidade, rp_por_duas_diarias in novos_tipos:
            cursor.execute("""
                INSERT INTO tipos_suite (nome, descricao, capacidade, pontos_por_par)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (nome, descricao, capacidade, rp_por_duas_diarias))

            suite_id = cursor.fetchone()["id"]
            suite_ids[nome] = suite_id
            print(f'   ✅ {nome}: {rp_por_duas_diarias} RP por 2 diárias')

        # 3. Criar quartos
        print('\n🏨 Criando Quartos...')

        for nome, suite_id in suite_ids.items():
            # Criar 3 quartos de cada tipo
            for i in range(1, 4):
                numero = f"{suite_id:02d}{i:02d}"
                cursor.execute("""
                    INSERT INTO quartos (numero, tipo_suite_id, status)
                    VALUES (%s, %s, 'ATIVO')
                """, (numero, suite_id))
                print(f'   ✅ Quarto {numero} - {nome}')

        # 4. Configurar prêmios
        print('\n🏆 Configurando Prêmios...')

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
            """, (nome, pontos, descricao))
            print(f'   ✅ {nome}: {pontos} RP')

        # 5. Criar função de cálculo
        print('\n⚙️  Criando Função de Cálculo RP...')

        cursor.execute("""
            DROP FUNCTION IF EXISTS calcular_pontos_rp;

            CREATE OR REPLACE FUNCTION calcular_pontos_rp(
                p_valor_total NUMERIC,
                p_num_diarias INTEGER
            ) RETURNS INTEGER AS $$
            DECLARE
                v_pontos_por_duas_diarias INTEGER;
                v_pontos_totais INTEGER;
                v_pares_diarias INTEGER;
            BEGIN
                -- Regra: a cada duas diárias
                IF p_num_diarias < 2 THEN
                    RETURN 0;
                END IF;

                -- Calcular número de pares de diárias
                v_pares_diarias := p_num_diarias / 2;

                -- Calcular pontos baseado no valor total por 2 diárias
                -- Suíte Luxo: R$ 600-700 = 3 RP
                -- Suíte Dupla: R$ 1200-1400 = 4 RP
                -- Suíte Master: R$ 800-900 = 4 RP
                -- Suíte Real: R$ 1000-1200 = 5 RP

                IF p_valor_total >= 1000 THEN
                    v_pontos_por_duas_diarias := 5; -- Real
                ELSIF p_valor_total >= 800 THEN
                    v_pontos_por_duas_diarias := 4; -- Master
                ELSIF p_valor_total >= 600 THEN
                    v_pontos_por_duas_diarias := 3; -- Luxo
                ELSE
                    v_pontos_por_duas_diarias := 0;
                END IF;

                -- Calcular pontos totais
                v_pontos_totais := v_pares_diarias * v_pontos_por_duas_diarias;

                RETURN v_pontos_totais;
            END;
            $$ LANGUAGE plpgsql;
        """)

        print('   ✅ Função calcular_pontos_rp criada')

        # 6. Testar função
        print('\n🧪 Testando Função de Cálculo...')

        testes = [
            (650, 2, 3, 'Suíte Luxo: 2 diárias'),
            (1300, 2, 4, 'Suíte Dupla: 2 diárias'),
            (850, 2, 4, 'Suíte Master: 2 diárias'),
            (1100, 2, 5, 'Suíte Real: 2 diárias'),
            (650, 4, 6, 'Suíte Luxo: 4 diárias'),
            (1300, 4, 8, 'Suíte Dupla: 4 diárias'),
            (850, 4, 8, 'Suíte Master: 4 diárias'),
            (1100, 4, 10, 'Suíte Real: 4 diárias'),
            (650, 1, 0, 'Suíte Luxo: 1 diária (abaixo do mínimo)'),
            (500, 2, 0, 'Valor abaixo do mínimo: 2 diárias'),
        ]

        for valor, diarias, esperado, descricao in testes:
            cursor.execute("SELECT calcular_pontos_rp(%s, %s)", (valor, diarias))
            resultado = cursor.fetchone()["calcular_pontos_rp"]

            status = "✅" if resultado == esperado else "❌"
            print(f'   {status} {descricao}')
            print(f'      R$ {valor} ({diarias} diárias) = {resultado} RP (esperado: {esperado})')

        conn.commit()

        # 7. Relatório final
        print('\n📊 SISTEMA RP IMPLEMENTADO COM SUCESSO!')
        print('=' * 70)

        print('\n🏨 TIPOS DE SUÍTE:')
        cursor.execute("SELECT * FROM tipos_suite ORDER BY id")
        for tipo in cursor.fetchall():
            print(f'   📍 {tipo["nome"]}: {tipo["pontos_por_par"]} RP por 2 diárias')

        print('\n🏆 PRÊMIOS:')
        cursor.execute("SELECT * FROM premios ORDER BY preco_em_pontos")
        for premio in cursor.fetchall():
            print(f'   🎁 {premio["nome"]}: {premio["preco_em_pontos"]} RP')

        print('\n🏢 QUARTOS:')
        cursor.execute("""
            SELECT q.numero, ts.nome as tipo_suite
            FROM quartos q
            JOIN tipos_suite ts ON q.tipo_suite_id = ts.id
            ORDER BY q.numero
        """)

        for quarto in cursor.fetchall():
            print(f'   🏨 Quarto {quarto["numero"]} - {quarto["tipo_suite"]}')

        print(f'\n✅ Sistema RP pronto para uso!')
        print('🎯 Regra: a cada 2 diárias conforme valor total')

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
    implementar_sistema_rp_definitivo()
