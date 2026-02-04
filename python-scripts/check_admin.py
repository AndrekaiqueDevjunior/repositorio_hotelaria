import asyncio
from app.core.database import get_db

async def check_admin():
    db = get_db()
    
    # Buscar todos os admins
    admins = await db.funcionario.find_many(where={'perfil': 'ADMIN'})
    
    print(f"\n{'='*60}")
    print(f"ADMINS ENCONTRADOS: {len(admins)}")
    print(f"{'='*60}\n")
    
    for admin in admins:
        print(f"ID: {admin.id}")
        print(f"Nome: {admin.nome}")
        print(f"Email: {admin.email}")
        print(f"Perfil: {admin.perfil}")
        print(f"Status: {admin.status}")
        print(f"Senha (hash): {admin.senha[:20]}..." if admin.senha else "Sem senha")
        print("-" * 60)
    
    # Testar se existe admin@hotel.com
    admin_email = await db.funcionario.find_first(where={'email': 'admin@hotel.com'})
    print(f"\nAdmin com email 'admin@hotel.com': {'✅ EXISTE' if admin_email else '❌ NÃO EXISTE'}")
    
    # Buscar qualquer funcionário ativo
    any_active = await db.funcionario.find_first(where={'status': 'ATIVO'})
    if any_active:
        print(f"\nPrimeiro funcionário ativo encontrado:")
        print(f"Email: {any_active.email}")
        print(f"Nome: {any_active.nome}")

if __name__ == "__main__":
    asyncio.run(check_admin())
