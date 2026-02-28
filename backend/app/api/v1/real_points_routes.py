from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.services.real_points_service import RealPointsService

router = APIRouter(prefix="/real-points", tags=["real-points"])

@router.get("/tabela")
async def obter_tabela_oficial():
    """Obter tabela oficial de pontos"""
    return RealPointsService.get_tabela_oficial()

@router.get("/premios")
async def listar_premios():
    """Listar prêmios disponíveis"""
    return RealPointsService.listar_premios()

@router.get("/premios/{premio_id}")
async def obter_premio(premio_id: str):
    """Obter prêmio específico"""
    premio = RealPointsService.get_premio(premio_id)
    if not premio:
        raise HTTPException(status_code=404, detail="Prêmio não encontrado")
    return premio

@router.post("/calcular")
async def calcular_pontos(
    suite: str,
    diarias: int,
    valor_total: float
):
    """Calcular pontos para uma reserva"""
    rp, detalhe = RealPointsService.calcular_rp_oficial(suite, diarias, valor_total)
    return {
        "suite": suite,
        "diarias": diarias,
        "valor_total": valor_total,
        "rp_calculados": rp,
        "detalhe": detalhe
    }

@router.post("/simular")
async def simular_calculo(
    suite: str,
    diarias: int,
    valor_total: float
):
    """Simular cálculo completo com validações"""
    return RealPointsService.simular_calculo(suite, diarias, valor_total)

@router.post("/validar-requisitos")
async def validar_requisitos(reserva: Dict[str, Any]):
    """Validar requisitos oficiais para concessão de pontos"""
    pode, motivo = RealPointsService.validar_requisitos_oficiais(reserva)
    return {
        "pode_conceder": pode,
        "motivo": motivo
    }

@router.post("/validar-antifraude")
async def validar_antifraude(reserva: Dict[str, Any]):
    """Validar antifraude"""
    valido, motivo = RealPointsService.validar_antifraude(reserva)
    return {
        "valido": valido,
        "motivo": motivo
    }

@router.post("/pode-resgatar")
async def pode_resgatar_premio(
    cliente_rp: int,
    premio_id: str
):
    """Verificar se cliente pode resgatar prêmio"""
    pode, motivo = RealPointsService.pode_resgatar_premio(cliente_rp, premio_id)
    return {
        "pode_resgatar": pode,
        "motivo": motivo
    }
