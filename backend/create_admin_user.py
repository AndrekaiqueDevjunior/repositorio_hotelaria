import asyncio
import os
from app.core.database import get_db
from app.core.security import hash_password

async def create_admin():
    db = get_db()
    await db.connect()
    
    # Criar usuário admin
    admin_data = {
        "email": "admin@hotel.com",
        "senha_hash": hash_password(os.environ["ADMIN_PASSWORD"]),
        "nome": "Administrador do Sistema",
        "nome_completo": "Administrador do Sistema",
        "is_active": True,
        "perfil": "ADMIN"
    }
    
    admin = await db.usuario.create(admin_data)
    print(f'Admin criado: {admin.email} (ID: {admin.id})')
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(create_admin())
