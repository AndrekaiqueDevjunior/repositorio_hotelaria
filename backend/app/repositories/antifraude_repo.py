from app.core.database import db


async def create_operacao(data: dict):
    return await db.OperacaoAntifraude.create(data=data)


async def update_operacao(operacao_id: int, data: dict):
    return await db.OperacaoAntifraude.update(where={"id": operacao_id}, data=data)


async def update_by_pagamento_id(pagamento_id: int, data: dict):
    return await db.OperacaoAntifraude.update_many(
        where={"pagamentoId": pagamento_id},
        data=data
    )


async def list_all(limit: int = 20, offset: int = 0):
    return await db.OperacaoAntifraude.find_many(
        order={"id": "desc"},
        skip=offset,
        take=limit,
        include={
            "reserva": {"include": {"cliente": True}},
            "pagamento": True
        }
    )


async def count_by_status(status: str):
    return await db.OperacaoAntifraude.count(where={"status": status})