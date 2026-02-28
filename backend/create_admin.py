#!/usr/bin/env python3
"""
Criar usuário administrador padrão no banco de dados Prisma.

Uso:
    cd backend
    python create_admin.py
"""
import asyncio
from prisma import Prisma
from app.repositories.funcionario_repo import FuncionarioRepository
from app.schemas.funcionario_schema import FuncionarioCreate

async def create_admin():
    prisma = Prisma()
    await prisma.connect()
    
    try:
        repo = FuncionarioRepository(prisma)
        
        # Verificar se admin já existe
        try:
            existing_admin = await repo.get_by_email("admin@hotelreal.com.br")
            print("✅ Admin já existe:")
            print(f"   Email: {existing_admin['email']}")
            print(f"   Perfil: {existing_admin['perfil']}")
            print(f"   Status: {existing_admin['status']}")
            return
        except ValueError:
            pass  # Admin não existe, continue
        
        # Criar admin
        admin_data = FuncionarioCreate(
            nome="Administrador",
            email="admin@hotelreal.com.br",
            perfil="ADMIN",
            status="ATIVO",
            senha="admin123"
        )
        
        admin = await repo.create(admin_data)
        
        print("✅ Admin criado com sucesso!")
        print(f"   Email: {admin['email']}")
        print(f"   Senha: admin123")
        print(f"   Perfil: {admin['perfil']}")
        print(f"   Status: {admin['status']}")
        
    except Exception as e:
        print(f"❌ Erro ao criar admin: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(create_admin())
