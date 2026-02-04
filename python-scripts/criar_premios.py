#!/usr/bin/env python3
"""
Script para criar premios de exemplo no banco de dados.
"""
import asyncio
from app.core.database import get_db

async def criar_premios():
    db = get_db()
    await db.connect()
    
    premios = [
        {
            'nome': 'Upgrade de Suite',
            'descricao': 'Upgrade gratuito para suite superior na proxima reserva',
            'precoEmPontos': 50,
            'precoEmRp': 50,
            'categoria': 'HOSPEDAGEM',
            'ativo': True
        },
        {
            'nome': 'Late Checkout',
            'descricao': 'Checkout ate 16h sem custo adicional',
            'precoEmPontos': 30,
            'precoEmRp': 30,
            'categoria': 'HOSPEDAGEM',
            'ativo': True
        },
        {
            'nome': 'Cafe da Manha Gratis',
            'descricao': 'Cafe da manha completo para 2 pessoas',
            'precoEmPontos': 25,
            'precoEmRp': 25,
            'categoria': 'GASTRONOMIA',
            'ativo': True
        },
        {
            'nome': 'Diaria Gratis',
            'descricao': 'Uma diaria gratis em suite standard',
            'precoEmPontos': 100,
            'precoEmRp': 100,
            'categoria': 'HOSPEDAGEM',
            'ativo': True
        },
        {
            'nome': 'Spa Day',
            'descricao': 'Acesso completo ao spa por um dia',
            'precoEmPontos': 75,
            'precoEmRp': 75,
            'categoria': 'LAZER',
            'ativo': True
        },
        {
            'nome': 'Jantar Romantico',
            'descricao': 'Jantar para 2 pessoas no restaurante do hotel',
            'precoEmPontos': 60,
            'precoEmRp': 60,
            'categoria': 'GASTRONOMIA',
            'ativo': True
        },
        {
            'nome': 'Transfer Aeroporto',
            'descricao': 'Transfer ida e volta do aeroporto',
            'precoEmPontos': 40,
            'precoEmRp': 40,
            'categoria': 'SERVICOS',
            'ativo': True
        },
        {
            'nome': 'Desconto 10 porcento',
            'descricao': '10 porcento de desconto na proxima reserva',
            'precoEmPontos': 20,
            'precoEmRp': 20,
            'categoria': 'DESCONTO',
            'ativo': True
        }
    ]
    
    for premio_data in premios:
        existente = await db.premio.find_first(where={'nome': premio_data['nome']})
        if not existente:
            premio = await db.premio.create(data=premio_data)
            print(f'[OK] Premio criado: {premio.nome} - {premio.precoEmPontos} pts')
        else:
            print(f'[--] Premio ja existe: {existente.nome}')
    
    # Listar todos
    todos = await db.premio.find_many(where={'ativo': True})
    print(f'\nTotal de premios ativos: {len(todos)}')
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(criar_premios())
