# API v1 Routes
from .auth_routes import router as auth_router
from .cliente_routes import router as cliente_router
from .quarto_routes import router as quarto_router
from .reserva_routes import router as reserva_router
from .pagamento_routes import router as pagamento_router
from .real_points_routes import router as real_points_router
from .public_routes import router as public_router
from .voucher_routes import router as voucher_router
from .cielo_routes import router as cielo_router
from .premios_routes import router as premios_router
from .tarifas_routes import router as tarifas_router
from .notificacao_routes import router as notificacao_router
# from .checkin_routes import router as checkin_router
# from .consumo_routes import router as consumo_router
# from .cancelamento_routes import router as cancelamento_router
# from .operacional_routes import router as operacional_router
# from .state_machine_routes import router as state_machine_router
# from .overbooking_routes import router as overbooking_router

__all__ = [
    "auth_router",
    "cliente_router", 
    "quarto_router",
    "reserva_router",
    "pagamento_router",
    "real_points_router",
    "public_router",
    "voucher_router",
    "cielo_router",
    "premios_router",
    "tarifas_router",
    "notificacao_router",
]
