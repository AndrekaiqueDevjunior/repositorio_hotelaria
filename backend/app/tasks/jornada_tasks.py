import asyncio
from typing import Callable, Awaitable, Any

from app.core.celery_app import celery_app


async def _run_with_db(fn: Callable) -> Any:
    """Cria conexao Prisma isolada para cada task Celery.

    O worker Celery e um processo separado — o db global do FastAPI
    nunca e conectado aqui. Criamos uma instancia fresh por execucao.
    """
    from prisma import Prisma
    from app.core.database import get_database_url

    db = Prisma(datasource={"url": get_database_url()})
    await db.connect()
    try:
        return await fn(db)
    finally:
        await db.disconnect()


@celery_app.task(name="jornada.liberar_pontos_pendentes")
def liberar_pontos_pendentes_task(limit: int = 100):
    from app.services.pontos_checkout_service import liberar_pontos_pendentes

    async def _fn(db):
        return await liberar_pontos_pendentes(db, limit=limit)

    return asyncio.run(_run_with_db(_fn))


@celery_app.task(name="jornada.invalidar_codigos_vencidos")
def invalidar_codigos_vencidos_task():
    from app.repositories.cupom_repo import CupomRepository
    from app.repositories.premio_repo_atomic import PremioRepositoryAtomic

    async def _fn(db):
        cupons = await CupomRepository(db).processar_invalidacoes_automaticas()
        codigos = await PremioRepositoryAtomic(db).expirar_codigos_vencidos()
        return {"success": True, "cupons": cupons, "codigos_resgate": codigos}

    return asyncio.run(_run_with_db(_fn))


@celery_app.task(name="jornada.notificar_premios_proximos")
def notificar_premios_proximos_task(limit: int = 100):
    from app.services.notification_service import NotificationService

    async def _fn(db):
        return await NotificationService.varrer_premios_proximos(db, limit=limit)

    return asyncio.run(_run_with_db(_fn))
