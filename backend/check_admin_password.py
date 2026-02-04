import asyncio
from app.core.database import get_db
from app.core.security import verify_password

async def check_admin():
    db = get_db()
    await db.connect()
    
    user = await db.funcionario.find_unique(where={'email': 'admin@hotelreal.com.br'})
    
    if user:
        print(f"✅ Usuário encontrado:")
        print(f"   Email: {user.email}")
        print(f"   Nome: {user.nome}")
        print(f"   Perfil: {user.perfil}")
        print(f"   Status: {user.status}")
        print(f"   Senha hash: {user.senha[:60]}...")
        print()
        
        # Testar senhas comuns
        senhas_teste = ['admin123', 'Admin123', 'admin', '123456']
        
        for senha in senhas_teste:
            resultado = verify_password(senha, user.senha)
            status = "✅ CORRETA" if resultado else "❌ INCORRETA"
            print(f"   Senha '{senha}': {status}")
    else:
        print("❌ Usuário não encontrado")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_admin())
