from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.security import User
from app.middleware.auth_middleware import require_admin_or_manager
from app.repositories.cupom_repo import CupomRepository
from app.schemas.cupom_schema import AdminCouponGenerateRequest, AdminCouponUpdateRequest
from app.services.cupom_service import CupomService


router = APIRouter(prefix="/admin/coupons", tags=["admin-coupons"])


async def get_cupom_service() -> CupomService:
    return CupomService(CupomRepository(get_db()))


@router.post("/generate", response_model=dict, status_code=201)
async def generate_admin_coupon(
    payload: AdminCouponGenerateRequest,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.admin_generate_coupon(
        payload.model_dump(exclude_unset=True),
        criado_por=current_user.id,
    )


@router.get("", response_model=dict)
async def list_admin_coupons(
    status: Optional[str] = Query(None),
    campaign_type: Optional[str] = Query(None, alias="campaignType"),
    campaign_type_snake: Optional[str] = Query(None, alias="campaign_type"),
    influencer_only: bool = Query(False, alias="influencerOnly"),
    influencer_only_snake: Optional[bool] = Query(None, alias="influencer_only"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.admin_list_coupons(
        status=status,
        campaign_type=campaign_type or campaign_type_snake,
        influencer_only=influencer_only if influencer_only_snake is None else influencer_only_snake,
        limit=limit,
        offset=offset,
    )


@router.get("/{code}", response_model=dict)
async def get_admin_coupon(
    code: str,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.admin_get_coupon(code)


@router.put("/{code}", response_model=dict)
async def update_admin_coupon(
    code: str,
    payload: AdminCouponUpdateRequest,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.admin_update_coupon(code, payload.model_dump(exclude_unset=True))


@router.delete("/{code}", response_model=dict)
async def deactivate_admin_coupon(
    code: str,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.admin_delete_coupon(code)
