from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TipoSuite(str, Enum):
    LUXO = "LUXO"
    LUXO_2 = "LUXO 2º"
    LUXO_3 = "LUXO 3º"
    LUXO_4_EC = "LUXO 4º EC"
    DUPLA = "DUPLA"
    MASTER = "MASTER"
    REAL = "REAL"
    STANDARD = "STANDARD"
    SUITE = "SUITE"


class StatusQuarto(str, Enum):
    LIVRE = "LIVRE"
    OCUPADO = "OCUPADO"
    MANUTENCAO = "MANUTENCAO"
    BLOQUEADO = "BLOQUEADO"


class QuartoCreate(BaseModel):
    numero: str
    tipo_suite: TipoSuite
    status: StatusQuarto = StatusQuarto.LIVRE


class QuartoUpdate(BaseModel):
    numero: Optional[str] = None
    tipo_suite: Optional[TipoSuite] = None
    status: Optional[StatusQuarto] = None


class QuartoResponse(BaseModel):
    id: int
    numero: str
    tipo_suite: TipoSuite
    status: StatusQuarto
    created_at: Optional[datetime]
