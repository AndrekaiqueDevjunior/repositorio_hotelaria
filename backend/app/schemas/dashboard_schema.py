from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict


class DashboardResponse(BaseModel):
    success: bool
    timestamp: datetime
    kpis_principais: Dict[str, Any]
    operacoes_dia: Dict[str, Any]
    sistema_pontos: Dict[str, Any]
    segmentacao_clientes: Dict[str, Any]
    top_clientes: Dict[str, Any]
    distribuicao_quartos: Dict[str, Any]
    antifraude: Dict[str, Any]
    tendencias: Dict[str, Any]
    alertas: Dict[str, Any]
