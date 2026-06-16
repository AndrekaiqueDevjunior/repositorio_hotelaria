from app.core.database import get_db
from app.repositories.cupom_repo import CupomRepository
from app.repositories.premio_repo_atomic import PremioRepositoryAtomic
from app.services.notification_service import NotificationService
from app.services.pontos_checkout_service import liberar_pontos_pendentes


async def liberar_pontos_pendentes_jornada(limit: int = 100):
    """Job agendavel para liberar pontos da Jornada Real apos 48h."""
    db = get_db()
    return await liberar_pontos_pendentes(db, limit=limit)


async def invalidar_codigos_vencidos_jornada():
    """Job agendavel para expirar cupons e codigos de resgate vencidos."""
    db = get_db()
    cupons = await CupomRepository(db).processar_invalidacoes_automaticas()
    codigos = await PremioRepositoryAtomic(db).expirar_codigos_vencidos()
    return {
        "success": True,
        "cupons": cupons,
        "codigos_resgate": codigos,
    }


async def notificar_premios_proximos_jornada(limit: int = 100):
    """Job agendavel para avisar clientes perto do proximo premio."""
    db = get_db()
    return await NotificationService.varrer_premios_proximos(db, limit=limit)
