#!/usr/bin/env python3
"""Script para criar usuário admin padrão"""
import asyncio
from app.core.database import get_db, connect_db, disconnect_db
from app.repositories.funcionario_repo import FuncionarioRepository
from app.schemas.funcionario_schema import FuncionarioCreate

async def criar_admin():
    """Criar usuário admin padrão"""
    await connect_db()
    db = get_db()
    repo = FuncionarioRepository(db)
    
    email = "admin@hotelreal.com.br"
    senha = "admin123"
    
    try:
        # Verificar se já existe
        funcionario = await repo.get_by_email(email)
        print(f"✅ Funcionário {email} já existe!")
        print(f"   ID: {funcionario['id']}")
        print(f"   Nome: {funcionario['nome']}")
        print(f"   Perfil: {funcionario['perfil']}")
        print(f"   Status: {funcionario['status']}")
    except ValueError:
        # Criar novo admin
        print(f"📝 Criando funcionário admin: {email}")
        admin_data = FuncionarioCreate(
            nome="Administrador",
            email=email,
            perfil="ADMIN",
            status="ATIVO",
            senha=senha
        )
        
        funcionario = await repo.create(admin_data)
        print(f"✅ Admin criado com sucesso!")
        print(f"   ID: {funcionario['id']}")
        print(f"   Email: {funcionario['email']}")
        print(f"   Perfil: {funcionario['perfil']}")
    
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(criar_admin())

