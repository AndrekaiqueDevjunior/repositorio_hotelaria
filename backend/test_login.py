#!/usr/bin/env python3
"""Testar login do admin"""
import asyncio
from app.services.funcionario_service import FuncionarioService
from app.repositories.funcionario_repo import FuncionarioRepository
from app.core.database import get_db, connect_db, disconnect_db
from app.utils.hashing import verify_password, hash_password

async def test_login():
    """Testar login"""
    await connect_db()
    db = get_db()
    service = FuncionarioService(FuncionarioRepository(db))
    
    email = "admin@hotelreal.com.br"
    senha = "admin123"
    
    print(f"🔐 Testando login com:")
    print(f"   Email: {email}")
    print(f"   Senha: {senha}")
    print()
    
    try:
        # Obter funcionário
        funcionario = await service.get_by_email(email)
        print(f"✅ Funcionário encontrado:")
        print(f"   ID: {funcionario['id']}")
        print(f"   Nome: {funcionario['nome']}")
        print(f"   Email: {funcionario['email']}")
        print(f"   Perfil: {funcionario['perfil']}")
        print(f"   Status: {funcionario['status']}")
        print()
        
        # Verificar senha diretamente
        funcionario_db = await db.funcionario.find_unique(where={"email": email})
        if funcionario_db:
            print(f"🔍 Verificando senha:")
            print(f"   Senha fornecida: {senha}")
            print(f"   Hash no banco: {funcionario_db.senha[:20]}...")
            
            # Testar hash
            hash_test = hash_password(senha)
            print(f"   Hash calculado: {hash_test[:20]}...")
            print(f"   Hashs iguais: {hash_test == funcionario_db.senha}")
            print()
            
            # Testar verify_password
            is_valid = verify_password(senha, funcionario_db.senha)
            print(f"   verify_password resultado: {is_valid}")
            print()
        
        # Tentar autenticar
        print("🔐 Tentando autenticar...")
        result = await service.authenticate(email, senha)
        print("✅ Autenticação bem-sucedida!")
        print(f"   Token: {result['access_token'][:50]}...")
        print(f"   Funcionário: {result['funcionario']['nome']}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(test_login())

