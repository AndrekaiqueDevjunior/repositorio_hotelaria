#!/usr/bin/env python3
"""
Criar 5 funcionários e 5 clientes no banco de dados Prisma.

Uso:
    cd backend
    .\\venv312\\Scripts\\Activate.ps1  # Windows
    python seed_5_users.py
"""
import asyncio
from datetime import datetime
from typing import Dict, Any

from app.core.database import connect_db, disconnect_db, get_db
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.funcionario_repo import FuncionarioRepository
from app.schemas.cliente_schema import ClienteCreate
from app.schemas.funcionario_schema import FuncionarioCreate


FUNCIONARIOS = [
    {
        "nome": "João Silva",
        "email": "joao.silva@hotelreal.com.br",
        "perfil": "RECEPCAO",
        "status": "ATIVO",
        "senha": "joao123",
    },
    {
        "nome": "Maria Santos",
        "email": "maria.santos@hotelreal.com.br",
        "perfil": "GERENTE",
        "status": "ATIVO",
        "senha": "maria123",
    },
    {
        "nome": "Pedro Oliveira",
        "email": "pedro.oliveira@hotelreal.com.br",
        "perfil": "FUNCIONARIO",
        "status": "ATIVO",
        "senha": "pedro123",
    },
    {
        "nome": "Ana Costa",
        "email": "ana.costa@hotelreal.com.br",
        "perfil": "RECEPCAO",
        "status": "ATIVO",
        "senha": "ana123",
    },
    {
        "nome": "Carlos Ferreira",
        "email": "carlos.ferreira@hotelreal.com.br",
        "perfil": "FUNCIONARIO",
        "status": "ATIVO",
        "senha": "carlos123",
    },
]


CLIENTES = [
    {
        "nome_completo": "Roberto Almeida",
        "documento": "12345678901",
        "telefone": "21987654321",
        "email": "roberto.almeida@email.com",
        "data_nascimento": datetime(1985, 3, 15),
        "nacionalidade": "Brasileira",
        "endereco_completo": "Rua das Flores, 123",
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "pais": "Brasil",
        "tipo_hospede": "VIP",
    },
    {
        "nome_completo": "Juliana Rodrigues",
        "documento": "98765432109",
        "telefone": "21976543210",
        "email": "juliana.rodrigues@email.com",
        "data_nascimento": datetime(1990, 7, 22),
        "nacionalidade": "Brasileira",
        "endereco_completo": "Av. Atlântica, 456",
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "pais": "Brasil",
        "tipo_hospede": "NORMAL",
    },
    {
        "nome_completo": "Fernando Martins",
        "documento": "11223344556",
        "telefone": "21965432109",
        "email": "fernando.martins@email.com",
        "data_nascimento": datetime(1978, 11, 5),
        "nacionalidade": "Brasileira",
        "endereco_completo": "Rua do Sol, 789",
        "cidade": "Cabo Frio",
        "estado": "RJ",
        "pais": "Brasil",
        "tipo_hospede": "NORMAL",
    },
    {
        "nome_completo": "Patricia Lima",
        "documento": "55667788990",
        "telefone": "21954321098",
        "email": "patricia.lima@email.com",
        "data_nascimento": datetime(1992, 4, 18),
        "nacionalidade": "Brasileira",
        "endereco_completo": "Rua das Palmeiras, 321",
        "cidade": "Búzios",
        "estado": "RJ",
        "pais": "Brasil",
        "tipo_hospede": "VIP",
    },
    {
        "nome_completo": "Marcos Pereira",
        "documento": "99887766554",
        "telefone": "21943210987",
        "email": "marcos.pereira@email.com",
        "data_nascimento": datetime(1988, 9, 30),
        "nacionalidade": "Brasileira",
        "endereco_completo": "Av. Brasil, 654",
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "pais": "Brasil",
        "tipo_hospede": "NORMAL",
    },
]


async def ensure_funcionario(repo: FuncionarioRepository, data: Dict[str, Any]) -> Dict[str, Any]:
    """Cria funcionário se não existir, ou retorna o existente."""
    try:
        funcionario = await repo.create(FuncionarioCreate(**data))
        funcionario["created_now"] = True
        return funcionario
    except ValueError:
        funcionario = await repo.get_by_email(data["email"])
        funcionario["created_now"] = False
        return funcionario


async def ensure_cliente(repo: ClienteRepository, data: Dict[str, Any]) -> Dict[str, Any]:
    """Cria cliente se não existir, ou retorna o existente."""
    try:
        cliente = await repo.create(ClienteCreate(**data))
        cliente["created_now"] = True
        return cliente
    except ValueError:
        cliente = await repo.get_by_documento(data["documento"])
        cliente["created_now"] = False
        return cliente


async def seed():
    await connect_db()
    db = get_db()

    funcionario_repo = FuncionarioRepository(db)
    cliente_repo = ClienteRepository(db)

    print("=" * 70)
    print("🌱 Criando 5 Funcionários e 5 Clientes no Banco de Dados")
    print("=" * 70)
    print()

    print("👔 FUNCIONÁRIOS:")
    print("-" * 70)
    funcionarios_criados = 0
    funcionarios_existentes = 0
    
    for data in FUNCIONARIOS:
        funcionario = await ensure_funcionario(funcionario_repo, data)
        if funcionario.get("created_now"):
            funcionarios_criados += 1
            status = "✅ CRIADO"
        else:
            funcionarios_existentes += 1
            status = "⚠️  JÁ EXISTIA"
        
        print(f"  {status} - {funcionario['nome']}")
        print(f"           Email: {funcionario['email']}")
        print(f"           Perfil: {funcionario['perfil']}")
        print(f"           Senha: {data['senha']}")
        print()

    print()
    print("👤 CLIENTES:")
    print("-" * 70)
    clientes_criados = 0
    clientes_existentes = 0
    
    for data in CLIENTES:
        cliente = await ensure_cliente(cliente_repo, data)
        if cliente.get("created_now"):
            clientes_criados += 1
            status = "✅ CRIADO"
        else:
            clientes_existentes += 1
            status = "⚠️  JÁ EXISTIA"
        
        print(f"  {status} - {cliente['nome_completo']}")
        print(f"           CPF: {cliente['documento']}")
        print(f"           Email: {cliente['email']}")
        print(f"           Telefone: {cliente['telefone']}")
        print()

    print()
    print("=" * 70)
    print("📊 RESUMO:")
    print("=" * 70)
    print(f"  Funcionários criados: {funcionarios_criados}")
    print(f"  Funcionários já existentes: {funcionarios_existentes}")
    print(f"  Total de funcionários: {len(FUNCIONARIOS)}")
    print()
    print(f"  Clientes criados: {clientes_criados}")
    print(f"  Clientes já existentes: {clientes_existentes}")
    print(f"  Total de clientes: {len(CLIENTES)}")
    print("=" * 70)
    print()
    print("✅ Processo concluído!")
    print()

    await disconnect_db()


if __name__ == "__main__":
    asyncio.run(seed())
