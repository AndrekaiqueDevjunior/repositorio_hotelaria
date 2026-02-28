#!/usr/bin/env python3
"""
Verificar logs de auditoria
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.database import get_db_connected

async def check_logs():
    db = await get_db_connected()
    
    logs = await db.auditoria.find_many(
        order={'createdAt': 'desc'},
        take=10
    )
    
    print(f'Logs registrados: {len(logs)}')
    
    for i, log in enumerate(logs, 1):
        print(f'{i}. {log.createdAt.strftime("%H:%M:%S")} - User {log.usuarioId}')
        print(f'   {log.acao} {log.entidade}:{log.entidadeId}')
        if log.payloadResumo:
            print(f'   📝 {log.payloadResumo[:100]}...')
        print()

if __name__ == "__main__":
    asyncio.run(check_logs())
