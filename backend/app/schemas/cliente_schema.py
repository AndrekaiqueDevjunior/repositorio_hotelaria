from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


def _blank_to_none(v):
    """Converte string vazia/somente-espacos em None.

    O formulario do painel envia "" para campos opcionais nao preenchidos.
    Sem isso, `email: Optional[EmailStr]` rejeita "" com 422
    ("value is not a valid email address"), impedindo o cadastro de clientes
    sem email.
    """
    if isinstance(v, str) and not v.strip():
        return None
    return v


class ClienteCreate(BaseModel):
    nome_completo: str
    documento: str
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    data_nascimento: Optional[date] = None
    nacionalidade: Optional[str] = None
    endereco_completo: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    pais: Optional[str] = None
    observacoes: Optional[str] = None

    @field_validator(
        "telefone", "email", "data_nascimento", "nacionalidade",
        "endereco_completo", "cidade", "estado", "pais", "observacoes",
        mode="before",
    )
    @classmethod
    def _vazio_para_none(cls, v):
        return _blank_to_none(v)


class ClienteUpdate(BaseModel):
    nome_completo: Optional[str] = None
    documento: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    data_nascimento: Optional[date] = None
    nacionalidade: Optional[str] = None
    endereco_completo: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    pais: Optional[str] = None
    observacoes: Optional[str] = None
    status: Optional[str] = None

    @field_validator(
        "telefone", "email", "data_nascimento", "nacionalidade",
        "endereco_completo", "cidade", "estado", "pais", "observacoes",
        mode="before",
    )
    @classmethod
    def _vazio_para_none(cls, v):
        return _blank_to_none(v)


class ClienteResponse(BaseModel):
    id: int
    nome_completo: str
    documento: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    data_nascimento: Optional[datetime] = None
    nacionalidade: Optional[str] = None
    endereco_completo: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    pais: Optional[str] = None
    observacoes: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
