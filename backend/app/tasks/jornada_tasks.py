import asyncio
import logging
from typing import Callable, Awaitable, Any

from app.core.celery_app import celery_app

try:
    from celery.signals import worker_process_shutdown
except ImportError:  # ambiente de teste sem celery instalado
    worker_process_shutdown = None


logger = logging.getLogger(__name__)

# Um client Prisma e um event loop por PROCESSO do pool Celery, reutilizados
# entre tasks. O padrao anterior (client novo + asyncio.run por task) vazava
# um subprocesso query-engine por execucao — prisma 0.11 retornava do
# disconnect sem o engine morrer — e saturou o max_connections=200 do
# Postgres em ~2 dias ("FATAL: sorry, too many clients already").
_task_client = None
_task_loop = None


def _run_async(coro: Awaitable) -> Any:
    """Executa a coroutine no loop persistente do processo (o client Prisma
    guarda sessoes HTTP presas ao loop em que nasceu; asyncio.run por task
    quebraria o reuso)."""
    global _task_loop
    if _task_loop is None or _task_loop.is_closed():
        _task_loop = asyncio.new_event_loop()
    return _task_loop.run_until_complete(coro)


async def _run_with_db(fn: Callable) -> Any:
    """Roda a task com o client Prisma persistente do processo.

    O worker Celery e um processo separado — o db global do FastAPI nunca e
    conectado aqui. Em caso de erro o client e descartado (com kill garantido
    do engine em disconnect_prisma_client) e o proximo uso recria do zero.
    """
    global _task_client
    from app.core.database import (
        create_celery_prisma_client,
        disconnect_prisma_client,
    )

    db = _task_client if _task_client is not None else create_celery_prisma_client()
    try:
        if not db.is_connected():
            await db.connect()
        resultado = await fn(db)
    except Exception:
        # Client pode ter engine/conexao quebrada: descarta e encerra.
        _task_client = None
        try:
            await disconnect_prisma_client(db)
        except Exception:
            # A limpeza nao pode substituir a falha original nem provocar retry
            # de uma task que ja concluiu mutacoes com sucesso.
            logger.exception("Falha ao encerrar o Prisma da task Celery")
        raise
    else:
        _task_client = db
        return resultado


if worker_process_shutdown is not None:
    @worker_process_shutdown.connect
    def _fechar_prisma_no_shutdown(**kwargs):
        """Encerra o client persistente quando o processo do pool recicla
        (ex.: --max-tasks-per-child), para nao orfanar o query engine."""
        global _task_client
        db = _task_client
        _task_client = None
        if db is None:
            return
        from app.core.database import disconnect_prisma_client

        try:
            _run_async(disconnect_prisma_client(db))
        except Exception:
            logger.exception("Falha ao encerrar o Prisma no shutdown do worker")


@celery_app.task(name="jornada.liberar_pontos_pendentes")
def liberar_pontos_pendentes_task(limit: int = 100):
    from app.services.pontos_checkout_service import liberar_pontos_pendentes

    async def _fn(db):
        return await liberar_pontos_pendentes(db, limit=limit)

    return _run_async(_run_with_db(_fn))


@celery_app.task(name="jornada.retentar_estornos_pendentes")
def retentar_estornos_pendentes_task(limit: int = 100):
    from app.services.pontos_checkout_service import retentar_estornos_pendentes

    async def _fn(db):
        return await retentar_estornos_pendentes(db, limit=limit)

    return _run_async(_run_with_db(_fn))


async def _invalidar_codigos_vencidos(db) -> Any:
    from app.repositories.cupom_repo import CupomRepository
    from app.repositories.premio_repo_atomic import PremioRepositoryAtomic

    cupons = await CupomRepository(db).processar_invalidacoes_automaticas()
    codigos = await PremioRepositoryAtomic(db).expirar_codigos_vencidos()
    return {"success": True, "cupons": cupons, "codigos_resgate": codigos}


async def invalidar_codigos_vencidos_jornada() -> Any:
    """Versao para uso direto dentro do processo FastAPI (db ja conectado)."""
    from app.core.database import get_db

    return await _invalidar_codigos_vencidos(get_db())


@celery_app.task(name="jornada.invalidar_codigos_vencidos")
def invalidar_codigos_vencidos_task():
    return _run_async(_run_with_db(_invalidar_codigos_vencidos))


@celery_app.task(name="jornada.notificar_premios_proximos")
def notificar_premios_proximos_task(limit: int = 100):
    from app.services.notification_service import NotificationService

    async def _fn(db):
        return await NotificationService.varrer_premios_proximos(db, limit=limit)

    return _run_async(_run_with_db(_fn))
