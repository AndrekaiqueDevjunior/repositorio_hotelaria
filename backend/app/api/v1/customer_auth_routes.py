from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.database import get_db
from app.middleware.rate_limit import rate_limit_moderate, rate_limit_strict
from app.schemas.customer_auth_schema import (
    CustomerCreatePublicRequest,
    CustomerPublicResponse,
    OtpGenerateRequest,
    OtpValidateRequest,
)
from app.services.otp_service import OtpService


router = APIRouter(tags=["customer-auth"])


def get_otp_service() -> OtpService:
    return OtpService(get_db())


def _request_meta(request: Request) -> tuple[str, str]:
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    user_agent = request.headers.get("User-Agent", "unknown")
    return ip, user_agent


@router.get("/customers/{cpf}", response_model=CustomerPublicResponse)
async def obter_customer_publico(
    cpf: str,
    service: OtpService = Depends(get_otp_service),
    _rate_limit: None = Depends(rate_limit_moderate),
):
    return await service.obter_customer_por_cpf(cpf)


@router.post("/customers/create", response_model=CustomerPublicResponse, status_code=status.HTTP_201_CREATED)
async def criar_customer_publico(
    payload: CustomerCreatePublicRequest,
    service: OtpService = Depends(get_otp_service),
    _rate_limit: None = Depends(rate_limit_strict),
):
    return await service.criar_customer(payload.model_dump())


@router.post("/auth/otp/generate", response_model=dict)
async def gerar_otp_customer(
    payload: OtpGenerateRequest,
    request: Request,
    service: OtpService = Depends(get_otp_service),
    _rate_limit: None = Depends(rate_limit_strict),
):
    ip, user_agent = _request_meta(request)
    return await service.gerar_otp(
        cpf=payload.cpf,
        telefone=payload.telefone,
        ip=ip,
        user_agent=user_agent,
    )


@router.post("/auth/otp/validate", response_model=dict)
async def validar_otp_customer(
    payload: OtpValidateRequest,
    request: Request,
    service: OtpService = Depends(get_otp_service),
    _rate_limit: None = Depends(rate_limit_strict),
):
    ip, user_agent = _request_meta(request)
    try:
        return await service.validar_otp(
            otp_id=payload.otp_id,
            code=payload.code,
            ip=ip,
            user_agent=user_agent,
        )
    except HTTPException:
        raise
