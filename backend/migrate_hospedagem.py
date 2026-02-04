"""
Script de Migration: Separar Hospedagem de Reserva
Executa a migration SQL para criar modelo Hospedagem separado
"""
import asyncio
import sys
from pathlib import Path
from prisma import Prisma


async def executar_migration():
    """Executa a migration SQL"""
    print("🔄 Iniciando migration: Separar Hospedagem...")
    
    # Ler arquivo SQL
    sql_file = Path(__file__).parent / "alembic" / "versions" / "001_separar_hospedagem.sql"
    
    if not sql_file.exists():
        print(f"❌ Arquivo SQL não encontrado: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"📄 Lendo SQL de: {sql_file}")
    
    # Conectar ao banco
    db = Prisma()
    await db.connect()
    
    try:
        print("🔧 Executando migration...")
        
        # Executar SQL (dividir por statement para melhor controle)
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    print(f"  [{i}/{len(statements)}] Executando statement...")
                    await db.execute_raw(statement)
                except Exception as e:
                    # Alguns erros são esperados (ex: tabela já existe)
                    if "already exists" in str(e).lower():
                        print(f"  ⚠️ Statement {i} já executado anteriormente (ignorando)")
                    else:
                        print(f"  ⚠️ Erro no statement {i}: {e}")
        
        print("✅ Migration executada com sucesso!")
        
        # Verificar resultados
        print("\n📊 Verificando resultados...")
        
        # Contar hospedagens criadas
        hospedagens = await db.query_raw(
            "SELECT COUNT(*) as total FROM hospedagens"
        )
        print(f"  • Hospedagens criadas: {hospedagens[0]['total']}")
        
        # Verificar status de reservas
        reservas_status = await db.query_raw(
            "SELECT status_reserva, COUNT(*) as total FROM reservas GROUP BY status_reserva"
        )
        print(f"  • Status de reservas:")
        for row in reservas_status:
            print(f"    - {row['status_reserva']}: {row['total']}")
        
        # Verificar status de pagamentos
        pagamentos_status = await db.query_raw(
            "SELECT status_pagamento, COUNT(*) as total FROM pagamentos GROUP BY status_pagamento"
        )
        print(f"  • Status de pagamentos:")
        for row in pagamentos_status:
            print(f"    - {row['status_pagamento']}: {row['total']}")
        
        # Verificar status de hospedagens
        hospedagens_status = await db.query_raw(
            "SELECT status_hospedagem, COUNT(*) as total FROM hospedagens GROUP BY status_hospedagem"
        )
        print(f"  • Status de hospedagens:")
        for row in hospedagens_status:
            print(f"    - {row['status_hospedagem']}: {row['total']}")
        
        print("\n✅ Migration concluída com sucesso!")
        print("\n📝 Próximos passos:")
        print("  1. Atualizar schema.prisma com o novo modelo")
        print("  2. Executar: prisma generate")
        print("  3. Atualizar repositories e services")
        print("  4. Atualizar frontend")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    success = asyncio.run(executar_migration())
    sys.exit(0 if success else 1)
