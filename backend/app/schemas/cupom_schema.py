from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


TIPOS_DESCONTO_VALIDOS = {"PERCENTUAL", "FIXO"}


def _normalizar_codigo(value: str) -> str:
    return (value or "").strip().upper()


def _normalizar_tipo_desconto(value: str) -> str:
    return (value or "").strip().upper()


class CupomCreateRequest(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=50)
    descricao: Optional[str] = None
    tipo_desconto: str
    valor_desconto: Decimal = Field(..., gt=0)
    pontos_bonus: Optional[int] = Field(None, ge=0, le=1000)
    min_diarias: Optional[int] = Field(None, ge=1, le=365)
    suites_permitidas: Optional[List[str]] = None
    data_inicio: datetime
    data_fim: datetime
    limite_total_usos: Optional[int] = Field(None, ge=1)
    limite_por_cliente: Optional[int] = Field(None, ge=1)
    ativo: bool = True

    @field_validator("codigo")
    @classmethod
    def validar_codigo(cls, value: str) -> str:
        codigo = _normalizar_codigo(value)
        if not codigo:
            raise ValueError("Código do cupom é obrigatório")
        return codigo

    @field_validator("tipo_desconto")
    @classmethod
    def validar_tipo_desconto(cls, value: str) -> str:
        tipo = _normalizar_tipo_desconto(value)
        if tipo not in TIPOS_DESCONTO_VALIDOS:
            raise ValueError("tipo_desconto deve ser PERCENTUAL ou FIXO")
        return tipo

    @field_validator("suites_permitidas")
    @classmethod
    def normalizar_suites(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if not value:
            return None
        suites = []
        for item in value:
            suite = (item or "").strip().upper()
            if suite:
                suites.append(suite)
        return suites or None

    @model_validator(mode="after")
    def validar_regra_datas(self):
        if self.data_fim <= self.data_inicio:
            raise ValueError("data_fim deve ser posterior a data_inicio")
        if self.tipo_desconto == "PERCENTUAL" and self.valor_desconto > Decimal("100"):
            raise ValueError("Desconto percentual não pode ser maior que 100")
        return self


class CupomUpdateRequest(BaseModel):
    descricao: Optional[str] = None
    tipo_desconto: Optional[str] = None
    valor_desconto: Optional[Decimal] = Field(None, gt=0)
    pontos_bonus: Optional[int] = Field(None, ge=0, le=1000)
    min_diarias: Optional[int] = Field(None, ge=1, le=365)
    suites_permitidas: Optional[List[str]] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    limite_total_usos: Optional[int] = Field(None, ge=1)
    limite_por_cliente: Optional[int] = Field(None, ge=1)
    ativo: Optional[bool] = None

    @field_validator("tipo_desconto")
    @classmethod
    def validar_tipo_desconto(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        tipo = _normalizar_tipo_desconto(value)
        if tipo not in TIPOS_DESCONTO_VALIDOS:
            raise ValueError("tipo_desconto deve ser PERCENTUAL ou FIXO")
        return tipo

    @field_validator("suites_permitidas")
    @classmethod
    def normalizar_suites(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        suites = []
        for item in value:
            suite = (item or "").strip().upper()
            if suite:
                suites.append(suite)
        return suites or []

    @model_validator(mode="after")
    def validar_percentual(self):
        if self.tipo_desconto == "PERCENTUAL" and self.valor_desconto and self.valor_desconto > Decimal("100"):
            raise ValueError("Desconto percentual não pode ser maior que 100")
        if self.data_inicio and self.data_fim and self.data_fim <= self.data_inicio:
            raise ValueError("data_fim deve ser posterior a data_inicio")
        return self


class CupomStatusRequest(BaseModel):
    ativo: bool


class CupomValidarRequest(BaseModel):
    codigo: str
    cliente_id: Optional[int] = None
    reserva_id: Optional[int] = None
    suite_tipo: Optional[str] = None
    num_diarias: Optional[int] = Field(None, ge=1, le=365)
    valor_total_base: Optional[Decimal] = Field(None, gt=0)

    @field_validator("codigo")
    @classmethod
    def validar_codigo(cls, value: str) -> str:
        codigo = _normalizar_codigo(value)
        if not codigo:
            raise ValueError("Código do cupom é obrigatório")
        return codigo

    @field_validator("suite_tipo")
    @classmethod
    def normalizar_suite(cls, value: Optional[str]) -> Optional[str]:
        return (value or "").strip().upper() or None


class AplicarCupomRequest(BaseModel):
    codigo: str

    @field_validator("codigo")
    @classmethod
    def validar_codigo(cls, value: str) -> str:
        codigo = _normalizar_codigo(value)
        if not codigo:
            raise ValueError("Código do cupom é obrigatório")
        return codigo


class CupomUsoResponse(BaseModel):
    id: int
    cupom_id: int
    codigo: str
    valor_original: float
    valor_desconto: float
    valor_final: float
    pontos_bonus: int = 0
    created_at: Optional[datetime] = None


class CupomResponse(BaseModel):
    id: int
    codigo: str
    descricao: Optional[str] = None
    tipo_desconto: str
    valor_desconto: float
    pontos_bonus: int = 0
    min_diarias: Optional[int] = None
    suites_permitidas: Optional[List[str]] = None
    data_inicio: datetime
    data_fim: datetime
    limite_total_usos: Optional[int] = None
    limite_por_cliente: Optional[int] = None
    total_usos: int = 0
    ativo: bool = True
    criado_por: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CupomValidarResponse(BaseModel):
    valido: bool
    mensagem: str
    codigo: Optional[str] = None
    tipo_desconto: Optional[str] = None
    valor_desconto: Optional[float] = None
    valor_desconto_calculado: Optional[float] = None
    valor_final_estimado: Optional[float] = None
    pontos_bonus: int = 0


class CupomAplicadoResponse(BaseModel):
    success: bool
    reserva_id: int
    cupom: CupomUsoResponse
    reserva: dict
