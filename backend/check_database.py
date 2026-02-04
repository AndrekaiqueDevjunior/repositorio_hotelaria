"""
Script para verificar estrutura atual do banco de dados
"""
import asyncio
from prisma import Prisma


async def verificar_estrutura():
    """Verifica estrutura atual do banco"""
    print("🔍 Verificando estrutura do banco de dados...\n")
    
    db = Prisma()
    await db.connect()
    
    try:
        # Listar tabelas
        print("📋 TABELAS:")
        tables = await db.query_raw(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        )
        for t in tables:
            print(f"  • {t['table_name']}")
        
        print("\n" + "="*60)
        
        # Estrutura da tabela reservas
        print("\n📊 ESTRUTURA: reservas")
        cols_reservas = await db.query_raw(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'reservas' 
            ORDER BY ordinal_position
            """
        )
        for col in cols_reservas:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  • {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        print("\n" + "="*60)
        
        # Estrutura da tabela pagamentos
        print("\n💰 ESTRUTURA: pagamentos")
        cols_pagamentos = await db.query_raw(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'pagamentos' 
            ORDER BY ordinal_position
            """
        )
        for col in cols_pagamentos:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  • {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        print("\n" + "="*60)
        
        # Verificar se hospedagens existe
        print("\n🏨 TABELA hospedagens:")
        hospedagens_exists = await db.query_raw(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'hospedagens')"
        )
        if hospedagens_exists[0]['exists']:
            print("  ✅ Tabela existe")
            cols_hospedagens = await db.query_raw(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'hospedagens' 
                ORDER BY ordinal_position
                """
            )
            for col in cols_hospedagens:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  • {col['column_name']}: {col['data_type']} {nullable}")
        else:
            print("  ❌ Tabela NÃO existe")
        
        print("\n" + "="*60)
        
        # Status atuais
        print("\n📊 STATUS ATUAIS:")
        
        print("\n  Reservas:")
        status_reservas = await db.query_raw(
            "SELECT DISTINCT status FROM reservas ORDER BY status"
        )
        for s in status_reservas:
            print(f"    • {s['status']}")
        
        # Verificar se existe status_reserva
        has_status_reserva = await db.query_raw(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'reservas' AND column_name = 'status_reserva'
            )
            """
        )
        if has_status_reserva[0]['exists']:
            print("\n  Reservas (status_reserva):")
            status_reservas_new = await db.query_raw(
                "SELECT DISTINCT status_reserva FROM reservas ORDER BY status_reserva"
            )
            for s in status_reservas_new:
                print(f"    • {s['status_reserva']}")
        
        print("\n  Pagamentos:")
        status_pagamentos = await db.query_raw(
            "SELECT DISTINCT status FROM pagamentos ORDER BY status"
        )
        for s in status_pagamentos:
            print(f"    • {s['status']}")
        
        print("\n" + "="*60)
        
        # Contagens
        print("\n📈 CONTAGENS:")
        count_reservas = await db.query_raw("SELECT COUNT(*) as total FROM reservas")
        print(f"  • Reservas: {count_reservas[0]['total']}")
        
        count_pagamentos = await db.query_raw("SELECT COUNT(*) as total FROM pagamentos")
        print(f"  • Pagamentos: {count_pagamentos[0]['total']}")
        
        if hospedagens_exists[0]['exists']:
            count_hospedagens = await db.query_raw("SELECT COUNT(*) as total FROM hospedagens")
            print(f"  • Hospedagens: {count_hospedagens[0]['total']}")
        
        print("\n✅ Verificação concluída!")
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(verificar_estrutura())
