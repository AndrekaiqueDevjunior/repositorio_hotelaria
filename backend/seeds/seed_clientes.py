import asyncio
import sys
import os

# Adicionar o diretório app ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import connect_db, disconnect_db, get_db
from app.schemas.cliente_schema import ClienteCreate
from app.repositories.cliente_repo import ClienteRepository

# Dados de clientes reais
CLIENTES = [
    {
        "nome_completo": "Ana Carolina Silva Santos",
        "documento": "12345678901",
        "email": "ana.santos@email.com",
        "telefone": "(22) 98765-4321",
        "endereco": "Av. Lúcio Meira, 1234 - Centro, Cabo Frio - RJ",
        "data_nascimento": "1985-03-15"
    },
    {
        "nome_completo": "Carlos Eduardo Pereira Lima",
        "documento": "98765432109",
        "email": "carlos.lima@email.com",
        "telefone": "(22) 99876-5432",
        "endereco": "Rua dos Coqueiros, 567 - Bairro da Lagoa, Cabo Frio - RJ",
        "data_nascimento": "1978-07-22"
    },
    {
        "nome_completo": "Mariana Ferreira Costa",
        "documento": "45678901234",
        "email": "mariana.costa@email.com",
        "telefone": "(22) 97654-3210",
        "endereco": "Praça das Águas, 89 - Peró, Cabo Frio - RJ",
        "data_nascimento": "1992-11-08"
    }
]

async def seed():
    await connect_db()
    db = get_db()
    
    print("\n=== CRIANDO CLIENTES ===\n")
    
    cliente_repo = ClienteRepository(db)
    
    for cliente_data in CLIENTES:
        try:
            # Verificar se cliente já existe pelo documento
            existente = await db.cliente.find_unique(where={"documento": cliente_data["documento"]})
            
            if existente:
                print(f"⚠️  Cliente {cliente_data['nome_completo']} já existe (CPF: {cliente_data['documento']})")
                continue
            
            # Criar cliente
            cliente_create = ClienteCreate(**cliente_data)
            cliente = await cliente_repo.create(cliente_create)
            
            print(f"✅ Cliente {cliente_data['nome_completo']} criado com sucesso")
            print(f"   📧 Email: {cliente_data['email']}")
            print(f"   📱 Telefone: {cliente_data['telefone']}")
            print(f"   🆔 ID: {cliente['id']}")
            print()
            
        except Exception as e:
            print(f"❌ Erro ao criar cliente {cliente_data['nome_completo']}: {e}")
    
    total = await db.cliente.count()
    print(f"\n📊 Total de clientes: {total}")
    
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(seed())
