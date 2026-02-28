#!/usr/bin/env python3
"""
Script para criar todas as tabelas faltantes no banco de dados
"""

import sys
import os
sys.path.append('/app')

from sqlalchemy import create_engine, text
import psycopg2
from psycopg2.extras import RealDictCursor

def criar_tabelas_faltantes():
    """Cria todas as tabelas que estão nos models mas não existem no BD"""
    
    print('🏗️  Criando Tabelas Faltantes no Banco de Dados')
    print('=' * 60)
    
    try:
        # Conectar ao PostgreSQL
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        print('✅ Conectado ao PostgreSQL')
        
        # 1. Tabela tipos_suite
        print('\n📁 Criando tabela tipos_suite...')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipos_suite (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                descricao VARCHAR(500),
                capacidade INTEGER DEFAULT 2 NOT NULL,
                pontos_por_par INTEGER NOT NULL,
                ativo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 2. Tabela quartos
        print('📁 Criando tabela quartos...')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quartos (
                id SERIAL PRIMARY KEY,
                numero VARCHAR(10) UNIQUE NOT NULL,
                tipo_suite_id INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'ATIVO',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (tipo_suite_id) REFERENCES tipos_suite(id)
            )
        """)
        
        # 3. Tabela reservas
        print('📁 Criando tabela reservas...')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservas (
                id SERIAL PRIMARY KEY,
                codigo_reserva VARCHAR(50) UNIQUE NOT NULL,
                cliente_id INTEGER NOT NULL,
                quarto_id INTEGER,
                status_reserva VARCHAR(20) DEFAULT 'PENDENTE',
                origem VARCHAR(20) DEFAULT 'BALCAO',
                checkin_previsto TIMESTAMP NOT NULL,
                checkout_previsto TIMESTAMP NOT NULL,
                checkin_real TIMESTAMP,
                checkout_real TIMESTAMP,
                valor_diaria DECIMAL(10,2) NOT NULL,
                num_diarias_previstas INTEGER NOT NULL,
                valor_previsto DECIMAL(10,2) NOT NULL,
                observacoes TEXT,
                criado_por_usuario_id INTEGER NOT NULL,
                atualizado_por_usuario_id INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (quarto_id) REFERENCES quartos(id),
                FOREIGN KEY (criado_por_usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY (atualizado_por_usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # 4. Tabela pagamentos
        print('📁 Criando tabela pagamentos...')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagamentos (
                id SERIAL PRIMARY KEY,
                reserva_id INTEGER NOT NULL,
                cliente_id INTEGER NOT NULL,
                metodo VARCHAR(20) NOT NULL,
                valor DECIMAL(10,2) NOT NULL,
                observacao TEXT,
                data_pagamento TIMESTAMP DEFAULT NOW(),
                status_pagamento VARCHAR(20) DEFAULT 'PENDENTE',
                provider VARCHAR(50),
                payment_id VARCHAR(100),
                raw_response TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (reserva_id) REFERENCES reservas(id),
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        """)
        
        # 5. Tabela hospedes_adicionais
        print('📁 Criando tabela hospedes_adicionais...')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hospedes_adicionais (
                id SERIAL PRIMARY KEY,
                reserva_id INTEGER NOT NULL,
                nome_completo VARCHAR(255) NOT NULL,
                documento VARCHAR(20),
                parentesco VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (reserva_id) REFERENCES reservas(id) ON DELETE CASCADE
            )
        """)
        
        # 6. Tabela itens_cobranca
        print('📁 Criando tabela itens_cobranca...')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_cobranca (
                id SERIAL PRIMARY KEY,
                reserva_id INTEGER NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                descricao VARCHAR(255) NOT NULL,
                quantidade INTEGER DEFAULT 1,
                valor_unitario DECIMAL(10,2) NOT NULL,
                valor_total DECIMAL(10,2) NOT NULL,
                data_lancamento TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (reserva_id) REFERENCES reservas(id) ON DELETE CASCADE
            )
        """)
        
        # 7. Tabela auditorias
        print('📁 Criando tabela auditorias...')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auditorias (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER,
                acao VARCHAR(100) NOT NULL,
                tabela VARCHAR(50),
                registro_id INTEGER,
                valores_antigos TEXT,
                valores_novos TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # 8. Tabela antifraude_operacoes
        print('📁 Criando tabela antifraude_operacoes...')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS antifraude_operacoes (
                id SERIAL PRIMARY KEY,
                tipo_operacao VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'PENDENTE',
                dados_analise TEXT,
                score_risco DECIMAL(5,2),
                decisao VARCHAR(20),
                motivo_decisao TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Criar índices importantes
        print('\n🔍 Criando índices de performance...')
        
        indices = [
            ("idx_reservas_cliente_id", "reservas", "cliente_id"),
            ("idx_reservas_quarto_id", "reservas", "quarto_id"),
            ("idx_reservas_status", "reservas", "status_reserva"),
            ("idx_reservas_codigo", "reservas", "codigo_reserva"),
            ("idx_pagamentos_reserva_id", "pagamentos", "reserva_id"),
            ("idx_pagamentos_cliente_id", "pagamentos", "cliente_id"),
            ("idx_pagamentos_status", "pagamentos", "status_pagamento"),
            ("idx_quartos_numero", "quartos", "numero"),
            ("idx_quartos_tipo_suite", "quartos", "tipo_suite_id"),
            ("idx_quartos_status", "quartos", "status"),
            ("idx_tipos_suite_ativo", "tipos_suite", "ativo"),
            ("idx_auditorias_usuario_id", "auditorias", "usuario_id"),
            ("idx_auditorias_created_at", "auditorias", "created_at"),
            ("idx_antifraude_status", "antifraude_operacoes", "status"),
            ("idx_antifraude_created_at", "antifraude_operacoes", "created_at")
        ]
        
        for nome_idx, tabela, coluna in indices:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {nome_idx} 
                ON {tabela}({coluna})
            """)
        
        conn.commit()
        print('✅ Índices criados com sucesso!')
        
        # 9. Inserir dados iniciais
        print('\n📝 Inserindo dados iniciais...')
        
        # Tipos de suíte
        cursor.execute("""
            INSERT INTO tipos_suite (nome, descricao, capacidade, pontos_por_par)
            VALUES 
                ('Suíte Standard', 'Suíte confortável com vista para o mar', 2, 50),
                ('Suíte Deluxe', 'Suíte ampla com varanda', 2, 75),
                ('Suíte Premium', 'Suíte de luxo com sacada privativa', 3, 100),
                ('Suíte Familiar', 'Suíte espaçosa para famílias', 4, 125)
            ON CONFLICT DO NOTHING
        """)
        
        # Quartos
        cursor.execute("""
            INSERT INTO quartos (numero, tipo_suite_id, status)
            VALUES 
                ('101', 1, 'ATIVO'),
                ('102', 1, 'ATIVO'),
                ('201', 2, 'ATIVO'),
                ('202', 2, 'MANUTENCAO'),
                ('301', 3, 'ATIVO'),
                ('401', 4, 'ATIVO')
            ON CONFLICT (numero) DO NOTHING
        """)
        
        conn.commit()
        print('✅ Dados iniciais inseridos!')
        
        # 10. Verificação final
        print('\n🔍 Verificação final das tabelas...')
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tabelas = cursor.fetchall()
        print(f'\n📊 Total de tabelas criadas: {len(tabelas)}')
        
        for tabela in tabelas:
            cursor.execute(f'SELECT COUNT(*) as total FROM {tabela["table_name"]}')
            total = cursor.fetchone()["total"]
            print(f'   📁 {tabela["table_name"]}: {total} registros')
        
        print('\n🎉 Todas as tabelas foram criadas com sucesso!')
        print('✅ Banco de dados 100% estruturado!')
        
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
    criar_tabelas_faltantes()
