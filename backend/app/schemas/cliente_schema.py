from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr


class ClienteCreate(BaseModel):
    nome_completo: str
    documento: str
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None


class ClienteUpdate(BaseModel):
    nome_completo: Optional[str] = None
    documento: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[str] = None


class ClienteResponse(BaseModel):
    id: int
    nome_completo: str
    documento: str
    telefone: Optional[str]
    email: Optional[EmailStr]
    status: Optional[str] = None
    created_at: Optional[datetime] = None
