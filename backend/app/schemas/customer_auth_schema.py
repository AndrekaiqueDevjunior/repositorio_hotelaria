from typing import Optional

from pydantic import AliasChoices, BaseModel, EmailStr, Field


class CustomerPublicResponse(BaseModel):
    id: int
    nome_completo: str
    documento: str
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[str] = None
    created_at: Optional[str] = None


class CustomerCreatePublicRequest(BaseModel):
    nome_completo: str = Field(..., min_length=3)
    documento: str = Field(..., min_length=11)
    telefone: str = Field(..., min_length=8)
    email: Optional[EmailStr] = None


class OtpGenerateRequest(BaseModel):
    cpf: str = Field(
        ...,
        validation_alias=AliasChoices("cpf", "documento", "customer_ref"),
        min_length=11,
    )
    telefone: Optional[str] = None


class OtpValidateRequest(BaseModel):
    otp_id: str = Field(..., min_length=8)
    code: str = Field(..., pattern=r"^\d{6}$")

