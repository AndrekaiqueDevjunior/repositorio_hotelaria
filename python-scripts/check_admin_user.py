import asyncio
import sys
import os
sys.path.append('/app')

from app.core.database import get_db
from app.models.usuario import Usuario
from app.core.security import get_password_hash

async def check_admin():
    async for db in get_db():
        # Verificar se admin existe
        result = await db.execute('SELECT * FROM usuarios WHERE email = ?', ('admin@hotelreal.com.br',))
        admin = result.fetchone()
        
        if admin:
            print('✅ Admin encontrado:', admin.email)
            print('   Status:', admin.status)
            print('   Perfil:', admin.perfil)
        else:
            print('❌ Admin não encontrado')
            # Criar admin
            password_hash = get_password_hash('admin123')
            await db.execute('''
                INSERT INTO usuarios (email, senha_hash, nome, perfil, status, criado_em)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (password_hash, 'admin@hotelreal.com.br', 'Administrador', 'ADMIN', 'ATIVO'))
            await db.commit()
            print('✅ Admin criado com sucesso!')
        break

if __name__ == "__main__":
    asyncio.run(check_admin())
