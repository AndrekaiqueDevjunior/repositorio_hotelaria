#!/usr/bin/env python3
import asyncio
from app.core.database import get_db, connect_db, disconnect_db

async def check():
    await connect_db()
    db = get_db()
    
    notifs = await db.notificacao.find_many()
    
    print(f'\n=== NOTIFICAÇÕES NO BANCO ===')
    print(f'Total: {len(notifs)}')
    
    if len(notifs) == 0:
        print('\n⚠️  PROBLEMA: Nenhuma notificação encontrada no banco!')
        print('O sistema de notificações está órfão - não há gatilhos criando notificações.')
    else:
        for n in notifs:
            print(f'\n- {n.titulo}')
            print(f'  Tipo: {n.tipo} | Categoria: {n.categoria}')
            print(f'  Lida: {n.lida}')
    
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(check())
