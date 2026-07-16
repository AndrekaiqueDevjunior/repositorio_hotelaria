from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CheckinCashApprovalRequest(BaseModel):
    reservation_id: int = Field(..., ge=1)
    amount: Decimal = Field(..., gt=0)
    payment_method: str = "cash"
    foto_url: Optional[str] = Field(None, max_length=500)
    # Foto do comprovante em base64: entra no fluxo padrao de comprovantes
    # (tela /comprovantes) e vai embutida no card WhatsApp do gerente.
    # 10MB de arquivo ~ 14MB em base64.
    foto_base64: Optional[str] = Field(None, max_length=15_000_000)
    foto_nome: Optional[str] = Field(None, max_length=200)


class CheckinCashApprovalResponse(BaseModel):
    success: bool
    approval_id: Optional[int] = None
    approval_code: str
    expires_at: str
    qr_code: str
    payment_id: Optional[int] = None
    comprovante_id: Optional[int] = None
    whatsapp: Optional[dict] = None
    whatsapp_gerente: Optional[dict] = None

