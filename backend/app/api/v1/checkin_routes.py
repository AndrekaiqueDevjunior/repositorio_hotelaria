from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, validator
from datetime import datetime, date

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.core.security import User
from app.repositories.hospedagem_repo import HospedagemRepository
from app.core.state_validators import StateValidator, get_acoes_disponiveis


router = APIRouter(prefix="/checkin", tags=["check-in"])


# Schemas para Check-in
class HospedeCheckinData(BaseModel):
    nome_completo: str
    documento: str
    documento_tipo: str
    nacionalidade: str = "Brasil"
    data_nascimento: datetime = None
    telefone: str = None
    email: str = None
    e_menor: bool = False
    responsavel_nome: str = None
    responsavel_documento: str = None


class CheckinRequest(BaseModel):
    hospede_titular_nome: str
    hospede_titular_documento: str
    hospede_titular_documento_tipo: str
    num_hospedes_real: int
    num_criancas: int = 0
    veiculo_placa: str = None
    observacoes_checkin: str = None
    caucao_cobrada: float = 0
    caucao_forma_pagamento: str = None
    pagamento_validado: bool = True
    documentos_conferidos: bool = True
    termos_aceitos: bool = True
    assinatura_digital: str = None
    hospedes: List[HospedeCheckinData] = []
    
    @validator('num_hospedes_real')
    def validate_num_hospedes(cls, v):
        if v <= 0:
            raise ValueError('Número de hóspedes deve ser maior que zero')
        return v
    
    @validator('termos_aceitos')
    def validate_termos(cls, v):
        if not v:
            raise ValueError('Aceite dos termos é obrigatório')
        return v


# Schemas para Check-out
class ConsumoAdicional(BaseModel):
    tipo: str
    descricao: str
    quantidade: int = 1
    valor_unitario: float


class CheckoutRequest(BaseModel):
    vistoria_ok: bool = True
    danos_encontrados: str = None
    valor_danos: float = 0
    consumo_frigobar: float = 0
    servicos_extras: float = 0
    taxa_late_checkout: float = 0
    caucao_devolvida: float = 0
    caucao_retida: float = 0
    motivo_retencao: str = None
    avaliacao_hospede: int = 5
    comentario_hospede: str = None
    forma_acerto: str = None
    observacoes_checkout: str = None
    consumos_adicionais: List[ConsumoAdicional] = []
    
    @validator('avaliacao_hospede')
    def validate_avaliacao(cls, v):
        if not (1 <= v <= 5):
            raise ValueError('Avaliação deve ser entre 1 e 5')
        return v


def _normalizar_status_pagamento_para_validacao(status_pagamento: Optional[str]) -> str:
    if not status_pagamento:
        return "PENDENTE"
    if status_pagamento in ("PAGO", "APROVADO", "APPROVED", "CONFIRMADO", "CAPTURED", "AUTHORIZED"):
        return "CONFIRMADO"
    return status_pagamento


def _selecionar_status_pagamento(reserva) -> str:
    if not hasattr(reserva, "pagamentos") or not reserva.pagamentos:
        return "PENDENTE"

    for p in reserva.pagamentos:
        status_pagamento = getattr(p, "statusPagamento", None) or getattr(p, "status", None)
        status_pagamento_norm = _normalizar_status_pagamento_para_validacao(status_pagamento)
        if status_pagamento_norm == "CONFIRMADO":
            return status_pagamento

    p0 = reserva.pagamentos[0]
    return getattr(p0, "statusPagamento", None) or getattr(p0, "status", None) or "PENDENTE"


@router.get("/{reserva_id}/validar", response_model=Dict[str, Any])
async def validar_pre_checkin(
    reserva_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Validação pré check-in
    Verifica se a reserva pode fazer check-in e retorna bloqueios/warnings
    """
    try:
        db = get_db()
        reserva = await db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True, "pagamentos": True}
        )
 
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")
 
        status_reserva = getattr(reserva, "statusReserva", None) or getattr(reserva, "status", None) or "PENDENTE"
        status_hospedagem = getattr(getattr(reserva, "hospedagem", None), "statusHospedagem", None) or "NAO_INICIADA"
        status_pagamento_raw = _selecionar_status_pagamento(reserva)
        status_pagamento = _normalizar_status_pagamento_para_validacao(status_pagamento_raw)
 
        pode, motivo = StateValidator.validar_acao_checkin(
            status_reserva,
            status_pagamento,
            status_hospedagem
        )
 
        return {
            "pode_checkin": pode,
            "motivo": motivo,
            "capacidade_maxima": 1,
            "status": {
                "reserva": status_reserva,
                "pagamento": status_pagamento_raw,
                "hospedagem": status_hospedagem,
            },
            "acoes_disponiveis": get_acoes_disponiveis(status_reserva, status_pagamento, status_hospedagem),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/{reserva_id}/realizar")
async def realizar_checkin(
    reserva_id: int,
    dados_checkin: CheckinRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Realiza o check-in formal da reserva
    Cria registro completo com hóspedes, validações e assinaturas
    """
    try:
        db = get_db()
        repo = HospedagemRepository(db)
 
        await repo.checkin(
            reserva_id=reserva_id,
            num_hospedes=dados_checkin.num_hospedes_real,
            num_criancas=dados_checkin.num_criancas,
            placa_veiculo=dados_checkin.veiculo_placa,
            observacoes=dados_checkin.observacoes_checkin,
            funcionario_id=current_user.id,
        )
 
        reserva_atualizada = await db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True, "pagamentos": True}
        )
 
        return {
            "success": True,
            "message": "Check-in realizado com sucesso!",
            "reserva": {
                "id": reserva_atualizada.id,
                "codigo_reserva": reserva_atualizada.codigoReserva,
                "status": getattr(reserva_atualizada, "statusReserva", None) or getattr(reserva_atualizada, "status", None),
            },
            "hospedagem": {
                "status": getattr(getattr(reserva_atualizada, "hospedagem", None), "statusHospedagem", None),
                "checkin_realizado_em": getattr(getattr(reserva_atualizada, "hospedagem", None), "checkinRealizadoEm", None),
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/{reserva_id}/detalhes")
async def consultar_checkin(
    reserva_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Consulta detalhes completos do check-in"""
    try:
        db = get_db()
        reserva = await db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True}
        )
 
        if not reserva or not reserva.hospedagem:
            raise HTTPException(status_code=404, detail="Hospedagem não encontrada para esta reserva")
 
        return {
            "reserva_id": reserva.id,
            "codigo_reserva": reserva.codigoReserva,
            "status_reserva": reserva.status_reserva,
            "hospedagem": {
                "status_hospedagem": reserva.hospedagem.statusHospedagem,
                "checkin_realizado_em": reserva.hospedagem.checkinRealizadoEm,
                "checkin_realizado_por": reserva.hospedagem.checkinRealizadoPor,
                "num_hospedes": reserva.hospedagem.numHospedes,
                "num_criancas": reserva.hospedagem.numCriancas,
                "placa_veiculo": reserva.hospedagem.placaVeiculo,
                "observacoes": reserva.hospedagem.observacoes,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# Rotas de Check-out
@router.get("/{reserva_id}/checkout/validar", response_model=Dict[str, Any])
async def validar_pre_checkout(
    reserva_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Validação pré check-out
    Calcula acerto financeiro e verifica pendências
    """
    try:
        db = get_db()
        reserva = await db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True}
        )
 
        if not reserva or not reserva.hospedagem:
            raise HTTPException(status_code=404, detail="Hospedagem não encontrada para esta reserva")
 
        status_hospedagem = reserva.hospedagem.statusHospedagem
        pode, motivo = StateValidator.validar_acao_checkout(status_hospedagem)
 
        return {
            "pode_checkout": pode,
            "motivo": motivo,
            "caucao_cobrada": 0,
            "status": {
                "hospedagem": status_hospedagem,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/{reserva_id}/checkout/realizar")
async def realizar_checkout(
    reserva_id: int,
    dados_checkout: CheckoutRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Realiza o check-out formal da hospedagem
    Inclui vistoria, acerto financeiro e consumos finais
    """
    try:
        db = get_db()
        repo = HospedagemRepository(db)
 
        await repo.checkout(
            reserva_id=reserva_id,
            consumo_frigobar=float(dados_checkout.consumo_frigobar or 0),
            servicos_extras=float(dados_checkout.servicos_extras or 0),
            avaliacao=int(dados_checkout.avaliacao_hospede or 5),
            comentario_avaliacao=dados_checkout.comentario_hospede,
            funcionario_id=current_user.id,
        )
 
        reserva_atualizada = await db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True}
        )
 
        return {
            "success": True,
            "message": "Check-out realizado com sucesso!",
            "reserva": {
                "id": reserva_atualizada.id,
                "codigo_reserva": reserva_atualizada.codigoReserva,
                "status": getattr(reserva_atualizada, "statusReserva", None) or getattr(reserva_atualizada, "status", None),
            },
            "hospedagem": {
                "status": getattr(getattr(reserva_atualizada, "hospedagem", None), "statusHospedagem", None),
                "checkout_realizado_em": getattr(getattr(reserva_atualizada, "hospedagem", None), "checkoutRealizadoEm", None),
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/{reserva_id}/checkout/detalhes")
async def consultar_checkout(
    reserva_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Consulta detalhes completos do check-out"""
    try:
        db = get_db()
        reserva = await db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True}
        )
 
        if not reserva or not reserva.hospedagem:
            raise HTTPException(status_code=404, detail="Hospedagem não encontrada para esta reserva")
 
        return {
            "reserva_id": reserva.id,
            "codigo_reserva": reserva.codigoReserva,
            "status_reserva": reserva.status_reserva,
            "hospedagem": {
                "status_hospedagem": reserva.hospedagem.statusHospedagem,
                "checkout_realizado_em": reserva.hospedagem.checkoutRealizadoEm,
                "checkout_realizado_por": reserva.hospedagem.checkoutRealizadoPor,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/relatorio/checkouts/{data}")
async def relatorio_checkouts_dia(
    data: date,
    current_user: User = Depends(get_current_active_user)
):
    raise HTTPException(status_code=410, detail="Endpoint descontinuado")
