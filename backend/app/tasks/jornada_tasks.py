from app.core.database import get_db
from app.services.pontos_checkout_service import liberar_pontos_pendentes


async def liberar_pontos_pendentes_jornada(limit: int = 100):
    """Job agendavel para liberar pontos da Jornada Real apos 48h."""
    db = get_db()
    return await liberar_pontos_pendentes(db, limit=limit)
