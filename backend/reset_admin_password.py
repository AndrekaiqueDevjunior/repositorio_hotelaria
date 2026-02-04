"""
Script para resetar senha do admin
"""

import asyncio
from app.core.database import get_db
from app.core.security import hash_password

async def reset_admin():
    db = get_db()
    await db.connect()
    
    print("=== RESET SENHA ADMIN ===\n")
    
    # Buscar admin
    admin = await db.funcionario.find_first(
        where={'email': 'admin@hotelreal.com.br'}
    )
    
    if not admin:
        print("✗ Admin não encontrado")
        await db.disconnect()
        return
    
    print(f"✓ Admin encontrado: {admin.nome}")
    print(f"  Email: {admin.email}")
    
    # Nova senha
    nova_senha = "admin123"
    senha_hash = hash_password(nova_senha)
    
    # Atualizar
    await db.funcionario.update(
        where={'id': admin.id},
        data={'senha': senha_hash}
    )
    
    print(f"\n✓ Senha resetada com sucesso!")
    print(f"  Nova senha: {nova_senha}")
    print(f"  Hash: {senha_hash[:30]}...")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(reset_admin())
