"""
ROTAS DE FLUXO DE RESERVAS
==========================
API que implementa o fluxo completo: Criar → Pagar → Check-in → Checkout
Substitui APIs fragmentadas por fluxo unificado
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.fluxo_reserva_service import FluxoReservaService
from app.core.unified_state_validator import UnifiedStateValidator

router = APIRouter(prefix="/fluxo-reservas", tags=["fluxo-reservas"])

# ==================== MODELS ====================

class ReservaCreate(BaseModel):
    cliente_id: int
    quarto_id: int
    checkin_previsto: str
    checkout_previsto: str
    valor_diaria: float
    num_diarias: int

class PagamentoCreate(BaseModel):
    metodo: str
    valor: float
    cartao_numero: Optional[str] = None
    cartao_validade: Optional[str] = None
    cartao_cvv: Optional[str] = None
    cartao_nome: Optional[str] = None

class CheckinCreate(BaseModel):
    funcionario_id: int
    observacoes: Optional[str] = None

class CheckoutCreate(BaseModel):
    observacoes: Optional[str] = None

class CancelamentoCreate(BaseModel):
    motivo: Optional[str] = None

# ==================== FLUXO COMPLETO ====================

@router.post("/criar", summary="Etapa 1: Criar reserva")
async def criar_reserva(
    dados: ReservaCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Etapa 1 do fluxo: Criar nova reserva
    Status inicial: PENDENTE
    """
    try:
        db = next(get_db())
        service = FluxoReservaService(db)
        
        reserva = await service.criar_reserva(dados.dict())
        
        return {
            "success": True,
            "message": "Reserva criada com sucesso",
            "data": reserva,
            "proxima_acao": "PAGAR",
            "fluxo_atual": "CRIADA_AGUARDANDO_PAGAMENTO"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{reserva_id}/pagar", summary="Etapa 2: Processar pagamento")
async def processar_pagamento(
    reserva_id: int,
    dados: PagamentoCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Etapa 2 do fluxo: Processar pagamento
    Se aprovado, confirma reserva automaticamente
    """
    try:
        db = next(get_db())
        service = FluxoReservaService(db)
        
        pagamento = await service.processar_pagamento(reserva_id, dados.dict())
        
        # Buscar reserva atualizada
        reserva = await service._buscar_reserva(reserva_id)
        
        return {
            "success": True,
            "message": "Pagamento processado com sucesso",
            "data": pagamento,
            "reserva": reserva,
            "proxima_acao": "FAZER_CHECKIN" if reserva['status'] == "CONFIRMADA" else "VERIFICAR_PAGAMENTO",
            "fluxo_atual": reserva.get('fluxo_atual', 'PAGAMENTO_PROCESSADO')
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{reserva_id}/checkin", summary="Etapa 3: Fazer check-in")
async def fazer_checkin(
    reserva_id: int,
    dados: CheckinCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Etapa 3 do fluxo: Realizar check-in
    Requer reserva confirmada e pagamento aprovado
    """
    try:
        db = next(get_db())
        service = FluxoReservaService(db)
        
        checkin = await service.fazer_checkin(reserva_id, dados.dict())
        
        return {
            "success": True,
            "message": "Check-in realizado com sucesso",
            "data": checkin,
            "proxima_acao": "FAZER_CHECKOUT",
            "fluxo_atual": "HOSPEDAGEM_EM_ANDAMENTO"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{reserva_id}/checkout", summary="Etapa 4: Fazer check-out")
async def fazer_checkout(
    reserva_id: int,
    dados: CheckoutCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Etapa 4 do fluxo: Realizar check-out
    Finaliza a hospedagem
    """
    try:
        db = next(get_db())
        service = FluxoReservaService(db)
        
        checkout = await service.fazer_checkout(reserva_id, dados.dict())
        
        return {
            "success": True,
            "message": "Check-out realizado com sucesso",
            "data": checkout,
            "proxima_acao": "LIMPAR_QUARTO",
            "fluxo_atual": "HOSPEDAGEM_FINALIZADA"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{reserva_id}/cancelar", summary="Cancelar reserva")
async def cancelar_reserva(
    reserva_id: int,
    dados: CancelamentoCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Fluxo alternativo: Cancelar reserva
    """
    try:
        db = next(get_db())
        service = FluxoReservaService(db)
        
        reserva = await service.cancelar_reserva(reserva_id, dados.motivo)
        
        return {
            "success": True,
            "message": "Reserva cancelada com sucesso",
            "data": reserva,
            "fluxo_atual": "RESERVA_CANCELADA"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== CONSULTAS E DIAGNÓSTICO ====================

@router.get("/{reserva_id}/diagnostico", summary="Diagnosticar fluxo")
async def diagnosticar_fluxo(
    reserva_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Diagnostica o estado atual do fluxo de uma reserva
    Retorna problemas, ações disponíveis e recomendações
    """
    try:
        db = next(get_db())
        service = FluxoReservaService(db)
        
        diagnostico = await service.diagnosticar_fluxo(reserva_id)
        
        return {
            "success": True,
            "data": diagnostico
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/fluxo-esperado", summary="Obter fluxo esperado")
async def get_fluxo_esperado():
    """
    Retorna o fluxo esperado do sistema
    """
    return {
        "success": True,
        "data": FluxoReservaService.get_fluxo_esperado()
    }

@router.post("/validar-sequencia", summary="Validar sequência")
async def validar_sequencia(
    sequencia: List[str] = Body(...)
):
    """
    Valida se uma sequência de eventos segue o fluxo correto
    """
    valido, mensagem = FluxoReservaService.validar_sequencia_fluxo(sequencia)
    
    return {
        "success": valido,
        "message": mensagem,
        "sequencia": sequencia
    }

# ==================== VALIDAÇÕES INDIVIDUAIS ====================

@router.get("/{reserva_id}/pode-pagar", summary="Verificar se pode pagar")
async def pode_pagar(
    reserva_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Verifica se reserva pode ser paga"""
    try:
        db = next(get_db())
        service = FluxoReservaService(db)
        reserva = await service._buscar_reserva(reserva_id)
        
        pode, motivo = UnifiedStateValidator.pode_pagar(reserva)
        
        return {
            "pode": pode,
            "motivo": motivo,
            "reserva_id": reserva_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{reserva_id}/pode-checkin", summary="Verificar se pode fazer check-in")
async def pode_checkin(
    reserva_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Verifica se pode fazer check-in"""
    try:
        db = next(get_db())
        service = FluxoReservaService(db)
        reserva = await service._buscar_reserva(reserva_id)
        pagamentos = await service._buscar_pagamentos(reserva_id)
        
        pode, motivo = UnifiedStateValidator.pode_fazer_checkin(reserva, pagamentos)
        
        return {
            "pode": pode,
            "motivo": motivo,
            "reserva_id": reserva_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{reserva_id}/pode-checkout", summary="Verificar se pode fazer check-out")
async def pode_checkout(
    reserva_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Verifica se pode fazer check-out"""
    try:
        db = next(get_db())
        service = FluxoReservaService(db)
        hospedagem = await service._buscar_hospedagem(reserva_id)
        
        if not hospedagem:
            return {
                "pode": False,
                "motivo": "Check-in não realizado"
            }
        
        pode, motivo = UnifiedStateValidator.pode_fazer_checkout(hospedagem)
        
        return {
            "pode": pode,
            "motivo": motivo,
            "reserva_id": reserva_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== UTILITÁRIOS ====================

@router.get("/estados", summary="Obter estados disponíveis")
async def get_estados():
    """Retorna todos os estados padronizados"""
    validator = UnifiedStateValidator()
    
    return {
        "success": True,
        "data": {
            "reserva": validator.get_estados_reserva(),
            "pagamento": validator.get_estados_pagamento(),
            "hospedagem": validator.get_estados_hospedagem()
        }
    }

@router.get("/cores-status", summary="Obter cores dos status")
async def get_cores_status():
    """Retorna mapeamento de cores para status"""
    validator = UnifiedStateValidator()
    
    return {
        "success": True,
        "data": {
            "reserva": {
                status: validator.get_cor_status(status, 'reserva')
                for status in validator.get_estados_reserva()
            },
            "pagamento": {
                status: validator.get_cor_status(status, 'pagamento')
                for status in validator.get_estados_pagamento()
            }
        }
    }
