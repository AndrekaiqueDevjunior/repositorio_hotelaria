from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.reserva import Reserva
from app.models.pagamento import Pagamento
from app.core.enums import (
    StatusReserva, StatusPagamento, StatusFinanceiro, 
    MetodoPagamento, TipoItemCobranca
)
from app.utils.datetime_utils import now_utc
from app.core.exceptions import BusinessRuleViolation, ValidationError


class PagamentoRobustoService:
    """
    Serviço profissional para gerenciamento financeiro robusto
    Estados financeiros independentes do status da reserva
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calcular_status_financeiro(self, reserva_id: int) -> Dict[str, Any]:
        """
        Calcula status financeiro independente baseado em pagamentos
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        # Buscar todos os pagamentos aprovados
        pagamentos_aprovados = self.db.query(Pagamento).filter(
            and_(
                Pagamento.reserva_id == reserva_id,
                Pagamento.status.in_([StatusPagamento.CONFIRMADO, StatusPagamento.APROVADO])
            )
        ).all()
        
        valor_total_pago = sum(Decimal(str(p.valor)) for p in pagamentos_aprovados)
        valor_reserva = reserva.valor_previsto
        
        # Calcular percentual pago
        percentual_pago = (valor_total_pago / valor_reserva) * 100 if valor_reserva > 0 else 0
        
        # Determinar status financeiro
        if valor_total_pago == 0:
            status_financeiro = StatusFinanceiro.AGUARDANDO_PAGAMENTO
        elif valor_total_pago < valor_reserva * Decimal('0.3'):  # Menos de 30%
            status_financeiro = StatusFinanceiro.AGUARDANDO_PAGAMENTO
        elif valor_total_pago < valor_reserva:  # Entre 30% e 99%
            status_financeiro = StatusFinanceiro.SINAL_PAGO
        elif valor_total_pago >= valor_reserva:  # 100% ou mais
            status_financeiro = StatusFinanceiro.PAGO_TOTAL
        else:
            status_financeiro = StatusFinanceiro.AGUARDANDO_PAGAMENTO
        
        # Verificar se pode fazer check-in (mínimo 80% pago)
        pode_checkin = valor_total_pago >= (valor_reserva * Decimal('0.8'))
        
        return {
            "status_financeiro": status_financeiro,
            "valor_reserva": float(valor_reserva),
            "valor_pago": float(valor_total_pago),
            "valor_pendente": float(valor_reserva - valor_total_pago),
            "percentual_pago": float(percentual_pago),
            "pode_checkin": pode_checkin,
            "valor_minimo_checkin": float(valor_reserva * Decimal('0.8')),
            "pagamentos": [
                {
                    "id": p.id,
                    "valor": float(p.valor),
                    "metodo": p.metodo_pagamento.value,
                    "status": p.status.value,
                    "data": p.created_at.isoformat()
                }
                for p in pagamentos_aprovados
            ]
        }
    
    def processar_pagamento_sinal(
        self, 
        reserva_id: int, 
        valor_sinal: Decimal, 
        metodo: MetodoPagamento,
        dados_adicionais: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Processa pagamento de sinal (entrada)
        Valida se o valor é suficiente para garantir a reserva
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        if reserva.status_reserva == StatusReserva.CANCELADO:
            raise BusinessRuleViolation("Não é possível pagar reserva cancelada")
        
        # Validar valor mínimo do sinal (30% do valor total)
        valor_minimo_sinal = reserva.valor_previsto * Decimal('0.3')
        if valor_sinal < valor_minimo_sinal:
            raise ValidationError(
                f"Valor do sinal insuficiente. "
                f"Mínimo: R$ {valor_minimo_sinal:.2f}, "
                f"Informado: R$ {valor_sinal:.2f}"
            )
        
        # Verificar se não ultrapassa o valor total
        status_atual = self.calcular_status_financeiro(reserva_id)
        novo_total = Decimal(str(status_atual["valor_pago"])) + valor_sinal
        
        if novo_total > reserva.valor_previsto * Decimal('1.1'):  # Tolerância de 10%
            raise ValidationError("Valor excede o total da reserva em mais de 10%")
        
        # Criar pagamento
        pagamento_data = {
            "reserva_id": reserva_id,
            "valor": valor_sinal,
            "metodo_pagamento": metodo,
            "tipo": "SINAL",
            "observacoes": "Pagamento de sinal/entrada"
        }
        
        if dados_adicionais:
            pagamento_data.update(dados_adicionais)
        
        # Atualizar status da reserva baseado no novo status financeiro
        novo_status_financeiro = self._determinar_novo_status_financeiro(
            reserva.valor_previsto, novo_total
        )
        
        reserva.status_financeiro = novo_status_financeiro
        
        # Se sinal suficiente, confirmar reserva
        if novo_status_financeiro in [StatusFinanceiro.SINAL_PAGO, StatusFinanceiro.PAGO_TOTAL]:
            if reserva.status_reserva == StatusReserva.PENDENTE:
                reserva.status_reserva = StatusReserva.CONFIRMADA
        
        self.db.commit()
        
        return {
            "success": True,
            "pagamento": pagamento_data,
            "novo_status_financeiro": novo_status_financeiro.value,
            "novo_status_reserva": reserva.status_reserva.value,
            "valor_restante": float(reserva.valor_previsto - novo_total)
        }
    
    def processar_pagamento_restante(
        self, 
        reserva_id: int, 
        valor: Decimal, 
        metodo: MetodoPagamento
    ) -> Dict[str, Any]:
        """
        Processa pagamento do valor restante
        Usado tipicamente no check-in ou para quitar a reserva
        """
        status_atual = self.calcular_status_financeiro(reserva_id)
        
        if status_atual["status_financeiro"] == StatusFinanceiro.PAGO_TOTAL:
            raise BusinessRuleViolation("Reserva já está totalmente paga")
        
        valor_restante = Decimal(str(status_atual["valor_pendente"]))
        
        if valor > valor_restante * Decimal('1.05'):  # Tolerância de 5%
            raise ValidationError(
                f"Valor excede o restante da reserva. "
                f"Restante: R$ {valor_restante:.2f}, "
                f"Informado: R$ {valor:.2f}"
            )
        
        # Processar pagamento
        novo_total_pago = Decimal(str(status_atual["valor_pago"])) + valor
        
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        novo_status_financeiro = self._determinar_novo_status_financeiro(
            reserva.valor_previsto, novo_total_pago
        )
        
        reserva.status_financeiro = novo_status_financeiro
        self.db.commit()
        
        return {
            "success": True,
            "novo_status_financeiro": novo_status_financeiro.value,
            "valor_quitado": valor >= valor_restante,
            "valor_restante_apos": float(max(valor_restante - valor, 0))
        }
    
    def processar_caucao(
        self, 
        reserva_id: int, 
        valor_caucao: Decimal, 
        metodo: MetodoPagamento
    ) -> Dict[str, Any]:
        """
        Processa caução separadamente da hospedagem
        Caução não conta para quitação da reserva
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        if reserva.status_reserva not in [StatusReserva.CONFIRMADA, StatusReserva.HOSPEDADO]:
            raise BusinessRuleViolation(
                "Caução só pode ser cobrada em reservas confirmadas ou hospedadas"
            )
        
        # Registrar caução como item separado
        pagamento_caucao = {
            "reserva_id": reserva_id,
            "valor": valor_caucao,
            "metodo_pagamento": metodo,
            "tipo": "CAUCAO",
            "observacoes": "Caução - valor retornável"
        }
        
        return {
            "success": True,
            "caucao": pagamento_caucao,
            "valor_caucao": float(valor_caucao)
        }
    
    def _determinar_novo_status_financeiro(
        self, 
        valor_total: Decimal, 
        valor_pago: Decimal
    ) -> StatusFinanceiro:
        """Determina status financeiro baseado em valores"""
        percentual = (valor_pago / valor_total) * 100 if valor_total > 0 else 0
        
        if percentual >= 100:
            return StatusFinanceiro.PAGO_TOTAL
        elif percentual >= 30:
            return StatusFinanceiro.SINAL_PAGO
        else:
            return StatusFinanceiro.AGUARDANDO_PAGAMENTO
    
    def validar_regras_checkin_financeiro(self, reserva_id: int) -> Dict[str, Any]:
        """
        Valida se a reserva está financeiramente apta para check-in
        Regra: mínimo 80% do valor pago
        """
        status_financeiro = self.calcular_status_financeiro(reserva_id)
        
        pode_checkin = status_financeiro["pode_checkin"]
        
        if not pode_checkin:
            return {
                "pode_checkin": False,
                "motivo": "PAGAMENTO_INSUFICIENTE",
                "detalhes": (
                    f"Check-in requer 80% do valor pago. "
                    f"Pago: R$ {status_financeiro['valor_pago']:.2f} "
                    f"({status_financeiro['percentual_pago']:.1f}%) "
                    f"de R$ {status_financeiro['valor_reserva']:.2f}"
                ),
                "valor_minimo": status_financeiro["valor_minimo_checkin"],
                "valor_atual": status_financeiro["valor_pago"],
                "valor_necessario": status_financeiro["valor_minimo_checkin"] - status_financeiro["valor_pago"]
            }
        
        return {
            "pode_checkin": True,
            "status_financeiro": status_financeiro["status_financeiro"].value,
            "percentual_pago": status_financeiro["percentual_pago"]
        }
    
    def validar_regras_checkout_financeiro(self, reserva_id: int) -> Dict[str, Any]:
        """
        Valida se a reserva pode fazer check-out
        Regra: deve estar 100% quitada incluindo consumos
        """
        from app.services.checkout_service import CheckoutService
        checkout_service = CheckoutService(self.db)
        
        try:
            calculo = checkout_service._calcular_acerto_financeiro(reserva_id)
            
            saldo_devedor = calculo["saldo_devedor"]
            
            if saldo_devedor > 1.0:  # Tolerância de R$ 1,00
                return {
                    "pode_checkout": False,
                    "motivo": "SALDO_DEVEDOR",
                    "detalhes": f"Há saldo devedor de R$ {saldo_devedor:.2f}",
                    "valor_devedor": saldo_devedor,
                    "calculo_completo": calculo
                }
            
            return {
                "pode_checkout": True,
                "saldo_final": calculo["saldo"],
                "valor_total_final": calculo["valor_total_final"]
            }
            
        except Exception as e:
            return {
                "pode_checkout": False,
                "motivo": "ERRO_CALCULO",
                "detalhes": f"Erro ao calcular acerto: {str(e)}"
            }
    
    def obter_historico_financeiro(self, reserva_id: int) -> Dict[str, Any]:
        """
        Histórico completo financeiro da reserva
        """
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValidationError("Reserva não encontrada")
        
        # Todos os pagamentos (aprovados e pendentes)
        todos_pagamentos = self.db.query(Pagamento).filter(
            Pagamento.reserva_id == reserva_id
        ).order_by(Pagamento.created_at).all()
        
        historico = []
        for p in todos_pagamentos:
            historico.append({
                "data": p.created_at.isoformat(),
                "tipo": "PAGAMENTO",
                "descricao": f"{p.metodo_pagamento.value} - {p.status.value}",
                "valor": float(p.valor),
                "status": p.status.value
            })
        
        # Status financeiro atual
        status_atual = self.calcular_status_financeiro(reserva_id)
        
        return {
            "reserva_id": reserva_id,
            "codigo_reserva": reserva.codigo_reserva,
            "status_financeiro_atual": reserva.status_financeiro.value,
            "historico_pagamentos": historico,
            "resumo_atual": status_atual
        }
