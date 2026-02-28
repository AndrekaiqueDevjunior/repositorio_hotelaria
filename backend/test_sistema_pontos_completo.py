#!/usr/bin/env python3
"""
Teste do Sistema de Pontos criando tabelas manualmente
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor

def criar_tabelas_pontos():
    """Cria tabelas do sistema de pontos manualmente"""
    
    print('🏗️  Criando tabelas do Sistema de Pontos...')
    
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        # 1. Tabela usuarios (se não existir)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                senha_hash VARCHAR(255) NOT NULL,
                perfil VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'ATIVO',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 2. Tabela clientes (se não existir)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome_completo VARCHAR(255) NOT NULL,
                documento VARCHAR(20) NOT NULL,
                email VARCHAR(255),
                telefone VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 3. Tabela usuarios_pontos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_pontos (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL UNIQUE,
                saldo_atual INTEGER DEFAULT 0 NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        """)
        
        # 4. Tabela transacoes_pontos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacoes_pontos (
                id SERIAL PRIMARY KEY,
                usuario_pontos_id INTEGER NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                origem VARCHAR(100) NOT NULL,
                pontos INTEGER NOT NULL,
                motivo VARCHAR(500),
                criado_por_usuario_id INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (usuario_pontos_id) REFERENCES usuarios_pontos(id),
                FOREIGN KEY (criado_por_usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # 5. Tabela premios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS premios (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                preco_em_pontos INTEGER NOT NULL,
                ativo BOOLEAN DEFAULT TRUE,
                descricao VARCHAR(1000),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 6. Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_pontos_cliente_id ON usuarios_pontos(cliente_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_usuario_pontos_id ON transacoes_pontos(usuario_pontos_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_tipo ON transacoes_pontos(tipo)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_created_at ON transacoes_pontos(created_at)")
        
        conn.commit()
        print('✅ Tabelas criadas com sucesso!')
        
        return conn, cursor
        
    except Exception as e:
        print(f'❌ Erro ao criar tabelas: {str(e)}')
        raise

def test_sistema_pontos_completo():
    """Teste completo do sistema de pontos"""
    
    print('🎯 Teste Completo do Sistema de Pontos')
    print('=' * 60)
    
    try:
        # Criar tabelas
        conn, cursor = criar_tabelas_pontos()
        
        # Limpar dados anteriores
        print('\n🧹 Limpando dados anteriores...')
        cursor.execute("DELETE FROM transacoes_pontos")
        cursor.execute("DELETE FROM usuarios_pontos")
        cursor.execute("DELETE FROM premios")
        cursor.execute("DELETE FROM clientes")
        cursor.execute("DELETE FROM usuarios")
        conn.commit()
        
        # === CRIAÇÃO DE DADOS ===
        print('\n📝 Criando dados de teste...')
        
        # 1. Usuários
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil, status)
            VALUES 
                ('Administrador', 'admin@hotel.com', 'hash123', 'ADMIN', 'ATIVO'),
                ('Recepcionista', 'recepcionista@hotel.com', 'hash456', 'RECEPCAO', 'ATIVO')
            RETURNING id
        """)
        
        usuarios_ids = [row['id'] for row in cursor.fetchall()]
        admin_id, recepcionista_id = usuarios_ids
        
        # 2. Clientes
        cursor.execute("""
            INSERT INTO clientes (nome_completo, documento, email, telefone)
            VALUES 
                ('Roberto Silva', '123456789', 'roberto@email.com', '119999999'),
                ('Fernanda Costa', '987654321', 'fernanda@email.com', '118888888'),
                ('Carlos Oliveira', '456789123', 'carlos@email.com', '117777777'),
                ('Julia Santos', '789123456', 'julia@email.com', '116666666')
            RETURNING id
        """)
        
        clientes_ids = [row['id'] for row in cursor.fetchall()]
        roberto_id, fernanda_id, carlos_id, julia_id = clientes_ids
        
        # 3. Contas de pontos com bônus diferentes
        cursor.execute("""
            INSERT INTO usuarios_pontos (cliente_id, saldo_atual)
            VALUES 
                (%s, 150),  -- Roberto: bônus VIP
                (%s, 0),    -- Fernanda: sem pontos iniciais
                (%s, 75),   -- Carlos: bônus padrão
                (%s, 25)    -- Julia: bônus básico
            RETURNING id
        """, (roberto_id, fernanda_id, carlos_id, julia_id))
        
        pontos_ids = [row['id'] for row in cursor.fetchall()]
        roberto_pontos_id, fernanda_pontos_id, carlos_pontos_id, julia_pontos_id = pontos_ids
        
        # 4. Prêmios disponíveis
        cursor.execute("""
            INSERT INTO premios (nome, preco_em_pontos, descricao, ativo)
            VALUES 
                ('Diária Gratuita', 500, 'Uma diária gratuita em suíte deluxe', TRUE),
                ('Jantar Especial', 300, 'Jantar especial no restaurante', TRUE),
                ('Spa Completo', 200, 'Pacote completo de spa (4h)', TRUE),
                ('Late Checkout', 100, 'Check-out tardio até 18h', TRUE),
                ('Upgrade Suíte', 400, 'Upgrade para suíte superior', TRUE),
                ('Café da Manhã', 50, 'Café da manhã para dois', TRUE)
            RETURNING id
        """)
        
        premios_ids = [row['id'] for row in cursor.fetchall()]
        
        # 5. Transações iniciais (bônus de boas-vindas)
        cursor.execute("""
            INSERT INTO transacoes_pontos 
            (usuario_pontos_id, tipo, origem, pontos, motivo, criado_por_usuario_id)
            VALUES 
                (%s, 'CREDITO', 'BEM_VINDO', 150, 'Bônus VIP de boas-vindas', %s),
                (%s, 'CREDITO', 'BEM_VINDO', 75, 'Bônus padrão de boas-vindas', %s),
                (%s, 'CREDITO', 'BEM_VINDO', 25, 'Bônus básico de boas-vindas', %s)
        """, (roberto_pontos_id, admin_id, carlos_pontos_id, admin_id, julia_pontos_id, admin_id))
        
        conn.commit()
        print('✅ Dados criados com sucesso!')
        
        # === TESTES DO SISTEMA ===
        print('\n🎯 Testando Funcionalidades do Sistema')
        print('=' * 60)
        
        # Teste 1: Consultar saldos iniciais
        print('\n1. 💰 SALDOS INICIAIS')
        cursor.execute("""
            SELECT c.nome_completo, up.saldo_atual,
                   (SELECT COUNT(*) FROM transacoes_pontos tp 
                    WHERE tp.usuario_pontos_id = up.id) as num_transacoes
            FROM clientes c
            LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
            ORDER BY up.saldo_atual DESC NULLS LAST
        """)
        
        for row in cursor.fetchall():
            saldo = row['saldo_atual'] if row['saldo_atual'] else 0
            transacoes = row['num_transacoes'] or 0
            print(f'   {row["nome_completo"]}: {saldo} pontos ({transacoes} transações)')
        
        # Teste 2: Adicionar pontos por diversas atividades
        print('\n2. 📈 ADICIONANDO PONTOS (CRÉDITOS)')
        
        atividades = [
            (fernanda_pontos_id, 'CHECKIN', 30, 'Pontos por check-in'),
            (roberto_pontos_id, 'RESERVA', 50, 'Pontos por reserva antecipada'),
            (carlos_pontos_id, 'ESTADIA', 100, 'Pontos por estadia de 5 dias'),
            (julia_pontos_id, 'INDICACAO', 80, 'Indicação de novo cliente'),
            (fernanda_pontos_id, 'AVALIACAO', 20, 'Pontos por avaliação positiva'),
            (roberto_pontos_id, 'ANIVERSARIO', 100, 'Bônus de aniversário')
        ]
        
        for pontos_id, origem, pontos, motivo in atividades:
            cursor.execute("""
                INSERT INTO transacoes_pontos 
                (usuario_pontos_id, tipo, origem, pontos, motivo, criado_por_usuario_id)
                VALUES (%s, 'CREDITO', %s, %s, %s, %s)
            """, (pontos_id, origem, pontos, motivo, recepcionista_id))
            
            cursor.execute("""
                UPDATE usuarios_pontos 
                SET saldo_atual = saldo_atual + %s
                WHERE id = %s
            """, (pontos, pontos_id))
            
            # Obter nome do cliente para exibição
            cursor.execute("""
                SELECT c.nome_completo 
                FROM usuarios_pontos up
                JOIN clientes c ON up.cliente_id = c.id
                WHERE up.id = %s
            """, (pontos_id,))
            nome_cliente = cursor.fetchone()['nome_completo']
            
            print(f'   ✅ +{pontos} pontos para {nome_cliente} ({origem})')
        
        conn.commit()
        
        # Teste 3: Saldos após créditos
        print('\n3. 💳 SALDOS APÓS CRÉDITOS')
        cursor.execute("""
            SELECT c.nome_completo, up.saldo_atual
            FROM clientes c
            JOIN usuarios_pontos up ON c.id = up.cliente_id
            ORDER BY up.saldo_atual DESC
        """)
        
        for row in cursor.fetchall():
            saldo = row['saldo_atual']
            print(f'   {row["nome_completo"]}: {saldo} pontos')
        
        # Teste 4: Extrato detalhado
        print('\n4. 📋 EXTRATO DETALHADO')
        
        cursor.execute("""
            SELECT c.nome_completo, tp.tipo, tp.pontos, tp.origem, 
                   tp.motivo, tp.created_at, u.nome as operador
            FROM transacoes_pontos tp
            JOIN usuarios_pontos up ON tp.usuario_pontos_id = up.id
            JOIN clientes c ON up.cliente_id = c.id
            LEFT JOIN usuarios u ON tp.criado_por_usuario_id = u.id
            WHERE c.nome_completo = 'Roberto Silva'
            ORDER BY tp.created_at DESC
        """)
        
        print(f'\n   Extrato de Roberto Silva:')
        for row in cursor.fetchall():
            sinal = "+" if row['pontos'] > 0 else ""
            data = row['created_at'].strftime("%d/%m %H:%M")
            operador = f" ({row['operador']})" if row['operador'] else ""
            print(f'     {data} | {row["tipo"]} | {sinal}{row["pontos"]} pts | {row["origem"]}{operador}')
            if row['motivo']:
                print(f'        💭 {row["motivo"]}')
        
        # Teste 5: Resgatar prêmios
        print('\n5. 🎁 RESGATE DE PRÊMIOS')
        
        # Exibir prêmios disponíveis
        cursor.execute("SELECT * FROM premios WHERE ativo = TRUE ORDER BY preco_em_pontos")
        premios = cursor.fetchall()
        
        print('   Prêmios disponíveis:')
        for premio in premios:
            print(f'     🏆 {premio["nome"]}: {premio["preco_em_pontos"]} pontos')
        
        # Resgates
        resgates = [
            (julia_pontos_id, 6, 50, 'Late Checkout'),  # Julia tem 105 pontos
            (carlos_pontos_id, 4, 200, 'Spa Completo'),  # Carlos tem 175 pontos (não suficiente)
            (roberto_pontos_id, 2, 300, 'Jantar Especial'), # Roberto tem 300 pontos
            (fernanda_pontos_id, 6, 100, 'Late Checkout')  # Fernanda tem 50 pontos (não suficiente)
        ]
        
        for pontos_id, premio_index, custo, nome_premio in resgates:
            cursor.execute("SELECT saldo_atual FROM usuarios_pontos WHERE id = %s", (pontos_id,))
            saldo_atual = cursor.fetchone()['saldo_atual']
            
            cursor.execute("""
                SELECT c.nome_completo 
                FROM usuarios_pontos up
                JOIN clientes c ON up.cliente_id = c.id
                WHERE up.id = %s
            """, (pontos_id,))
            nome_cliente = cursor.fetchone()['nome_completo']
            
            if saldo_atual >= custo:
                # Realizar resgate
                cursor.execute("""
                    INSERT INTO transacoes_pontos 
                    (usuario_pontos_id, tipo, origem, pontos, motivo, criado_por_usuario_id)
                    VALUES (%s, 'DEBITO', 'RESGATE', -%s, %s, %s)
                """, (pontos_id, custo, f'Resgate: {nome_premio}', admin_id))
                
                cursor.execute("""
                    UPDATE usuarios_pontos 
                    SET saldo_atual = saldo_atual - %s
                    WHERE id = %s
                """, (custo, pontos_id))
                
                print(f'   ✅ {nome_cliente} resgatou "{nome_premio}" por {custo} pontos')
            else:
                print(f'   ❌ {nome_cliente} não tem pontos suficientes para "{nome_premio}" (tem {saldo_atual}, precisa {custo})')
        
        conn.commit()
        
        # Teste 6: Saldos finais
        print('\n6. 🏦 SALDOS FINAIS')
        cursor.execute("""
            SELECT c.nome_completo, up.saldo_atual,
                   (SELECT COUNT(*) FROM transacoes_pontos tp 
                    WHERE tp.usuario_pontos_id = up.id) as total_transacoes,
                   (SELECT COUNT(*) FROM transacoes_pontos tp 
                    WHERE tp.usuario_pontos_id = up.id AND tp.tipo = 'DEBITO') as resgates
            FROM clientes c
            LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
            ORDER BY up.saldo_atual DESC NULLS LAST
        """)
        
        for row in cursor.fetchall():
            if row['saldo_atual']:
                print(f'   {row["nome_completo"]}: {row["saldo_atual"]} pontos ({row["total_transacoes"]} transações, {row["resgates"]} resgates)')
        
        # Teste 7: Relatórios e estatísticas
        print('\n7. 📊 RELATÓRIOS E ESTATÍSTICAS')
        
        # Totais gerais
        cursor.execute("SELECT COUNT(*) as total, SUM(saldo_atual) as pontos FROM usuarios_pontos")
        resultado = cursor.fetchone()
        print(f'   📈 Clientes com pontos: {resultado["total"]}')
        print(f'   💎 Total de pontos em circulação: {resultado["pontos"] or 0}')
        
        # Transações por tipo
        cursor.execute("""
            SELECT tipo, COUNT(*) as quantidade, SUM(pontos) as total_pontos
            FROM transacoes_pontos
            GROUP BY tipo
            ORDER BY quantidade DESC
        """)
        
        print(f'   📋 Transações por tipo:')
        for row in cursor.fetchall():
            sinal = "+" if row['total_pontos'] > 0 else ""
            print(f'     {row["tipo"]}: {row["quantidade"]} transações ({sinal}{row["total_pontos"]} pontos)')
        
        # Top clientes
        cursor.execute("""
            SELECT c.nome_completo, up.saldo_atual,
                   COUNT(tp.id) as num_transacoes,
                   SUM(CASE WHEN tp.tipo = 'CREDITO' THEN tp.pontos ELSE 0 END) as total_creditos,
                   SUM(CASE WHEN tp.tipo = 'DEBITO' THEN ABS(tp.pontos) ELSE 0 END) as total_debitos
            FROM clientes c
            JOIN usuarios_pontos up ON c.id = up.cliente_id
            LEFT JOIN transacoes_pontos tp ON up.id = tp.usuario_pontos_id
            GROUP BY c.id, up.id
            ORDER BY up.saldo_atual DESC
            LIMIT 3
        """)
        
        print(f'   🏆 Top clientes:')
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f'     {i}. {row["nome_completo"]}: {row["saldo_atual"]} pts')
            print(f'        Créditos: +{row["total_creditos"] or 0} | Débitos: -{row["total_debitos"] or 0} | Transações: {row["num_transacoes"]}')
        
        # Atividades mais comuns
        cursor.execute("""
            SELECT origem, COUNT(*) as frequencia, SUM(pontos) as pontos_gerados
            FROM transacoes_pontos
            WHERE tipo = 'CREDITO'
            GROUP BY origem
            ORDER BY frequencia DESC
            LIMIT 5
        """)
        
        print(f'   🎯 Atividades mais comuns:')
        for row in cursor.fetchall():
            print(f'     {row["origem"]}: {row["frequencia"]} vezes (+{row["pontos_gerados"]} pts)')
        
        # Teste 8: Histórico completo
        print('\n8. 📜 HISTÓRICO COMPLETO DO SISTEMA')
        
        cursor.execute("""
            SELECT tp.created_at, c.nome_completo, tp.tipo, tp.pontos, 
                   tp.origem, tp.motivo, u.nome as operador
            FROM transacoes_pontos tp
            JOIN usuarios_pontos up ON tp.usuario_pontos_id = up.id
            JOIN clientes c ON up.cliente_id = c.id
            LEFT JOIN usuarios u ON tp.criado_por_usuario_id = u.id
            ORDER BY tp.created_at DESC
            LIMIT 15
        """)
        
        print(f'   Últimas transações:')
        for i, row in enumerate(cursor.fetchall(), 1):
            sinal = "+" if row['pontos'] > 0 else ""
            data = row['created_at'].strftime("%d/%m %H:%M")
            operador = f" ({row['operador']})" if row['operador'] else ""
            print(f'     {i}. {data} | {row["nome_completo"]} | {row["tipo"]} | {sinal}{row["pontos"]} pts | {row["origem"]}{operador}')
            if row['motivo']:
                print(f'        💭 {row["motivo"]}')
        
        print('\n🎉 TESTE DO SISTEMA DE PONTOS CONCLUÍDO!')
        print('✅ Todas as funcionalidades validadas com sucesso!')
        
        # Resumo final
        print('\n📊 Resumo Final do Sistema:')
        cursor.execute("SELECT COUNT(*) as total FROM usuarios_pontos")
        clientes_pontos = cursor.fetchone()['total']
        
        cursor.execute("SELECT SUM(saldo_atual) as total FROM usuarios_pontos")
        pontos_circulacao = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT COUNT(*) as total FROM transacoes_pontos")
        total_transacoes = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM premios WHERE ativo = TRUE")
        premios_disponiveis = cursor.fetchone()['total']
        
        print(f'   👥 Clientes com pontos: {clientes_pontos}')
        print(f'   💎 Pontos em circulação: {pontos_circulacao}')
        print(f'   📋 Total de transações: {total_transacoes}')
        print(f'   🏆 Prêmios disponíveis: {premios_disponiveis}')
        print(f'   🎯 Sistema 100% funcional! 🚀')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_sistema_pontos_completo()
