from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CheckinCashApprovalRequest(BaseModel):
    reservation_id: int = Field(..., ge=1)
    amount: Decimal = Field(..., gt=0)
    payment_method: str = "cash"


class CheckinCashApprovalResponse(BaseModel):
    success: bool
    approval_id: Optional[int] = None
    approval_code: str
    expires_at: str
    qr_code: str
    whatsapp: Optional[dict] = None

