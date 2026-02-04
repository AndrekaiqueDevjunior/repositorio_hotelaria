"""
Migration script to add missing fields to transacoes_pontos table
"""
import asyncio
from app.core.database import db

async def migrate():
    print("🔄 Conectando ao banco de dados...")
    await db.connect()
    
    try:
        print("📝 Adicionando campo cliente_id...")
        await db.execute_raw("""
            ALTER TABLE transacoes_pontos 
            ADD COLUMN IF NOT EXISTS cliente_id INTEGER;
        """)
        
        print("📝 Adicionando campo funcionario_id...")
        await db.execute_raw("""
            ALTER TABLE transacoes_pontos 
            ADD COLUMN IF NOT EXISTS funcionario_id INTEGER;
        """)
        
        print("📝 Adicionando campo saldo_anterior...")
        await db.execute_raw("""
            ALTER TABLE transacoes_pontos 
            ADD COLUMN IF NOT EXISTS saldo_anterior INTEGER DEFAULT 0;
        """)
        
        print("📝 Adicionando campo saldo_posterior...")
        await db.execute_raw("""
            ALTER TABLE transacoes_pontos 
            ADD COLUMN IF NOT EXISTS saldo_posterior INTEGER DEFAULT 0;
        """)
        
        print("🔄 Populando cliente_id a partir de usuarios_pontos...")
        await db.execute_raw("""
            UPDATE transacoes_pontos tp
            SET cliente_id = up.cliente_id
            FROM usuarios_pontos up
            WHERE tp.usuario_id = up.id
              AND tp.cliente_id IS NULL;
        """)
        
        print("🔗 Criando índices...")
        await db.execute_raw("""
            CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_cliente 
            ON transacoes_pontos(cliente_id);
        """)
        
        await db.execute_raw("""
            CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_funcionario 
            ON transacoes_pontos(funcionario_id);
        """)
        
        await db.execute_raw("""
            CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_reserva 
            ON transacoes_pontos(reserva_id);
        """)
        
        print("🔗 Adicionando foreign keys...")
        await db.execute_raw("""
            ALTER TABLE transacoes_pontos
            DROP CONSTRAINT IF EXISTS fk_transacoes_pontos_cliente;
        """)
        
        await db.execute_raw("""
            ALTER TABLE transacoes_pontos
            ADD CONSTRAINT fk_transacoes_pontos_cliente
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            ON DELETE CASCADE;
        """)
        
        await db.execute_raw("""
            ALTER TABLE transacoes_pontos
            DROP CONSTRAINT IF EXISTS fk_transacoes_pontos_funcionario;
        """)
        
        await db.execute_raw("""
            ALTER TABLE transacoes_pontos
            ADD CONSTRAINT fk_transacoes_pontos_funcionario
            FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
            ON DELETE SET NULL;
        """)
        
        print("✅ Migration concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante migration: {e}")
        raise
    finally:
        await db.disconnect()
        print("🔌 Desconectado do banco de dados")

if __name__ == "__main__":
    asyncio.run(migrate())
