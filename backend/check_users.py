import asyncio
from app.core.database import get_db

async def check_admin():
    db = get_db()
    await db.connect()
    
    usuarios = await db.usuario.find_many()
    print(f'Total usuarios: {len(usuarios)}')
    for u in usuarios:
        print(f'Email: {u.email} | Ativo: {getattr(u, "is_active", "N/A")} | Perfil: {getattr(u, "perfil", "N/A")}')
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_admin())
