"""
Integração das Notificações nos Serviços Principais
Este arquivo contém os gatilhos para enviar notificações nos eventos críticos
"""

from app.services.notification_service import NotificationService

async def notificar_em_reserva_criada(db, reserva):
    """Gatilho: Notificar quando reserva é criada"""
    await NotificationService.notificar_nova_reserva(db, reserva)

async def notificar_em_checkin(db, reserva):
    """Gatilho: Notificar quando check-in é realizado"""
    await NotificationService.notificar_checkin_realizado(db, reserva)

async def notificar_em_checkout(db, reserva):
    """Gatilho: Notificar quando check-out é realizado"""
    await NotificationService.notificar_checkout_realizado(db, reserva)

async def notificar_em_cancelamento(db, reserva):
    """Gatilho: Notificar quando reserva é cancelada"""
    await NotificationService.notificar_reserva_cancelada(db, reserva)

async def notificar_em_pagamento_aprovado(db, pagamento, reserva):
    """Gatilho: Notificar quando pagamento é aprovado"""
    await NotificationService.notificar_pagamento_aprovado(db, pagamento, reserva)

async def notificar_em_pagamento_recusado(db, pagamento, reserva):
    """Gatilho: Notificar quando pagamento é recusado (CRÍTICO)"""
    await NotificationService.notificar_pagamento_recusado(db, pagamento, reserva)

async def notificar_em_pagamento_pendente(db, pagamento, reserva):
    """Gatilho: Notificar quando pagamento fica pendente"""
    await NotificationService.notificar_pagamento_pendente(db, pagamento, reserva)

async def notificar_erro_sistema(db, mensagem: str):
    """Gatilho: Notificar erro crítico do sistema"""
    await NotificationService.notificar_erro_sistema(db, mensagem)
