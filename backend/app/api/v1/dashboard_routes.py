"""
Rotas do Dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from prisma import Client
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/dashboard/stats")
async def obter_estatisticas_dashboard(
    db: Client = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obter estatísticas do dashboard para usuários autenticados"""
    try:
        from datetime import date
        
        # Data atual
        hoje = date.today()
        inicio_hoje = datetime.combine(hoje, datetime.min.time())
        
        # KPIs principais
        total_reservas = await db.reserva.count()
        total_clientes = await db.cliente.count()
        total_quartos = await db.quarto.count()
        
        # Taxa de ocupação
        quartos_ocupados = await db.quarto.count(where={'status': 'OCUPADO'})
        taxa_ocupacao = (quartos_ocupados / total_quartos * 100) if total_quartos > 0 else 0
        
        # Receita total (soma de pagamentos confirmados/aprovados)
        pagamentos_aprovados = await db.pagamento.find_many(
            where={'statusPagamento': {'in': ['CONFIRMADO', 'APROVADO']}}
        )
        receita_total = sum(float(p.valor) for p in pagamentos_aprovados)
        
        # Operações do dia
        checkins_hoje = await db.reserva.count(
            where={
                'checkinReal': {'gte': inicio_hoje}
            }
        )
        checkouts_hoje = await db.reserva.count(
            where={
                'checkoutReal': {'gte': inicio_hoje}
            }
        )
        reservas_ativas = await db.reserva.count(
            where={'statusReserva': {'in': ['CONFIRMADA', 'HOSPEDADO', 'CHECKIN_REALIZADO', 'EM_ANDAMENTO']}}
        )
        
        # Contagens adicionais - 3 categorias distintas
        reservas_pendentes = await db.reserva.count(
            where={
                'statusReserva': {'in': ['PENDENTE', 'PENDENTE_PAGAMENTO', 'AGUARDANDO_COMPROVANTE', 'EM_ANALISE', 'PAGA_REJEITADA']}
            }
        )
        
        reservas_ativas = await db.reserva.count(
            where={
                'statusReserva': {'in': ['CONFIRMADA', 'HOSPEDADO', 'CHECKIN_REALIZADO', 'EM_ANDAMENTO']}
            }
        )
        
        reservas_finalizadas = await db.reserva.count(
            where={
                'statusReserva': {'in': ['CHECKOUT_REALIZADO', 'CHECKED_OUT', 'CANCELADA', 'CANCELADO', 'FINALIZADA', 'NO_SHOW']}
            }
        )
        
        total_quartos = await db.quarto.count()
        total_comprovantes = await db.comprovantepagamento.count()
        comprovantes_aguardando = await db.comprovantepagamento.count(
            where={"statusValidacao": "AGUARDANDO_COMPROVANTE"}
        )
        comprovantes_em_analise = await db.comprovantepagamento.count(
            where={"statusValidacao": "EM_ANALISE"}
        )

        # Formato esperado pelo frontend (compatibilidade dupla)
        response = {
            "success": True,
            "kpis_principais": {
                "total_clientes": total_clientes,
                "total_reservas": total_reservas,
                "total_quartos": total_quartos,
                "taxa_ocupacao": round(taxa_ocupacao, 1),
                "receita_total": round(receita_total, 2),
                "reservas_pendentes": reservas_pendentes,
                "reservas_ativas": reservas_ativas,
                "reservas_finalizadas": reservas_finalizadas,
                "total_comprovantes": total_comprovantes,
                "comprovantes_aguardando": comprovantes_aguardando,
                "comprovantes_em_analise": comprovantes_em_analise,
            },
            "operacoes_dia": {
                "checkins_hoje": checkins_hoje,
                "checkouts_hoje": checkouts_hoje,
                "reservas_ativas": reservas_ativas,
                "quartos_ocupados": quartos_ocupados
            },
            "graficos": {
                "reservas_por_status": {
                    "PENDENTE": await db.reserva.count(where={'statusReserva': {'in': ['PENDENTE', 'PENDENTE_PAGAMENTO', 'AGUARDANDO_COMPROVANTE', 'EM_ANALISE']}}),
                    "CONFIRMADA": await db.reserva.count(where={'statusReserva': 'CONFIRMADA'}),
                    "ATIVA": await db.reserva.count(where={'statusReserva': {'in': ['HOSPEDADO', 'CHECKIN_REALIZADO', 'EM_ANDAMENTO']}}),
                    "FINALIZADA": await db.reserva.count(where={'statusReserva': {'in': ['CHECKOUT_REALIZADO', 'CHECKED_OUT', 'FINALIZADA']}}),
                    "CANCELADA": await db.reserva.count(where={'statusReserva': {'in': ['CANCELADA', 'CANCELADO', 'NO_SHOW']}})
                },
                "pagamentos_por_status": {
                    "CONFIRMADO": await db.pagamento.count(where={'statusPagamento': {'in': ['CONFIRMADO', 'APROVADO']}}),
                    "PENDENTE": await db.pagamento.count(where={'statusPagamento': 'PENDENTE'}),
                    "NEGADO": await db.pagamento.count(where={'statusPagamento': {'in': ['NEGADO', 'RECUSADO']}})
                },
                "quartos_por_status": {
                    "LIVRE": await db.quarto.count(where={'status': 'LIVRE'}),
                    "OCUPADO": quartos_ocupados,
                    "MANUTENCAO": await db.quarto.count(where={'status': 'MANUTENCAO'})
                }
            },
            "data_ultima_atualizacao": datetime.now().isoformat()
        }
        
        # Adicionar campo "data" para compatibilidade com formato antigo
        response["data"] = {
            "total_clientes": total_clientes,
            "total_reservas": total_reservas,
            "total_quartos": total_quartos,
            "taxa_ocupacao": round(taxa_ocupacao, 1),
            "receita_total": round(receita_total, 2),
            "checkins_hoje": checkins_hoje,
            "checkouts_hoje": checkouts_hoje,
            "reservas_pendentes": reservas_pendentes,
            "quartos_ocupados": quartos_ocupados,
            "quartos_disponiveis": total_quartos - quartos_ocupados,
            "reservas_confirmadas": reservas_ativas,
            "total_comprovantes": total_comprovantes,
            "comprovantes_aguardando": comprovantes_aguardando,
            "comprovantes_em_analise": comprovantes_em_analise,
            "reservas_ativas": reservas_ativas,
            "reservas_finalizadas": reservas_finalizadas,
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@router.get("/dashboard/stats/public")
async def obter_estatisticas_publicas(
    db: Client = Depends(get_db)
):
    """Obter estatísticas públicas (sem autenticação)"""
    try:
        # Estatísticas limitadas para público
        total_quartos = await db.quarto.count()
        quartos_livres = await db.quarto.count(where={'status': 'LIVRE'})
        quartos_ocupados = await db.quarto.count(where={'status': 'OCUPADO'})
        
        # Total de tipos de suíte
        tipos_suite = await db.quarto.find_many()
        suites_unicas = list(set(q.tipoSuite for q in tipos_suite))
        
        response = {
            "success": True,
            "kpis_principais": {
                "total_quartos": total_quartos,
                "quartos_disponiveis": quartos_livres,
                "taxa_ocupacao": round((quartos_ocupados / total_quartos * 100), 1) if total_quartos > 0 else 0
            },
            "info_publica": {
                "tipos_suite": len(suites_unicas),
                "quartos_livres": quartos_livres
            },
            "data_ultima_atualizacao": datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas públicas: {str(e)}")
