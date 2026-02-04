from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class FuncionarioBase(BaseModel):
    nome: str
    email: EmailStr
    perfil: str = "FUNCIONARIO"
    status: str = "ATIVO"


class FuncionarioCreate(FuncionarioBase):
    senha: str = "123456"


class FuncionarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    perfil: Optional[str] = None
    status: Optional[str] = None
    senha: Optional[str] = None


class FuncionarioResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    perfil: str
    status: str
    fotoUrl: Optional[str] = None
