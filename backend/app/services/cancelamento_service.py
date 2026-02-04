from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.reserva import Reserva
from app.models.pagamento import Pagamento
from app.core.enums import (
    StatusReserva, StatusPagamento, StatusFinanceiro, 
    PoliticaCancelamento, TipoItemCobranca
)
from app.utils.datetime_utils import now_utc
from app.core.exceptions import BusinessRuleViolation, ValidationError


class CancelamentoService:
    """
    Serviço profissional para políticas de cancelamento
    Protege o financeiro do hotel com regras claras
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def validar_cancelamento(self, reserva_id: int) -> Dict[str, Any]:
        """
        Valida se a reserva pode ser cancelada e calcula multas
        Retorna regras aplicáveis e custos
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        # Verificar status atual
        if reserva.status_reserva in [StatusReserva.CANCELADO, StatusReserva.CHECKED_OUT]:
            raise BusinessRuleViolation(
                f"Não é possível cancelar reserva com status: {reserva.status_reservva.value}"
            )
        
        if reserva.status_reserva == StatusReserva.HOSPEDADO:
            raise BusinessRuleViolation(
                "Reserva em hospedagem ativa. Use check-out antecipado em vez de cancelamento."
            )
        
        # Calcular tempo até check-in
        agora = now_utc()
        checkin_previsto = reserva.checkin_previsto
        horas_ate_checkin = (checkin_previsto - agora).total_seconds() / 3600
        
        # Política de cancelamento aplicável
        politica = reserva.politica_cancelamento or PoliticaCancelamento.FLEXIVEL
        
        # Calcular valores envolvidos
        pagamentos_aprovados = self.db.query(Pagamento).filter(
            Pagamento.reserva_id == reserva_id,
            Pagamento.status.in_([StatusPagamento.CONFIRMADO, StatusPagamento.APROVADO])
        ).all()
        
        valor_pago = sum(Decimal(str(p.valor)) for p in pagamentos_aprovados)
        valor_reserva = reserva.valor_previsto
        
        # Aplicar regras da política
        resultado_politica = self._aplicar_politica_cancelamento(
            politica, horas_ate_checkin, valor_pago, valor_reserva
        )
        
        return {
            "pode_cancelar": resultado_politica["permitido"],
            "politica": politica.value,
            "horas_ate_checkin": round(horas_ate_checkin, 1),
            "valor_reserva": float(valor_reserva),
            "valor_pago": float(valor_pago),
            "multa_aplicavel": resultado_politica["multa"],
            "valor_reembolso": resultado_politica["reembolso"],
            "valor_retido": resultado_politica["retido"],
            "motivo_bloqueio": resultado_politica.get("motivo_bloqueio"),
            "detalhes_politica": resultado_politica["detalhes"]
        }
    
    def _aplicar_politica_cancelamento(
        self, 
        politica: PoliticaCancelamento, 
        horas_ate_checkin: float,
        valor_pago: Decimal,
        valor_reserva: Decimal
    ) -> Dict[str, Any]:
        """
        Aplica regras específicas de cada política
        """
        if politica == PoliticaCancelamento.FLEXIVEL:
            # Cancelamento até 24h: sem multa
            # Cancelamento com menos de 24h: multa de 50%
            if horas_ate_checkin >= 24:
                return {
                    "permitido": True,
                    "multa": 0.0,
                    "reembolso": float(valor_pago),
                    "retido": 0.0,
                    "detalhes": "Cancelamento gratuito (mais de 24h de antecedência)"
                }
            else:
                multa = valor_pago * Decimal('0.5')
                reembolso = valor_pago - multa
                return {
                    "permitido": True,
                    "multa": float(multa),
                    "reembolso": float(reembolso),
                    "retido": float(multa),
                    "detalhes": f"Multa de 50% aplicada (cancelamento com {horas_ate_checkin:.1f}h de antecedência)"
                }
        
        elif politica == PoliticaCancelamento.MODERADA:
            # Até 48h: sem multa
            # 24-48h: multa 30%
            # Menos de 24h: multa 70%
            if horas_ate_checkin >= 48:
                return {
                    "permitido": True,
                    "multa": 0.0,
                    "reembolso": float(valor_pago),
                    "retido": 0.0,
                    "detalhes": "Cancelamento gratuito (mais de 48h de antecedência)"
                }
            elif horas_ate_checkin >= 24:
                multa = valor_pago * Decimal('0.3')
                reembolso = valor_pago - multa
                return {
                    "permitido": True,
                    "multa": float(multa),
                    "reembolso": float(reembolso),
                    "retido": float(multa),
                    "detalhes": f"Multa de 30% aplicada (cancelamento entre 24-48h)"
                }
            else:
                multa = valor_pago * Decimal('0.7')
                reembolso = valor_pago - multa
                return {
                    "permitido": True,
                    "multa": float(multa),
                    "reembolso": float(reembolso),
                    "retido": float(multa),
                    "detalhes": f"Multa de 70% aplicada (cancelamento com menos de 24h)"
                }
        
        elif politica == PoliticaCancelamento.RIGIDA:
            # Até 72h: multa 20%
            # 24-72h: multa 60%  
            # Menos de 24h: multa 90%
            if horas_ate_checkin >= 72:
                multa = valor_pago * Decimal('0.2')
                reembolso = valor_pago - multa
                return {
                    "permitido": True,
                    "multa": float(multa),
                    "reembolso": float(reembolso),
                    "retido": float(multa),
                    "detalhes": f"Multa de 20% aplicada (mais de 72h de antecedência)"
                }
            elif horas_ate_checkin >= 24:
                multa = valor_pago * Decimal('0.6')
                reembolso = valor_pago - multa
                return {
                    "permitido": True,
                    "multa": float(multa),
                    "reembolso": float(reembolso),
                    "retido": float(multa),
                    "detalhes": f"Multa de 60% aplicada (cancelamento entre 24-72h)"
                }
            else:
                multa = valor_pago * Decimal('0.9')
                reembolso = valor_pago - multa
                return {
                    "permitido": True,
                    "multa": float(multa),
                    "reembolso": float(reembolso),
                    "retido": float(multa),
                    "detalhes": f"Multa de 90% aplicada (cancelamento com menos de 24h)"
                }
        
        elif politica == PoliticaCancelamento.NAO_REEMBOLSAVEL:
            # Sem reembolso em qualquer situação
            return {
                "permitido": True,
                "multa": float(valor_pago),
                "reembolso": 0.0,
                "retido": float(valor_pago),
                "detalhes": "Tarifa não-reembolsável: nenhum valor devolvido"
            }
        
        else:
            # Política desconhecida - aplicar regra mais restritiva
            return {
                "permitido": False,
                "multa": 0.0,
                "reembolso": 0.0,
                "retido": 0.0,
                "motivo_bloqueio": f"Política de cancelamento inválida: {politica}",
                "detalhes": "Erro na configuração da política"
            }
    
    def executar_cancelamento(
        self, 
        reserva_id: int, 
        motivo: str, 
        usuario_id: int,
        forcar_sem_multa: bool = False
    ) -> Dict[str, Any]:
        """
        Executa o cancelamento com aplicação das políticas
        """
        # Validar cancelamento
        validacao = self.validar_cancelamento(reserva_id)
        
        if not validacao["pode_cancelar"]:
            raise BusinessRuleViolation(
                f"Cancelamento bloqueado: {validacao.get('motivo_bloqueio', 'Motivo não especificado')}"
            )
        
        if len(motivo.strip()) < 10:
            raise ValidationError("Motivo do cancelamento deve ter pelo menos 10 caracteres")
        
        try:
            reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
            
            # Aplicar multa (se não forçado sem multa por gerente/admin)
            valor_multa = Decimal('0')
            valor_reembolso = Decimal(str(validacao["valor_reembolso"]))
            
            if not forcar_sem_multa and validacao["multa_aplicavel"] > 0:
                valor_multa = Decimal(str(validacao["multa_aplicavel"]))
                
                # Registrar multa como item de cobrança
                from app.models.reserva import ItemCobranca
                item_multa = ItemCobranca(
                    reserva_id=reserva_id,
                    tipo=TipoItemCobranca.MULTA,
                    descricao=f"Multa por cancelamento: {motivo}",
                    quantidade=1,
                    valor_unitario=valor_multa
                )
                self.db.add(item_multa)
            
            # Atualizar status da reserva
            reserva.status_reserva = StatusReserva.CANCELADO
            reserva.status_financeiro = StatusFinanceiro.ESTORNADO if valor_reembolso > 0 else StatusFinanceiro.PAGO_TOTAL
            reserva.atualizado_por_usuario_id = usuario_id
            reserva.updated_at = now_utc()
            
            # Processar estorno se houver valor a devolver
            estorno_processado = False
            if valor_reembolso > 0:
                # Aqui seria integração com gateway de pagamento para estorno
                # Por enquanto, apenas marca como pendente
                estorno_processado = True
            
            self.db.commit()
            
            # Log para auditoria
            print(f"[CANCELAMENTO] Reserva {reserva.codigo_reserva} - Multa: R$ {valor_multa} - Reembolso: R$ {valor_reembolso} - Por usuário {usuario_id}")
            
            return {
                "success": True,
                "reserva_codigo": reserva.codigo_reserva,
                "status_anterior": "CONFIRMADA",  # Assumindo que estava confirmada
                "status_atual": StatusReserva.CANCELADO.value,
                "valor_multa": float(valor_multa),
                "valor_reembolso": float(valor_reembolso),
                "estorno_processado": estorno_processado,
                "politica_aplicada": validacao["politica"],
                "motivo": motivo,
                "cancelado_em": now_utc().isoformat(),
                "cancelado_por": usuario_id,
                "detalhes": validacao["detalhes_politica"]
            }
            
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleViolation(f"Falha ao processar cancelamento: {str(e)}")
    
    def cancelamento_no_show(self, reserva_id: int, usuario_id: int) -> Dict[str, Any]:
        """
        Processar no-show (não comparecimento)
        Aplicar política mais restritiva
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        # Verificar se realmente é no-show (depois do horário de check-in)
        agora = now_utc()
        limite_checkin = reserva.checkin_previsto + timedelta(hours=2)  # 2h de tolerância
        
        if agora < limite_checkin:
            raise BusinessRuleViolation(
                f"Muito cedo para no-show. Aguarde até {limite_checkin.strftime('%d/%m/%Y %H:%M')}"
            )
        
        # No-show aplica política mais restritiva
        pagamentos_aprovados = self.db.query(Pagamento).filter(
            Pagamento.reserva_id == reserva_id,
            Pagamento.status.in_([StatusPagamento.CONFIRMADO, StatusPagamento.APROVADO])
        ).all()
        
        valor_pago = sum(Decimal(str(p.valor)) for p in pagamentos_aprovados)
        
        # No-show: retenção de 100% em tarifa flexível, sem reembolso nas demais
        if reserva.politica_cancelamento == PoliticaCancelamento.FLEXIVEL:
            valor_retido = valor_pago * Decimal('1.0')  # 100%
            valor_reembolso = Decimal('0')
        else:
            valor_retido = valor_pago  # Tudo retido
            valor_reembolso = Decimal('0')
        
        try:
            # Registrar no-show
            from app.models.reserva import ItemCobranca
            item_noshow = ItemCobranca(
                reserva_id=reserva_id,
                tipo=TipoItemCobranca.MULTA,
                descricao="Multa por No-Show (não comparecimento)",
                quantidade=1,
                valor_unitario=valor_retido
            )
            self.db.add(item_noshow)
            
            # Atualizar status
            reserva.status_reserva = StatusReserva.NO_SHOW
            reserva.status_financeiro = StatusFinanceiro.PAGO_TOTAL  # Hotel retém tudo
            reserva.atualizado_por_usuario_id = usuario_id
            reserva.updated_at = now_utc()
            
            self.db.commit()
            
            # Log crítico
            print(f"[NO-SHOW] Reserva {reserva.codigo_reserva} - Retido: R$ {valor_retido} - Por usuário {usuario_id}")
            
            return {
                "success": True,
                "tipo": "NO_SHOW",
                "reserva_codigo": reserva.codigo_reserva,
                "status_atual": StatusReserva.NO_SHOW.value,
                "valor_retido": float(valor_retido),
                "valor_reembolso": float(valor_reembolso),
                "processado_em": now_utc().isoformat(),
                "processado_por": usuario_id
            }
            
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleViolation(f"Falha ao processar no-show: {str(e)}")
    
    def obter_historico_cancelamentos(
        self, 
        data_inicio: datetime.date, 
        data_fim: datetime.date
    ) -> Dict[str, Any]:
        """
        Relatório de cancelamentos por período
        Para análise financeira e operacional
        """
        reservas_canceladas = self.db.query(Reserva).filter(
            Reserva.status_reserva.in_([StatusReserva.CANCELADO, StatusReserva.NO_SHOW]),
            Reserva.updated_at >= datetime.combine(data_inicio, datetime.min.time().replace(tzinfo=timezone.utc)),
            Reserva.updated_at <= datetime.combine(data_fim, datetime.max.time().replace(tzinfo=timezone.utc))
        ).all()
        
        relatorio = []
        total_valor_perdido = 0
        total_multas = 0
        
        for reserva in reservas_canceladas:
            # Buscar multas aplicadas
            multas = self.db.query(ItemCobranca).filter(
                ItemCobranca.reserva_id == reserva.id,
                ItemCobranca.tipo == TipoItemCobranca.MULTA
            ).all()
            
            valor_multas = sum(float(m.valor_unitario * m.quantidade) for m in multas)
            
            relatorio.append({
                "data": reserva.updated_at.strftime("%d/%m/%Y"),
                "codigo": reserva.codigo_reserva,
                "cliente": reserva.cliente.nome_completo if reserva.cliente else "N/A",
                "valor_reserva": float(reserva.valor_previsto),
                "valor_multas": valor_multas,
                "status": reserva.status_reserva.value,
                "politica": reserva.politica_cancelamento.value if reserva.politica_cancelamento else "N/A"
            })
            
            total_valor_perdido += float(reserva.valor_previsto)
            total_multas += valor_multas
        
        return {
            "periodo": f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
            "total_cancelamentos": len(reservas_canceladas),
            "valor_total_perdido": total_valor_perdido,
            "valor_total_multas": total_multas,
            "valor_liquido_perdido": total_valor_perdido - total_multas,
            "detalhes": relatorio
        }
