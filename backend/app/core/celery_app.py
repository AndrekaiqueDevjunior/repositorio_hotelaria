from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "hotel_real_cabo_frio",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.antifraude_tasks",
        "app.tasks.relatorio_tasks",
        "app.tasks.limpeza_tasks",
        "app.tasks.jornada_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Prisma spawna um subprocesso e precisa de stdout/stderr reais (com fileno).
    # Celery substitui sys.stdout por LoggingProxy sem fileno — isso quebra o spawn.
    worker_redirect_stdouts=False,
    beat_schedule={
        "jornada-liberar-pontos-pendentes": {
            "task": "jornada.liberar_pontos_pendentes",
            "schedule": crontab(minute="*/15"),
        },
        "jornada-retentar-estornos-pendentes": {
            "task": "jornada.retentar_estornos_pendentes",
            "schedule": crontab(minute="*/30"),
        },
        "jornada-invalidar-codigos-vencidos": {
            "task": "jornada.invalidar_codigos_vencidos",
            "schedule": crontab(minute=0),
        },
        "jornada-notificar-premios-proximos": {
            "task": "jornada.notificar_premios_proximos",
            "schedule": crontab(minute="0,30"),
        },
    },
)
