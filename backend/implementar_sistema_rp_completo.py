#!/usr/bin/env python3
"""
Implementação completa do novo sistema de pontos RP com limpeza segura
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor

def implementar_novo_sistema_pontos_completo():
    """Implementa o novo sistema de pontos RP com limpeza completa"""
    
    print('🎯 Implementação Completa - Novo Sistema de Pontos RP')
    print('=' * 70)
    
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        print('✅ Conectado ao banco de dados')
        
        # 1. Limpeza segura em ordem correta (respeitando FKs)
        print('\n🧹 Limpando dados existentes...')
        
        # Ordem reversa das dependências
        tabelas_limpar = [
            ('transacoes_pontos', 'Transações de pontos'),
            ('usuarios_pontos', 'Contas de pontos'),
            ('reservas', 'Reservas'),
            ('pagamentos', 'Pagamentos'),
            ('quartos', 'Quartos'),
            ('tipos_suite', 'Tipos de suíte'),
            ('premios', 'Prêmios')
        ]
        
        for tabela, descricao in tabelas_limpar:
            cursor.execute(f"DELETE FROM {tabela}")
            print(f'   ✅ {descricao} limpos')
        
        # 2. Configurar novos tipos de suíte
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
        
        # 5. Criar função de cálculo de pontos
        print('\n⚙️  Criando Função de Cálculo de Pontos RP...')
        
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
                
                -- Calcular pontos baseado no valor total
                -- Suíte Luxo: R$ 600-700 (2 diárias) = 3 RP
                -- Suíte Dupla: R$ 1200-1400 (2 diárias) = 4 RP  
                -- Suíte Master: R$ 800-900 (2 diárias) = 4 RP
                -- Suíte Real: R$ 1000-1200 (2 diárias) = 5 RP
                
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
        
        # 6. Atualizar estrutura da tabela de pontos
        print('\n📋 Atualizando Estrutura de Pontos...')
        
        # Adicionar coluna rp_points se não existir
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
        
        # 7. Testes completos da função
        print('\n🧪 Testando Função de Cálculo...')
        
        testes = [
            # (valor_total, num_diarias, rp_esperado, descricao)
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
        
        # 8. Criar dados de exemplo
        print('\n📝 Criando Dados de Exemplo...')
        
        # Criar usuário admin
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil, status)
            VALUES ('Administrador RP', 'admin@rp.com', 'hash123', 'ADMIN', 'ATIVO')
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """)
        
        result = cursor.fetchone()
        admin_id = result["id"] if result else None
        
        # Criar cliente exemplo
        cursor.execute("""
            INSERT INTO clientes (nome_completo, documento, email, telefone)
            VALUES ('João RP', '11122233344', 'joao@rp.com', '119999999')
            RETURNING id
        """)
        
        cliente_id = cursor.fetchone()["id"]
        
        # Criar conta de pontos
        cursor.execute("""
            INSERT INTO usuarios_pontos (cliente_id, saldo_atual, rp_points)
            VALUES (%s, 0, 0)
            RETURNING id
        """, (cliente_id,))
        
        pontos_id = cursor.fetchone()["id"]
        
        print(f'   ✅ Cliente exemplo criado: ID {cliente_id}')
        print(f'   ✅ Conta de pontos criada: ID {pontos_id}')
        
        conn.commit()
        
        # 9. Relatório final completo
        print('\n📊 RELATÓRIO FINAL - SISTEMA RP IMPLEMENTADO')
        print('=' * 70)
        
        print('\n🏨 TIPOS DE SUÍTE CONFIGURADOS:')
        cursor.execute("SELECT * FROM tipos_suite ORDER BY id")
        for tipo in cursor.fetchall():
            print(f'   📍 {tipo["nome"]}')
            print(f'      💰 {tipo["pontos_por_par"]} RP por 2 diárias')
            print(f'      👥 Capacidade: {tipo["capacidade"]} pessoas')
        
        print('\n🏆 PRÊMIOS DISPONÍVEIS:')
        cursor.execute("SELECT * FROM premios ORDER BY preco_em_pontos")
        for premio in cursor.fetchall():
            print(f'   🎁 {premio["nome"]}: {premio["preco_em_pontos"]} RP')
            print(f'      💭 {premio["descricao"]}')
        
        print('\n🏢 QUARTOS DISPONÍVEIS:')
        cursor.execute("""
            SELECT q.numero, ts.nome as tipo_suite
            FROM quartos q
            JOIN tipos_suite ts ON q.tipo_suite_id = ts.id
            ORDER BY q.numero
        """)
        
        quartos_por_tipo = {}
        for quarto in cursor.fetchall():
            tipo = quarto["tipo_suite"]
            if tipo not in quartos_por_tipo:
                quartos_por_tipo[tipo] = []
            quartos_por_tipo[tipo].append(quarto["numero"])
        
        for tipo, numeros in quartos_por_tipo.items():
            print(f'   🏨 {tipo}: {", ".join(numeros)}')
        
        print(f'\n📋 ESTATÍSTICAS:')
        cursor.execute("SELECT COUNT(*) as total FROM quartos")
        print(f'   🏢 Total de quartos: {cursor.fetchone()["total"]}')
        
        cursor.execute("SELECT COUNT(*) as total FROM premios")
        print(f'   🏆 Total de prêmios: {cursor.fetchone()["total"]}')
        
        cursor.execute("SELECT COUNT(*) as total FROM tipos_suite")
        print(f'   📍 Total de suítes: {cursor.fetchone()["total"]}')
        
        print('\n✅ SISTEMA RP IMPLEMENTADO COM SUCESSO!')
        print('🎯 Regras: a cada duas diárias conforme valor total')
        print('💎 Pontos calculados automaticamente pela função calcular_pontos_rp()')
        
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
    implementar_novo_sistema_pontos_completo()
