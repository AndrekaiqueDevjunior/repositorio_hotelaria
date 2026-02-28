"""
Migration V2: Criar modelo Hospedagem (corrigido para estrutura real)
"""
import asyncio
from prisma import Prisma


async def executar_migration():
    """Executa migration SQL corrigida"""
    print("🔄 Iniciando migration: Criar modelo Hospedagem...\n")
    
    db = Prisma()
    await db.connect()
    
    try:
        # ============= PASSO 1: Criar tabela hospedagens =============
        print("📝 [1/6] Criando tabela hospedagens...")
        await db.execute_raw("""
            CREATE TABLE IF NOT EXISTS hospedagens (
                id SERIAL PRIMARY KEY,
                reserva_id INTEGER UNIQUE NOT NULL,
                status_hospedagem VARCHAR(50) DEFAULT 'NAO_INICIADA' NOT NULL,
                checkin_realizado_em TIMESTAMP,
                checkin_realizado_por INTEGER,
                checkout_realizado_em TIMESTAMP,
                checkout_realizado_por INTEGER,
                num_hospedes INTEGER,
                num_criancas INTEGER,
                placa_veiculo VARCHAR(20),
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT fk_hospedagem_reserva FOREIGN KEY (reserva_id) REFERENCES reservas(id) ON DELETE CASCADE
            )
        """)
        print("  ✅ Tabela hospedagens criada")
        
        # ============= PASSO 2: Criar índices =============
        print("\n📝 [2/6] Criando índices...")
        await db.execute_raw("CREATE INDEX IF NOT EXISTS idx_hospedagens_status ON hospedagens(status_hospedagem)")
        await db.execute_raw("CREATE INDEX IF NOT EXISTS idx_hospedagens_reserva ON hospedagens(reserva_id)")
        print("  ✅ Índices criados")
        
        # ============= PASSO 3: Migrar dados existentes =============
        print("\n📝 [3/6] Migrando dados de reservas para hospedagens...")
        
        # Mapear status antigos para novos
        await db.execute_raw("""
            INSERT INTO hospedagens (
                reserva_id,
                status_hospedagem,
                checkin_realizado_em,
                checkout_realizado_em,
                created_at,
                updated_at
            )
            SELECT 
                r.id,
                CASE 
                    WHEN r.status = 'CHECKED_OUT' THEN 'CHECKOUT_REALIZADO'
                    WHEN r.status = 'HOSPEDADO' THEN 'CHECKIN_REALIZADO'
                    WHEN r.status = 'CONFIRMADA' THEN 'NAO_INICIADA'
                    WHEN r.status = 'PENDENTE' THEN 'NAO_INICIADA'
                    ELSE 'NAO_INICIADA'
                END,
                r.checkin_real,
                r.checkout_real,
                r.created_at,
                r.updated_at
            FROM reservas r
            WHERE NOT EXISTS (
                SELECT 1 FROM hospedagens h WHERE h.reserva_id = r.id
            )
        """)
        
        count = await db.query_raw("SELECT COUNT(*) as total FROM hospedagens")
        print(f"  ✅ {count[0]['total']} hospedagens criadas")
        
        # ============= PASSO 4: Padronizar status de reservas =============
        print("\n📝 [4/6] Padronizando status de reservas...")
        
        # Atualizar campo status_reserva baseado no status atual
        await db.execute_raw("""
            UPDATE reservas SET status_reserva = 
                CASE 
                    WHEN status IN ('PENDENTE', 'AGUARDANDO_PAGAMENTO') THEN 'AGUARDANDO_PAGAMENTO'
                    WHEN status IN ('CONFIRMADA', 'CONFIRMADO', 'HOSPEDADO', 'CHECKED_OUT') THEN 'CONFIRMADA'
                    WHEN status = 'CANCELADO' THEN 'CANCELADA'
                    WHEN status = 'NO_SHOW' THEN 'NO_SHOW'
                    ELSE status_reserva
                END
        """)
        
        status_reservas = await db.query_raw(
            "SELECT status_reserva, COUNT(*) as total FROM reservas GROUP BY status_reserva"
        )
        print("  ✅ Status de reservas padronizados:")
        for row in status_reservas:
            print(f"    • {row['status_reserva']}: {row['total']}")
        
        # ============= PASSO 5: Adicionar coluna status_pagamento =============
        print("\n📝 [5/6] Adicionando coluna status_pagamento...")
        
        # Verificar se coluna já existe
        col_exists = await db.query_raw("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'pagamentos' AND column_name = 'status_pagamento'
            )
        """)
        
        if not col_exists[0]['exists']:
            # Adicionar coluna
            await db.execute_raw("""
                ALTER TABLE pagamentos 
                ADD COLUMN status_pagamento VARCHAR(50) DEFAULT 'PENDENTE'
            """)
            
            # Copiar valores de status para status_pagamento
            await db.execute_raw("""
                UPDATE pagamentos SET status_pagamento = 
                    CASE 
                        WHEN status IN ('APROVADO', 'CONFIRMADO', 'APPROVED') THEN 'PAGO'
                        WHEN status IN ('PENDENTE', 'PROCESSANDO') THEN 'PENDENTE'
                        WHEN status IN ('RECUSADO', 'NEGADO', 'FAILED') THEN 'FALHOU'
                        WHEN status = 'ESTORNADO' THEN 'ESTORNADO'
                        ELSE 'PENDENTE'
                    END
            """)
            
            print("  ✅ Coluna status_pagamento criada e populada")
        else:
            print("  ⚠️ Coluna status_pagamento já existe")
        
        status_pagamentos = await db.query_raw(
            "SELECT status_pagamento, COUNT(*) as total FROM pagamentos GROUP BY status_pagamento"
        )
        print("  ✅ Status de pagamentos:")
        for row in status_pagamentos:
            print(f"    • {row['status_pagamento']}: {row['total']}")
        
        # ============= PASSO 6: Criar constraints =============
        print("\n📝 [6/6] Criando constraints de validação...")
        
        # Constraint para hospedagens
        await db.execute_raw("""
            ALTER TABLE hospedagens DROP CONSTRAINT IF EXISTS check_status_hospedagem
        """)
        await db.execute_raw("""
            ALTER TABLE hospedagens ADD CONSTRAINT check_status_hospedagem 
            CHECK (status_hospedagem IN ('NAO_INICIADA', 'CHECKIN_REALIZADO', 'CHECKOUT_REALIZADO', 'ENCERRADA'))
        """)
        
        print("  ✅ Constraints criadas")
        
        # ============= RESUMO FINAL =============
        print("\n" + "="*60)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("="*60)
        
        print("\n📊 Resumo:")
        count_reservas = await db.query_raw("SELECT COUNT(*) as total FROM reservas")
        count_pagamentos = await db.query_raw("SELECT COUNT(*) as total FROM pagamentos")
        count_hospedagens = await db.query_raw("SELECT COUNT(*) as total FROM hospedagens")
        
        print(f"  • Reservas: {count_reservas[0]['total']}")
        print(f"  • Pagamentos: {count_pagamentos[0]['total']}")
        print(f"  • Hospedagens: {count_hospedagens[0]['total']}")
        
        print("\n📝 Próximos passos:")
        print("  1. ✅ Tabela hospedagens criada")
        print("  2. ✅ Dados migrados")
        print("  3. ✅ Status padronizados")
        print("  4. ⏳ Atualizar schema.prisma")
        print("  5. ⏳ Executar: docker-compose exec backend prisma generate")
        print("  6. ⏳ Atualizar código backend/frontend")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    import sys
    success = asyncio.run(executar_migration())
    sys.exit(0 if success else 1)
