from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.operacional_service import OperacionalService
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from app.core.exceptions import ValidationError


router = APIRouter(prefix="/operacional", tags=["visao-operacional"])


@router.get("/mapa-ocupacao/{data}")
async def obter_mapa_ocupacao(
    data: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mapa completo de ocupação para data específica
    Fundamental para operação diária do hotel
    """
    try:
        service = OperacionalService(db)
        mapa = service.obter_mapa_ocupacao(data)
        return mapa
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/mapa-ocupacao/hoje")
async def obter_mapa_ocupacao_hoje(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mapa de ocupação para hoje
    Atalho para consulta mais frequente
    """
    try:
        service = OperacionalService(db)
        mapa = service.obter_mapa_ocupacao(date.today())
        return mapa
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/movimentacao/{data}")
async def obter_movimentacao_diaria(
    data: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Relatório detalhado de movimentação do dia
    Check-ins, check-outs realizados e pendentes
    """
    try:
        service = OperacionalService(db)
        movimentacao = service.obter_movimentacao_diaria(data)
        return movimentacao
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/movimentacao/hoje")
async def obter_movimentacao_hoje(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Movimentação de hoje
    Dashboard operacional em tempo real
    """
    try:
        service = OperacionalService(db)
        movimentacao = service.obter_movimentacao_diaria(date.today())
        
        # Adicionar status em tempo real
        agora = datetime.now()
        movimentacao["atualizado_em"] = agora.strftime("%H:%M:%S")
        movimentacao["proxima_atualizacao"] = (agora + timedelta(minutes=15)).strftime("%H:%M")
        
        return movimentacao
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/taxa-ocupacao/{data_inicio}/{data_fim}")
async def obter_taxa_ocupacao_periodo(
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Análise de taxa de ocupação por período
    Fundamental para gestão de receita
    """
    try:
        service = OperacionalService(db)
        analise = service.obter_taxa_ocupacao_periodo(data_inicio, data_fim)
        return analise
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/taxa-ocupacao/mensal/{ano}/{mes}")
async def obter_taxa_ocupacao_mensal(
    ano: int,
    mes: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Taxa de ocupação mensal
    Análise consolidada por mês
    """
    try:
        if not (1 <= mes <= 12):
            raise ValidationError("Mês deve ser entre 1 e 12")
        
        # Primeiro e último dia do mês
        data_inicio = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = date(ano, mes + 1, 1) - timedelta(days=1)
        
        service = OperacionalService(db)
        analise = service.obter_taxa_ocupacao_periodo(data_inicio, data_fim)
        
        # Adicionar informações específicas do mês
        analise["mes"] = f"{mes:02d}/{ano}"
        analise["nome_mes"] = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ][mes - 1]
        
        return analise
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/previsao-ocupacao")
async def obter_previsao_ocupacao(
    dias_futuro: int = Query(30, ge=1, le=365, description="Dias de previsão (1-365)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Previsão de ocupação para os próximos dias
    Auxilia planejamento operacional
    """
    try:
        service = OperacionalService(db)
        previsao = service.obter_previsao_ocupacao(dias_futuro)
        return previsao
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/dashboard-gerencial")
async def obter_dashboard_gerencial(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Dashboard executivo com KPIs principais
    Restrito à gerência - Visão consolidada
    """
    try:
        service = OperacionalService(db)
        hoje = date.today()
        
        # Dados de hoje
        mapa_hoje = service.obter_mapa_ocupacao(hoje)
        movimentacao_hoje = service.obter_movimentacao_diaria(hoje)
        
        # Dados do mês atual
        primeiro_dia_mes = date(hoje.year, hoje.month, 1)
        taxa_mes = service.obter_taxa_ocupacao_periodo(primeiro_dia_mes, hoje)
        
        # Previsão próximos 7 dias
        previsao_semana = service.obter_previsao_ocupacao(7)
        
        # KPIs consolidados
        dashboard = {
            "data_atualizacao": hoje.isoformat(),
            "kpis_hoje": {
                "taxa_ocupacao": mapa_hoje["estatisticas"]["taxa_ocupacao"],
                "quartos_ocupados": mapa_hoje["estatisticas"]["quartos_ocupados"],
                "total_quartos": mapa_hoje["estatisticas"]["total_quartos"],
                "checkins_realizados": movimentacao_hoje["resumo"]["checkins_realizados"],
                "checkouts_realizados": movimentacao_hoje["resumo"]["checkouts_realizados"],
                "checkins_pendentes": movimentacao_hoje["resumo"]["checkins_pendentes"],
                "checkouts_pendentes": movimentacao_hoje["resumo"]["checkouts_pendentes"]
            },
            "performance_mes": {
                "taxa_ocupacao_media": taxa_mes["taxa_ocupacao_media"],
                "receita_total": taxa_mes["receita_total"],
                "receita_media_diaria": taxa_mes["receita_media_diaria"],
                "dias_analisados": taxa_mes["dias_analisados"]
            },
            "previsao_proxima_semana": {
                "total_chegadas": previsao_semana["total_chegadas_previstas"],
                "receita_prevista": previsao_semana["receita_total_prevista"],
                "alertas": previsao_semana["alertas"]
            },
            "alertas_operacionais": _gerar_alertas_operacionais(
                mapa_hoje, movimentacao_hoje, previsao_semana
            )
        }
        
        return dashboard
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


def _gerar_alertas_operacionais(mapa, movimentacao, previsao) -> list:
    """Gera alertas operacionais críticos"""
    alertas = []
    
    # Taxa de ocupação crítica
    if mapa["estatisticas"]["taxa_ocupacao"] < 30:
        alertas.append({
            "tipo": "OCUPACAO_BAIXA",
            "mensagem": f"Taxa de ocupação baixa: {mapa['estatisticas']['taxa_ocupacao']}%",
            "prioridade": "MEDIA"
        })
    elif mapa["estatisticas"]["taxa_ocupacao"] > 95:
        alertas.append({
            "tipo": "OCUPACAO_ALTA",
            "mensagem": f"Ocupação quase lotada: {mapa['estatisticas']['taxa_ocupacao']}%",
            "prioridade": "ALTA"
        })
    
    # Check-ins pendentes
    if movimentacao["resumo"]["checkins_pendentes"] > 5:
        alertas.append({
            "tipo": "CHECKINS_PENDENTES",
            "mensagem": f"{movimentacao['resumo']['checkins_pendentes']} check-ins pendentes",
            "prioridade": "ALTA"
        })
    
    # Check-outs pendentes
    if movimentacao["resumo"]["checkouts_pendentes"] > 3:
        alertas.append({
            "tipo": "CHECKOUTS_PENDENTES", 
            "mensagem": f"{movimentacao['resumo']['checkouts_pendentes']} check-outs pendentes",
            "prioridade": "MEDIA"
        })
    
    # Alertas de previsão
    for alerta_previsao in previsao["alertas"]:
        alertas.append({
            "tipo": "PREVISAO",
            "mensagem": alerta_previsao,
            "prioridade": "BAIXA"
        })
    
    return alertas


@router.get("/relatorio-receita/{data_inicio}/{data_fim}")
async def obter_relatorio_receita(
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Relatório detalhado de receita por período
    Análise financeira - Restrito à gerência
    """
    try:
        service = OperacionalService(db)
        
        # Análise de ocupação (que já inclui receita)
        analise_ocupacao = service.obter_taxa_ocupacao_periodo(data_inicio, data_fim)
        
        # Calcular métricas adicionais
        dias_periodo = (data_fim - data_inicio).days + 1
        
        # RevPAR (Revenue Per Available Room)
        total_quartos = analise_ocupacao["ocupacao_diaria"][0]["quartos_disponiveis"] if analise_ocupacao["ocupacao_diaria"] else 1
        quartos_disponiveis_periodo = total_quartos * dias_periodo
        revpar = analise_ocupacao["receita_total"] / quartos_disponiveis_periodo if quartos_disponiveis_periodo > 0 else 0
        
        # ADR (Average Daily Rate)
        quartos_ocupados_periodo = analise_ocupacao["quartos_noite_ocupadas"]
        adr = analise_ocupacao["receita_total"] / quartos_ocupados_periodo if quartos_ocupados_periodo > 0 else 0
        
        relatorio_receita = {
            **analise_ocupacao,
            "metricas_receita": {
                "revpar": round(revpar, 2),
                "adr": round(adr, 2),
                "quartos_disponiveis_periodo": quartos_disponiveis_periodo,
                "quartos_ocupados_periodo": quartos_ocupados_periodo
            },
            "analise_performance": {
                "receita_por_dia_semana": _calcular_receita_por_dia_semana(analise_ocupacao["ocupacao_diaria"]),
                "melhor_semana": _identificar_melhor_semana(analise_ocupacao["ocupacao_diaria"])
            }
        }
        
        return relatorio_receita
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


def _calcular_receita_por_dia_semana(ocupacao_diaria):
    """Calcula receita média por dia da semana"""
    receita_por_dia = {}
    
    for dia in ocupacao_diaria:
        dia_semana = dia["dia_semana"]
        receita = dia["receita"]
        
        if dia_semana not in receita_por_dia:
            receita_por_dia[dia_semana] = {"total": 0, "dias": 0}
        
        receita_por_dia[dia_semana]["total"] += receita
        receita_por_dia[dia_semana]["dias"] += 1
    
    return {
        dia: {
            "receita_total": dados["total"],
            "receita_media": round(dados["total"] / dados["dias"], 2) if dados["dias"] > 0 else 0,
            "dias_analisados": dados["dias"]
        }
        for dia, dados in receita_por_dia.items()
    }


def _identificar_melhor_semana(ocupacao_diaria):
    """Identifica a semana com melhor performance"""
    if len(ocupacao_diaria) < 7:
        return None
    
    melhor_receita = 0
    melhor_semana = None
    
    # Analisar janelas de 7 dias
    for i in range(len(ocupacao_diaria) - 6):
        semana = ocupacao_diaria[i:i+7]
        receita_semana = sum(dia["receita"] for dia in semana)
        
        if receita_semana > melhor_receita:
            melhor_receita = receita_semana
            melhor_semana = {
                "inicio": semana[0]["data"],
                "fim": semana[6]["data"],
                "receita_total": receita_semana,
                "receita_media_dia": round(receita_semana / 7, 2),
                "ocupacao_media": round(sum(dia["taxa_ocupacao"] for dia in semana) / 7, 1)
            }
    
    return melhor_semana
