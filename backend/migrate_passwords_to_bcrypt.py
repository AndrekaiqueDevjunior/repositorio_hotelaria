"""
Script de migração de senhas SHA256 para bcrypt
EXECUTAR UMA VEZ EM PRODUÇÃO

Este script:
1. Identifica senhas em SHA256 (64 caracteres)
2. Gera senha temporária
3. Faz hash com bcrypt
4. Atualiza no banco
5. Envia email com senha temporária (opcional)
"""

import asyncio
import sys
import os

# Adicionar path do backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.core.security import hash_password


async def migrate_passwords():
    """Migrar senhas SHA256 para bcrypt"""
    
    print("=" * 60)
    print("MIGRAÇÃO DE SENHAS SHA256 → BCRYPT")
    print("=" * 60)
    print()
    
    db = get_db()
    
    try:
        # Conectar ao banco
        await db.connect()
        print("✓ Conectado ao banco de dados")
        
        # Buscar todos os funcionários
        funcionarios = await db.funcionario.find_many()
        print(f"✓ Encontrados {len(funcionarios)} funcionários")
        print()
        
        migrated = 0
        skipped = 0
        
        for func in funcionarios:
            # Verificar se senha é SHA256 (64 caracteres hex)
            if len(func.senha) == 64 and all(c in '0123456789abcdef' for c in func.senha.lower()):
                print(f"Migrando: {func.nome} ({func.email})")
                
                # Gerar senha temporária
                senha_temp = f"Hotel@{func.id}2025"
                
                # Hash com bcrypt
                novo_hash = hash_password(senha_temp)
                
                # Atualizar no banco
                await db.funcionario.update(
                    where={"id": func.id},
                    data={
                        "senha": novo_hash
                    }
                )
                
                print(f"  → Senha temporária: {senha_temp}")
                print(f"  → Hash bcrypt: {novo_hash[:20]}...")
                print(f"  ✓ Migrado com sucesso")
                print()
                
                migrated += 1
                
                # TODO: Enviar email com senha temporária
                # await send_password_reset_email(func.email, senha_temp)
                
            else:
                print(f"Pulando: {func.nome} ({func.email}) - Já está em bcrypt")
                skipped += 1
        
        print()
        print("=" * 60)
        print("RESUMO DA MIGRAÇÃO")
        print("=" * 60)
        print(f"Total de funcionários: {len(funcionarios)}")
        print(f"Migrados: {migrated}")
        print(f"Pulados (já em bcrypt): {skipped}")
        print()
        
        if migrated > 0:
            print("⚠️  IMPORTANTE:")
            print("   1. Anote as senhas temporárias acima")
            print("   2. Envie para os funcionários por canal seguro")
            print("   3. Peça para alterarem na primeira vez que fizerem login")
            print()
        
        print("✓ Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"✗ Erro durante migração: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await db.disconnect()
        print("✓ Desconectado do banco de dados")
    
    return True


if __name__ == "__main__":
    print()
    print("⚠️  ATENÇÃO: Este script irá alterar as senhas dos funcionários!")
    print("   As senhas atuais serão substituídas por senhas temporárias.")
    print()
    
    resposta = input("Deseja continuar? (sim/não): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        print()
        success = asyncio.run(migrate_passwords())
        sys.exit(0 if success else 1)
    else:
        print("Migração cancelada.")
        sys.exit(0)
