from datetime import date
from typing import Optional

from pydantic import BaseModel


class PontosRegraCreateRequest(BaseModel):
    suite_tipo: str
    diarias_base: int = 2
    rp_por_base: int
    temporada: Optional[str] = None
    data_inicio: date
    data_fim: date
    ativo: bool = True


class PontosRegraUpdateRequest(BaseModel):
    suite_tipo: str
    diarias_base: int = 2
    rp_por_base: int
    temporada: Optional[str] = None
    data_inicio: date
    data_fim: date
    ativo: bool = True


class PontosRegraResponse(BaseModel):
    id: int
    suite_tipo: str
    diarias_base: int
    rp_por_base: int
    temporada: Optional[str] = None
    data_inicio: date
    data_fim: date
    ativo: bool
