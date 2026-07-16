from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

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
        foto_url=payload.foto_url,
        foto_base64=payload.foto_base64,
        foto_nome=payload.foto_nome,
    )


@router.get("/cash-approvals", response_model=dict)
async def list_cash_approvals(
    status: Optional[str] = Query("all"),
    limit: int = Query(50, ge=1, le=200),
    service: CheckinCashApprovalService = Depends(get_service),
    current_user: User = Depends(require_staff),
):
    return await service.listar(status=status, limit=limit)


@router.get("/foto/{code}")
async def foto_checkin_cash(
    code: str,
    service: CheckinCashApprovalService = Depends(get_service),
):
    """Foto do comprovante do CHK, consumida pelo WhatsApp para embutir a
    imagem no card do gerente. Publica por necessidade (a Meta busca a media
    sem autenticacao); protegida pelo codigo CHK nao-adivinhavel e pela
    janela de 24h validada no service."""
    info = await service.obter_foto(code)
    caminho = Path(info["caminho"])
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Foto nao encontrada")

    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }
    media_type = media_types.get(caminho.suffix.lower(), "application/octet-stream")
    return FileResponse(
        path=str(caminho),
        filename=info["nome"],
        media_type=media_type,
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.post("/{code}/approve", response_model=dict)
async def approve_cash_checkin(
    code: str,
    service: CheckinCashApprovalService = Depends(get_service),
    current_user: User = Depends(require_staff),
):
    return await service.aprovar(code, funcionario_id=current_user.id)


@router.post("/{code}/reject", response_model=dict)
async def reject_cash_checkin(
    code: str,
    service: CheckinCashApprovalService = Depends(get_service),
    current_user: User = Depends(require_staff),
):
    return await service.recusar(code, funcionario_id=current_user.id)
