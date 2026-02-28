#!/usr/bin/env python3
import asyncio
from app.core.database import get_db, connect_db, disconnect_db

async def check():
    await connect_db()
    db = get_db()
    
    clientes = await db.cliente.find_many()
    funcionarios = await db.funcionario.find_many()
    
    print(f'\n=== DADOS NO BANCO ===')
    print(f'\nTotal de clientes: {len(clientes)}')
    for c in clientes:
        print(f'  - {c.nomeCompleto} ({c.documento})')
    
    print(f'\nTotal de funcionários: {len(funcionarios)}')
    for f in funcionarios:
        print(f'  - {f.nome} ({f.email})')
    
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(check())
