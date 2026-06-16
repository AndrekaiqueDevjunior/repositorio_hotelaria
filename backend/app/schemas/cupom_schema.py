from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator


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
    tipo_campanha: Optional[str] = Field(None, max_length=50)
    cliente_indicador_id: Optional[int] = Field(None, ge=1)

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
    tipo_campanha: Optional[str] = None
    cliente_indicador_id: Optional[int] = Field(None, ge=1)

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


class CupomAmigoRequest(BaseModel):
    cliente_id: int = Field(..., ge=1)
    percentual_desconto: Decimal = Field(Decimal("10"), gt=0, le=100)
    pontos_bonus: int = Field(50, ge=0, le=1000)
    dias_validade: int = Field(30, ge=1, le=365)
    limite_total_usos: int = Field(5, ge=1)
    telefone_destino: Optional[str] = None
    enviar_whatsapp: bool = False


class ReferralGenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    customer_id: int = Field(
        ...,
        validation_alias=AliasChoices("customer_id", "cliente_id"),
        ge=1,
    )
    discount_percentage: Decimal = Field(
        Decimal("10"),
        validation_alias=AliasChoices("discount_percentage", "percentual_desconto"),
        gt=0,
        le=100,
    )
    bonus_points: int = Field(
        50,
        validation_alias=AliasChoices("bonus_points", "pontos_bonus"),
        ge=0,
        le=1000,
    )
    valid_days: int = Field(
        30,
        validation_alias=AliasChoices("valid_days", "dias_validade"),
        ge=1,
        le=365,
    )
    max_uses: int = Field(
        5,
        validation_alias=AliasChoices("max_uses", "limite_total_usos"),
        ge=1,
    )
    recipient_phone: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("recipient_phone", "telefone_destino"),
    )
    send_whatsapp: bool = Field(
        False,
        validation_alias=AliasChoices("send_whatsapp", "enviar_whatsapp"),
    )


class ReferralApplyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reservation_id: int = Field(
        ...,
        validation_alias=AliasChoices("reservation_id", "reserva_id"),
        ge=1,
    )
    code: str = Field(..., validation_alias=AliasChoices("code", "codigo"), min_length=3, max_length=50)

    @field_validator("code")
    @classmethod
    def validar_codigo(cls, value: str) -> str:
        codigo = _normalizar_codigo(value)
        if not codigo:
            raise ValueError("Código de indicação é obrigatório")
        return codigo


class CupomRastreadoRequest(BaseModel):
    codigo: Optional[str] = Field(None, min_length=3, max_length=50)
    descricao: Optional[str] = None
    tipo_campanha: str = Field("DESCONTO", max_length=50)
    tipo_desconto: str = "PERCENTUAL"
    valor_desconto: Decimal = Field(..., gt=0)
    dias_validade: int = Field(30, ge=1, le=365)
    limite_total_usos: Optional[int] = Field(None, ge=1)
    limite_por_cliente: Optional[int] = Field(1, ge=1)
    pontos_bonus: Optional[int] = Field(0, ge=0, le=1000)
    min_diarias: Optional[int] = Field(None, ge=1, le=365)
    suites_permitidas: Optional[List[str]] = None
    influencer_nome: Optional[str] = None
    commission_percentage: Optional[Decimal] = Field(None, ge=0, le=100)

    @field_validator("codigo")
    @classmethod
    def validar_codigo_opcional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
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


class AdminCouponGenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("code", "codigo"),
        min_length=3,
        max_length=50,
    )
    description: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("description", "descricao"),
    )
    discount_type: str = Field(
        ...,
        validation_alias=AliasChoices("discountType", "discount_type", "tipo_desconto"),
    )
    discount_value: Decimal = Field(
        ...,
        validation_alias=AliasChoices("discountValue", "discount_value", "valor_desconto"),
        gt=0,
    )
    valid_from: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("validFrom", "valid_from", "data_inicio"),
    )
    valid_until: datetime = Field(
        ...,
        validation_alias=AliasChoices("validUntil", "valid_until", "data_fim"),
    )
    max_uses: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("maxUses", "max_uses", "limite_total_usos"),
        ge=1,
    )
    per_customer_limit: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("perCustomerLimit", "per_customer_limit", "limite_por_cliente"),
        ge=1,
    )
    status: str = "ACTIVE"
    campaign_type: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("campaignType", "campaign_type", "tipo_campanha"),
        max_length=50,
    )
    influencer_name: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("influencerName", "influencer_name", "influencer_nome"),
        max_length=180,
    )
    commission_percentage: Optional[Decimal] = Field(
        None,
        validation_alias=AliasChoices("commissionPercentage", "commission_percentage", "commission_percentual"),
        ge=0,
        le=100,
    )
    bonus_points: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("bonusPoints", "bonus_points", "pontos_bonus"),
        ge=0,
        le=1000,
    )
    min_nights: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("minNights", "min_nights", "min_diarias"),
        ge=1,
        le=365,
    )
    suite_types: Optional[List[str]] = Field(
        None,
        validation_alias=AliasChoices("suiteTypes", "suite_types", "suites_permitidas"),
    )

    @field_validator("code")
    @classmethod
    def validar_codigo_opcional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        codigo = _normalizar_codigo(value)
        if not codigo:
            raise ValueError("Codigo do cupom e obrigatorio")
        return codigo

    @field_validator("discount_type")
    @classmethod
    def validar_tipo_desconto_admin(cls, value: str) -> str:
        tipo = _normalizar_tipo_desconto(value)
        if tipo in {"PERCENTAGE", "PERCENTUAL"}:
            return "PERCENTUAL"
        if tipo in {"FIXED_AMOUNT", "FIXO"}:
            return "FIXO"
        raise ValueError("discountType deve ser PERCENTAGE ou FIXED_AMOUNT")

    @field_validator("status")
    @classmethod
    def validar_status_admin(cls, value: str) -> str:
        status = (value or "").strip().upper()
        if status not in {"ACTIVE", "INACTIVE", "EXPIRED", "MAXED"}:
            raise ValueError("status deve ser ACTIVE, INACTIVE, EXPIRED ou MAXED")
        return status

    @field_validator("campaign_type")
    @classmethod
    def normalizar_tipo_campanha(cls, value: Optional[str]) -> Optional[str]:
        return (value or "").strip().upper() or None

    @field_validator("suite_types")
    @classmethod
    def normalizar_suites_admin(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if not value:
            return None
        suites = []
        for item in value:
            suite = (item or "").strip().upper()
            if suite:
                suites.append(suite)
        return suites or None

    @model_validator(mode="after")
    def validar_datas_admin(self):
        inicio = self.valid_from
        if inicio and self.valid_until <= inicio:
            raise ValueError("validUntil deve ser posterior a validFrom")
        if self.discount_type == "PERCENTUAL" and self.discount_value > Decimal("100"):
            raise ValueError("Desconto percentual nao pode ser maior que 100")
        return self


class AdminCouponUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("description", "descricao"),
    )
    discount_type: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("discountType", "discount_type", "tipo_desconto"),
    )
    discount_value: Optional[Decimal] = Field(
        None,
        validation_alias=AliasChoices("discountValue", "discount_value", "valor_desconto"),
        gt=0,
    )
    valid_from: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("validFrom", "valid_from", "data_inicio"),
    )
    valid_until: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("validUntil", "valid_until", "data_fim"),
    )
    max_uses: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("maxUses", "max_uses", "limite_total_usos"),
        ge=1,
    )
    per_customer_limit: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("perCustomerLimit", "per_customer_limit", "limite_por_cliente"),
        ge=1,
    )
    status: Optional[str] = None
    campaign_type: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("campaignType", "campaign_type", "tipo_campanha"),
        max_length=50,
    )
    influencer_name: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("influencerName", "influencer_name", "influencer_nome"),
        max_length=180,
    )
    commission_percentage: Optional[Decimal] = Field(
        None,
        validation_alias=AliasChoices("commissionPercentage", "commission_percentage", "commission_percentual"),
        ge=0,
        le=100,
    )
    bonus_points: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("bonusPoints", "bonus_points", "pontos_bonus"),
        ge=0,
        le=1000,
    )
    min_nights: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("minNights", "min_nights", "min_diarias"),
        ge=1,
        le=365,
    )
    suite_types: Optional[List[str]] = Field(
        None,
        validation_alias=AliasChoices("suiteTypes", "suite_types", "suites_permitidas"),
    )

    @field_validator("discount_type")
    @classmethod
    def validar_tipo_desconto_admin(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        tipo = _normalizar_tipo_desconto(value)
        if tipo in {"PERCENTAGE", "PERCENTUAL"}:
            return "PERCENTUAL"
        if tipo in {"FIXED_AMOUNT", "FIXO"}:
            return "FIXO"
        raise ValueError("discountType deve ser PERCENTAGE ou FIXED_AMOUNT")

    @field_validator("status")
    @classmethod
    def validar_status_admin(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        status = value.strip().upper()
        if status not in {"ACTIVE", "INACTIVE", "EXPIRED", "MAXED"}:
            raise ValueError("status deve ser ACTIVE, INACTIVE, EXPIRED ou MAXED")
        return status

    @field_validator("campaign_type")
    @classmethod
    def normalizar_tipo_campanha(cls, value: Optional[str]) -> Optional[str]:
        return (value or "").strip().upper() or None

    @field_validator("suite_types")
    @classmethod
    def normalizar_suites_admin(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        suites = []
        for item in value:
            suite = (item or "").strip().upper()
            if suite:
                suites.append(suite)
        return suites or []

    @model_validator(mode="after")
    def validar_percentual_admin(self):
        if self.discount_type == "PERCENTUAL" and self.discount_value and self.discount_value > Decimal("100"):
            raise ValueError("Desconto percentual nao pode ser maior que 100")
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("validUntil deve ser posterior a validFrom")
        return self


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
    tipo_campanha: Optional[str] = None
    cliente_indicador_id: Optional[int] = None
    status: Optional[str] = None
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
    status: str = "active"
    tracking_slug: Optional[str] = None
    link_rastreado: Optional[str] = None
    whatsapp_message: Optional[str] = None
    whatsapp_share_url: Optional[str] = None
    criado_por: Optional[int] = None
    tipo_campanha: Optional[str] = None
    influencer_nome: Optional[str] = None
    commission_percentual: Optional[float] = None
    cliente_indicador_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CupomValidarResponse(BaseModel):
    valido: bool
    mensagem: str
    codigo: Optional[str] = None
    status: Optional[str] = None
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
