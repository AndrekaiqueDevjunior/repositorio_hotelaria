"""
FRAUD DETECTION ORCHESTRATOR - Integração Anti-fraude + PaymentOrchestrator
Unifica validações de risco com fluxo de pagamentos

Arquitetura: Event-Driven + Strategy Pattern
- Risk Assessment: Análise de risco em tempo real
- Fraud Prevention: Bloqueio automático de transações suspeitas
- Manual Review: Fluxo para aprovação manual
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services.antifraude_service import AntifraaudeService
from app.services.payment_orchestrator import PaymentOrchestrator, PaymentRequest, PaymentResult, PaymentStatus
from app.repositories.pagamento_repo import PagamentoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.core.enums import StatusAntifraude
from app.utils.datetime_utils import now_utc


class RiskLevel(Enum):
    LOW = "BAIXO"
    MEDIUM = "MÉDIO"
    HIGH = "ALTO"
    CRITICAL = "CRÍTICO"


class FraudAction(Enum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"
    DELAY = "DELAY"


@dataclass
class RiskAssessment:
    """Value Object para avaliação de risco"""
    risk_level: RiskLevel
    score: int
    alerts: List[str]
    action: FraudAction
    reason: str
    requires_manual_review: bool = False
    delay_hours: int = 0


@dataclass
class FraudCheckResult:
    """Resultado da verificação anti-fraude"""
    passed: bool
    risk_assessment: RiskAssessment
    payment_allowed: bool
    message: str
    next_action: str


class FraudDetectionOrchestrator:
    """
    ORQUESTRADOR DE DETECÇÃO DE FRAUDES
    
    Responsabilidades:
    1. Integrar análise anti-fraude no fluxo de pagamento
    2. Aplicar regras de risco em tempo real
    3. Coordenar aprovações manuais
    4. Implementar delays de segurança
    """
    
    def __init__(
        self,
        payment_orchestrator: PaymentOrchestrator,
        pagamento_repo: PagamentoRepository,
        reserva_repo: ReservaRepository
    ):
        self.payment_orchestrator = payment_orchestrator
        self.pagamento_repo = pagamento_repo
        self.reserva_repo = reserva_repo
        
        # Configurações de risco
        self.risk_thresholds = {
            "auto_approve": 30,    # Score < 30: Aprovação automática
            "manual_review": 70,   # Score 30-69: Revisão manual
            "auto_block": 90       # Score >= 90: Bloqueio automático
        }
        
        # Delays por nível de risco
        self.risk_delays = {
            RiskLevel.MEDIUM: 2,   # 2 horas
            RiskLevel.HIGH: 24,    # 24 horas
            RiskLevel.CRITICAL: 72 # 72 horas
        }
    
    async def process_payment_with_fraud_check(self, request: PaymentRequest) -> PaymentResult:
        """
        MÉTODO PRINCIPAL: Processar pagamento com verificação anti-fraude
        
        Fluxo:
        1. Análise de risco pré-pagamento
        2. Decisão baseada no risco
        3. Processamento ou bloqueio
        4. Registro da operação anti-fraude
        """
        try:
            # 1. ANÁLISE DE RISCO PRÉ-PAGAMENTO
            fraud_check = await self._perform_fraud_check(request)
            
            # 2. REGISTRAR OPERAÇÃO ANTI-FRAUDE
            await self._log_fraud_operation(request, fraud_check)
            
            # 3. DECISÃO BASEADA NO RISCO
            if not fraud_check.payment_allowed:
                return PaymentResult(
                    success=False,
                    payment_id=0,
                    cielo_payment_id=None,
                    status=PaymentStatus.DENIED,
                    message=fraud_check.message
                )
            
            # 4. PROCESSAR PAGAMENTO SE APROVADO
            if fraud_check.risk_assessment.action == FraudAction.APPROVE:
                # Aprovação automática - processar normalmente
                return await self.payment_orchestrator.process_payment(request)
            
            elif fraud_check.risk_assessment.action == FraudAction.DELAY:
                # Delay de segurança - criar pagamento pendente
                return await self._create_delayed_payment(request, fraud_check)
            
            elif fraud_check.risk_assessment.action == FraudAction.REVIEW:
                # Revisão manual - criar pagamento pendente
                return await self._create_pending_payment(request, fraud_check)
            
            else:  # BLOCK
                return PaymentResult(
                    success=False,
                    payment_id=0,
                    cielo_payment_id=None,
                    status=PaymentStatus.DENIED,
                    message="Transação bloqueada por alto risco de fraude"
                )
                
        except Exception as e:
            return PaymentResult(
                success=False,
                payment_id=0,
                cielo_payment_id=None,
                status=PaymentStatus.DENIED,
                message=f"Erro na verificação anti-fraude: {str(e)}"
            )
    
    async def _perform_fraud_check(self, request: PaymentRequest) -> FraudCheckResult:
        """Realizar verificação completa anti-fraude"""
        try:
            # Obter dados da reserva
            reserva = await self.reserva_repo.get_by_id(request.reserva_id)
            cliente_id = reserva["cliente_id"]
            
            # Análise de risco do cliente
            client_analysis = await AntifraaudeService.analisar_cliente(cliente_id)
            
            # Análise de risco da reserva
            reservation_analysis = await AntifraaudeService.analisar_reserva(request.reserva_id)
            
            # Análise específica do pagamento
            payment_risk = await self._analyze_payment_risk(request, reserva)
            
            # Combinar scores
            total_score = 0
            all_alerts = []
            
            if client_analysis.get("success"):
                total_score += client_analysis.get("score", 0)
                all_alerts.extend(client_analysis.get("alertas", []))
            
            if reservation_analysis.get("success"):
                total_score += reservation_analysis.get("score", 0)
                all_alerts.extend(reservation_analysis.get("alertas", []))
            
            total_score += payment_risk["score"]
            all_alerts.extend(payment_risk["alerts"])
            
            # Determinar nível de risco e ação
            risk_assessment = self._determine_risk_action(total_score, all_alerts)
            
            # Verificar se pagamento é permitido
            payment_allowed = risk_assessment.action in [FraudAction.APPROVE, FraudAction.DELAY, FraudAction.REVIEW]
            
            return FraudCheckResult(
                passed=risk_assessment.action != FraudAction.BLOCK,
                risk_assessment=risk_assessment,
                payment_allowed=payment_allowed,
                message=self._get_risk_message(risk_assessment),
                next_action=risk_assessment.action.value
            )
            
        except Exception as e:
            # Em caso de erro, permitir pagamento mas registrar
            return FraudCheckResult(
                passed=True,
                risk_assessment=RiskAssessment(
                    risk_level=RiskLevel.LOW,
                    score=0,
                    alerts=[f"Erro na análise: {str(e)}"],
                    action=FraudAction.APPROVE,
                    reason="Erro no sistema anti-fraude - aprovação por segurança"
                ),
                payment_allowed=True,
                message="Pagamento aprovado (sistema anti-fraude indisponível)",
                next_action="APPROVE"
            )
    
    async def _analyze_payment_risk(self, request: PaymentRequest, reserva: Dict[str, Any]) -> Dict[str, Any]:
        """Análise específica de risco do pagamento"""
        score = 0
        alerts = []
        
        # Valor muito alto para o método
        if request.metodo.value == "pix" and request.valor > 2000:
            score += 20
            alerts.append(f"PIX de valor alto: R$ {request.valor:.2f}")
        
        if request.metodo.value in ["credit_card", "debit_card"] and request.valor > 5000:
            score += 15
            alerts.append(f"Cartão de valor alto: R$ {request.valor:.2f}")
        
        # Horário suspeito (madrugada)
        hora_atual = now_utc().hour
        if hora_atual >= 2 and hora_atual <= 5:
            score += 10
            alerts.append("Transação em horário suspeito (madrugada)")
        
        # Muitas parcelas
        if request.parcelas and request.parcelas > 6:
            score += 10
            alerts.append(f"Muitas parcelas: {request.parcelas}x")
        
        # Check-in muito próximo (mesmo dia)
        if reserva.get("checkin"):
            checkin_date = datetime.fromisoformat(reserva["checkin"].replace("Z", "+00:00"))
            if (checkin_date.date() - now_utc().date()).days <= 0:
                score += 15
                alerts.append("Check-in no mesmo dia da reserva")
        
        return {
            "score": score,
            "alerts": alerts
        }
    
    def _determine_risk_action(self, score: int, alerts: List[str]) -> RiskAssessment:
        """Determinar ação baseada no score de risco"""
        if score >= self.risk_thresholds["auto_block"]:
            return RiskAssessment(
                risk_level=RiskLevel.CRITICAL,
                score=score,
                alerts=alerts,
                action=FraudAction.BLOCK,
                reason="Score de risco crítico - transação bloqueada",
                requires_manual_review=True
            )
        
        elif score >= self.risk_thresholds["manual_review"]:
            return RiskAssessment(
                risk_level=RiskLevel.HIGH,
                score=score,
                alerts=alerts,
                action=FraudAction.DELAY,
                reason="Score de risco alto - delay de segurança aplicado",
                requires_manual_review=True,
                delay_hours=self.risk_delays[RiskLevel.HIGH]
            )
        
        elif score >= self.risk_thresholds["auto_approve"]:
            return RiskAssessment(
                risk_level=RiskLevel.MEDIUM,
                score=score,
                alerts=alerts,
                action=FraudAction.REVIEW,
                reason="Score de risco médio - revisão recomendada",
                requires_manual_review=True,
                delay_hours=self.risk_delays[RiskLevel.MEDIUM]
            )
        
        else:
            return RiskAssessment(
                risk_level=RiskLevel.LOW,
                score=score,
                alerts=alerts,
                action=FraudAction.APPROVE,
                reason="Score de risco baixo - aprovação automática"
            )
    
    def _get_risk_message(self, assessment: RiskAssessment) -> str:
        """Gerar mensagem baseada na avaliação de risco"""
        messages = {
            FraudAction.APPROVE: "Pagamento aprovado - risco baixo",
            FraudAction.REVIEW: f"Pagamento em revisão - risco {assessment.risk_level.value.lower()}. Aguarde aprovação manual.",
            FraudAction.DELAY: f"Pagamento em análise - delay de {assessment.delay_hours}h por segurança",
            FraudAction.BLOCK: f"Pagamento bloqueado - risco {assessment.risk_level.value.lower()}"
        }
        
        message = messages.get(assessment.action, "Status desconhecido")
        
        if assessment.alerts:
            message += f" | Alertas: {', '.join(assessment.alerts[:3])}"
        
        return message
    
    async def _create_delayed_payment(self, request: PaymentRequest, fraud_check: FraudCheckResult) -> PaymentResult:
        """Criar pagamento com delay de segurança"""
        # TODO: Implementar sistema de agendamento
        # Por ora, criar como pendente com flag de delay
        
        return PaymentResult(
            success=False,
            payment_id=0,
            cielo_payment_id=None,
            status=PaymentStatus.PENDING,
            message=f"Pagamento em análise - delay de {fraud_check.risk_assessment.delay_hours}h aplicado"
        )
    
    async def _create_pending_payment(self, request: PaymentRequest, fraud_check: FraudCheckResult) -> PaymentResult:
        """Criar pagamento pendente para revisão manual"""
        # TODO: Implementar fila de revisão manual
        
        return PaymentResult(
            success=False,
            payment_id=0,
            cielo_payment_id=None,
            status=PaymentStatus.PENDING,
            message="Pagamento aguardando aprovação manual da equipe de segurança"
        )
    
    async def _log_fraud_operation(self, request: PaymentRequest, fraud_check: FraudCheckResult):
        """Registrar operação anti-fraude"""
        try:
            # Obter dados da reserva
            reserva = await self.reserva_repo.get_by_id(request.reserva_id)
            
            # TODO: Implementar log estruturado
            log_data = {
                "reserva_id": request.reserva_id,
                "cliente_id": reserva["cliente_id"],
                "valor": request.valor,
                "metodo": request.metodo.value,
                "risk_score": fraud_check.risk_assessment.score,
                "risk_level": fraud_check.risk_assessment.risk_level.value,
                "action": fraud_check.risk_assessment.action.value,
                "alerts": fraud_check.risk_assessment.alerts,
                "timestamp": now_utc().isoformat()
            }
            
            print(f"[FRAUD-LOG] {log_data}")
            
        except Exception as e:
            print(f"Erro ao registrar operação anti-fraude: {e}")
    
    async def approve_manual_payment(self, payment_id: int, approved_by: int) -> PaymentResult:
        """Aprovar pagamento manualmente após revisão"""
        try:
            # Obter dados do pagamento
            pagamento = await self.pagamento_repo.get_by_id(payment_id)
            
            if pagamento["status"] != "PENDENTE":
                return PaymentResult(
                    success=False,
                    payment_id=payment_id,
                    cielo_payment_id=None,
                    status=PaymentStatus.DENIED,
                    message="Pagamento não está pendente de aprovação"
                )
            
            # Recriar request para processar
            # TODO: Implementar storage de requests pendentes
            
            # Por ora, atualizar status diretamente
            await self.pagamento_repo.update_status(payment_id, "APROVADO")
            
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                cielo_payment_id=pagamento.get("cielo_payment_id"),
                status=PaymentStatus.APPROVED,
                message=f"Pagamento aprovado manualmente por usuário {approved_by}"
            )
            
        except Exception as e:
            return PaymentResult(
                success=False,
                payment_id=payment_id,
                cielo_payment_id=None,
                status=PaymentStatus.DENIED,
                message=f"Erro ao aprovar pagamento: {str(e)}"
            )
    
    async def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """Obter lista de pagamentos pendentes de revisão"""
        try:
            # Buscar pagamentos pendentes
            # TODO: Implementar filtro específico para revisão anti-fraude
            
            return []
            
        except Exception as e:
            print(f"Erro ao buscar revisões pendentes: {e}")
            return []


# FACTORY FUNCTION
def create_fraud_detection_orchestrator() -> FraudDetectionOrchestrator:
    """Factory para criar instância do orquestrador anti-fraude"""
    from app.services.payment_orchestrator import create_payment_orchestrator
    from app.repositories.pagamento_repo import PagamentoRepository
    from app.repositories.reserva_repo import ReservaRepository
    from app.db.database import get_db
    
    db = get_db()
    payment_orchestrator = create_payment_orchestrator()
    pagamento_repo = PagamentoRepository(db)
    reserva_repo = ReservaRepository(db)
    
    return FraudDetectionOrchestrator(
        payment_orchestrator=payment_orchestrator,
        pagamento_repo=pagamento_repo,
        reserva_repo=reserva_repo
    )
