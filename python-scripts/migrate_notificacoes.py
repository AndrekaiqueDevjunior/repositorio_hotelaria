#!/usr/bin/env python3
"""
Migration manual para criar tabela de notificações
Execute: python migrate_notificacoes.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import get_db

def criar_tabela_notificacoes():
    """Criar tabela de notificações manualmente"""
    
    sql = """
    CREATE TABLE IF NOT EXISTS notificacoes (
        id SERIAL PRIMARY KEY,
        titulo VARCHAR(255) NOT NULL,
        mensagem TEXT NOT NULL,
        tipo VARCHAR(20) DEFAULT 'info' CHECK (tipo IN ('info', 'warning', 'critical', 'success')),
        categoria VARCHAR(50) DEFAULT 'sistema' CHECK (categoria IN ('reserva', 'pagamento', 'sistema', 'antifraude')),
        perfil VARCHAR(20),
        lida BOOLEAN DEFAULT FALSE NOT NULL,
        reserva_id INTEGER REFERENCES reservas(id),
        pagamento_id INTEGER REFERENCES pagamentos(id),
        usuario_destino_id INTEGER REFERENCES usuarios(id),
        usuario_criacao_id INTEGER REFERENCES usuarios(id),
        url_acao VARCHAR(500),
        dados_adicionais TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE,
        lida_at TIMESTAMP WITH TIME ZONE
    );

    -- Índices para performance
    CREATE INDEX IF NOT EXISTS idx_notificacoes_lida ON notificacoes(lida);
    CREATE INDEX IF NOT EXISTS idx_notificacoes_perfil ON notificacoes(perfil);
    CREATE INDEX IF NOT EXISTS idx_notificacoes_usuario_destino ON notificacoes(usuario_destino_id);
    CREATE INDEX IF NOT EXISTS idx_notificacoes_created_at ON notificacoes(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_notificacoes_categoria ON notificacoes(categoria);
    CREATE INDEX IF NOT EXISTS idx_notificacoes_reserva_id ON notificacoes(reserva_id);
    CREATE INDEX IF NOT EXISTS idx_notificacoes_pagamento_id ON notificacoes(pagamento_id);

    -- Trigger para updated_at
    CREATE OR REPLACE FUNCTION update_notificacoes_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    DROP TRIGGER IF EXISTS trigger_update_notificacoes_updated_at ON notificacoes;
    CREATE TRIGGER trigger_update_notificacoes_updated_at
        BEFORE UPDATE ON notificacoes
        FOR EACH ROW
        EXECUTE FUNCTION update_notificacoes_updated_at();
    """
    
    try:
        db = next(get_db())
        result = db.execute(text(sql))
        db.commit()
        
        print("✅ Tabela 'notificacoes' criada com sucesso!")
        print("✅ Índices criados para performance")
        print("✅ Trigger para updated_at configurado")
        
        # Inserir algumas notificações de teste
        sql_teste = """
        INSERT INTO notificacoes (titulo, mensagem, tipo, categoria, perfil, lida) VALUES
        ('🔴 Sistema Iniciado', 'Sistema de notificações foi ativado com sucesso', 'success', 'sistema', 'ADMIN', FALSE),
        ('📋 Bem-vindo', 'Sistema de notificações está funcionando', 'info', 'sistema', NULL, FALSE),
        ('⚠️ Teste Crítico', 'Esta é uma notificação de teste crítica', 'critical', 'sistema', 'ADMIN', FALSE);
        """
        
        db.execute(text(sql_teste))
        db.commit()
        
        print("✅ 3 notificações de teste inseridas")
        print("\n🚀 Sistema de notificações pronto para uso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Criando tabela de notificações...")
    criar_tabela_notificacoes()
