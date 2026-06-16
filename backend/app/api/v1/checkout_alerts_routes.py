from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.security import User
from app.middleware.auth_middleware import require_staff
from app.services.checkout_alert_service import CheckoutAlertService


router = APIRouter(prefix="/checkout-alerts", tags=["checkout-alerts"])


def get_service() -> CheckoutAlertService:
    return CheckoutAlertService(get_db())


@router.get("/pending", response_model=dict)
async def listar_checkout_alerts_pendentes(
    limit: int = Query(20, ge=1, le=100),
    service: CheckoutAlertService = Depends(get_service),
    current_user: User = Depends(require_staff),
):
    return await service.listar_pendentes(limit=limit)


@router.post("/{reservation_id}/viewed", response_model=dict)
async def marcar_checkout_alert_visto(
    reservation_id: int,
    service: CheckoutAlertService = Depends(get_service),
    current_user: User = Depends(require_staff),
):
    return await service.marcar_visto(reservation_id)

