"""
Integração das Notificações nos Serviços Principais
Este arquivo contém os gatilhos para enviar notificações nos eventos críticos
"""

from app.services.notification_service import NotificationService

async def notificar_em_reserva_criada(db, reserva):
    """Gatilho: Notificar quando reserva é criada"""
    notification_service = NotificationService(db)
    await notification_service.notificar_nova_reserva(reserva)

async def notificar_em_checkin(db, reserva):
    """Gatilho: Notificar quando check-in é realizado"""
    notification_service = NotificationService(db)
    await notification_service.notificar_checkin_realizado(reserva)

async def notificar_em_checkout(db, reserva):
    """Gatilho: Notificar quando check-out é realizado"""
    notification_service = NotificationService(db)
    await notification_service.notificar_checkout_realizado(reserva)

async def notificar_em_cancelamento(db, reserva):
    """Gatilho: Notificar quando reserva é cancelada"""
    notification_service = NotificationService(db)
    await notification_service.notificar_reserva_cancelada(reserva)

async def notificar_em_pagamento_aprovado(db, pagamento, reserva):
    """Gatilho: Notificar quando pagamento é aprovado"""
    notification_service = NotificationService(db)
    await notification_service.notificar_pagamento_aprovado(pagamento, reserva)

async def notificar_em_pagamento_recusado(db, pagamento, reserva):
    """Gatilho: Notificar quando pagamento é recusado (CRÍTICO)"""
    notification_service = NotificationService(db)
    await notification_service.notificar_pagamento_recusado(pagamento, reserva)

async def notificar_em_pagamento_pendente(db, pagamento, reserva):
    """Gatilho: Notificar quando pagamento fica pendente"""
    notification_service = NotificationService(db)
    await notification_service.notificar_pagamento_pendente(pagamento, reserva)

async def notificar_erro_sistema(db, mensagem: str):
    """Gatilho: Notificar erro crítico do sistema"""
    notification_service = NotificationService(db)
    await notification_service.notificar_erro_sistema(mensagem)
