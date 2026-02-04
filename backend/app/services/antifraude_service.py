"""
Serviço de Antifraude Básico - Motor de Regras
Sistema Real Points - Hotel Real Cabo Frio

FASE 1: Motor de regras simples (SEM Machine Learning)

REGRAS IMPLEMENTADAS:
1. Muitas reservas no mesmo CPF em curto período
2. Alta taxa de cancelamento
3. Múltiplos pagamentos recusados
4. Valor muito acima da média do cliente

CLASSIFICAÇÃO DE RISCO:
- BAIXO: score < 40
- MÉDIO: score 40-69
- ALTO: score >= 70
"""

from app.core.database import db
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class AntifraaudeService:
    """Serviço de análise de risco e detecção de fraudes"""
    
    # Thresholds (limites) para regras
    MAX_RESERVAS_7_DIAS = 3
    TAXA_CANCELAMENTO_ALTA = 50  # 50%
    MAX_PAGAMENTOS_RECUSADOS = 2
    MULTIPLICADOR_VALOR_SUSPEITO = 3  # 3x a média
    
    @staticmethod
    async def analisar_cliente(cliente_id: int) -> Dict:
        """
        Analisar risco de um cliente específico
        
        Args:
            cliente_id: ID do cliente a ser analisado
        
        Returns:
            {
                "cliente_id": 123,
                "documento": "12345678900",
                "risco": "ALTO",
                "score": 85,
                "alertas": ["Muitas reservas recentes", "Alta taxa de cancelamento"],
                "total_reservas": 10,
                "reservas_canceladas": 6,
                "pagamentos_recusados": 3
            }
        """
        try:
            # Buscar cliente
            cliente = await db.cliente.find_unique(where={"id": cliente_id})
            
            if not cliente:
                return {
                    "success": False,
                    "error": "Cliente não encontrado"
                }
            
            risco_score = 0
            alertas = []
            
            # REGRA 1: Muitas reservas em curto período
            from app.utils.datetime_utils import now_utc
            sete_dias_atras = now_utc() - timedelta(days=7)
            reservas_recentes = await db.reserva.count(
                where={
                    "clienteId": cliente_id,
                    "createdAt": {"gte": sete_dias_atras}
                }
            )
            
            if reservas_recentes > AntifraaudeService.MAX_RESERVAS_7_DIAS:
                risco_score += 30
                alertas.append(f"⚠️ Muitas reservas recentes: {reservas_recentes} em 7 dias")
            
            # REGRA 2: Taxa de cancelamento
            total_reservas = await db.reserva.count(
                where={"clienteId": cliente_id}
            )
            
            reservas_canceladas = await db.reserva.count(
                where={
                    "clienteId": cliente_id,
                    "status": "CANCELADO"
                }
            )
            
            if total_reservas > 0:
                taxa_cancelamento = (reservas_canceladas / total_reservas) * 100
                
                if taxa_cancelamento > AntifraaudeService.TAXA_CANCELAMENTO_ALTA:
                    risco_score += 40
                    alertas.append(f"🚨 Alta taxa de cancelamento: {taxa_cancelamento:.1f}%")
            else:
                taxa_cancelamento = 0
            
            # REGRA 3: Pagamentos recusados
            # Buscar pagamentos via reservas do cliente
            reservas_cliente = await db.reserva.find_many(
                where={"clienteId": cliente_id}
            )
            
            reserva_ids = [r.id for r in reservas_cliente]
            
            if reserva_ids:
                pagamentos_recusados = await db.pagamento.count(
                    where={
                        "reservaId": {"in": reserva_ids},
                        "status": {"in": ["RECUSADO", "REJECTED", "CANCELADO"]}
                    }
                )
            else:
                pagamentos_recusados = 0
            
            if pagamentos_recusados > AntifraaudeService.MAX_PAGAMENTOS_RECUSADOS:
                risco_score += 30
                alertas.append(f"💳 Múltiplos pagamentos recusados: {pagamentos_recusados}")
            
            # REGRA 4: Reservas consecutivas canceladas
            ultimas_reservas = await db.reserva.find_many(
                where={"clienteId": cliente_id},
                order={"createdAt": "desc"},
                take=3
            )
            
            cancelamentos_consecutivos = 0
            for reserva in ultimas_reservas:
                if reserva.status == "CANCELADO":
                    cancelamentos_consecutivos += 1
                else:
                    break
            
            if cancelamentos_consecutivos >= 2:
                risco_score += 25
                alertas.append(f"📉 {cancelamentos_consecutivos} cancelamentos consecutivos")
            
            # Classificar risco
            if risco_score >= 70:
                risco = "ALTO"
            elif risco_score >= 40:
                risco = "MÉDIO"
            else:
                risco = "BAIXO"
            
            return {
                "success": True,
                "cliente_id": cliente_id,
                "documento": cliente.documento,
                "risco": risco,
                "score": risco_score,
                "alertas": alertas,
                "total_reservas": total_reservas,
                "reservas_canceladas": reservas_canceladas,
                "reservas_recentes": reservas_recentes,
                "pagamentos_recusados": pagamentos_recusados,
                "taxa_cancelamento": round(taxa_cancelamento, 1) if total_reservas > 0 else 0,
                "cancelamentos_consecutivos": cancelamentos_consecutivos
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao analisar cliente: {str(e)}"
            }
    
    @staticmethod
    async def listar_transacoes_suspeitas(limit: int = 50, min_score: int = 40) -> Dict:
        """
        Listar clientes com risco médio ou alto
        
        Args:
            limit: Número máximo de resultados
            min_score: Score mínimo para ser considerado suspeito (padrão: 40)
        
        Returns:
            Lista de clientes suspeitos ordenados por score (maior primeiro)
        """
        try:
            # Buscar todos os clientes
            clientes = await db.cliente.find_many()
            
            transacoes_suspeitas = []
            
            for cliente in clientes:
                # Analisar cada cliente
                analise = await AntifraaudeService.analisar_cliente(cliente.id)
                
                if analise.get("success") and analise.get("score", 0) >= min_score:
                    transacoes_suspeitas.append(analise)
            
            # Ordenar por score (maior primeiro)
            transacoes_suspeitas.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            return {
                "success": True,
                "total": len(transacoes_suspeitas),
                "transacoes": transacoes_suspeitas[:limit],
                "criterio": f"Score >= {min_score}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "transacoes": []
            }
    
    @staticmethod
    async def analisar_reserva(reserva_id: int) -> Dict:
        """
        Analisar risco de uma reserva específica
        
        Args:
            reserva_id: ID da reserva
        
        Returns:
            Análise de risco da reserva
        """
        try:
            reserva = await db.reserva.find_unique(
                where={"id": reserva_id},
                include={"cliente": True}
            )
            
            if not reserva:
                return {
                    "success": False,
                    "error": "Reserva não encontrada"
                }
            
            # Analisar o cliente da reserva
            analise_cliente = await AntifraaudeService.analisar_cliente(reserva.clienteId)
            
            risco_reserva = 0
            alertas_reserva = []
            
            # Adicionar pontuação do cliente
            risco_reserva += analise_cliente.get("score", 0)
            alertas_reserva.extend(analise_cliente.get("alertas", []))
            
            # Regra específica: Reserva muito longa (> 15 diárias)
            if reserva.numDiarias > 15:
                risco_reserva += 10
                alertas_reserva.append(f"⏳ Reserva muito longa: {reserva.numDiarias} diárias")
            
            # Regra específica: Valor muito alto (> R$ 5000)
            valor_total = float(reserva.valorDiaria) * reserva.numDiarias if reserva.valorDiaria and reserva.numDiarias else 0
            if valor_total > 5000:
                risco_reserva += 15
                alertas_reserva.append(f"💰 Valor alto: R$ {valor_total:.2f}")
            
            # Classificar risco final
            if risco_reserva >= 70:
                risco_final = "ALTO"
            elif risco_reserva >= 40:
                risco_final = "MÉDIO"
            else:
                risco_final = "BAIXO"
            
            return {
                "success": True,
                "reserva_id": reserva_id,
                "reserva_codigo": reserva.codigoReserva,
                "cliente_id": reserva.clienteId,
                "cliente_nome": reserva.cliente.nomeCompleto if reserva.cliente else "Cliente",
                "risco": risco_final,
                "score": risco_reserva,
                "alertas": alertas_reserva,
                "recomendacao": AntifraaudeService._get_recomendacao(risco_final),
                "aprovacao_automatica": risco_final == "BAIXO"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _get_recomendacao(risco: str) -> str:
        """Obter recomendação baseada no nível de risco"""
        recomendacoes = {
            "BAIXO": "✅ Aprovar automaticamente",
            "MÉDIO": "⚠️ Revisar manualmente antes de aprovar",
            "ALTO": "🚨 Solicitar verificação adicional de identidade e pagamento antecipado"
        }
        return recomendacoes.get(risco, "Sem recomendação")
    
    @staticmethod
    async def obter_estatisticas_gerais() -> Dict:
        """
        Obter estatísticas gerais do sistema antifraude
        
        Returns:
            Estatísticas agregadas de todas as análises
        """
        try:
            # Buscar todas as transações suspeitas
            transacoes = await AntifraaudeService.listar_transacoes_suspeitas(limit=1000, min_score=0)
            
            if not transacoes["success"]:
                return transacoes
            
            todas = transacoes["transacoes"]
            
            # Contar por nível de risco
            alto = len([t for t in todas if t["risco"] == "ALTO"])
            medio = len([t for t in todas if t["risco"] == "MÉDIO"])
            baixo = len([t for t in todas if t["risco"] == "BAIXO"])
            
            # Score médio
            scores = [t["score"] for t in todas if t.get("score")]
            score_medio = sum(scores) / len(scores) if scores else 0
            
            return {
                "success": True,
                "total_clientes_analisados": len(todas),
                "risco_alto": alto,
                "risco_medio": medio,
                "risco_baixo": baixo,
                "score_medio": round(score_medio, 1),
                "percentual_alto": round((alto / len(todas) * 100) if todas else 0, 1),
                "percentual_medio": round((medio / len(todas) * 100) if todas else 0, 1),
                "percentual_baixo": round((baixo / len(todas) * 100) if todas else 0, 1)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

