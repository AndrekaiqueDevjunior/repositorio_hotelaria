from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.security import User
from app.middleware.auth_middleware import require_staff
from app.schemas.checkin_cash_approval_schema import (
    CheckinCashApprovalRequest,
    CheckinCashApprovalResponse,
)
from app.services.checkin_cash_approval_service import CheckinCashApprovalService


router = APIRouter(prefix="/checkins", tags=["checkins"])


def get_service() -> CheckinCashApprovalService:
    return CheckinCashApprovalService(get_db())


@router.post("/request-cash-approval", response_model=CheckinCashApprovalResponse)
async def request_cash_approval(
    payload: CheckinCashApprovalRequest,
    service: CheckinCashApprovalService = Depends(get_service),
    current_user: User = Depends(require_staff),
):
    return await service.solicitar(
        reservation_id=payload.reservation_id,
        amount=payload.amount,
        funcionario_id=current_user.id,
        payment_method=payload.payment_method,
    )


@router.get("/cash-approvals", response_model=dict)
async def list_cash_approvals(
    status: Optional[str] = Query("all"),
    limit: int = Query(50, ge=1, le=200),
    service: CheckinCashApprovalService = Depends(get_service),
    current_user: User = Depends(require_staff),
):
    return await service.listar(status=status, limit=limit)


@router.post("/{code}/approve", response_model=dict)
async def approve_cash_checkin(
    code: str,
    service: CheckinCashApprovalService = Depends(get_service),
    current_user: User = Depends(require_staff),
):
    return await service.aprovar(code, funcionario_id=current_user.id)
