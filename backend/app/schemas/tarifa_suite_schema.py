from datetime import date
from typing import Optional

from pydantic import BaseModel
from app.schemas.quarto_schema import TipoSuite


class TarifaSuiteCreateRequest(BaseModel):
    suite_tipo: TipoSuite
    temporada: Optional[str] = None
    data_inicio: date
    data_fim: date
    preco_diaria: float
    ativo: bool = True


class TarifaSuiteUpdateRequest(BaseModel):
    suite_tipo: TipoSuite
    temporada: Optional[str] = None
    data_inicio: date
    data_fim: date
    preco_diaria: float
    ativo: bool = True


class TarifaSuiteResponse(BaseModel):
    id: int
    suite_tipo: TipoSuite
    temporada: Optional[str] = None
    data_inicio: date
    data_fim: date
    preco_diaria: float
    ativo: bool
